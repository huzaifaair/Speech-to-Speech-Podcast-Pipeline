"""
Pipeline orchestration: connects the Whisper module to the XTTS v2 module.

This is where the two independently-developed modules meet. It:
  1. Transcribes (and optionally translates) input audio via whisper_module
  2. Feeds the resulting text + a reference voice into xtts_module
  3. Produces the final cloned-voice audio

Kept intentionally thin so Developer A and Developer B can work in their own
modules without touching each other's code.
"""

from __future__ import annotations

from pathlib import Path

from shared import config
from shared.utils import get_logger

logger = get_logger("pipeline")


def run_pipeline(
    input_audio: str,
    reference_voice: str,
    output_audio: str,
    translate: bool = False,
) -> str:
    """Run the full speech-to-speech pipeline end to end."""
    config.ensure_dirs()

    # Import inside the function so each module's heavy deps load only when used.
    from whisper_module.src.transcribe import transcribe, save_transcript
    from xtts_module.src.synthesize import synthesize

    logger.info("Step 1/2: transcribing %s", input_audio)
    result = transcribe(
        input_audio,
        model_name=config.WHISPER_MODEL_SIZE,
        language=config.SOURCE_LANGUAGE,
    )

    if translate:
        from whisper_module.src.translate import translate_text

        result["text"] = translate_text(result["text"], config.TARGET_LANGUAGE)

    stem = Path(input_audio).stem
    save_transcript(result, str(config.TRANSCRIPTS_DIR), stem)

    logger.info("Step 2/2: synthesizing cloned voice -> %s", output_audio)
    final_path = synthesize(
        text=result["text"],
        speaker_wav=reference_voice,
        output_path=output_audio,
        language=config.TARGET_LANGUAGE,
    )

    logger.info("Pipeline complete: %s", final_path)
    return final_path
