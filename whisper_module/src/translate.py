"""
Optional translation step for the Whisper module.

Owner: Developer B

Whisper can translate speech directly to English via task="translate".
For other target languages, plug in a translation service/model here.
"""

from __future__ import annotations


def translate_text(text: str, target_language: str = "en") -> str:
    """Translate transcript text into the target language.

    TODO (Developer B): implement translation. Options include:
    - Whisper's built-in task="translate" (audio -> English)
    - A dedicated MT model (e.g. NLLB, M2M100) or a translation API
    """
    raise NotImplementedError("Implement translation here.")
