"""Tells Konkani from English in a complaint, so follow-up messages go out in the complainant's language.

This only looks at the script of the letters (Konkani is written in Devanagari, which has its own block in Unicode; Marathi and Hindi share it). It does not translate.
A complaint written mostly in Konkani letters is "kok"; everything else is "en". Mixed text counts as Konkani
when at least a third of its letters are Konkani, because then the citizen is comfortable in Konkani.
"""

from typing import Any

KONKANI_FROM = "\u0900"
KONKANI_TO = "\u097f"
LANGUAGES = {"en": "English", "kok": "Konkani"}


def detect_language(text: Any) -> str:
    """Return 'kok' when the text is mostly Konkani, otherwise 'en'."""
    letters = [char for char in text if char.isalpha()] if isinstance(text, str) else []
    if not letters:
        return "en"
    konkani = sum(1 for char in letters if KONKANI_FROM <= char <= KONKANI_TO)
    return "kok" if konkani / len(letters) >= 1 / 3 else "en"


def language_name(code: Any) -> str:
    return LANGUAGES.get(code if isinstance(code, str) else "", "English")
