"""
main.py
=======
Root entry point for the local Speech-to-Speech pipeline
(Whisper transcription -> XTTS v2 voice cloning).

Everything runs locally and free — no paid API keys required.

Usage
-----
    python main.py --step all          # extract -> transcribe -> generate
    python main.py --step extract      # only build the reference voice clip
    python main.py --step whisper      # only transcribe data/raw/ audio
    python main.py --step xtts         # only generate cloned audio from transcript

Useful flags
------------
    --translate     transcribe-to-English mode (Whisper)
    --streaming     use XTTS streaming generation
    --input PATH    explicit source audio (default: first file in data/raw/)
    --output PATH   explicit output audio path (default: outputs/audio/)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure the project root is importable (so "shared.*" resolves) no matter
# where the script is launched from.
_PROJECT_ROOT = Path(__file__).resolve().parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from shared import config, pipeline           # noqa: E402
from shared.utils import get_logger           # noqa: E402

logger = get_logger("main")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Local Speech-to-Speech pipeline (Whisper + XTTS v2)."
    )
    parser.add_argument(
        "--step",
        choices=["all", "extract", "whisper", "xtts"],
        default="all",
        help="Which pipeline stage to run (default: all)",
    )
    parser.add_argument("--input", default=None, help="Source audio (default: data/raw/*)")
    parser.add_argument("--output", default=None, help="Output audio path (xtts)")
    parser.add_argument(
        "--translate", action="store_true",
        help="Whisper: translate speech to English",
    )
    parser.add_argument(
        "--streaming", action="store_true",
        help="XTTS: use streaming generation",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config.ensure_dirs()
    logger.info("Configuration:\n%s", config.summary())

    if args.step == "extract":
        path = pipeline.run_extract(force=False)
        print(f"Reference clip ready: {path}")

    elif args.step == "whisper":
        pipeline.run_whisper(audio_path=args.input, translate=args.translate)
        print(f"Transcripts written to: {config.TRANSCRIPTS_DIR}")

    elif args.step == "xtts":
        # Make sure a reference exists before generating.
        pipeline.run_extract(force=False)
        path = pipeline.run_xtts(output_path=args.output, streaming=args.streaming)
        print(f"Generated audio: {path}")

    else:  # all
        path = pipeline.run_all(
            audio_path=args.input,
            translate=args.translate,
            streaming=args.streaming,
            output_path=args.output,
        )
        print(f"Done. Final audio: {path}")


if __name__ == "__main__":
    main()
