# Speech-to-Speech Podcast Pipeline

Turn a long podcast recording into **new audio spoken in the same (cloned)
voice**. The pipeline:

```
data/raw/  ──▶  Whisper (ASR)  ──▶  transcript (.txt/.srt)  ──▶  XTTS v2 (voice clone)  ──▶  outputs/audio/
                                          ▲
     auto-extracted reference.wav  ───────┘  (6-10s clean clip from the podcast)
```

> **100% free and local.** Both models (OpenAI Whisper and Coqui XTTS v2) are
> open-source and run on your own machine. **No paid API keys are required
> anywhere in this project.** (An optional free Hugging Face token is only ever
> needed for gated models, which this project does not use by default.)

---

## What it does

1. **Extract reference voice** — you don't need a separate voice sample. The
   code auto-detects a clean, single-speaker 6-10 second segment from your
   40-minute podcast in `data/raw/` and saves it to
   `data/reference_voices/reference.wav`.
2. **Transcribe** — Whisper converts the podcast to text with timestamps and
   writes `.txt` + `.srt` into `outputs/transcripts/` (optional translate-to-English).
3. **Clone & generate** — XTTS v2 speaks the transcript (or any custom text) in
   the cloned voice and saves audio to `outputs/audio/`.

---

## Project layout

```
project_root/
├── data/
│   ├── raw/                 # put your podcast audio here
│   └── reference_voices/    # reference.wav is auto-generated here
├── outputs/
│   ├── audio/               # generated cloned audio
│   ├── logs/                # run logs
│   └── transcripts/         # .txt / .srt transcripts
├── shared/
│   ├── config.py            # .env loader + all paths/settings
│   ├── utils.py             # logging + extract_reference_clip()
│   └── pipeline.py          # orchestration (extract -> whisper -> xtts)
├── whisper_module/          # ASR (Developer B)
│   ├── src/transcribe.py
│   ├── models/              # cached Whisper weights (gitignored)
│   └── requirements.txt
├── xtts_module/             # TTS / voice cloning (Developer A)
│   ├── src/clone_and_generate.py
│   ├── models/              # cached XTTS weights (gitignored)
│   └── requirements.txt
├── main.py                  # CLI entry point
├── requirements.txt         # shared deps (pydub, librosa, soundfile, dotenv)
├── .env.example             # copy to .env
└── README.md
```

---

## Team split

| Developer | Owns | Works in |
|-----------|------|----------|
| **You (A)** | Voice cloning / TTS | `xtts_module/` |
| **Friend (B)** | Transcription / ASR | `whisper_module/` |
| Shared | Config, utils, orchestration | `shared/` |

---

## Setup

### 0. Prerequisites
- **Python 3.9-3.11** (Coqui TTS supports these best)
- **FFmpeg** installed and on your PATH (required by Whisper and pydub):
  - Windows: `winget install Gyan.FFmpeg`
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt install ffmpeg`

### 1. Get the code and configure
```bash
git clone <your-repo-url>
cd project_root
copy .env.example .env        # Windows   (cp .env.example .env on macOS/Linux)
```
Then edit `.env` if needed (model size, language, `DEVICE=cuda` if you have a GPU).

### 2. Install dependencies

You can use one shared environment for everything:
```bash
python -m venv .venv
.venv\Scripts\activate                       # Windows
# source .venv/bin/activate                  # macOS/Linux

pip install -r requirements.txt              # shared deps
pip install -r whisper_module/requirements.txt
pip install -r xtts_module/requirements.txt
```

> Running the **full pipeline** via `main.py` needs both modules installed in
> the same environment (the orchestrator imports both). If you only work on one
> module, you can install just that module's `requirements.txt`.

### 3. Add your audio
Drop your 40-minute podcast file into `data/raw/` (e.g. `data/raw/podcast.mp3`).

---

## Running

### Full pipeline
```bash
python main.py --step all
python main.py --step all --translate      # transcript translated to English
python main.py --step all --streaming      # XTTS streaming generation
```

### One stage at a time
```bash
python main.py --step extract      # build data/reference_voices/reference.wav
python main.py --step whisper      # transcribe -> outputs/transcripts/
python main.py --step xtts         # generate cloned audio -> outputs/audio/
```

### Run a module independently
```bash
# Whisper only (Developer B)
python whisper_module/src/transcribe.py --model base

# XTTS only (Developer A) — auto-extracts reference if missing
python xtts_module/src/clone_and_generate.py --text "Hello from the podcast"
```

---

## Notes
- First XTTS run downloads the model weights (cached locally); subsequent runs
  are faster.
- On CPU, larger Whisper models and long transcripts take time — start with
  `WHISPER_MODEL_SIZE=base` and set `DEVICE=cuda` if you have an NVIDIA GPU.
- Large files (audio, models, logs) are gitignored; only code and empty-folder
  `.gitkeep` placeholders are committed.
