"""
shared/config.py
================
Central configuration for the whole Speech-to-Speech pipeline.

Reads settings from the project-root ``.env`` file (via python-dotenv) and
exposes them as importable constants, together with every important filesystem
path used by the Whisper module, the XTTS module and the shared code.

Import from anywhere in the project like:

    from shared.config import (
        WHISPER_MODEL_SIZE, XTTS_LANGUAGE, DEVICE, HF_TOKEN,
        RAW_AUDIO_DIR, REFERENCE_VOICE_DIR, TRANSCRIPTS_DIR,
        AUDIO_OUTPUT_DIR, LOGS_DIR, REFERENCE_CLIP_PATH,
    )
"""

from __future__ import annotations

import os
from pathlib import Path

# --------------------------------------------------------------------------- #
# Load .env (safe if python-dotenv is missing or the file does not exist yet)
# --------------------------------------------------------------------------- #
# The project root is one level up from this file (shared/ -> project_root/).
PROJECT_ROOT = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv

    # Load the real .env if present; otherwise fall back to .env.example so the
    # project still runs with sensible defaults out of the box.
    _env_file = PROJECT_ROOT / ".env"
    if not _env_file.exists():
        _env_file = PROJECT_ROOT / ".env.example"
    load_dotenv(dotenv_path=_env_file)
except ImportError:
    # python-dotenv not installed yet — os.getenv() below still works with
    # real environment variables and the hard-coded defaults.
    pass


# --------------------------------------------------------------------------- #
# Environment-driven settings (with safe, free/local defaults)
# --------------------------------------------------------------------------- #
# Whisper model size: tiny | base | small | medium | large-v3
WHISPER_MODEL_SIZE: str = os.getenv("WHISPER_MODEL_SIZE", "base")

# Language code XTTS v2 should speak in, e.g. "en", "es", "fr", "de", "hi"...
XTTS_LANGUAGE: str = os.getenv("XTTS_LANGUAGE", "en")

# Compute device: "cuda" if you have an NVIDIA GPU, otherwise "cpu".
DEVICE: str = os.getenv("DEVICE", "cpu")

# Hugging Face token — ONLY needed for gated models. Optional and free.
HF_TOKEN: str = os.getenv("HF_TOKEN", "").strip()

# If a token was provided, expose it under the standard variable names that
# Hugging Face libraries read, so it is actually consumed downstream (e.g. if a
# gated model is ever used). Harmless when blank.
if HF_TOKEN:
    os.environ.setdefault("HUGGING_FACE_HUB_TOKEN", HF_TOKEN)
    os.environ.setdefault("HF_TOKEN", HF_TOKEN)

# Coqui XTTS v2 model identifier (open-source, downloaded automatically).
XTTS_MODEL_NAME: str = os.getenv(
    "XTTS_MODEL_NAME", "tts_models/multilingual/multi-dataset/xtts_v2"
)


# --------------------------------------------------------------------------- #
# Filesystem paths (all derived from PROJECT_ROOT; never hard-coded absolutes)
# --------------------------------------------------------------------------- #
DATA_DIR = PROJECT_ROOT / "data"
RAW_AUDIO_DIR = DATA_DIR / "raw"                       # input podcast audio
REFERENCE_VOICE_DIR = DATA_DIR / "reference_voices"    # extracted ref clip lives here
REFERENCE_CLIP_PATH = REFERENCE_VOICE_DIR / "reference.wav"

OUTPUT_DIR = PROJECT_ROOT / "outputs"
TRANSCRIPTS_DIR = OUTPUT_DIR / "transcripts"           # .txt / .srt transcripts
AUDIO_OUTPUT_DIR = OUTPUT_DIR / "audio"                # generated cloned audio
LOGS_DIR = OUTPUT_DIR / "logs"                         # run logs

WHISPER_MODELS_DIR = PROJECT_ROOT / "whisper_module" / "models"   # cached weights
XTTS_MODELS_DIR = PROJECT_ROOT / "xtts_module" / "models"         # cached weights


def ensure_dirs() -> None:
    """Create all output/model directories if they do not exist yet.

    Safe to call repeatedly. Input directories (data/raw, data/reference_voices)
    are expected to already exist as part of the project structure, but we make
    sure the output/model sinks exist before writing to them.
    """
    for directory in (
        TRANSCRIPTS_DIR,
        AUDIO_OUTPUT_DIR,
        LOGS_DIR,
        REFERENCE_VOICE_DIR,
        WHISPER_MODELS_DIR,
        XTTS_MODELS_DIR,
    ):
        directory.mkdir(parents=True, exist_ok=True)


def summary() -> str:
    """Return a human-readable summary of the active configuration."""
    return (
        "Speech-to-Speech configuration\n"
        f"  WHISPER_MODEL_SIZE = {WHISPER_MODEL_SIZE}\n"
        f"  XTTS_LANGUAGE      = {XTTS_LANGUAGE}\n"
        f"  DEVICE             = {DEVICE}\n"
        f"  HF_TOKEN set       = {'yes' if HF_TOKEN else 'no'}\n"
        f"  RAW_AUDIO_DIR      = {RAW_AUDIO_DIR}\n"
        f"  REFERENCE_CLIP     = {REFERENCE_CLIP_PATH}\n"
        f"  TRANSCRIPTS_DIR    = {TRANSCRIPTS_DIR}\n"
        f"  AUDIO_OUTPUT_DIR   = {AUDIO_OUTPUT_DIR}\n"
    )


if __name__ == "__main__":
    # Quick manual check: `python shared/config.py`
    ensure_dirs()
    print(summary())
