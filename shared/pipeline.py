"""
shared/pipeline.py
==================
Pipeline orchestration — connects the Whisper module and the XTTS module.

This is the single place where the two independently-developed modules meet.
It exposes small, importable step functions plus a ``run_all`` convenience,
all of which are called from ``main.py``.

Pipeline order:
    1. extract   -> ensure data/reference_voices/reference.wav exists
    2. whisper   -> transcribe data/raw/ audio into outputs/transcripts/
    3. xtts      -> generate cloned speech into outputs/audio/

Everything runs locally and free — no paid APIs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from shared import config
from shared.utils import extract_reference_clip, find_first_audio, get_logger

logger = get_logger("pipeline")


# --------------------------------------------------------------------------- #
# Step 1 — reference clip extraction
# --------------------------------------------------------------------------- #
def run_extract(force: bool = False) -> Path:
    """Ensure a reference voice clip exists; extract from data/raw/ if needed."""
    config.ensure_dirs()
    if config.REFERENCE_CLIP_PATH.exists() and not force:
        logger.info("Reference clip already present: %s", config.REFERENCE_CLIP_PATH)
        return config.REFERENCE_CLIP_PATH
    logger.info("=== Step: extract reference clip ===")
    return extract_reference_clip(overwrite=force)


# --------------------------------------------------------------------------- #
# Step 2 — Whisper transcription
# --------------------------------------------------------------------------- #
def run_whisper(
    audio_path: Optional[str | Path] = None,
    model_size: Optional[str] = None,
    translate: bool = False,
    language: Optional[str] = None,
) -> dict:
    """Transcribe the podcast audio into outputs/transcripts/."""
    logger.info("=== Step: Whisper transcription ===")
    # Imported lazily so this module can be used even if only one module's
    # dependencies are installed in the current environment.
    from whisper_module.src.transcribe import transcribe_audio

    return transcribe_audio(
        audio_path=audio_path,
        model_size=model_size,
        translate=translate,
        language=language,
    )


# --------------------------------------------------------------------------- #
# Step 3 — XTTS generation
# --------------------------------------------------------------------------- #
def run_xtts(
    text: Optional[str] = None,
    text_file: Optional[str | Path] = None,
    reference_wav: Optional[str | Path] = None,
    output_path: Optional[str | Path] = None,
    language: Optional[str] = None,
    streaming: bool = False,
) -> Path:
    """Generate cloned speech from a transcript (or custom text)."""
    logger.info("=== Step: XTTS voice cloning ===")
    from xtts_module.src.clone_and_generate import (
        generate_speech,
        generate_speech_streaming,
    )

    fn = generate_speech_streaming if streaming else generate_speech
    return fn(
        text=text,
        text_file=text_file,
        reference_wav=reference_wav,
        output_path=output_path,
        language=language,
    )


# --------------------------------------------------------------------------- #
# Full pipeline
# --------------------------------------------------------------------------- #
def run_all(
    audio_path: Optional[str | Path] = None,
    translate: bool = False,
    streaming: bool = False,
    output_path: Optional[str | Path] = None,
) -> Path:
    """Run the complete pipeline: extract -> transcribe -> generate.

    Returns the path to the final generated audio file.
    """
    config.ensure_dirs()

    # Resolve the source audio once so both steps agree on it.
    audio_path = Path(audio_path) if audio_path else find_first_audio(config.RAW_AUDIO_DIR)
    if audio_path is None:
        raise FileNotFoundError(
            f"No podcast audio found in {config.RAW_AUDIO_DIR}. Add a file and retry."
        )

    logger.info("Starting full pipeline for: %s", audio_path)

    # 1) Reference clip
    run_extract()

    # 2) Transcription
    run_whisper(audio_path=audio_path, translate=translate)

    # 3) Generation (uses the latest transcript automatically)
    final = run_xtts(output_path=output_path, streaming=streaming)

    logger.info("Pipeline complete. Final audio: %s", final)
    return final
