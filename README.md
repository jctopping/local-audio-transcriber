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

* Create a virtual environment
* Install dependencies
* Copy `.env.sample` to `.env`

---

### 3. Add Your Hugging Face Token

1. Create a free account: [huggingface.co](https://huggingface.co)
2. Generate a token: [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
3. Accept the model terms for:

   * [pyannote/speaker-diarization](https://huggingface.co/pyannote/speaker-diarization)
   * [pyannote/segmentation](https://huggingface.co/pyannote/segmentation)
   * [pyannote/embedding](https://huggingface.co/pyannote/embedding)
4. Open the `.env` file created during setup and paste your token:

```env
HUGGINGFACE_TOKEN=your_token_here
```

---

## How to Use

```bash
python local_audio_transcriber.py <input_audio_file> [--force] [--srt]
```

### Options

| Flag      | Description                                            |
| --------- | ------------------------------------------------------ |
| `--force` | Force reprocessing even if cached transcription exists |
| `--srt`   | Generate `.srt` subtitle file in addition to `.txt`    |

### Example

```bash
python local_audio_transcriber.py "interview.m4a" --srt
```

---

## Output Files

For `interview.m4a`, you'll get:

| File                                       | Description                                |
| ------------------------------------------ | ------------------------------------------ |
| `interview_<hash>.wav`                     | Converted audio file                       |
| `interview_<hash>_whisper_transcript.json` | Whisper transcription cache                |
| `interview_<hash>_diarized_transcript.txt` | Speaker-labeled transcript with timestamps |
| `interview_<hash>_diarized_transcript.srt` | Subtitles (if `--srt` is used)             |

---

## Project Structure

```
local-audio-transcriber/
├── local_audio_transcriber.py   # Main script
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

**ImportError: `Pipeline` not found**
You're likely using `pyannote.audio >= 2.0`. Downgrade to the supported version:

```bash
pip install pyannote.audio==1.1.1
```

**torch install fails**
Use a compatible version for `pyannote.audio==1.1.1`:

```bash
pip install torch==1.13.1+cpu -f https://download.pytorch.org/whl/torch_stable.html
```

---

## Credits

* [Whisper](https://github.com/openai/whisper) by OpenAI
* [pyannote.audio](https://github.com/pyannote/pyannote-audio) by Hervé Bredin
* Inspired by and built for the open-source community

---

## License

MIT License