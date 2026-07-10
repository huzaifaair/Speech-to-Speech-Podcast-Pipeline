# XTTS v2 Module (TTS / Voice Cloning)

**Owner:** Developer A

This module handles **Text-to-Speech (TTS) with voice cloning** using
**XTTS v2** (Coqui TTS). It takes text (produced by the Whisper module) plus a
short reference audio sample, and generates speech in the cloned voice.

## Responsibilities
- Load text (from `../outputs/transcripts/` or passed by the pipeline)
- Load a reference voice sample from `../data/reference_voices/`
- Generate cloned speech with XTTS v2
- Write the final audio to `../outputs/audio/`

## Structure
```
xtts_module/
├── src/
│   ├── clone_voice.py   # Load reference sample + prepare speaker latents
│   └── synthesize.py    # Generate speech from text in the cloned voice
├── models/              # Cached XTTS v2 model weights (gitignored)
├── requirements.txt     # Module-specific dependencies
└── README.md
```

## Setup
```bash
# From the xtts_module folder, using a dedicated virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
```

> **Note:** XTTS v2 downloads a large model on first run. It is cached into
> `models/` and ignored by git. Coqui may prompt to accept its model license.

## Usage
```bash
python src/synthesize.py \
  --text "Hello from our software house podcast" \
  --speaker ../data/reference_voices/host.wav \
  --output ../outputs/audio/episode01.wav \
  --language en
```

## Output
Generated audio (`.wav`) is written to `../outputs/audio/`.
