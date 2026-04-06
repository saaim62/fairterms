from __future__ import annotations

import os
import re

from services.analyzer_rules import RULES, Rule
from services.category_registry import ALL_CATEGORY_KEYS
from services.groq_analyze import analyze_with_groq
from services.language_detect import detect_document_language
from services.locale_patterns import LOCALE_EXTRA_PATTERNS, LOCALE_PATTERN_LANGUAGES
from services.script_locale_hints import script_locale_hints


_UK_CHARS = frozenset("іїєґІЇЄҐ")
_RU_CHARS = frozenset("ыэёъЫЭЁЪ")
_FA_CHARS = frozenset("پچژگ")


def _refine_document_language_from_script(safe_text: str, extra_locales: list[str]) -> str | None:
    """
    When several script-derived locales apply (ru+uk, ar+fa+ur), pick a likelier label for
    API consumers. Pattern banks for all hinted locales still run unchanged.
    """
    if not safe_text or not extra_locales:
        return None
    ls = frozenset(extra_locales)
    if ls >= frozenset({"ru", "uk"}):
        uk_marks = ru_marks = 0
        for c in safe_text:
            if c in _UK_CHARS:
                uk_marks += 1
            elif c in _RU_CHARS:
                ru_marks += 1
        if uk_marks >= 2 and uk_marks >= ru_marks:
            return "uk"
        if ru_marks >= 2 and ru_marks > uk_marks:
            return "ru"
        return None
    if ls >= frozenset({"ar", "fa", "ur"}):
        fa_marks = sum(1 for c in safe_text if c in _FA_CHARS)
        if fa_marks >= 2:
            return "fa"
        return None
    return None


_LOCALE_PATTERN_CACHE: dict[str, dict[str, list[re.Pattern[str]]]] = {}


def _get_compiled_locale_patterns(category: str, locale: str) -> list[re.Pattern[str]]:
    key = f"{category}:{locale}"
    if key not in _LOCALE_PATTERN_CACHE:
        raw = LOCALE_EXTRA_PATTERNS.get(category, {}).get(locale, [])
        _LOCALE_PATTERN_CACHE[key] = [re.compile(p) for p in raw]
    return _LOCALE_PATTERN_CACHE[key]


def _compiled_patterns_for_rule(rule: Rule, extra_locales: list[str]) -> list[re.Pattern[str]]:
    combined = list(rule.compiled)
    for loc in extra_locales:
        combined.extend(_get_compiled_locale_patterns(rule.category, loc))
    return combined


def _pick_signal(issues: list[dict]) -> str:
    severities = {issue["severity"] for issue in issues}
    if "red" in severities:
        return "red"
    if "yellow" in severities:
        return "yellow"
    return "green"


def _severity_sort_key(issue: dict) -> tuple[int, float, str]:
    sev = str(issue.get("severity", "")).lower()
    rank = 0 if sev == "red" else 1 if sev == "yellow" else 2
    try:
        conf = float(issue.get("confidence", 0) or 0)
    except (TypeError, ValueError):
        conf = 0.0
    label = str(issue.get("label", ""))
    return (rank, -conf, label)


def _sort_issues_by_severity(issues: list[dict]) -> list[dict]:
    return sorted(issues, key=_severity_sort_key)


def _resolve_rule_locales(safe_text: str, detected: str | None) -> tuple[list[str], str | None]:
    """
    Extra locale pattern banks to merge (English Rule.patterns always apply).
    Script hints cover CJK, Hangul, Thai, Devanagari, Bengali, Arabic→ar/fa/ur, Cyrillic→ru/uk.
    Latin locales use detect_document_language.
    """
    forced = os.environ.get("FAIRTERMS_RULE_LOCALES", "").strip().lower()
    if forced:
        out: list[str] = []
        for part in forced.split(","):
            p = part.strip()
            if p in LOCALE_PATTERN_LANGUAGES and p not in out:
                out.append(p)
        doc_lang = detected if detected else (out[0] if out else None)
        return out, doc_lang

    out: list[str] = []
    if detected and detected in LOCALE_PATTERN_LANGUAGES:
        out.append(detected)

    use_script = os.environ.get("FAIRTERMS_SCRIPT_LOCALE_HINT", "1").strip().lower() in (
        "1", "true", "yes", "",
    )
    if use_script:
        for loc in script_locale_hints(safe_text):
            if loc in LOCALE_PATTERN_LANGUAGES and loc not in out:
                out.append(loc)

    doc_lang = detected if detected else (out[0] if out else None)
    if not detected and out:
        refined = _refine_document_language_from_script(safe_text, out)
        if refined:
            doc_lang = refined
    return out, doc_lang


def _merge_issues(rule_issues: list[dict], groq_issues: list[dict] | None) -> list[dict]:
    """
    Rules win for canonical categories. Groq fills canonical gaps. Semantic-only LLM categories
    (snake_case keys not in ALL_CATEGORY_KEYS) are merged separately so multiple distinct findings stay.
    """
    by_cat: dict[str, dict] = {issue["category"]: issue for issue in rule_issues}
    if not groq_issues:
        return list(by_cat.values())

    groq_canonical_added: set[str] = set()
    semantic: list[dict] = []
    seen_semantic: set[tuple[str, str]] = set()

    for g in groq_issues:
        cat = g.get("category")
        if not cat:
            continue
        quote_key = ((g.get("evidence_quote") or "").strip())[:160]

        if cat in ALL_CATEGORY_KEYS:
            if cat in by_cat:
                continue
            if cat in groq_canonical_added:
                continue
            groq_canonical_added.add(cat)
            by_cat[cat] = g
            continue

        dedup = (str(cat), quote_key)
        if dedup in seen_semantic:
            continue
        seen_semantic.add(dedup)
        semantic.append(g)

    return list(by_cat.values()) + semantic


def analyze_contract_text(text: str, source_url: str | None = None) -> dict:
    safe_text = (text or "").strip()
    lowered = safe_text.lower()

    use_detect = os.environ.get("FAIRTERMS_DETECT_LANGUAGE", "1").strip().lower() in (
        "1", "true", "yes", "",
    )
    detected: str | None = detect_document_language(safe_text) if use_detect else None
    extra_locales, document_language = _resolve_rule_locales(safe_text, detected)
    rule_locales_used = ["en"] + extra_locales

    issues: list[dict] = []
    for rule in RULES:
        for compiled_pat in _compiled_patterns_for_rule(rule, extra_locales):
            match = compiled_pat.search(lowered)
            if not match:
                continue
            evidence_quote = _extract_sentence_context(safe_text, match.start(), match.end())
            issues.append(
                {
                    "category": rule.category,
                    "label": rule.label,
                    "severity": rule.severity,
                    "explanation": rule.explanation,
                    # Heuristic tier for sorting vs Groq — not a calibrated probability.
                    "confidence": 0.7 if rule.severity == "red" else 0.6,
                    "evidence_quote": evidence_quote,
                }
            )
            break

    analysis_source = "rules"
    if os.environ.get("GROQ_API_KEY", "").strip():
        groq_issues = analyze_with_groq(safe_text)
        if groq_issues is not None:
            analysis_source = "rules+groq"
            issues = _merge_issues(issues, groq_issues)

    issues = _sort_issues_by_severity(issues)

    return {
        "signal": _pick_signal(issues),
        "source_url": source_url,
        "issue_count": len(issues),
        "issues": issues,
        "analysis_source": analysis_source,
        "document_language": document_language,
        "rule_locales_used": rule_locales_used,
        "disclaimer": "FairTerms provides informational risk signals, not legal advice.",
    }


def _is_decimal_separator_dot(text: str, i: int) -> bool:
    if i < 0 or i >= len(text) or text[i] != ".":
        return False
    before = text[i - 1] if i > 0 else ""
    after = text[i + 1] if i + 1 < len(text) else ""
    return before.isdigit() and after.isdigit()


def _rfind_sentence_period(text: str, end: int) -> int:
    pos = end
    while True:
        j = text.rfind(".", 0, pos)
        if j == -1:
            return -1
        if _is_decimal_separator_dot(text, j):
            pos = j
            continue
        return j


def _find_sentence_period(text: str, start: int) -> int:
    pos = start
    while True:
        j = text.find(".", pos)
        if j == -1:
            return -1
        if _is_decimal_separator_dot(text, j):
            pos = j + 1
            continue
        return j


def _extract_sentence_context(text: str, start_idx: int, end_idx: int) -> str:
    if not text:
        return ""

    left_period = _rfind_sentence_period(text, start_idx)
    left_cjk = text.rfind("\u3002", 0, start_idx)
    left_bound = max(
        left_period, left_cjk,
        text.rfind("\n", 0, start_idx),
        text.rfind(";", 0, start_idx),
    )
    right_period = _find_sentence_period(text, end_idx)
    right_cjk = text.find("\u3002", end_idx)
    right_newline = text.find("\n", end_idx)
    right_semicolon = text.find(";", end_idx)
    candidates = [
        idx for idx in (right_period, right_cjk, right_newline, right_semicolon) if idx != -1
    ]
    right_bound = min(candidates) if candidates else len(text)

    slice_start = 0 if left_bound == -1 else left_bound + 1
    slice_end = len(text) if right_bound == -1 else right_bound + 1
    snippet = text[slice_start:slice_end].strip()

    if len(snippet) <= 320:
        return re.sub(r"\s+", " ", snippet)

    focused = text[max(0, start_idx - 90) : min(len(text), end_idx + 180)].strip()
    return re.sub(r"\s+", " ", focused)
