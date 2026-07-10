"""
Voice cloning helpers for XTTS v2.

Owner: Developer A

Prepares a reference speaker sample so it can be reused across multiple
synthesis calls without recomputing speaker embeddings every time.
"""

from __future__ import annotations

from pathlib import Path


def validate_reference(reference_path: str) -> Path:
    """Ensure the reference voice sample exists and looks usable."""
    ref = Path(reference_path)
    if not ref.exists():
        raise FileNotFoundError(f"Reference voice sample not found: {ref}")
    # XTTS v2 works best with a clean 6-30 second mono sample.
    return ref


def compute_speaker_latents(model, reference_path: str):
    """Compute speaker embeddings/latents from a reference sample.

    TODO (Developer A): implement using the XTTS model, e.g.
        gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(
            audio_path=[reference_path]
        )
        return gpt_cond_latent, speaker_embedding
    """
    raise NotImplementedError("Implement speaker latent extraction here.")
