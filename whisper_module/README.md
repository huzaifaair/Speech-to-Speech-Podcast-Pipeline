# Whisper Module (ASR / Transcription)

**Owner:** Developer B

This module handles **Automatic Speech Recognition (ASR)**. It takes a raw
podcast audio file and produces a text transcript with timestamps, and can
optionally translate the transcript into another language.

## Responsibilities
- Load a podcast audio file from `../data/raw/`
- Transcribe speech to text using Whisper (with word/segment timestamps)
- Optionally translate the transcript to a target language
- Write results to `../outputs/transcripts/`

## Structure
```
whisper_module/
├── src/
│   ├── transcribe.py   # Core transcription logic
│   └── translate.py    # Optional translation step
├── models/             # Cached Whisper model weights (gitignored)
├── requirements.txt    # Module-specific dependencies
└── README.md
```

## Setup
```bash
# From the whisper_module folder, using a dedicated virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
```

> **Note:** Whisper requires `ffmpeg` installed on your system.
> Windows: `winget install Gyan.FFmpeg` — macOS: `brew install ffmpeg`

## Usage
```bash
python src/transcribe.py --input ../data/raw/podcast.mp3 --model small
```

## Output
A transcript is written to `../outputs/transcripts/` as both a `.txt` file and
a `.json` file (the JSON includes timestamps used by the pipeline downstream).
