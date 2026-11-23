import os
import sys
import json
import time
import datetime
import hashlib
from pathlib import Path
import torch
import whisper
from tqdm import tqdm
from pyannote.audio import Pipeline
from pyannote.audio.core.task import Specifications, Problem, Resolution
import ffmpeg
from dotenv import load_dotenv

# torch >= 2.6 only unpickles allowlisted classes; these are the ones pyannote checkpoints contain.
torch.serialization.add_safe_globals([torch.torch_version.TorchVersion, Specifications, Problem, Resolution])

# --------------------------- Load Environment --------------------------- #

load_dotenv()
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
if not HUGGINGFACE_TOKEN:
    print("Error: Hugging Face token not found. Please define it in a .env file.")
    sys.exit(1)


# --------------------------- Configuration --------------------------- #

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "turbo")
DIARIZATION_MODEL = "pyannote/speaker-diarization-3.1"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")  # ROCm GPUs also show up as "cuda"

# --------------------------- Argument Parsing --------------------------- #

if len(sys.argv) < 2:
    print("Usage: python local-audio-transcriber.py <input_audio_file> [--force] [--srt]")
    sys.exit(1)

input_file = Path(sys.argv[1])
force = "--force" in sys.argv
export_srt = "--srt" in sys.argv

if not input_file.exists():
    print(f"Error: File not found – {input_file}")
    sys.exit(1)

# --------------------------- Utility: File Hash --------------------------- #

def file_hash(path, block_size=65536):
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(block_size):
            hasher.update(chunk)
    return hasher.hexdigest()[:12]  # Shorten to 12 characters for brevity

# --------------------------- File Conversion --------------------------- #

converted_wav = input_file.with_suffix(".wav")
if input_file.suffix.lower() != ".wav":
    print(f"Converting {input_file.name} to WAV format...")
    try:
        ffmpeg.input(str(input_file)).output(str(converted_wav), ac=1, ar=16000).run(quiet=True, overwrite_output=True)
        print(f"Converted to: {converted_wav}")
    except Exception as e:
        print(f"Error during ffmpeg conversion: {e}")
        sys.exit(1)
else:
    converted_wav = input_file

# --------------------------- Output File Naming --------------------------- #

hash_id = file_hash(input_file)
base_name = input_file.stem
prefix = f"{base_name}_{hash_id}"

transcript_json = input_file.parent / f"{prefix}_whisper_{WHISPER_MODEL}_transcript.json"
final_transcript_txt = input_file.parent / f"{prefix}_diarized_transcript.txt"
srt_output = input_file.parent / f"{prefix}_diarized_transcript.srt"

# --------------------------- Whisper Transcription --------------------------- #

print(f"Using device: {DEVICE}" + (f" ({torch.cuda.get_device_name(0)})" if DEVICE.type == "cuda" else ""))
print("Loading Whisper model...")
start_time = time.time()
whisper_model = whisper.load_model(WHISPER_MODEL, device=DEVICE)
print(f"Whisper model loaded in {time.time() - start_time:.1f} seconds")

if transcript_json.exists() and not force:
    print(f"Using cached transcription: {transcript_json}")
    with open(transcript_json, "r", encoding="utf-8") as f:
        result = json.load(f)
else:
    print("Running Whisper transcription...")
    start_time = time.time()
    result = whisper_model.transcribe(str(converted_wav))
    with open(transcript_json, "w", encoding="utf-8") as f:
        json.dump(result, f)
    print(f"Transcription completed and saved in {time.time() - start_time:.1f} seconds")

# --------------------------- Hallucination Cleanup --------------------------- #

def clean_segments(segments, audio_duration, max_repeats=2):
    """Drop Whisper's typical hallucinations: segments starting past the end of the
    audio, and runs of identical consecutive lines (e.g. "Oh." x20 over trailing
    music or laughter), keeping at most `max_repeats` of each run."""
    cleaned, run_text, run_len = [], None, 0
    for seg in segments:
        if seg["start"] >= audio_duration:
            continue
        text = seg["text"].strip().lower()
        run_len = run_len + 1 if text == run_text else 1
        run_text = text
        if run_len <= max_repeats:
            cleaned.append(seg)
    return cleaned

audio_duration = whisper.audio.load_audio(str(converted_wav)).shape[0] / whisper.audio.SAMPLE_RATE
n_before = len(result["segments"])
result["segments"] = clean_segments(result["segments"], audio_duration)
if len(result["segments"]) < n_before:
    print(f"Removed {n_before - len(result['segments'])} repeated/out-of-range segments (likely hallucinations)")

# --------------------------- Pyannote Diarization --------------------------- #

print("Loading speaker diarization pipeline...")
try:
    pipeline = Pipeline.from_pretrained(DIARIZATION_MODEL, use_auth_token=HUGGINGFACE_TOKEN)
    if pipeline is None:
        raise RuntimeError("access denied (gated model)")
except Exception as e:
    print("Failed to load diarization model. Make sure you've accepted model access:")
    print(" - https://huggingface.co/pyannote/speaker-diarization-3.1")
    print(" - https://huggingface.co/pyannote/segmentation-3.0")
    print(f"Error: {e}")
    sys.exit(1)
pipeline.to(DEVICE)

if DEVICE.type == "cuda" and torch.version.hip:
    # On ROCm, MIOpen's LSTM JIT-compiles a dropout kernel that needs the rocrand
    # headers installed system-wide. Run the segmentation LSTM on PyTorch's native
    # GPU implementation instead (only ~1s per 5 min of audio, so no real cost).
    def _disable_miopen(module, args):
        module._miopen_off = torch.backends.cudnn.flags(enabled=False)
        module._miopen_off.__enter__()

    def _restore_miopen(module, args, output):
        module._miopen_off.__exit__(None, None, None)

    for m in pipeline._segmentation.model.modules():
        if isinstance(m, torch.nn.LSTM):
            m.register_forward_pre_hook(_disable_miopen)
            m.register_forward_hook(_restore_miopen)

print("Running diarization...")
start_time = time.time()
diarization = pipeline(str(converted_wav))
print(f"Diarization completed in {time.time() - start_time:.1f} seconds")

# --------------------------- Output Alignment --------------------------- #

def format_time(seconds):
    return str(datetime.timedelta(seconds=int(seconds)))[2:]

def format_srt_timestamp(seconds):
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

print("Aligning transcript with diarization...")
speaker_segments = []
for turn, _, speaker in tqdm(diarization.itertracks(yield_label=True), desc="Speaker Segments"):
    speaker_segments.append({
        "start": turn.start,
        "end": turn.end,
        "speaker": speaker
    })

def pick_speaker(start, end):
    """Speaker with the most overlap with [start, end]; nearest turn if none overlap."""
    best, best_overlap = None, 0.0
    for seg in speaker_segments:
        overlap = min(end, seg["end"]) - max(start, seg["start"])
        if overlap > best_overlap:
            best, best_overlap = seg["speaker"], overlap
    if best is None and speaker_segments:
        nearest = min(speaker_segments,
                      key=lambda seg: min(abs(start - seg["end"]), abs(seg["start"] - end)))
        best = nearest["speaker"]
    return best or "UNKNOWN"

aligned_output = []
for segment in tqdm(result['segments'], desc="Merging Segments"):
    start, end = segment['start'], segment['end']
    aligned_output.append({
        "speaker": pick_speaker(start, end),
        "timestamp": format_time(start),
        "start": start,
        "end": end,
        "text": segment['text'].strip()
    })

# Save to plain text
with open(final_transcript_txt, "w", encoding="utf-8") as f:
    for line in aligned_output:
        f.write(f"[{line['speaker']}] {line['timestamp']} – {line['text']}\n")
print(f"Transcript saved to: {final_transcript_txt}")

# Save to SRT format
if export_srt:
    print("Generating SRT file...")
    with open(srt_output, "w", encoding="utf-8") as f:
        for idx, entry in enumerate(aligned_output, 1):
            f.write(f"{idx}\n")
            f.write(f"{format_srt_timestamp(entry['start'])} --> {format_srt_timestamp(entry['end'])}\n")
            f.write(f"{entry['speaker']}: {entry['text']}\n\n")
    print(f"SRT file saved to: {srt_output}")