# Local Audio Transcriber

A lightweight, offline-friendly tool to transcribe audio and automatically label speakers using OpenAI's Whisper and pyannote.audio.

---

## Purpose

Most transcription tools struggle with:
- No speaker attribution
- Poor performance on noisy or long recordings
- Reliance on cloud uploads or APIs

**Local Audio Transcriber** solves that by combining:

- [Whisper](https://github.com/openai/whisper) for accurate, local transcription
- [pyannote.audio](https://github.com/pyannote/pyannote-audio) for speaker diarization

It runs entirely on your machine after setup — with no recurring fees or privacy trade-offs.

---

## Features

- Accepts `.m4a`, `.mp3`, `.wav`, and more
- Converts audio to `.wav` using `ffmpeg`
- Transcribes with Whisper
- Labels speakers using Hugging Face's diarization model
- Outputs:
  - Speaker-labeled `.txt` transcript
  - Optional `.srt` subtitle file
- Caches output to avoid recomputation
- Supports `--srt` and `--force` command-line flags

---

## Requirements

- Python 3.9 or newer
- `ffmpeg` installed on your system
- Hugging Face access token (for diarization models)

---

## Installation

### 1. Install `ffmpeg`

**macOS:**
```bash
brew install ffmpeg
````

**Linux:**

```bash
sudo apt install ffmpeg
```

**Windows:**
[Download and install `ffmpeg`](https://ffmpeg.org/download.html), and add it to your system PATH.

---

### 2. Clone and Set Up the Project

```bash
git clone https://github.com/your-username/local-audio-transcriber.git
cd local-audio-transcriber
```

Run the platform-specific setup script:

**macOS/Linux:**

```bash
./setup.sh
```

**Windows:**

```cmd
setup.bat
```

This will:

* Detect your GPU (AMD via ROCm, NVIDIA via CUDA, otherwise CPU) and install the matching PyTorch build
  (override with `TORCH=rocm|cuda|cpu ./setup.sh`)
* Create a virtual environment and install dependencies (uses `uv` if available)
* Copy `.env.sample` to `.env` if you don't already have one

On Windows, `setup.bat` installs the CPU build by default; set `TORCH_INDEX` to a CUDA index to use an NVIDIA GPU.

---

### 3. Add Your Hugging Face Token

1. Create a free account: [huggingface.co](https://huggingface.co)
2. Generate a token: [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
3. Accept the model terms for:

   * [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)
   * [pyannote/segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0)
4. Open the `.env` file created during setup and paste your token:

```env
HUGGINGFACE_TOKEN=your_token_here
```

---

## How to Use

```bash
diarize_env/bin/python local-audio-transcriber.py <input_audio_file> [--force] [--srt]
```

The Whisper model defaults to `turbo`; pick another with e.g. `WHISPER_MODEL=medium`.

### Options

| Flag      | Description                                            |
| --------- | ------------------------------------------------------ |
| `--force` | Force reprocessing even if cached transcription exists |
| `--srt`   | Generate `.srt` subtitle file in addition to `.txt`    |

### Example

```bash
python local-audio-transcriber.py "interview.m4a" --srt
```

---

## Output Files

For `interview.m4a`, you'll get:

| File                                       | Description                                |
| ------------------------------------------ | ------------------------------------------ |
| `interview_<hash>.wav`                     | Converted audio file                       |
| `interview_<hash>_whisper_<model>_transcript.json` | Whisper transcription cache (model set via `WHISPER_MODEL`, default `turbo`) |
| `interview_<hash>_diarized_transcript.txt` | Speaker-labeled transcript with timestamps |
| `interview_<hash>_diarized_transcript.srt` | Subtitles (if `--srt` is used)             |

---

## Project Structure

```
local-audio-transcriber/
├── local-audio-transcriber.py   # Main script
├── .env                         # Hugging Face token (not committed)
├── .env.sample                  # Template for creating .env
├── setup.sh                     # Installer for macOS/Linux
├── setup.bat                    # Installer for Windows
├── requirements.txt             # Python dependencies
├── .gitignore                   # Ignore cache, .env, and venv
├── README.md                    # Project documentation
└── sample_audio/                # Optional test files
```

---

## Troubleshooting

**`Failed to load diarization model`**
Your Hugging Face token is missing or you haven't accepted the terms for both models listed in step 3.

**AMD GPU not used (`Using device: cpu`)**
Re-run `TORCH=rocm ./setup.sh`. Your user needs access to `/dev/kfd` and `/dev/dri/renderD*`.
The first GPU run is slower while MIOpen builds its kernel cache in `~/.cache/miopen`.

**`amdgpu.ids: No such file or directory`**
Harmless; it's only the lookup for the GPU's marketing name.

---

## Credits

* [Whisper](https://github.com/openai/whisper) by OpenAI
* [pyannote.audio](https://github.com/pyannote/pyannote-audio) by Hervé Bredin
* Inspired by and built for the open-source community

---

## License

MIT License