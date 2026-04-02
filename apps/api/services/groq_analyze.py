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

ALLOWED_CATEGORIES = frozenset(
    {
        "auto_renewal",
        "zombie_renewal",
        "arbitration_waiver",
        "class_bar_standalone",
        "data_rights",
        "data_succession",
        "cross_service_tracking",
        "unilateral_changes",
        "retroactive_changes",
        "cancellation_friction",
        "fee_modification",
        "gag_clauses",
        "unilateral_interpretation",
        "liquidated_damages_penalties",
        "one_way_attorneys_fees",
        "no_injunctive_relief",
        "mandatory_delay_tactics",
        "perpetual_restraint",
        "no_assignment_by_user",
        "overbroad_ip_restrictions",
        "device_exploitation",
        "shadow_profiling",
        "waiver_of_statutory_rights",
        "english_language_supremacy",
        "survival_of_termination_vague",
        "limitation_of_liability",
        "disclaimer_of_warranties",
        "broad_indemnity",
        "forum_selection_exclusive",
        "discretionary_termination",
        "children_data_collection",
        "marketing_communications_burden",
    }
)

SYSTEM_PROMPT = """You are FairTerms, a forensic contract analyzer. Identify consumer-harmful clauses matching these EXACT categories:

EXISTING CATEGORIES (enhanced detection):
- auto_renewal: negative-option billing, auto-conversion of trials WITHOUT 7+ day clear notice, lacking email reminders before charge, or requiring cancellation BEFORE next period (vs anytime during period)
- zombie_renewal: auto-renewal designed to exploit forgetfulness (annual subscriptions with no 30-day reminder, or hiding auto-renew status in account submenus)
- arbitration_waiver: forced arbitration, class action bans, jury trial waivers
- class_bar_standalone: class action waiver IN ADDITION TO arbitration (survives even if arbitration struck down), or "no representative actions" clauses
- data_rights: perpetual/irrevocable licenses, AI/biometric data training rights, "commercial purposes" sharing, aggregation rights claiming data becomes "our proprietary information"
- data_succession: right to transfer/sell user data to successors/acquirers in bankruptcy/M&A without notice or new consent ("asset transfer" clauses)
- cross_service_tracking: combining data across distinct products/services (e.g., using shopping data for credit scoring) without explicit opt-in for specific secondary use
- unilateral_changes: changes effective immediately upon posting, "continued use = consent" for material terms, or applying changes retroactively to past conduct/data
- retroactive_changes: specifically applies to data already collected or conduct already occurred (not prospective-only)
- cancellation_friction: no prorated refunds, requiring phone/chat to cancel when signup was digital, early termination fees, or waiting periods before cancellation effective
- fee_modification: unilateral price increases with <30 days notice, "grandfathering" expiration without specific warning, automatic tier upgrades upon usage thresholds without per-instance confirmation

NEW HIGH-RISK CATEGORIES (commonly hidden):
- gag_clauses: prohibitions on negative reviews, disparagement, public criticism, or requiring removal of content/social media posts; "non-disparagement" obligations
- unilateral_interpretation: "we retain exclusive right to interpret these terms," "terms mean what we say they mean," or reserving sole discretion to determine breach/compliance
- liquidated_damages_penalties: predetermined monetary penalties for breach that are grossly disproportionate (e.g., $500 per infraction) functioning as punishment rather than estimate of actual damages
- one_way_attorneys_fees: prevailing party provision where ONLY provider can recover fees, or asymmetrical recovery (provider gets fees in broader circumstances than user)
- no_injunctive_relief: user cannot seek injunctions, restraining orders, or specific performance to stop ongoing harm (must settle for money damages after the fact)
- mandatory_delay_tactics: must engage in mediation/negotiation for 30-90 days before filing suit, or informal dispute resolution requirements designed to exhaust patience/statute of limitations
- perpetual_restraint: non-compete, non-solicit, non-disparagement, or confidentiality obligations surviving termination indefinitely (no time limit), or applying to former customers/employees broadly
- no_assignment_by_user: user cannot assign/transfer rights under contract, but provider can assign freely to any third party (including debt collectors/data brokers)
- overbroad_ip_restrictions: prohibition on reverse engineering even for security research/interoperability where legally permitted; claiming ownership of user modifications/derivatives of open-source components
- device_exploitation: claiming right to use user's device processing power (cryptomining), bandwidth (P2P networking), or storage for provider's benefit beyond core service delivery
- shadow_profiling: collecting data on non-users (contacts, "friends," site visitors without accounts) or supplementing profiles with third-party data broker information
- waiver_of_statutory_rights: disclaiming rights under specific consumer protection laws (CCPA opt-out, GDPR rights, Magnuson-Moss warranty rights, right to repair)
- english_language_supremacy: only English version binding despite offering translations, or user waives right to rely on local language version (problematic in EU/jurisdictions with language rights)
- survival_of_termination_vague: "survival necessary provisions" without specificity, allowing provider to later claim indefinite survival of advantageous clauses (payment, IP, confidentiality) while claiming expiration of obligations
- limitation_of_liability: caps on total liability, exclusion of consequential/indirect/punitive damages, or broad "not liable" carve-outs
- disclaimer_of_warranties: "as is," "as available," disclaimer of implied warranties/merchantability/fitness
- broad_indemnity: user must indemnify, defend, or hold harmless provider (or reimburse fees/costs) for broad third-party claims
- forum_selection_exclusive: exclusive jurisdiction/venue in specific courts or states/countries
- discretionary_termination: suspend/terminate accounts or service at sole discretion, without notice/cause, or refuse service broadly
- children_data_collection: under-13/children data practices, parental consent, or age restrictions
- marketing_communications_burden: marketing/SMS/calls consent bundled with signup, or difficult/impossible opt-out from promotional messages

SEVERITY RULES:
RED (immediate danger): arbitration/class waivers, zombie_renewal with no reminders, liquidated_damages_penalties >$500, gag_clauses prohibiting reviews, unilateral_interpretation, data_succession without consent, perpetual_restraint, waiver_of_statutory_rights (GDPR/CCPA), device_exploitation
YELLOW (significant concern): auto_renewal with poor notice, cross_service_tracking, retroactive_changes, one_way_attorneys_fees, no_injunctive_relief, mandatory_delay_tactics, auto_upgrade_traps

OUTPUT FORMAT (STRICT JSON, NO MARKDOWN):
{"issues":[{"category":"exact_key_from_list","label":"Short Human Title","severity":"red"|"yellow","explanation":"Why this hurts consumers, in plain language. Mention specific unfairness mechanism.","confidence":0.0-1.0,"evidence_quote":"EXACT verbatim substring from input, max 400 chars, no paraphrasing"}]}

CONSTRAINTS:
- Max 10 issues, ranked: RED severity first, then confidence, then consumer financial impact
- evidence_quote MUST be verbatim. If clause spans non-contiguous sections or requires inference, SKIP the issue (do not paraphrase)
- If clause uses synonyms (e.g., "eternal" vs "perpetual"), map to correct category but quote verbatim
- For unilateral_changes vs retroactive_changes: use retroactive_changes ONLY if text explicitly states changes apply to past conduct/data; otherwise use unilateral_changes
- For auto_renewal vs zombie_renewal: use zombie_renewal ONLY if text reveals deliberate dark pattern (no reminders, burying status) vs standard auto-renewal
- If nothing applies: {"issues":[]}
- No markdown code blocks, no trailing commas, valid JSON only
"""


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
    excerpt = _truncate(text, int(os.environ.get("GROQ_MAX_INPUT_CHARS", "14000")))

    logger.info(
        "Groq: request model=%s excerpt_chars=%s input_chars=%s",
        model,
        len(excerpt),
        len((text or "").strip()),
    )

    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=api_key)

    try:
        completion = client.chat.completions.create(
            model=model,
            temperature=0.15,
            max_tokens=2048,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Analyze this terms/policy text:\n\n{excerpt}",
                },
            ],
        )
    except Exception as exc:
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
    for item in issues_raw[:10]:
        if not isinstance(item, dict):
            skipped.append("non-dict item")
            continue
        cat = str(item.get("category", "")).strip()
        if cat not in ALLOWED_CATEGORIES:
            skipped.append(f"bad category={cat!r}")
            continue
        sev = str(item.get("severity", "")).strip().lower()
        if sev not in ("red", "yellow"):
            skipped.append(f"bad severity={sev!r} cat={cat}")
            continue
        label = str(item.get("label", "")).strip() or cat.replace("_", " ").title()
        expl = str(item.get("explanation", "")).strip()
        quote_raw = str(item.get("evidence_quote", "")).strip()
        quote = _evidence_in_excerpt(quote_raw, excerpt)
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
