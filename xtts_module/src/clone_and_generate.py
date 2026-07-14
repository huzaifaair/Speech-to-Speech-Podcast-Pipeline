"""
xtts_module/src/clone_and_generate.py
=====================================
Coqui XTTS v2 voice cloning + speech generation (100% local / free).

Owner: Developer A

What it does
------------
* Ensures a reference voice exists at ``data/reference_voices/reference.wav``.
  If it does not, it automatically triggers the shared extractor
  (``shared.utils.extract_reference_clip``) to carve one out of the long
  podcast in ``data/raw/``.
* Loads text either from ``outputs/transcripts/`` (latest .txt) or from a
  string / file you pass in.
* Generates cloned speech with XTTS v2. Language comes from
  ``shared/config.py`` (``XTTS_LANGUAGE``, default "en").
* Saves the generated audio into ``outputs/audio/``.
* Provides BOTH a non-streaming function (simple, whole-file) and a streaming
  function (generates audio in chunks).

Run independently
-----------------
    python xtts_module/src/clone_and_generate.py                     # use transcript
    python xtts_module/src/clone_and_generate.py --text "Hello world"
    python xtts_module/src/clone_and_generate.py --streaming --text "Hi there"
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

# --- Make the project root importable when run as a standalone script -------
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# Auto-accept Coqui's non-commercial license so the model download is not
# blocked by an interactive prompt. XTTS v2 is free for local/personal use.
os.environ.setdefault("COQUI_TOS_AGREED", "1")

from shared import config                              # noqa: E402
from shared.utils import extract_reference_clip, get_logger  # noqa: E402

logger = get_logger("xtts.generate")

# XTTS v2 renders audio at 24 kHz.
XTTS_SAMPLE_RATE = 24_000

# Cache the loaded model between calls (loading is slow).
_TTS_INSTANCE = None


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def ensure_reference_clip() -> Path:
    """Return the reference clip path, extracting it first if it is missing."""
    ref = config.REFERENCE_CLIP_PATH
    if ref.exists():
        logger.info("Using existing reference voice: %s", ref)
        return ref
    logger.info("Reference voice missing — extracting one from data/raw/ ...")
    return extract_reference_clip(output_path=ref)


def load_text(
    text: Optional[str] = None,
    text_file: Optional[str | Path] = None,
) -> str:
    """Resolve the text to synthesize.

    Priority: explicit ``text`` > ``text_file`` > latest .txt transcript in
    ``outputs/transcripts/``.
    """
    if text and text.strip():
        return text.strip()

    if text_file:
        path = Path(text_file)
        if not path.exists():
            raise FileNotFoundError(f"Text file not found: {path}")
        return path.read_text(encoding="utf-8").strip()

    # Fall back to the most recently modified transcript.
    transcripts = sorted(
        config.TRANSCRIPTS_DIR.glob("*.txt"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not transcripts:
        raise FileNotFoundError(
            f"No text provided and no transcripts in {config.TRANSCRIPTS_DIR}. "
            "Run the Whisper step first or pass --text."
        )
    logger.info("Using transcript: %s", transcripts[0])
    return transcripts[0].read_text(encoding="utf-8").strip()


def _get_tts():
    """Load (once) and return a cached Coqui ``TTS`` instance for XTTS v2."""
    global _TTS_INSTANCE
    if _TTS_INSTANCE is not None:
        return _TTS_INSTANCE

    from TTS.api import TTS  # imported lazily; heavy dependency

    logger.info(
        "Loading XTTS v2 model '%s' on %s (first run downloads weights)...",
        config.XTTS_MODEL_NAME, config.DEVICE,
    )
    # progress_bar off keeps logs clean; model files cache in ~/.local/share/tts
    _TTS_INSTANCE = TTS(config.XTTS_MODEL_NAME, progress_bar=False).to(config.DEVICE)
    return _TTS_INSTANCE


def _default_output_path(name: str = "generated.wav") -> Path:
    return config.AUDIO_OUTPUT_DIR / name


def _prepare_generation(
    text: Optional[str],
    text_file: Optional[str | Path],
    reference_wav: Optional[str | Path],
    output_path: Optional[str | Path],
    language: Optional[str],
    default_output_name: str,
) -> tuple[Path, str, str, Path]:
    """Shared setup for both generation paths.

    Resolves the reference clip (extracting it if needed), the text to speak,
    the language, and the output path. Returns ``(ref, content, language,
    output_path)``. Centralizing this avoids drift between the streaming and
    non-streaming functions.
    """
    config.ensure_dirs()

    ref = Path(reference_wav) if reference_wav else ensure_reference_clip()
    if not Path(ref).exists():
        raise FileNotFoundError(f"Reference voice not found: {ref}")

    content = load_text(text=text, text_file=text_file)
    language = language or config.XTTS_LANGUAGE
    output_path = (
        Path(output_path) if output_path else _default_output_path(default_output_name)
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return ref, content, language, output_path


def _split_text_into_chunks(text: str, max_chars: int = 220) -> list[str]:
    """Split text into chunks under ``max_chars``, preferring sentence breaks.

    XTTS v2's low-level ``inference_stream`` does NOT split sentences and has a
    per-generation length limit, so long transcripts must be chunked manually
    before streaming or the output is truncated.
    """
    import re

    # Split into sentences on ., !, ? (keeping the delimiter).
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        # A single sentence longer than the limit: hard-split on whitespace.
        if len(sentence) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            words = sentence.split()
            piece = ""
            for word in words:
                if len(piece) + len(word) + 1 > max_chars:
                    chunks.append(piece.strip())
                    piece = word
                else:
                    piece = f"{piece} {word}".strip()
            if piece:
                current = piece
            continue

        if len(current) + len(sentence) + 1 > max_chars:
            chunks.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()

    if current:
        chunks.append(current)
    return [c for c in chunks if c]


# --------------------------------------------------------------------------- #
# Non-streaming generation (simple: render the whole thing to one file)
# --------------------------------------------------------------------------- #
def generate_speech(
    text: Optional[str] = None,
    reference_wav: Optional[str | Path] = None,
    output_path: Optional[str | Path] = None,
    language: Optional[str] = None,
    text_file: Optional[str | Path] = None,
) -> Path:
    """Generate cloned speech and write it to a single WAV file.

    Returns the path to the generated audio.
    """
    ref, content, language, output_path = _prepare_generation(
        text, text_file, reference_wav, output_path, language, "generated.wav"
    )

    tts = _get_tts()

    logger.info("Generating speech (%d chars, lang=%s)...", len(content), language)
    try:
        # split_sentences=True lets XTTS handle long transcripts safely.
        tts.tts_to_file(
            text=content,
            speaker_wav=str(ref),
            language=language,
            file_path=str(output_path),
            split_sentences=True,
        )
    except Exception:
        logger.exception("Non-streaming generation failed")
        raise

    logger.info("Saved generated audio: %s", output_path)
    return output_path


# --------------------------------------------------------------------------- #
# Streaming generation (yields/collects audio chunks as they are produced)
# --------------------------------------------------------------------------- #
def generate_speech_streaming(
    text: Optional[str] = None,
    reference_wav: Optional[str | Path] = None,
    output_path: Optional[str | Path] = None,
    language: Optional[str] = None,
    text_file: Optional[str | Path] = None,
) -> Path:
    """Generate cloned speech using XTTS v2's low-level streaming inference.

    Audio is produced in chunks (useful for low-latency playback). Here we
    collect the chunks and write them to a single WAV file, but the same loop
    could feed a live audio player instead.

    Long transcripts are split into length-bounded chunks first, because
    ``inference_stream`` does not split sentences and would otherwise truncate
    text beyond XTTS v2's per-generation limit.
    """
    import torch  # bundled with Coqui TTS

    ref, content, language, output_path = _prepare_generation(
        text, text_file, reference_wav, output_path, language, "generated_streaming.wav"
    )

    tts = _get_tts()
    # Reach into the underlying Xtts model to access streaming inference.
    model = tts.synthesizer.tts_model

    logger.info("Computing speaker conditioning latents from reference...")
    gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(
        audio_path=[str(ref)]
    )

    # Chunk the text so nothing is silently truncated by the length limit.
    text_chunks = _split_text_into_chunks(content)
    logger.info(
        "Streaming generation (lang=%s, %d text chunk(s))...",
        language, len(text_chunks),
    )

    wav_chunks = []
    try:
        for c_idx, text_chunk in enumerate(text_chunks):
            logger.info("  synthesizing text chunk %d/%d", c_idx + 1, len(text_chunks))
            stream = model.inference_stream(
                text_chunk,
                language,
                gpt_cond_latent,
                speaker_embedding,
            )
            for chunk in stream:
                # Each chunk is a 1-D float tensor of audio samples.
                wav_chunks.append(chunk.squeeze().detach().cpu())
    except Exception:
        logger.exception("Streaming generation failed")
        raise

    if not wav_chunks:
        raise RuntimeError("Streaming produced no audio chunks.")

    wav = torch.cat(wav_chunks, dim=0).numpy()

    # Write with soundfile (installed as a Coqui TTS dependency).
    import soundfile as sf
    sf.write(str(output_path), wav, XTTS_SAMPLE_RATE)

    logger.info("Saved streamed audio: %s", output_path)
    return output_path


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="XTTS v2 voice cloning + generation (local, free)."
    )
    parser.add_argument("--text", default=None, help="Text to speak (inline)")
    parser.add_argument("--text-file", default=None, help="Path to a .txt file to speak")
    parser.add_argument(
        "--reference", default=None,
        help="Reference voice .wav (default: data/reference_voices/reference.wav, "
             "auto-extracted if missing)",
    )
    parser.add_argument(
        "--output", default=None,
        help="Output audio path (default: outputs/audio/generated.wav)",
    )
    parser.add_argument(
        "--language", default=None,
        help="Language code (default: from .env XTTS_LANGUAGE)",
    )
    parser.add_argument(
        "--streaming", action="store_true",
        help="Use streaming generation instead of non-streaming",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    fn = generate_speech_streaming if args.streaming else generate_speech
    fn(
        text=args.text,
        text_file=args.text_file,
        reference_wav=args.reference,
        output_path=args.output,
        language=args.language,
    )


if __name__ == "__main__":
    main()
