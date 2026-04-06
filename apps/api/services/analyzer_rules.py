"""Deterministic clause-detection rules: pattern lists compiled once at import."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from services.category_registry import get_explanation, get_label, get_severity


@dataclass
class Rule:
    category: str
    label: str
    severity: str
    explanation: str
    patterns: list[str]
    compiled: list[re.Pattern[str]] = field(default_factory=list, repr=False)


RULES: list[Rule] = [
    Rule(
        category="zombie_renewal",
        label=get_label("zombie_renewal"),
        severity=get_severity("zombie_renewal"),
        explanation=get_explanation("zombie_renewal"),
        patterns=[
            r"annual.{0,50}(subscription|renew).{0,80}(no|without).{0,30}(reminder|email|notice)",
            r"auto[- ]?renew.{0,100}(account|settings|profile|submenu)",
            r"renew(s|al)?.{0,40}automatically.{0,80}(no|without).{0,40}(remind|notice|email)",
        ],
    ),
    Rule(
        category="auto_renewal",
        label=get_label("auto_renewal"),
        severity=get_severity("auto_renewal"),
        explanation=get_explanation("auto_renewal"),
        patterns=[
            r"auto[- ]?renew",
            r"renews? automatically",
            r"cancel.{0,40}before.{0,40}(next|renew|billing|period)",
            r"trial.{0,60}(convert|end).{0,40}(subscri|charg|bill)",
        ],
    ),
    Rule(
        category="arbitration_waiver",
        label=get_label("arbitration_waiver"),
        severity=get_severity("arbitration_waiver"),
        explanation=get_explanation("arbitration_waiver"),
        patterns=[
            r"binding arbitration",
            r"class action waiver",
            r"waive.{0,40}jury trial",
            r"individual (basis|claim)",
        ],
    ),
    Rule(
        category="class_bar_standalone",
        label=get_label("class_bar_standalone"),
        severity=get_severity("class_bar_standalone"),
        explanation=get_explanation("class_bar_standalone"),
        patterns=[
            r"no class action",
            r"class action.{0,40}waiv",
            r"no representative.{0,30}(action|plaintiff|proceeding)",
            r"representative action.{0,40}waiv",
        ],
    ),
    Rule(
        category="data_succession",
        label=get_label("data_succession"),
        severity=get_severity("data_succession"),
        explanation=get_explanation("data_succession"),
        patterns=[
            r"successor.{0,60}(assign|transfer).{0,50}(data|information|personal)",
            r"merger.{0,50}(personal information|user data|your data)",
            r"bankruptcy.{0,70}(data|information|personal|assets)",
            r"acquisition.{0,50}(user data|personal information|customer data)",
        ],
    ),
    Rule(
        category="gag_clauses",
        label=get_label("gag_clauses"),
        severity=get_severity("gag_clauses"),
        explanation=get_explanation("gag_clauses"),
        patterns=[
            r"non[- ]disparag",
            r"negative review",
            r"prohibit.{0,50}(public|negative).{0,30}(review|statement|criticism)",
            r"remove.{0,40}(review|content|post|comment)",
        ],
    ),
    Rule(
        category="unilateral_interpretation",
        label=get_label("unilateral_interpretation"),
        severity=get_severity("unilateral_interpretation"),
        explanation=get_explanation("unilateral_interpretation"),
        patterns=[
            r"sole discretion.{0,50}(interpret|determine|construe|enforce)",
            r"exclusive right.{0,40}interpret",
            r"we (alone|solely).{0,30}determine.{0,40}(breach|compliance|meaning)",
        ],
    ),
    Rule(
        category="liquidated_damages_penalties",
        label=get_label("liquidated_damages_penalties"),
        severity=get_severity("liquidated_damages_penalties"),
        explanation=get_explanation("liquidated_damages_penalties"),
        patterns=[
            r"liquidated damages",
            r"\$\d+.{0,40}(per|each).{0,25}(infraction|violation|breach|instance)",
            r"penalt(y|ies).{0,30}(per|for each).{0,25}breach",
        ],
    ),
    Rule(
        category="perpetual_restraint",
        label=get_label("perpetual_restraint"),
        severity=get_severity("perpetual_restraint"),
        explanation=get_explanation("perpetual_restraint"),
        patterns=[
            r"non[- ]compete.{0,60}(indefinite|perpetual|without limitation)",
            r"survive.{0,40}termination.{0,60}(indefinite|perpetual|forever)",
            r"non[- ]solicit.{0,50}(indefinite|perpetual)",
        ],
    ),
    Rule(
        category="waiver_of_statutory_rights",
        label=get_label("waiver_of_statutory_rights"),
        severity=get_severity("waiver_of_statutory_rights"),
        explanation=get_explanation("waiver_of_statutory_rights"),
        patterns=[
            r"waive.{0,40}(ccpa|gdpr|california consumer)",
            r"magnuson[- ]?moss",
            r"waive.{0,40}(right to repair|statutory)",
        ],
    ),
    Rule(
        category="device_exploitation",
        label=get_label("device_exploitation"),
        severity=get_severity("device_exploitation"),
        explanation=get_explanation("device_exploitation"),
        patterns=[
            r"crypto[- ]?min",
            r"processing power.{0,50}(device|your computer|your machine)",
            r"bandwidth.{0,40}(peer|p2p|third)",
        ],
    ),
    Rule(
        category="data_rights",
        label=get_label("data_rights"),
        severity=get_severity("data_rights"),
        explanation=get_explanation("data_rights"),
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
        label=get_label("cross_service_tracking"),
        severity=get_severity("cross_service_tracking"),
        explanation=get_explanation("cross_service_tracking"),
        patterns=[
            r"cross[- ]service",
            r"across (our |all )?(products|services|properties)",
            r"combine.{0,50}data.{0,40}(services|products|platforms)",
        ],
    ),
    Rule(
        category="retroactive_changes",
        label=get_label("retroactive_changes"),
        severity=get_severity("retroactive_changes"),
        explanation=get_explanation("retroactive_changes"),
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
        label=get_label("unilateral_changes"),
        severity=get_severity("unilateral_changes"),
        explanation=get_explanation("unilateral_changes"),
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
        label=get_label("fee_modification"),
        severity=get_severity("fee_modification"),
        explanation=get_explanation("fee_modification"),
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
        label=get_label("cancellation_friction"),
        severity=get_severity("cancellation_friction"),
        explanation=get_explanation("cancellation_friction"),
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
        label=get_label("one_way_attorneys_fees"),
        severity=get_severity("one_way_attorneys_fees"),
        explanation=get_explanation("one_way_attorneys_fees"),
        patterns=[
            r"attorneys?.{0,15}fees.{0,50}(we|us|our company|provider).{0,30}prevail",
            r"prevail.{0,40}(we|us).{0,30}attorneys",
            r"recover.{0,30}fees.{0,40}(solely|only).{0,30}(us|we)",
        ],
    ),
    Rule(
        category="no_injunctive_relief",
        label=get_label("no_injunctive_relief"),
        severity=get_severity("no_injunctive_relief"),
        explanation=get_explanation("no_injunctive_relief"),
        patterns=[
            r"no injunctive",
            r"waive.{0,30}injunction",
            r"no.{0,20}equitable relief",
            r"no.{0,30}specific performance",
        ],
    ),
    Rule(
        category="mandatory_delay_tactics",
        label=get_label("mandatory_delay_tactics"),
        severity=get_severity("mandatory_delay_tactics"),
        explanation=get_explanation("mandatory_delay_tactics"),
        patterns=[
            r"mediat(e|ion).{0,70}before.{0,40}(suit|litigation|court|file)",
            r"\d+\s*days?.{0,50}(mediat|negotiat|informal).{0,40}before.{0,30}(file|suit|court)",
        ],
    ),
    Rule(
        category="no_assignment_by_user",
        label=get_label("no_assignment_by_user"),
        severity=get_severity("no_assignment_by_user"),
        explanation=get_explanation("no_assignment_by_user"),
        patterns=[
            r"you (may not|cannot) assign.{0,120}(we|us).{0,40}may assign",
            r"non[- ]assignable.{0,80}without.{0,40}(our|written).{0,30}consent",
            r"assignable (solely |only )?by (us|we|company)",
        ],
    ),
    Rule(
        category="overbroad_ip_restrictions",
        label=get_label("overbroad_ip_restrictions"),
        severity=get_severity("overbroad_ip_restrictions"),
        explanation=get_explanation("overbroad_ip_restrictions"),
        patterns=[
            r"reverse engineer",
            r"decompile",
            r"disassemble",
            r"circumvent.{0,40}(technical|technological).{0,30}(measure|protection)",
        ],
    ),
    Rule(
        category="shadow_profiling",
        label=get_label("shadow_profiling"),
        severity=get_severity("shadow_profiling"),
        explanation=get_explanation("shadow_profiling"),
        patterns=[
            r"contacts?.{0,40}(information|data).{0,40}(collect|upload|import)",
            r"data broker",
            r"non[- ]user.{0,40}(data|information)",
            r"supplement.{0,40}(profile|information).{0,40}third",
        ],
    ),
    Rule(
        category="english_language_supremacy",
        label=get_label("english_language_supremacy"),
        severity=get_severity("english_language_supremacy"),
        explanation=get_explanation("english_language_supremacy"),
        patterns=[
            r"english (version|language).{0,50}(control|govern|prevail|authoritative)",
            r"translation.{0,50}(convenience|informational).{0,40}english",
        ],
    ),
    Rule(
        category="survival_of_termination_vague",
        label=get_label("survival_of_termination_vague"),
        severity=get_severity("survival_of_termination_vague"),
        explanation=get_explanation("survival_of_termination_vague"),
        patterns=[
            r"surviv(e|es|ing).{0,30}termination.{0,50}(necessary|material|applicable|appropriate)",
            r"provisions?.{0,30}survive.{0,40}termination.{0,40}(include|such)",
        ],
    ),
    Rule(
        category="limitation_of_liability",
        label=get_label("limitation_of_liability"),
        severity=get_severity("limitation_of_liability"),
        explanation=get_explanation("limitation_of_liability"),
        patterns=[
            r"limitation of liability",
            r"limit(ed|ing)?.{0,30}liability.{0,40}(aggregate|total|maximum)",
            r"not liable.{0,40}(consequential|indirect|incidental|special|punitive)",
            r"disclaim.{0,30}(liability|responsibility).{0,40}(damages|loss)",
        ],
    ),
    Rule(
        category="disclaimer_of_warranties",
        label=get_label("disclaimer_of_warranties"),
        severity=get_severity("disclaimer_of_warranties"),
        explanation=get_explanation("disclaimer_of_warranties"),
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
        label=get_label("broad_indemnity"),
        severity=get_severity("broad_indemnity"),
        explanation=get_explanation("broad_indemnity"),
        patterns=[
            r"indemnif(y|ication).{0,40}(hold harmless|defend)",
            r"you (agree to |will )?indemnif",
            r"reimburse.{0,40}(us|we|our).{0,30}(loss|damage|claim|fee|cost)",
        ],
    ),
    Rule(
        category="forum_selection_exclusive",
        label=get_label("forum_selection_exclusive"),
        severity=get_severity("forum_selection_exclusive"),
        explanation=get_explanation("forum_selection_exclusive"),
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
        label=get_label("discretionary_termination"),
        severity=get_severity("discretionary_termination"),
        explanation=get_explanation("discretionary_termination"),
        patterns=[
            r"(suspend|terminate).{0,40}(account|access|service).{0,50}(sole discretion|at any time|without (notice|cause|liability))",
            r"sole discretion.{0,40}(suspend|terminat|refuse service)",
            r"refuse service.{0,40}(anyone|any reason|our discretion)",
        ],
    ),
    Rule(
        category="children_data_collection",
        label=get_label("children_data_collection"),
        severity=get_severity("children_data_collection"),
        explanation=get_explanation("children_data_collection"),
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
        label=get_label("marketing_communications_burden"),
        severity=get_severity("marketing_communications_burden"),
        explanation=get_explanation("marketing_communications_burden"),
        patterns=[
            r"marketing.{0,40}(email|message|text|sms|call)",
            r"promotional.{0,40}(communication|offer|material)",
            r"by (continuing|signing|registering).{0,50}(consent|agree).{0,30}(market|promo|sms)",
            r"cannot opt[- ]?out.{0,40}(transactional|service|essential)",
        ],
    ),
    Rule(
        category="data_selling",
        label=get_label("data_selling"),
        severity=get_severity("data_selling"),
        explanation=get_explanation("data_selling"),
        patterns=[
            r"(sell|sale of).{0,40}(personal data|personal information|user data)",
            r"monetize.{0,40}(personal information|your data)",
        ],
    ),
    Rule(
        category="private_message_monitoring",
        label=get_label("private_message_monitoring"),
        severity=get_severity("private_message_monitoring"),
        explanation=get_explanation("private_message_monitoring"),
        patterns=[
            r"(read|monitor|scan|review).{0,50}(private message|direct message|dms|communications)",
            r"access.{0,30}(inbox|private content|direct message)",
        ],
    ),
    Rule(
        category="device_fingerprinting",
        label=get_label("device_fingerprinting"),
        severity=get_severity("device_fingerprinting"),
        explanation=get_explanation("device_fingerprinting"),
        patterns=[
            r"device fingerprint",
            r"(web beacons|clear gifs|pixel tags)",
            r"track.{0,40}across (websites|devices|platforms)",
        ],
    ),
    Rule(
        category="continuous_location_tracking",
        label=get_label("continuous_location_tracking"),
        severity=get_severity("continuous_location_tracking"),
        explanation=get_explanation("continuous_location_tracking"),
        patterns=[
            r"(precise|exact|geolocation).{0,30}(data|tracking)",
            r"background.{0,40}location",
            r"gps (coordinates|location)",
        ],
    ),
    Rule(
        category="content_copyright_transfer",
        label=get_label("content_copyright_transfer"),
        severity=get_severity("content_copyright_transfer"),
        explanation=get_explanation("content_copyright_transfer"),
        patterns=[
            r"(transfer|assign).{0,40}(copyright|intellectual property).{0,30}(to us|to company)",
            r"exclusive license.{0,40}(user content|your content)",
            r"relinquish.{0,40}ownership",
        ],
    ),
    Rule(
        category="moral_rights_waiver",
        label=get_label("moral_rights_waiver"),
        severity=get_severity("moral_rights_waiver"),
        explanation=get_explanation("moral_rights_waiver"),
        patterns=[
            r"waive.{0,30}moral rights",
            r"moral rights.{0,30}relinquish",
            r"not entitled to.{0,30}(credit|attribution)",
        ],
    ),
    Rule(
        category="shortened_limitation_period",
        label=get_label("shortened_limitation_period"),
        severity=get_severity("shortened_limitation_period"),
        explanation=get_explanation("shortened_limitation_period"),
        patterns=[
            r"(cause of action|claim).{0,60}must be (filed|commenced).{0,40}(within|no later than).{0,20}(one|1)\s*(year|yr)",
            r"permanently barred.{0,40}(one|1)\s*year",
            r"time limit.{0,40}bring a claim",
        ],
    ),
    Rule(
        category="data_deletion_friction",
        label=get_label("data_deletion_friction"),
        severity=get_severity("data_deletion_friction"),
        explanation=get_explanation("data_deletion_friction"),
        patterns=[
            r"retain.{0,50}after (deletion|termination|cancellation)",
            r"backup copies.{0,40}(indefinitely|perpetually|commercial reasons)",
            r"(cannot|unable to|no obligation to).{0,40}(delete|remove).{0,30}content",
        ],
    ),
    Rule(
        category="third_party_disclaimer",
        label=get_label("third_party_disclaimer"),
        severity=get_severity("third_party_disclaimer"),
        explanation=get_explanation("third_party_disclaimer"),
        patterns=[
            r"not responsible.{0,40}third[- ]party (links|websites|content|ads)",
            r"no control over.{0,40}third[- ]party",
            r"at your own risk.{0,40}third[- ]party",
        ],
    ),
    Rule(
        category="force_majeure_broad",
        label=get_label("force_majeure_broad"),
        severity=get_severity("force_majeure_broad"),
        explanation=get_explanation("force_majeure_broad"),
        patterns=[
            r"force majeure",
            r"acts of god.{0,60}not liable",
            r"beyond (our|reasonable) control.{0,40}(interruption|failure|delay)",
        ],
    ),
    Rule(
        category="ai_training_license",
        label=get_label("ai_training_license"),
        severity=get_severity("ai_training_license"),
        explanation=get_explanation("ai_training_license"),
        patterns=[
            r"(train|develop|improve).{0,50}(artificial intelligence|ai model|machine learning|llm|generative)",
            r"use (your )?content.{0,40}(training data|neural network|algorithmic)",
        ],
    ),
    Rule(
        category="biometric_harvesting",
        label=get_label("biometric_harvesting"),
        severity=get_severity("biometric_harvesting"),
        explanation=get_explanation("biometric_harvesting"),
        patterns=[
            r"biometric (data|information)",
            r"(facial recognition|voiceprint|retina scan|fingerprint).{0,40}(collect|store|process)",
            r"physiological characteristics",
        ],
    ),
    Rule(
        category="off_platform_tracking",
        label=get_label("off_platform_tracking"),
        severity=get_severity("off_platform_tracking"),
        explanation=get_explanation("off_platform_tracking"),
        patterns=[
            r"(browser|browsing) history.{0,40}(collect|monitor|access|track)",
            r"track(ing)?.{0,50}(other applications|outside the service|third[- ]party websites)",
            r"(keystroke|key logging)",
        ],
    ),
    Rule(
        category="inactivity_fee_seizure",
        label=get_label("inactivity_fee_seizure"),
        severity=get_severity("inactivity_fee_seizure"),
        explanation=get_explanation("inactivity_fee_seizure"),
        patterns=[
            r"inactivity fee",
            r"(dormant|inactive) account.{0,50}(fee|charge|forfeit|expire)",
            r"unused (credits|funds|balance|tokens).{0,40}(expire|forfeit|reclaimed)",
        ],
    ),
    Rule(
        category="no_refund_on_ban",
        label=get_label("no_refund_on_ban"),
        severity=get_severity("no_refund_on_ban"),
        explanation=get_explanation("no_refund_on_ban"),
        patterns=[
            r"terminate.{0,50}without (refund|compensation)",
            r"forfeit.{0,50}(purchases|credits|wallet|balance|virtual).{0,40}(upon termination|suspended)",
            r"no right to a refund.{0,40}(suspended|terminated)",
        ],
    ),
    Rule(
        category="payment_method_updating",
        label=get_label("payment_method_updating"),
        severity=get_severity("payment_method_updating"),
        explanation=get_explanation("payment_method_updating"),
        patterns=[
            r"(obtain|receive|fetch).{0,40}updated (credit card|payment).{0,40}(bank|issuer)",
            r"account updater (service|program)",
            r"automatically update.{0,30}payment information",
        ],
    ),
    Rule(
        category="beta_testing_waiver",
        label=get_label("beta_testing_waiver"),
        severity=get_severity("beta_testing_waiver"),
        explanation=get_explanation("beta_testing_waiver"),
        patterns=[
            r"(beta|experimental|preview) (features|services).{0,60}(at your own risk|no warranty|disclaim all liability)",
            r"pre[- ]release software.{0,50}as is",
        ],
    ),
    Rule(
        category="notice_of_breach_delay",
        label=get_label("notice_of_breach_delay"),
        severity=get_severity("notice_of_breach_delay"),
        explanation=get_explanation("notice_of_breach_delay"),
        patterns=[
            r"notify you.{0,40}within (60|90|120)\s*days.{0,40}(breach|unauthorized access)",
            r"commercially reasonable time.{0,40}notify.{0,40}breach",
        ],
    ),
    Rule(
        category="consent_to_background_check",
        label=get_label("consent_to_background_check"),
        severity=get_severity("consent_to_background_check"),
        explanation=get_explanation("consent_to_background_check"),
        patterns=[
            r"consent to.{0,40}(background check|credit check|criminal history)",
            r"reserve the right to (conduct|run).{0,40}background",
        ],
    ),
]


def _compile_all_rules() -> None:
    for rule in RULES:
        rule.compiled = [re.compile(p) for p in rule.patterns]


_compile_all_rules()
