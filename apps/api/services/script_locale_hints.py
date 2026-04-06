"""
Infer locale from Unicode scripts when langdetect misses or Groq is off.

Single-pass character scan covers: CJK (ja/zh), Hangul (ko), Thai (th),
Devanagari (hi), Bengali (bn), Arabic block (ar/fa/ur), Cyrillic (ru/uk).

Latin-script locales rely on language_detect.detect_document_language.
"""

from __future__ import annotations

from services.locale_config import SUPPORTED_EXTRA_LOCALES


def script_locale_hints(text: str, sample_chars: int = 20000) -> list[str]:
    s = (text or "")[:sample_chars]
    if len(s) < 12:
        return []

    kana = han = hangul = thai = bengali = devanagari = arabic = cyrillic = 0

    for c in s:
        cp = ord(c)
        if 0x4E00 <= cp <= 0x9FFF:
            han += 1
        elif 0x3040 <= cp <= 0x309F or 0x30A0 <= cp <= 0x30FF:
            kana += 1
        elif 0xAC00 <= cp <= 0xD7A3:
            hangul += 1
        elif 0x0E00 <= cp <= 0x0E7F:
            thai += 1
        elif 0x0980 <= cp <= 0x09FF:
            bengali += 1
        elif 0x0900 <= cp <= 0x097F:
            devanagari += 1
        elif 0x0600 <= cp <= 0x06FF:
            arabic += 1
        elif 0x0400 <= cp <= 0x04FF:
            cyrillic += 1

    out: list[str] = []
    ko_hint = hangul >= 12

    if kana >= 8 and han >= 12:
        if "ja" in SUPPORTED_EXTRA_LOCALES:
            out.append("ja")
    elif han >= 12 and kana < 5 and not ko_hint:
        if "zh" in SUPPORTED_EXTRA_LOCALES:
            out.append("zh")

    if ko_hint and "ko" in SUPPORTED_EXTRA_LOCALES:
        out.append("ko")

    if thai >= 12 and "th" in SUPPORTED_EXTRA_LOCALES:
        out.append("th")

    if bengali >= 12 and "bn" in SUPPORTED_EXTRA_LOCALES:
        out.append("bn")

    if devanagari >= 12 and "hi" in SUPPORTED_EXTRA_LOCALES:
        out.append("hi")

    if arabic >= 28:
        for loc in ("ar", "fa", "ur"):
            if loc in SUPPORTED_EXTRA_LOCALES and loc not in out:
                out.append(loc)

    if cyrillic >= 22:
        for loc in ("ru", "uk"):
            if loc in SUPPORTED_EXTRA_LOCALES and loc not in out:
                out.append(loc)

    return out
