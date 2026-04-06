"""
Supported *extra* rule locales (ISO 639-1 style).

English is always covered by base `Rule.patterns` in analyzer.py — not listed here.
Together: 1 (en) + 24 extras = 25 languages for consumer ToS matching.

Top-25 alignment (user list): en (base) + zh, hi, ar, fr, pt, ru, ur, bn, de, ja, ko,
tr, id, vi, it, nl, pl, th, sw, fa, ms, tl, uk, es.
"""

from __future__ import annotations

# Non-English locales that may have regex banks in LOCALE_EXTRA_PATTERNS.
SUPPORTED_EXTRA_LOCALES: frozenset[str] = frozenset(
    {
        "es",
        "de",
        "fr",
        "zh",
        "hi",
        "ar",
        "pt",
        "ru",
        "ur",
        "bn",
        "ja",
        "ko",
        "tr",
        "id",
        "vi",
        "it",
        "nl",
        "pl",
        "th",
        "sw",
        "fa",
        "ms",
        "tl",
        "uk",
    }
)

# langdetect sometimes returns variants; normalize to our canonical codes.
LANGDETECT_NORMALIZE: dict[str, str] = {
    "zh-cn": "zh",
    "zh-tw": "zh",
    "fil": "tl",
    "in": "id",  # some stacks use 'in' for Indonesian
    "pt-br": "pt",
    "pt-pt": "pt",
    "es-mx": "es",
}
