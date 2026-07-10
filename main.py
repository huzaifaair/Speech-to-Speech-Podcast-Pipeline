"""
Entry point for the Speech-to-Speech podcast pipeline.

Connects the Whisper (ASR) module and the XTTS v2 (voice cloning) module
through the shared orchestrator.

Example:
    python main.py \
        --input data/raw/podcast.mp3 \
        --reference data/reference_voices/host.wav \
        --output outputs/audio/episode01.wav \
        --translate
"""

from __future__ import annotations

import argparse

from shared.pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Speech-to-Speech podcast pipeline (Whisper -> XTTS v2)"
    )
    parser.add_argument("--input", required=True, help="Raw podcast audio file")
    parser.add_argument(
        "--reference", required=True, help="Reference voice sample for cloning"
    )
    parser.add_argument(
        "--output",
        default="outputs/audio/final.wav",
        help="Path for the generated cloned-voice audio",
    )
    parser.add_argument(
        "--translate",
        action="store_true",
        help="Translate the transcript before synthesis",
    )
    args = parser.parse_args()

    final_path = run_pipeline(
        input_audio=args.input,
        reference_voice=args.reference,
        output_audio=args.output,
        translate=args.translate,
    )
    print(f"Done. Final audio: {final_path}")


if __name__ == "__main__":
    main()
