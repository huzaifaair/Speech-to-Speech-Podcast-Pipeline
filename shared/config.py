"""
Central configuration and shared paths for the whole pipeline.

Both modules and the orchestrator import from here so folder locations stay
consistent. Loads values from a .env file when present.
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv is optional at import time
    pass

# --- Project root and key directories -------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = ROOT_DIR / "data"
RAW_AUDIO_DIR = DATA_DIR / "raw"
REFERENCE_VOICE_DIR = DATA_DIR / "reference_voices"

OUTPUT_DIR = ROOT_DIR / "outputs"
TRANSCRIPTS_DIR = OUTPUT_DIR / "transcripts"
AUDIO_OUTPUT_DIR = OUTPUT_DIR / "audio"
LOGS_DIR = OUTPUT_DIR / "logs"

WHISPER_MODELS_DIR = ROOT_DIR / "whisper_module" / "models"
XTTS_MODELS_DIR = ROOT_DIR / "xtts_module" / "models"

# --- Tunable settings (override via .env) ---------------------------------
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "small")
SOURCE_LANGUAGE = os.getenv("SOURCE_LANGUAGE", "en")
TARGET_LANGUAGE = os.getenv("TARGET_LANGUAGE", "en")
XTTS_MODEL_NAME = os.getenv(
    "XTTS_MODEL_NAME", "tts_models/multilingual/multi-dataset/xtts_v2"
)


def ensure_dirs() -> None:
    """Create all output directories if they do not exist yet."""
    for d in (TRANSCRIPTS_DIR, AUDIO_OUTPUT_DIR, LOGS_DIR):
        d.mkdir(parents=True, exist_ok=True)
