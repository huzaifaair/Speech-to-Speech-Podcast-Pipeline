"""
Shared utility helpers used across both modules and the pipeline.
"""

from __future__ import annotations

import logging
from pathlib import Path

from shared import config


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger that also writes to outputs/logs/."""
    config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s | %(name)s | %(levelname)s | %(message)s")

    stream = logging.StreamHandler()
    stream.setFormatter(fmt)
    logger.addHandler(stream)

    file_handler = logging.FileHandler(config.LOGS_DIR / "pipeline.log", encoding="utf-8")
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    return logger


def find_first_audio(directory: Path, extensions=(".mp3", ".wav", ".m4a", ".flac")):
    """Return the first audio file found in a directory, or None."""
    for ext in extensions:
        matches = sorted(directory.glob(f"*{ext}"))
        if matches:
            return matches[0]
    return None
