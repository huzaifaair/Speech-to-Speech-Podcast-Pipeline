# Whisper Module (ASR / Transcription)

**Owner:** Developer B · Open-source · Local · Free (no paid API)

Transcribes the podcast audio in `data/raw/` into text using
[`openai-whisper`](https://github.com/openai/whisper), and writes `.txt` and
`.srt` (subtitles with timestamps) into `outputs/transcripts/`. Can optionally
translate speech to English.

## Files
```
whisper_module/
├── src/transcribe.py    # transcription logic (transcribe_audio())
├── models/              # cached Whisper weights (gitignored)
└── requirements.txt     # openai-whisper, torch, python-dotenv
```

## Setup
```bash
# from project_root, with your virtual environment active
pip install -r whisper_module/requirements.txt
```
Requires **FFmpeg** on your PATH.

## Run independently
```bash
# default: first file in data/raw/, model size from .env (base)
python whisper_module/src/transcribe.py

# choose model + input, translate to English
python whisper_module/src/transcribe.py --model small --input data/raw/podcast.mp3 --translate
```

CLI flags: `--input`, `--model` (tiny|base|small|medium|large-v3),
`--language`, `--translate`, `--output`.

## Import it
```python
from whisper_module.src.transcribe import transcribe_audio
result = transcribe_audio(model_size="base", translate=False)
```

## Output
- `outputs/transcripts/<name>.txt` — plain transcript
- `outputs/transcripts/<name>.srt` — subtitles with timestamps
- progress/errors logged to `outputs/logs/pipeline.log`

Configuration (`WHISPER_MODEL_SIZE`, `DEVICE`) comes from `.env` via
`shared/config.py`.
