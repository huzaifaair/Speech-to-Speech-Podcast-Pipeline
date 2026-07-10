# Speech-to-Speech Podcast Pipeline

A modular **Speech-to-Speech AI pipeline** for processing our software house
podcast. It transcribes raw podcast audio, optionally translates it, and then
regenerates the audio in a **cloned voice**.

```
Raw audio  ──▶  Whisper (ASR)  ──▶  Text + timestamps  ──▶  XTTS v2 (voice clone)  ──▶  Final audio
```

---

## Project Overview

| Stage | Tool | What it does |
|-------|------|--------------|
| 1. Transcription | **Whisper** | Converts podcast audio to text with timestamps; optional translation |
| 2. Voice cloning | **XTTS v2** | Generates speech from that text using a cloned voice from a reference sample |
| Orchestration | **shared/pipeline.py** | Connects both modules into one end-to-end flow |

The two modules are **fully independent** (own dependencies, code, models,
outputs) so two developers can work in parallel without merge conflicts, yet
they connect cleanly through the `shared` pipeline.

---

## Folder Structure

```
Project/
├── whisper_module/          # ASR / transcription (Developer B)
│   ├── src/
│   │   ├── transcribe.py
│   │   └── translate.py
│   ├── models/              # cached Whisper weights (gitignored)
│   ├── requirements.txt
│   └── README.md
├── xtts_module/             # TTS / voice cloning (Developer A)
│   ├── src/
│   │   ├── clone_voice.py
│   │   └── synthesize.py
│   ├── models/              # cached XTTS v2 weights (gitignored)
│   ├── requirements.txt
│   └── README.md
├── shared/                  # common code that links both modules
│   ├── config.py            # central paths & settings
│   ├── utils.py             # logging & helpers
│   └── pipeline.py          # end-to-end orchestration
├── data/
│   ├── raw/                 # input podcast audio (gitignored)
│   └── reference_voices/    # voice samples for cloning (gitignored)
├── outputs/
│   ├── transcripts/         # generated transcripts (gitignored)
│   ├── audio/               # generated cloned audio (gitignored)
│   └── logs/                # run logs (gitignored)
├── notebooks/               # experimentation for both devs
├── main.py                  # CLI entry point (runs full pipeline)
├── requirements.txt         # dev/orchestration deps (optional)
├── .gitignore
├── .env.example
└── README.md
```

---

## Team Responsibilities

| Developer | Owns | Works in | Does **not** touch |
|-----------|------|----------|--------------------|
| **Developer A** | Voice cloning / TTS | `xtts_module/` | `whisper_module/` |
| **Developer B** | Transcription / ASR | `whisper_module/` | `xtts_module/` |
| **Both / Lead** | Integration | `shared/`, `main.py` | — |

**Conflict-free workflow tips**
- Keep all changes inside your own module folder.
- Coordinate on `shared/` (it is the only shared code surface).
- Use branches like `feature/whisper-...` and `feature/xtts-...`.
- Name notebooks with a prefix (`whisper_`, `xtts_`) to avoid clashes.

---

## Setup Instructions

> Each module has its **own dependencies**. The recommended approach is a
> separate virtual environment per module (their ML stacks can conflict).

### 1. Clone & configure
```bash
git clone <your-repo-url>
cd Project
copy .env.example .env        # Windows  (cp .env.example .env on macOS/Linux)
```

### 2. Whisper module (Developer B)
```bash
cd whisper_module
python -m venv .venv
.venv\Scripts\activate            # Windows
pip install -r requirements.txt
```
> Requires `ffmpeg` installed on the system.

### 3. XTTS v2 module (Developer A)
```bash
cd xtts_module
python -m venv .venv
.venv\Scripts\activate            # Windows
pip install -r requirements.txt
```
> First run downloads the XTTS v2 model into `models/` (gitignored).

### 4. Run the full pipeline
Place a podcast file in `data/raw/` and a reference voice in
`data/reference_voices/`, then:
```bash
python main.py \
  --input data/raw/podcast.mp3 \
  --reference data/reference_voices/host.wav \
  --output outputs/audio/episode01.wav \
  --translate
```

---

## Notes
- Large files (models, audio, logs) are **gitignored**; only code and empty
  folder placeholders (`.gitkeep`) are committed.
- Never commit `.env`; commit `.env.example` instead.
- The scaffolded `src/` files contain `TODO`s where each developer plugs in
  their implementation.
