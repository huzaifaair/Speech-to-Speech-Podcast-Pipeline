"""
Transcribe a podcast audio file into text with timestamps using Whisper.

Owner: Developer B

This is a starter scaffold. Fill in the TODOs with your implementation.
Run standalone:
    python src/transcribe.py --input ../data/raw/podcast.mp3 --model small
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

# import whisper  # uncomment once dependencies are installed


def transcribe(
    input_path: str,
    model_name: str = "small",
    language: str | None = None,
) -> dict:
    """Transcribe an audio file and return a result dict with segments/timestamps.

    Returns a dict shaped like:
        {
            "text": "full transcript ...",
            "language": "en",
            "segments": [{"start": 0.0, "end": 3.2, "text": "..."}, ...],
        }
    """
    audio_file = Path(input_path)
    if not audio_file.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_file}")

    # TODO (Developer B): implement real transcription, e.g.
    # model = whisper.load_model(model_name, download_root="../models")
    # result = model.transcribe(str(audio_file), language=language)
    # return result

    raise NotImplementedError("Implement Whisper transcription here.")


def save_transcript(result: dict, output_dir: str, stem: str) -> None:
    """Write transcript as .txt and .json into the outputs/transcripts folder."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{stem}.txt").write_text(result.get("text", ""), encoding="utf-8")
    (out / f"{stem}.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Whisper transcription")
    parser.add_argument("--input", required=True, help="Path to input audio file")
    parser.add_argument("--model", default="small", help="Whisper model size")
    parser.add_argument("--language", default=None, help="Source language (optional)")
    parser.add_argument(
        "--output", default="../outputs/transcripts", help="Output directory"
    )
    args = parser.parse_args()

    result = transcribe(args.input, args.model, args.language)
    save_transcript(result, args.output, Path(args.input).stem)
    print(f"Transcript saved to {args.output}")


if __name__ == "__main__":
    main()
