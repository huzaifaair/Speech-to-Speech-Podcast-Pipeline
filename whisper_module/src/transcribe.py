"""
whisper_module/src/transcribe.py
================================
Whisper transcription (open-source ``openai-whisper``, 100% local / free).

Owner: Developer B

What it does
------------
* Loads the podcast audio from ``data/raw/`` (or an explicit path).
* Transcribes it with Whisper. Model size comes from ``shared/config.py``
  (``WHISPER_MODEL_SIZE``, default "base"), overridable via .env or CLI.
* Optionally translates the speech to English (``--translate``).
* Saves the result as ``.txt`` and ``.srt`` into ``outputs/transcripts/``.
* Logs progress and errors to ``outputs/logs/``.

Run independently
-----------------
    python whisper_module/src/transcribe.py                 # transcribe data/raw
    python whisper_module/src/transcribe.py --translate     # -> English
    python whisper_module/src/transcribe.py --model small --input data/raw/ep.mp3
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

# --- Make the project root importable when run as a standalone script -------
# (so "from shared.config import ..." works even when launched directly)
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from shared import config                       # noqa: E402
from shared.utils import (                      # noqa: E402
    find_first_audio,
    get_logger,
    seconds_to_timestamp,
)

logger = get_logger("whisper.transcribe")

# Cache loaded Whisper models per (size, device) so repeated calls in the same
# process do not rebuild the model in memory each time.
_MODEL_CACHE: dict[tuple[str, str], object] = {}


def _load_model(model_size: str, device: str):
    """Load (once) and return a cached Whisper model for (size, device)."""
    import whisper

    key = (model_size, device)
    cached = _MODEL_CACHE.get(key)
    if cached is not None:
        return cached

    logger.info("Loading Whisper model '%s' on %s ...", model_size, device)
    try:
        model = whisper.load_model(
            model_size,
            device=device,
            download_root=str(config.WHISPER_MODELS_DIR),
        )
    except Exception:
        logger.exception("Failed to load Whisper model '%s'", model_size)
        raise

    _MODEL_CACHE[key] = model
    return model


def _write_txt(text: str, out_path: Path) -> None:
    """Write the plain-text transcript."""
    out_path.write_text(text.strip() + "\n", encoding="utf-8")


def _write_srt(segments: list[dict], out_path: Path) -> None:
    """Write an SRT subtitle file from Whisper segments (with timestamps)."""
    lines: list[str] = []
    for i, seg in enumerate(segments, start=1):
        start = seconds_to_timestamp(seg.get("start", 0.0), sep=",")
        end = seconds_to_timestamp(seg.get("end", 0.0), sep=",")
        text = str(seg.get("text", "")).strip()
        lines.append(f"{i}\n{start} --> {end}\n{text}\n")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def transcribe_audio(
    audio_path: Optional[str | Path] = None,
    model_size: Optional[str] = None,
    translate: bool = False,
    language: Optional[str] = None,
    output_dir: Optional[str | Path] = None,
) -> dict:
    """Transcribe (or translate) an audio file and save .txt + .srt outputs.

    Parameters
    ----------
    audio_path:
        Audio to transcribe. Defaults to the first file in ``data/raw/``.
    model_size:
        Whisper model size (tiny|base|small|medium|large-v3). Defaults to
        ``config.WHISPER_MODEL_SIZE``.
    translate:
        If True, use Whisper's translate task (any language -> English).
    language:
        Source language hint (e.g. "en"). None = auto-detect.
    output_dir:
        Where to save transcripts. Defaults to ``outputs/transcripts/``.

    Returns
    -------
    The raw Whisper result dict (keys: ``text``, ``segments``, ``language``).
    """
    # Import here so the module can be imported without whisper installed.
    import whisper  # noqa: F401  (ensures a clear error if not installed)

    config.ensure_dirs()

    audio_path = Path(audio_path) if audio_path else find_first_audio(config.RAW_AUDIO_DIR)
    if audio_path is None or not Path(audio_path).exists():
        raise FileNotFoundError(
            f"No audio found. Put your podcast file in {config.RAW_AUDIO_DIR}"
        )

    model_size = model_size or config.WHISPER_MODEL_SIZE
    output_dir = Path(output_dir) if output_dir else config.TRANSCRIPTS_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    task = "translate" if translate else "transcribe"
    logger.info(
        "Preparing Whisper model '%s' on %s (task=%s)...",
        model_size, config.DEVICE, task,
    )

    # Cached load (see _load_model) avoids rebuilding the model each call.
    model = _load_model(model_size, config.DEVICE)

    logger.info("Transcribing: %s", audio_path)
    try:
        # fp16 only makes sense on CUDA; disable it on CPU to avoid warnings.
        result = model.transcribe(
            str(audio_path),
            task=task,
            language=language,
            fp16=(config.DEVICE == "cuda"),
            verbose=False,
        )
    except Exception:
        logger.exception("Transcription failed for %s", audio_path)
        raise

    stem = audio_path.stem
    txt_path = output_dir / f"{stem}.txt"
    srt_path = output_dir / f"{stem}.srt"

    _write_txt(result.get("text", ""), txt_path)
    _write_srt(result.get("segments", []), srt_path)

    logger.info("Saved transcript: %s", txt_path)
    logger.info("Saved subtitles:  %s", srt_path)
    logger.info(
        "Detected language: %s | segments: %d",
        result.get("language", "?"), len(result.get("segments", [])),
    )
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Whisper transcription (local, free)."
    )
    parser.add_argument(
        "--input", default=None,
        help="Audio file to transcribe (default: first file in data/raw/)",
    )
    parser.add_argument(
        "--model", default=None,
        help="Whisper model size: tiny|base|small|medium|large-v3 "
             "(default: from .env WHISPER_MODEL_SIZE)",
    )
    parser.add_argument(
        "--language", default=None,
        help="Source language hint, e.g. 'en' (default: auto-detect)",
    )
    parser.add_argument(
        "--translate", action="store_true",
        help="Translate speech to English instead of transcribing verbatim",
    )
    parser.add_argument(
        "--output", default=None,
        help="Output directory (default: outputs/transcripts/)",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    transcribe_audio(
        audio_path=args.input,
        model_size=args.model,
        translate=args.translate,
        language=args.language,
        output_dir=args.output,
    )


if __name__ == "__main__":
    main()
