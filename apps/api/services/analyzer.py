from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Rule:
    category: str
    label: str
    severity: str
    explanation: str
    patterns: list[str]


RULES: list[Rule] = [
    Rule(
        category="auto_renewal",
        label="Auto-Renewal Trap",
        severity="red",
        explanation="This may continue billing automatically unless you cancel in time.",
        patterns=[r"auto[- ]?renew", r"renews? automatically", r"cancel .* before"],
    ),
    Rule(
        category="arbitration_waiver",
        label="Forced Arbitration / Class Waiver",
        severity="red",
        explanation="You may be waiving your right to sue in court or join class actions.",
        patterns=[r"binding arbitration", r"class action waiver", r"waive .* jury trial"],
    ),
    Rule(
        category="data_rights",
        label="Broad Data Rights",
        severity="yellow",
        explanation="This grants broad permissions over your data or content.",
        patterns=[r"perpetual.*license", r"irrevocable.*license", r"share .* third parties?"],
    ),
    Rule(
        category="unilateral_changes",
        label="Unilateral Term Changes",
        severity="yellow",
        explanation="The provider can change terms without direct approval.",
        patterns=[
            r"(may|reserve the right to)\s+(modify|amend|change).{0,80}(terms|agreement|policy)",
            r"changes?\s+to\s+(the\s+)?(terms|agreement|policy)",
            r"without\s+notice.{0,80}(terms|agreement|policy)",
        ],
    ),
    Rule(
        category="cancellation_friction",
        label="Hard-to-Cancel Terms",
        severity="yellow",
        explanation="Cancellation rules may be restrictive or unclear.",
        patterns=[r"non[- ]?refundable", r"no refunds", r"written notice .* cancel"],
    ),
]


def _pick_signal(issues: list[dict]) -> str:
    severities = {issue["severity"] for issue in issues}
    if "red" in severities:
        return "red"
    if "yellow" in severities:
        return "yellow"
    return "green"


def analyze_contract_text(text: str, source_url: str | None = None) -> dict:
    safe_text = (text or "").strip()
    lowered = safe_text.lower()

    issues: list[dict] = []
    for rule in RULES:
        for pattern in rule.patterns:
            match = re.search(pattern, lowered)
            if not match:
                continue

            evidence_quote = _extract_sentence_context(safe_text, match.start(), match.end())

            issues.append(
                {
                    "category": rule.category,
                    "label": rule.label,
                    "severity": rule.severity,
                    "explanation": rule.explanation,
                    "confidence": 0.7 if rule.severity == "red" else 0.6,
                    "evidence_quote": evidence_quote,
                }
            )
            break

    return {
        "signal": _pick_signal(issues),
        "source_url": source_url,
        "issue_count": len(issues),
        "issues": issues,
        "disclaimer": "FairTerms provides informational risk signals, not legal advice.",
    }


def _extract_sentence_context(text: str, start_idx: int, end_idx: int) -> str:
    if not text:
        return ""

    left_bound = max(
        text.rfind(".", 0, start_idx),
        text.rfind("\n", 0, start_idx),
        text.rfind(";", 0, start_idx),
    )
    right_period = text.find(".", end_idx)
    right_newline = text.find("\n", end_idx)
    right_semicolon = text.find(";", end_idx)
    candidates = [idx for idx in (right_period, right_newline, right_semicolon) if idx != -1]
    right_bound = min(candidates) if candidates else len(text)

    slice_start = 0 if left_bound == -1 else left_bound + 1
    slice_end = len(text) if right_bound == -1 else right_bound + 1
    snippet = text[slice_start:slice_end].strip()

    if len(snippet) <= 320:
        return re.sub(r"\s+", " ", snippet)

    focused = text[max(0, start_idx - 90) : min(len(text), end_idx + 180)].strip()
    return re.sub(r"\s+", " ", focused)

