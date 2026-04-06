"""Optional Groq (OpenAI-compatible) LLM pass for richer clause detection."""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

logger = logging.getLogger(__name__)

# Set FAIRTERMS_LOG_LLM_FULL=1 to log full raw JSON body (can be large).
_LOG_FULL = os.environ.get("FAIRTERMS_LOG_LLM_FULL", "").strip() in ("1", "true", "yes")
_RAW_PREVIEW_LEN = int(os.environ.get("FAIRTERMS_LOG_LLM_PREVIEW", "800"))

from services.category_registry import ALL_CATEGORY_KEYS, CATEGORY_REGISTRY

# Canonical keys (regex rules + locale patterns). LLM may also emit new snake_case keys; see normalize_llm_category.
CANONICAL_CATEGORIES = ALL_CATEGORY_KEYS

# New semantic-only IDs from the model: lowercase, underscores, 3–64 chars, no double underscores.
_DYNAMIC_CATEGORY_RE = re.compile(r"^[a-z][a-z0-9_]{2,63}$")


def normalize_llm_category(raw: str) -> str | None:
    """
    Return a normalized category key if the model output is allowed, else None.

    Either a known canonical key or a new snake_case identifier for clauses that
    do not fit the fixed taxonomy (semantic / open-ended AI findings).
    """
    cat = (raw or "").strip().lower().replace(" ", "_")
    if not cat:
        return None
    if cat in CANONICAL_CATEGORIES:
        return cat
    if "__" in cat or not _DYNAMIC_CATEGORY_RE.fullmatch(cat):
        return None
    return cat

def _build_category_table() -> str:
    red = [c for c in CATEGORY_REGISTRY if c.severity == "red"]
    yellow = [c for c in CATEGORY_REGISTRY if c.severity == "yellow"]
    lines = ["RED categories (immediate danger):"]
    for c in red:
        lines.append(f"- {c.key}: {c.explanation}")
    lines.append("\nYELLOW categories (significant concern):")
    for c in yellow:
        lines.append(f"- {c.key}: {c.explanation}")
    return "\n".join(lines)


SYSTEM_PROMPT = f"""You are FairTerms, a forensic contract analyzer. Identify consumer-harmful clauses.

{_build_category_table()}

SEMANTIC / OPEN-ENDED DETECTION (important):
- Prefer a `category` from the lists above when it clearly fits.
- When a clause is unfair or risky but does NOT match any key above, still report it: invent a short
  snake_case `category` (lowercase letters, digits, underscores only; 3–64 chars; e.g. mandatory_insurance_bundle,
  opaque_fee_stacking). Put the human-readable name in `label` and the reasoning in `explanation`.
- Do not skip harmful language just because it is not in the fixed list—that is the main job of the AI pass.

OUTPUT (strict JSON, no markdown):
{{"issues":[{{"category":"key_from_list_or_new_snake_case","label":"Short Title","severity":"red"|"yellow","explanation":"Why harmful, plain language.","confidence":0.0-1.0,"evidence_quote":"EXACT verbatim substring, max 400 chars"}}]}}

RULES:
- Return ALL matching issues, RED first, then confidence, then financial impact.
- evidence_quote MUST be verbatim from input. If quote spans non-contiguous text, SKIP.
- retroactive_changes only if text explicitly covers past data/conduct; else unilateral_changes.
- zombie_renewal only for deliberate dark patterns (no reminders, buried settings); else auto_renewal.
- If nothing applies: {{"issues":[]}}
- Valid JSON only, no trailing commas.
"""


def _explanation_language_directive() -> str:
    mode = os.environ.get("FAIRTERMS_EXPLANATION_LANGUAGE", "same_as_input").strip().lower()
    if mode in ("en", "english"):
        return (
            "Write `label` and `explanation` in clear English even when `evidence_quote` is in another language."
        )
    return (
        "Write `label` and `explanation` in the same language as the quoted clause "
        "(the dominant language of that snippet)."
    )


def build_system_prompt() -> str:
    return (
        SYSTEM_PROMPT
        + "\n\nMULTILINGUAL ANALYSIS:\n"
        "- The contract may be in ANY human language (including mixed languages).\n"
        "- FairTerms targets global ToS: treat English, Chinese, Spanish, Hindi, Arabic, French, Portuguese, "
        "Russian, Urdu, Bengali, German, Japanese, Korean, Turkish, Indonesian, Vietnamese, Italian, Dutch, "
        "Polish, Thai, Swahili, Persian, Malay, Filipino/Tagalog, and Ukrainian the same as any other language.\n"
        "- `category`: use a key from the lists above when it fits; otherwise a new concise snake_case id "
        "(lowercase, underscores, 3–64 chars) for risks that have no listed key.\n"
        "- `evidence_quote` MUST be copied verbatim from the input (exact substring; same script, spelling, punctuation).\n"
        "- "
        + _explanation_language_directive()
        + "\n- Do not translate `evidence_quote`. Do not invent text not present in the input.\n"
    )


def _truncate(text: str, max_chars: int) -> str:
    t = (text or "").strip()
    if len(t) <= max_chars:
        return t
    return t[: max_chars - 20] + "\n...[truncated]..."


def _strip_outer_quotes(s: str) -> str:
    """Remove wrapping ASCII or curly quotes LLMs sometimes include in evidence_quote."""
    t = (s or "").strip()
    for _ in range(4):
        changed = False
        if len(t) >= 2:
            if (t[0] == t[-1] == '"') or (t[0] == t[-1] == "'"):
                t = t[1:-1].strip()
                changed = True
            elif t.startswith("\u201c") and t.endswith("\u201d"):
                t = t[1:-1].strip()
                changed = True
            elif t.startswith("\u2018") and t.endswith("\u2019"):
                t = t[1:-1].strip()
                changed = True
        if not changed:
            break
    return t


def _unify_typographic(s: str) -> str:
    """1:1 replacements so indices stay aligned with original string."""
    return (
        s.replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u201e", '"')
        .replace("\u201f", '"')
        .replace("\u00ab", '"')
        .replace("\u00bb", '"')
        .replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u201a", "'")
        .replace("\u201b", "'")
        .replace("\u2013", "-")
        .replace("\u2014", "-")
    )


def _evidence_in_excerpt(quote: str, excerpt: str) -> str | None:
    """Return quote text to persist if it appears in excerpt (after light normalization)."""
    raw = (quote or "").strip()
    if not raw:
        return None
    if raw in excerpt:
        return raw
    stripped = _strip_outer_quotes(raw)
    if stripped and stripped in excerpt:
        return stripped
    u_ex = _unify_typographic(excerpt)
    u_q = _unify_typographic(stripped or raw)
    if u_q and u_q in u_ex:
        idx = u_ex.find(u_q)
        end = idx + len(u_q)
        return excerpt[idx:end]
    return None


def _groq_payload_too_large(exc: BaseException) -> bool:
    msg = str(exc).lower()
    if getattr(exc, "status_code", None) == 413:
        return True
    if "413" in str(exc):
        return True
    if "too large" in msg or "reduce your message" in msg:
        return True
    if "rate_limit_exceeded" in msg and ("token" in msg or "tpm" in msg):
        return True
    return False


def analyze_with_groq(text: str) -> list[dict[str, Any]] | None:
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        logger.debug("Groq: skipped (GROQ_API_KEY not set)")
        return None

    try:
        from openai import OpenAI
    except ImportError:
        logger.warning("Groq: skipped (openai package not installed)")
        return None

    model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
    max_chars = int(os.environ.get("GROQ_MAX_INPUT_CHARS", "9000"))
    excerpt = _truncate(text, max_chars)
    excerpt_for_validation = excerpt

    logger.info(
        "Groq: request model=%s excerpt_chars=%s input_chars=%s",
        model,
        len(excerpt),
        len((text or "").strip()),
    )

    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=api_key)
    system_prompt = build_system_prompt()

    def _create(user_excerpt: str):
        return client.chat.completions.create(
            model=model,
            temperature=0.15,
            max_tokens=1536,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Analyze this terms/policy text:\n\n{user_excerpt}",
                },
            ],
        )

    try:
        completion = _create(excerpt)
    except Exception as exc:
        if _groq_payload_too_large(exc) and len(excerpt) > 4800:
            retry_cap = max(4500, len(excerpt) // 2)
            excerpt = _truncate(text, retry_cap)
            excerpt_for_validation = excerpt
            logger.warning(
                "Groq: payload/rate limit error (%s), retry excerpt_chars=%s",
                type(exc).__name__,
                len(excerpt),
            )
            try:
                completion = _create(excerpt)
            except Exception as exc2:
                logger.exception("Groq: retry failed: %s", exc2)
                return None
        else:
            logger.exception("Groq: API request failed: %s", exc)
            return None

    raw = completion.choices[0].message.content or "{}"
    finish = getattr(completion.choices[0], "finish_reason", None)
    usage = getattr(completion, "usage", None)
    if usage is not None:
        logger.info(
            "Groq: response finish_reason=%s prompt_tokens=%s completion_tokens=%s total=%s",
            finish,
            getattr(usage, "prompt_tokens", None),
            getattr(usage, "completion_tokens", None),
            getattr(usage, "total_tokens", None),
        )
    else:
        logger.info("Groq: response finish_reason=%s (no usage metadata)", finish)

    if _LOG_FULL:
        logger.info("Groq: raw message content:\n%s", raw)
    else:
        preview = raw if len(raw) <= _RAW_PREVIEW_LEN else raw[:_RAW_PREVIEW_LEN] + "…[truncated]"
        logger.info("Groq: raw preview (%s chars):\n%s", len(raw), preview)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as first_err:
        m = re.search(r"\{[\s\S]*\}", raw)
        if not m:
            logger.warning("Groq: JSON parse failed, no brace block: %s", first_err)
            return None
        try:
            data = json.loads(m.group(0))
        except json.JSONDecodeError as second_err:
            logger.warning("Groq: JSON parse failed after extract: %s", second_err)
            return None

    issues_raw = data.get("issues")
    if not isinstance(issues_raw, list):
        logger.warning(
            "Groq: expected issues list, got %s keys=%s",
            type(issues_raw).__name__,
            list(data.keys()) if isinstance(data, dict) else None,
        )
        return None

    out: list[dict[str, Any]] = []
    skipped: list[str] = []
    for item in issues_raw:
        if not isinstance(item, dict):
            skipped.append("non-dict item")
            continue
        cat = normalize_llm_category(str(item.get("category", "")))
        if not cat:
            skipped.append(f"bad category={item.get('category')!r}")
            continue
        sev = str(item.get("severity", "")).strip().lower()
        if sev not in ("red", "yellow"):
            skipped.append(f"bad severity={sev!r} cat={cat}")
            continue
        label = str(item.get("label", "")).strip() or cat.replace("_", " ").title()
        expl = str(item.get("explanation", "")).strip()
        quote_raw = str(item.get("evidence_quote", "")).strip()
        quote = _evidence_in_excerpt(quote_raw, excerpt_for_validation)
        if not quote:
            skipped.append(f"quote not in excerpt cat={cat} quote_len={len(quote_raw)}")
            continue
        try:
            conf = float(item.get("confidence", 0.75))
        except (TypeError, ValueError):
            conf = 0.75
        conf = max(0.0, min(1.0, conf))
        out.append(
            {
                "category": cat,
                "label": label,
                "severity": sev,
                "explanation": expl or "Flagged by AI review.",
                "confidence": conf,
                "evidence_quote": quote[:500],
            }
        )
    if skipped:
        logger.info("Groq: dropped %s candidate(s): %s", len(skipped), "; ".join(skipped[:12]))
    logger.info(
        "Groq: accepted_issues=%s from_llm_items=%s",
        len(out),
        len(issues_raw),
    )
    return out
