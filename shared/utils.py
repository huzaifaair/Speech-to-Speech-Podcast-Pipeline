"""
shared/utils.py
===============
Shared helper functions used by both modules and the pipeline:

* logging setup that writes to ``outputs/logs/``
* small audio / path helpers
* ``extract_reference_clip()`` — automatically carves a clean, single-speaker
  6-10 second clip out of the long podcast audio and saves it as
  ``data/reference_voices/reference.wav`` so XTTS v2 has a voice to clone.

Everything here is free / local — no paid APIs.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from shared import config


# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
def get_logger(name: str) -> logging.Logger:
    """Return a logger that prints to the console AND writes to outputs/logs/.

    Repeated calls with the same ``name`` reuse the existing handlers so we do
    not attach duplicate handlers (which would print each line multiple times).
    """
    config.LOGS_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    if logger.handlers:  # already configured
        return logger

    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s | %(name)s | %(levelname)s | %(message)s")

    # Console handler
    stream = logging.StreamHandler()
    stream.setFormatter(fmt)
    logger.addHandler(stream)

    # File handler (one shared log file for the whole pipeline)
    file_handler = logging.FileHandler(
        config.LOGS_DIR / "pipeline.log", encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    return logger


_log = get_logger("shared.utils")


# --------------------------------------------------------------------------- #
# Path / audio helpers
# --------------------------------------------------------------------------- #
AUDIO_EXTENSIONS = (".mp3", ".wav", ".m4a", ".flac", ".aac", ".ogg", ".wma")


def find_first_audio(
    directory: Path = config.RAW_AUDIO_DIR,
    extensions: tuple[str, ...] = AUDIO_EXTENSIONS,
) -> Optional[Path]:
    """Return the first audio file found in ``directory`` (sorted), or None."""
    directory = Path(directory)
    if not directory.exists():
        return None
    candidates = sorted(
        p for p in directory.iterdir()
        if p.is_file() and p.suffix.lower() in extensions
    )
    return candidates[0] if candidates else None


def seconds_to_timestamp(seconds: float, sep: str = ",") -> str:
    """Convert seconds to an SRT/VTT timestamp: HH:MM:SS,mmm.

    Use ``sep=","`` for SRT and ``sep="."`` for WebVTT.
    """
    if seconds < 0:
        seconds = 0.0
    millis = int(round(seconds * 1000))
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{sep}{millis:03d}"


# --------------------------------------------------------------------------- #
# Reference-clip extraction (the important one)
# --------------------------------------------------------------------------- #
def extract_reference_clip(
    input_path: Optional[str | Path] = None,
    output_path: Optional[str | Path] = None,
    duration: int = 8,
    skip_start_seconds: int = 20,
    min_silence_len: int = 400,
    silence_thresh_offset: float = 16.0,
    target_sample_rate: int = 22_050,
    overwrite: bool = False,
) -> Path:
    """Extract a clean single-speaker clip from a long podcast recording.

    Strategy (all offline, using ``pydub`` for silence/energy detection):

    1. Load the long audio and convert to mono.
    2. Skip the first ``skip_start_seconds`` (podcast intros are usually music
       or jingles, not clean speech).
    3. Detect the non-silent (speech) regions. A *continuous* speech region
       with no internal pause is very likely a single, uninterrupted speaker —
       exactly what we want for voice cloning.
    4. Pick the longest continuous speech region and cut a ``duration``-second
       window from just inside it (a small offset avoids the word onset).
    5. If no region is long enough, fall back to the loudest fixed-length
       window in the whole recording.
    6. Normalize the loudness and export to WAV.

    Parameters
    ----------
    input_path:
        Source audio. Defaults to the first audio file in ``data/raw/``.
    output_path:
        Destination WAV. Defaults to ``data/reference_voices/reference.wav``.
    duration:
        Length of the reference clip in seconds (8 by default; 6-10 is ideal
        for XTTS v2).
    skip_start_seconds:
        How many seconds to skip at the very start (to avoid intro music).
    min_silence_len:
        Minimum silence length (ms) that separates two speech regions.
    silence_thresh_offset:
        How many dB below the average loudness counts as "silence".
    target_sample_rate:
        Output sample rate for the reference clip.
    overwrite:
        If False and the output already exists, skip and return it.

    Returns
    -------
    Path to the exported reference clip.
    """
    # Imported here so the whole project can be imported even before pydub is
    # installed (only this function actually needs it).
    from pydub import AudioSegment
    from pydub.silence import detect_nonsilent
    from pydub.effects import normalize

    # Resolve defaults from config.
    input_path = Path(input_path) if input_path else find_first_audio(config.RAW_AUDIO_DIR)
    output_path = Path(output_path) if output_path else config.REFERENCE_CLIP_PATH

    if input_path is None or not Path(input_path).exists():
        raise FileNotFoundError(
            f"No source audio found. Put your podcast file in {config.RAW_AUDIO_DIR}"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists() and not overwrite:
        _log.info("Reference clip already exists, reusing: %s", output_path)
        return output_path

    _log.info("Extracting reference clip from: %s", input_path)

    # 1) Load + mono, and immediately downsample to the target rate. We export
    #    at target_sample_rate anyway, so the final clip is unchanged, but this
    #    roughly halves memory/CPU for high-rate sources during detection.
    audio = (
        AudioSegment.from_file(input_path)
        .set_channels(1)
        .set_frame_rate(target_sample_rate)
    )

    # 2) Skip the intro.
    skip_ms = min(skip_start_seconds * 1000, max(len(audio) - duration * 1000, 0))
    body = audio[skip_ms:]

    target_ms = duration * 1000
    silence_thresh = body.dBFS - silence_thresh_offset

    # 3) Detect speech regions.
    speech_regions = detect_nonsilent(
        body,
        min_silence_len=min_silence_len,
        silence_thresh=silence_thresh,
        seek_step=10,
    )

    clip: Optional[AudioSegment] = None

    # 4) Longest continuous speech region that is long enough.
    if speech_regions:
        longest = max(speech_regions, key=lambda r: r[1] - r[0])
        region_start, region_end = longest
        if (region_end - region_start) >= target_ms:
            # Start a little inside the region to avoid the very first onset,
            # but keep the window fully inside the region.
            offset = min(250, max(0, (region_end - region_start) - target_ms))
            start = region_start + offset
            clip = body[start:start + target_ms]
            _log.info(
                "Selected continuous speech region %.1fs-%.1fs",
                start / 1000, (start + target_ms) / 1000,
            )

    # 5) Fallback: loudest fixed-length window.
    if clip is None:
        _log.warning("No long-enough speech region found; using loudest window.")
        clip = _loudest_window(body, target_ms)

    # 6) Normalize loudness + set sample rate, then export as WAV.
    clip = normalize(clip).set_frame_rate(target_sample_rate).set_channels(1)
    clip.export(output_path, format="wav")

    _log.info("Reference clip saved: %s (%d s)", output_path, duration)
    return output_path


def _loudest_window(audio, window_ms: int, step_ms: int = 500):
    """Return the ``window_ms``-long slice with the highest energy.

    Uses a single NumPy pass with a cumulative sum of squares so we do not
    re-slice the (potentially 40-minute) audio thousands of times.
    """
    if len(audio) <= window_ms:
        return audio  # audio shorter than the window; return everything

    import numpy as np

    samples = np.array(audio.get_array_of_samples(), dtype=np.float64)
    frame_rate = audio.frame_rate
    window = max(1, int(window_ms / 1000 * frame_rate))
    step = max(1, int(step_ms / 1000 * frame_rate))

    if len(samples) <= window:
        return audio

    # Prefix sums of squared samples -> O(1) energy for any window.
    prefix = np.concatenate(([0.0], np.cumsum(samples * samples)))

    best_start = 0
    best_energy = -1.0
    for start in range(0, len(samples) - window, step):
        energy = prefix[start + window] - prefix[start]
        if energy > best_energy:
            best_energy = energy
            best_start = start

    start_ms = int(best_start / frame_rate * 1000)
    return audio[start_ms:start_ms + window_ms]


if __name__ == "__main__":
    # Standalone run: python shared/utils.py
    config.ensure_dirs()
    path = extract_reference_clip(overwrite=True)
    print(f"Reference clip written to: {path}")
