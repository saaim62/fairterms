from __future__ import annotations

import os
import re
from dataclasses import dataclass

from services.groq_analyze import analyze_with_groq


@dataclass
class Rule:
    category: str
    label: str
    severity: str
    explanation: str
    patterns: list[str]


# Aligned with services.groq_analyze.SYSTEM_PROMPT categories and severity guidance.
RULES: list[Rule] = [
    Rule(
        category="zombie_renewal",
        label="Zombie Renewal / Hidden Auto-Renew",
        severity="red",
        explanation="Auto-renewal may be easy to miss, with weak or buried reminders.",
        patterns=[
            r"annual.{0,50}(subscription|renew).{0,80}(no|without).{0,30}(reminder|email|notice)",
            r"auto[- ]?renew.{0,100}(account|settings|profile|submenu)",
            r"renew(s|al)?.{0,40}automatically.{0,80}(no|without).{0,40}(remind|notice|email)",
        ],
    ),
    Rule(
        category="auto_renewal",
        label="Auto-Renewal Terms",
        severity="yellow",
        explanation="Billing may continue automatically; check notice and cancellation windows.",
        patterns=[
            r"auto[- ]?renew",
            r"renews? automatically",
            r"cancel.{0,40}before.{0,40}(next|renew|billing|period)",
            r"trial.{0,60}(convert|end).{0,40}(subscri|charg|bill)",
        ],
    ),
    Rule(
        category="arbitration_waiver",
        label="Forced Arbitration / Class Waiver",
        severity="red",
        explanation="You may be waiving court, jury, or class-action rights.",
        patterns=[
            r"binding arbitration",
            r"class action waiver",
            r"waive.{0,40}jury trial",
            r"individual (basis|claim)",
        ],
    ),
    Rule(
        category="class_bar_standalone",
        label="Class / Representative Action Bar",
        severity="red",
        explanation="Class or representative actions may be barred even apart from arbitration.",
        patterns=[
            r"no class action",
            r"class action.{0,40}waiv",
            r"no representative.{0,30}(action|plaintiff|proceeding)",
            r"representative action.{0,40}waiv",
        ],
    ),
    Rule(
        category="data_succession",
        label="Data Transfer on Sale or Bankruptcy",
        severity="red",
        explanation="Your data may transfer to buyers or successors with little or no new consent.",
        patterns=[
            r"successor.{0,60}(assign|transfer).{0,50}(data|information|personal)",
            r"merger.{0,50}(personal information|user data|your data)",
            r"bankruptcy.{0,70}(data|information|personal|assets)",
            r"acquisition.{0,50}(user data|personal information|customer data)",
        ],
    ),
    Rule(
        category="gag_clauses",
        label="Reviews / Non-Disparagement Restrictions",
        severity="red",
        explanation="Terms may restrict honest reviews, criticism, or public comment.",
        patterns=[
            r"non[- ]disparag",
            r"negative review",
            r"prohibit.{0,50}(public|negative).{0,30}(review|statement|criticism)",
            r"remove.{0,40}(review|content|post|comment)",
        ],
    ),
    Rule(
        category="unilateral_interpretation",
        label="Provider-Only Interpretation",
        severity="red",
        explanation="The company may reserve sole power to interpret or enforce the agreement.",
        patterns=[
            r"sole discretion.{0,50}(interpret|determine|construe|enforce)",
            r"exclusive right.{0,40}interpret",
            r"we (alone|solely).{0,30}determine.{0,40}(breach|compliance|meaning)",
        ],
    ),
    Rule(
        category="liquidated_damages_penalties",
        label="Liquidated Damages / Penalty Fees",
        severity="red",
        explanation="Fixed penalties per breach may be disproportionate and punitive.",
        patterns=[
            r"liquidated damages",
            r"\$\d+.{0,40}(per|each).{0,25}(infraction|violation|breach|instance)",
            r"penalt(y|ies).{0,30}(per|for each).{0,25}breach",
        ],
    ),
    Rule(
        category="perpetual_restraint",
        label="Open-Ended Non-Compete / Survival",
        severity="red",
        explanation="Restrictive duties may survive termination without a clear time limit.",
        patterns=[
            r"non[- ]compete.{0,60}(indefinite|perpetual|without limitation)",
            r"survive.{0,40}termination.{0,60}(indefinite|perpetual|forever)",
            r"non[- ]solicit.{0,50}(indefinite|perpetual)",
        ],
    ),
    Rule(
        category="waiver_of_statutory_rights",
        label="Waiver of Statutory / Consumer Rights",
        severity="red",
        explanation="Language may try to waive rights under consumer or privacy laws.",
        patterns=[
            r"waive.{0,40}(ccpa|gdpr|california consumer)",
            r"magnuson[- ]?moss",
            r"waive.{0,40}(right to repair|statutory)",
        ],
    ),
    Rule(
        category="device_exploitation",
        label="Device / Resource Exploitation",
        severity="red",
        explanation="The service may claim use of your device resources beyond core delivery.",
        patterns=[
            r"crypto[- ]?min",
            r"processing power.{0,50}(device|your computer|your machine)",
            r"bandwidth.{0,40}(peer|p2p|third)",
        ],
    ),
    Rule(
        category="data_rights",
        label="Broad Data / IP Rights",
        severity="yellow",
        explanation="Broad licenses or sharing rights over your data or content.",
        patterns=[
            r"perpetual.{0,30}license",
            r"irrevocable.{0,30}license",
            r"share.{0,50}third parties?",
            r"biometric",
            r"(train|training).{0,40}(model|ai|artificial intelligence)",
            r"commercial purpose.{0,40}(data|information)",
            r"proprietary information.{0,40}(aggregate|deriv)",
        ],
    ),
    Rule(
        category="cross_service_tracking",
        label="Cross-Service Data Use",
        severity="yellow",
        explanation="Data from one product may be combined or reused across other services.",
        patterns=[
            r"cross[- ]service",
            r"across (our |all )?(products|services|properties)",
            r"combine.{0,50}data.{0,40}(services|products|platforms)",
        ],
    ),
    Rule(
        category="retroactive_changes",
        label="Retroactive Policy Changes",
        severity="yellow",
        explanation="Changes may apply to data or conduct that already occurred.",
        patterns=[
            r"retroactive",
            r"prior conduct",
            r"already collected",
            r"data previously",
            r"information (already|previously) (provided|submitted|collected)",
        ],
    ),
    Rule(
        category="unilateral_changes",
        label="Unilateral Term Changes",
        severity="yellow",
        explanation="The provider can change terms; continued use may count as acceptance.",
        patterns=[
            r"(may|reserve the right to)\s+(modify|amend|change).{0,80}(terms|agreement|policy)",
            r"changes?\s+to\s+(the\s+)?(terms|agreement|policy)",
            r"without\s+notice.{0,80}(terms|agreement|policy)",
            r"continued use.{0,50}(constitut|shall constitute|accept)",
            r"posting.{0,50}(terms|notice).{0,40}(effective|constitut)",
        ],
    ),
    Rule(
        category="fee_modification",
        label="Price / Fee Changes",
        severity="yellow",
        explanation="Fees or prices may change with limited notice or automatic tier jumps.",
        patterns=[
            r"(price|fee|rate).{0,40}(change|increase).{0,60}(notice|prior)",
            r"(30|thirty)\s*days?.{0,40}(notice|prior).{0,40}(price|fee)",
            r"unilateral.{0,40}(price|fee|rate|subscription)",
            r"grandfather.{0,40}(expir|end|terminat)",
            r"upgrade.{0,40}(automatic|auto).{0,30}(tier|plan)",
        ],
    ),
    Rule(
        category="cancellation_friction",
        label="Hard-to-Cancel Terms",
        severity="yellow",
        explanation="Cancellation or refunds may be harder than signup or unfair.",
        patterns=[
            r"non[- ]?refundable",
            r"no refunds",
            r"no prorat",
            r"written notice.{0,40}cancel",
            r"(phone|call|chat).{0,40}cancel",
            r"early terminat.{0,40}(fee|penalt)",
            r"cancellation.{0,40}(fee|charg)",
        ],
    ),
    Rule(
        category="one_way_attorneys_fees",
        label="One-Sided Attorneys' Fees",
        severity="yellow",
        explanation="Only the provider may recover legal fees if they prevail.",
        patterns=[
            r"attorneys?.{0,15}fees.{0,50}(we|us|our company|provider).{0,30}prevail",
            r"prevail.{0,40}(we|us).{0,30}attorneys",
            r"recover.{0,30}fees.{0,40}(solely|only).{0,30}(us|we)",
        ],
    ),
    Rule(
        category="no_injunctive_relief",
        label="No Injunctive / Equitable Relief",
        severity="yellow",
        explanation="You may be limited to money damages and unable to stop ongoing harm.",
        patterns=[
            r"no injunctive",
            r"waive.{0,30}injunction",
            r"no.{0,20}equitable relief",
            r"no.{0,30}specific performance",
        ],
    ),
    Rule(
        category="mandatory_delay_tactics",
        label="Mandatory Pre-Suit Delays",
        severity="yellow",
        explanation="You may have to wait through mediation or informal steps before suing.",
        patterns=[
            r"mediat(e|ion).{0,70}before.{0,40}(suit|litigation|court|file)",
            r"\d+\s*days?.{0,50}(mediat|negotiat|informal).{0,40}before.{0,30}(file|suit|court)",
        ],
    ),
    Rule(
        category="no_assignment_by_user",
        label="Assignment: You Can't, They Can",
        severity="yellow",
        explanation="You may not assign the contract while the provider can assign freely.",
        patterns=[
            r"you (may not|cannot) assign.{0,120}(we|us).{0,40}may assign",
            r"non[- ]assignable.{0,80}without.{0,40}(our|written).{0,30}consent",
            r"assignable (solely |only )?by (us|we|company)",
        ],
    ),
    Rule(
        category="overbroad_ip_restrictions",
        label="Restrictive IP / Reverse Engineering",
        severity="yellow",
        explanation="Restrictions on reverse engineering or derivatives may be very broad.",
        patterns=[
            r"reverse engineer",
            r"decompile",
            r"disassemble",
            r"circumvent.{0,40}(technical|technological).{0,30}(measure|protection)",
        ],
    ),
    Rule(
        category="shadow_profiling",
        label="Profiling Beyond Direct Users",
        severity="yellow",
        explanation="Data about non-users, contacts, or broker-augmented profiles may be collected.",
        patterns=[
            r"contacts?.{0,40}(information|data).{0,40}(collect|upload|import)",
            r"data broker",
            r"non[- ]user.{0,40}(data|information)",
            r"supplement.{0,40}(profile|information).{0,40}third",
        ],
    ),
    Rule(
        category="english_language_supremacy",
        label="English-Only Binding Version",
        severity="yellow",
        explanation="Only the English version may be binding despite translations offered.",
        patterns=[
            r"english (version|language).{0,50}(control|govern|prevail|authoritative)",
            r"translation.{0,50}(convenience|informational).{0,40}english",
        ],
    ),
    Rule(
        category="survival_of_termination_vague",
        label="Vague Post-Termination Survival",
        severity="yellow",
        explanation="Vague 'surviving provisions' clauses can leave important terms open-ended.",
        patterns=[
            r"surviv(e|es|ing).{0,30}termination.{0,50}(necessary|material|applicable|appropriate)",
            r"provisions?.{0,30}survive.{0,40}termination.{0,40}(include|such)",
        ],
    ),
    Rule(
        category="limitation_of_liability",
        label="Cap on Damages / Liability Limits",
        severity="yellow",
        explanation="Damages may be capped or consequential losses excluded, limiting recovery.",
        patterns=[
            r"limitation of liability",
            r"limit(ed|ing)?.{0,30}liability.{0,40}(aggregate|total|maximum)",
            r"not liable.{0,40}(consequential|indirect|incidental|special|punitive)",
            r"disclaim.{0,30}(liability|responsibility).{0,40}(damages|loss)",
        ],
    ),
    Rule(
        category="disclaimer_of_warranties",
        label="“As Is” / No Warranties",
        severity="yellow",
        explanation="The service may be offered without meaningful warranties or merchantability.",
        patterns=[
            r"as is\b",
            r"as[- ]available",
            r"disclaimer of warranties",
            r"merchantability",
            r"no warranties?.{0,30}(express|implied)",
            r"without warranty of any kind",
        ],
    ),
    Rule(
        category="broad_indemnity",
        label="Broad Indemnification",
        severity="yellow",
        explanation="You may have to pay the provider’s losses, fees, or third-party claims.",
        patterns=[
            r"indemnif(y|ication).{0,40}(hold harmless|defend)",
            r"you (agree to |will )?indemnif",
            r"reimburse.{0,40}(us|we|our).{0,30}(loss|damage|claim|fee|cost)",
        ],
    ),
    Rule(
        category="forum_selection_exclusive",
        label="Exclusive Court / Venue",
        severity="yellow",
        explanation="Disputes may be forced into specific courts or jurisdictions far from you.",
        patterns=[
            r"exclusive jurisdiction",
            r"exclusive venue",
            r"solely in the (state|federal|courts)",
            r"submit to the (exclusive )?jurisdiction",
            r"venue.{0,40}(shall be|only in|exclusively)",
        ],
    ),
    Rule(
        category="discretionary_termination",
        label="Discretionary Suspension / Termination",
        severity="yellow",
        explanation="The provider may cut off access with broad or unclear discretion.",
        patterns=[
            r"(suspend|terminate).{0,40}(account|access|service).{0,50}(sole discretion|at any time|without (notice|cause|liability))",
            r"sole discretion.{0,40}(suspend|terminat|refuse service)",
            r"refuse service.{0,40}(anyone|any reason|our discretion)",
        ],
    ),
    Rule(
        category="children_data_collection",
        label="Children / Minors Data",
        severity="yellow",
        explanation="Terms may address under-13 or minor data in ways worth reviewing.",
        patterns=[
            r"under (the age of )?13",
            r"children.{0,40}(personal information|data|privacy)",
            r"parental consent",
            r"not intended for children",
            r"do not collect.{0,40}(children|minors)",
        ],
    ),
    Rule(
        category="marketing_communications_burden",
        label="Marketing / Communications Opt-Out",
        severity="yellow",
        explanation="Promotional messages or SMS may be hard to opt out of or bundled with service notices.",
        patterns=[
            r"marketing.{0,40}(email|message|text|sms|call)",
            r"promotional.{0,40}(communication|offer|material)",
            r"by (continuing|signing|registering).{0,50}(consent|agree).{0,30}(market|promo|sms)",
            r"cannot opt[- ]?out.{0,40}(transactional|service|essential)",
        ],
    ),
]


def _pick_signal(issues: list[dict]) -> str:
    severities = {issue["severity"] for issue in issues}
    if "red" in severities:
        return "red"
    if "yellow" in severities:
        return "yellow"
    return "green"


def _merge_issues(rule_issues: list[dict], groq_issues: list[dict] | None) -> list[dict]:
    """Prefer rule-based hit per category; add Groq-only categories."""
    by_cat: dict[str, dict] = {}
    for issue in rule_issues:
        by_cat[issue["category"]] = issue

    if not groq_issues:
        return list(by_cat.values())

    for g in groq_issues:
        cat = g.get("category")
        if not cat or cat in by_cat:
            continue
        by_cat[cat] = g

    return list(by_cat.values())


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

    analysis_source = "rules"
    if os.environ.get("GROQ_API_KEY", "").strip():
        groq_issues = analyze_with_groq(safe_text)
        if groq_issues is not None:
            analysis_source = "rules+groq"
            issues = _merge_issues(issues, groq_issues)

    return {
        "signal": _pick_signal(issues),
        "source_url": source_url,
        "issue_count": len(issues),
        "issues": issues,
        "analysis_source": analysis_source,
        "disclaimer": "FairTerms provides informational risk signals, not legal advice.",
    }


def _is_decimal_separator_dot(text: str, i: int) -> bool:
    """True if '.' at i is part of a number like 1.5, 2.1, $3.99 (digit on both sides)."""
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
    left_bound = max(
        left_period,
        text.rfind("\n", 0, start_idx),
        text.rfind(";", 0, start_idx),
    )
    right_period = _find_sentence_period(text, end_idx)
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

