"""
Generate speech from text in a cloned voice using XTTS v2.

Owner: Developer A

This is a starter scaffold. Fill in the TODOs with your implementation.
Run standalone:
    python src/synthesize.py --text "Hello" --speaker ../data/reference_voices/host.wav \
        --output ../outputs/audio/out.wav --language en
"""

from __future__ import annotations

import argparse
from pathlib import Path

# from TTS.api import TTS  # uncomment once dependencies are installed


def synthesize(
    text: str,
    speaker_wav: str,
    output_path: str,
    language: str = "en",
) -> str:
    """Generate cloned speech for `text` and write it to `output_path`."""
    ref = Path(speaker_wav)
    if not ref.exists():
        raise FileNotFoundError(f"Reference voice sample not found: {ref}")

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    # TODO (Developer A): implement real synthesis, e.g.
    # tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
    # tts.tts_to_file(
    #     text=text,
    #     speaker_wav=str(ref),
    #     language=language,
    #     file_path=str(out),
    # )
    # return str(out)

    raise NotImplementedError("Implement XTTS v2 synthesis here.")


def main() -> None:
    parser = argparse.ArgumentParser(description="XTTS v2 voice-cloned synthesis")
    parser.add_argument("--text", required=True, help="Text to synthesize")
    parser.add_argument("--speaker", required=True, help="Reference voice .wav")
    parser.add_argument("--output", required=True, help="Output .wav path")
    parser.add_argument("--language", default="en", help="Target language code")
    args = parser.parse_args()

    path = synthesize(args.text, args.speaker, args.output, args.language)
    print(f"Audio saved to {path}")


if __name__ == "__main__":
    main()
