# XTTS v2 Module (TTS / Voice Cloning)

**Owner:** Developer A · Open-source (Coqui TTS) · Local · Free (no paid API)

Generates speech in a **cloned voice** using
[XTTS v2](https://github.com/coqui-ai/TTS). It reads text (from the latest
transcript in `outputs/transcripts/` or custom input), clones the voice from
`data/reference_voices/reference.wav`, and writes audio to `outputs/audio/`.

If the reference clip does not exist yet, this module **automatically triggers**
`shared/utils.extract_reference_clip()` to carve a clean 6-10s single-speaker
clip out of the podcast in `data/raw/`.

## Files
```
xtts_module/
├── src/clone_and_generate.py   # generate_speech() + generate_speech_streaming()
├── models/                     # cached XTTS weights (gitignored)
└── requirements.txt            # TTS (coqui-tts), torch, python-dotenv
```

## Setup
```bash
# from project_root, with your virtual environment active
pip install -r xtts_module/requirements.txt
```
> First run downloads the XTTS v2 model (cached locally). The Coqui license is
> auto-accepted for local/personal use via `COQUI_TOS_AGREED=1`.

## Run independently
```bash
# speak the latest transcript in the cloned voice
python xtts_module/src/clone_and_generate.py

# speak custom text
python xtts_module/src/clone_and_generate.py --text "Hello from our podcast"

# streaming generation
python xtts_module/src/clone_and_generate.py --streaming --text "Hi there"
```

CLI flags: `--text`, `--text-file`, `--reference`, `--output`, `--language`,
`--streaming`.

## Import it
```python
from xtts_module.src.clone_and_generate import generate_speech, generate_speech_streaming

generate_speech(text="Hello world")                 # non-streaming -> outputs/audio/
generate_speech_streaming(text="Hello world")       # streaming (chunked)
```

## Output
- `outputs/audio/generated.wav` (non-streaming)
- `outputs/audio/generated_streaming.wav` (streaming)

Configuration (`XTTS_LANGUAGE`, `DEVICE`) comes from `.env` via
`shared/config.py`.
