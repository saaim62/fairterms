"""Lightweight document language hint for selecting regex locale banks."""

from __future__ import annotations

from services.locale_config import LANGDETECT_NORMALIZE, SUPPORTED_EXTRA_LOCALES

SUPPORTED_LOCALE_CODES = SUPPORTED_EXTRA_LOCALES

# Short ToS excerpts (e.g. browser extension) should still get a locale when possible.
_MIN_CHARS = 48
# Scan ranked candidates: top may be "en" (not in extras); pick first supported locale.
_MIN_PROB = 0.42
_MAX_CANDIDATES = 6


def detect_document_language(text: str, sample_chars: int = 8000) -> str | None:
    """
    Return a supported extra-locale code when confident, else None.

    None means: no extra locale from detection (English base patterns still apply;
    script_locale_hints may still add non-Latin banks).
    """
    raw = (text or "").strip()
    if len(raw) < _MIN_CHARS:
        return None

    sample = raw[:sample_chars]

    try:
        from langdetect import detect_langs
    except ImportError:
        return None

    try:
        candidates = detect_langs(sample)
    except Exception:
        return None

    if not candidates:
        return None

    for cand in candidates[:_MAX_CANDIDATES]:
        prob = getattr(cand, "prob", 0.0) or 0.0
        if prob < _MIN_PROB:
            break
        lang = (getattr(cand, "lang", None) or "").lower()
        code = LANGDETECT_NORMALIZE.get(lang, lang)
        if code in SUPPORTED_LOCALE_CODES:
            return code

    return None
