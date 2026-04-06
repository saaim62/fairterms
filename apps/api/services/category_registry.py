"""
Single source of truth for all FairTerms clause categories.

Every category, its default severity, label, and explanation are defined here.
All other modules (analyzer, groq_analyze, extension) derive from this registry.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class CategoryMeta:
    key: str
    severity: Literal["red", "yellow"]
    label: str
    explanation: str


CATEGORY_REGISTRY: tuple[CategoryMeta, ...] = (
    CategoryMeta("zombie_renewal", "red", "Zombie Renewal / Hidden Auto-Renew", "Auto-renewal may be easy to miss, with weak or buried reminders."),
    CategoryMeta("arbitration_waiver", "red", "Forced Arbitration / Class Waiver", "You may be waiving court, jury, or class-action rights."),
    CategoryMeta("class_bar_standalone", "red", "Class / Representative Action Bar", "Class or representative actions may be barred even apart from arbitration."),
    CategoryMeta("data_succession", "red", "Data Transfer on Sale or Bankruptcy", "Your data may transfer to buyers or successors with little or no new consent."),
    CategoryMeta("gag_clauses", "red", "Reviews / Non-Disparagement Restrictions", "Terms may restrict honest reviews, criticism, or public comment."),
    CategoryMeta("unilateral_interpretation", "red", "Provider-Only Interpretation", "The company may reserve sole power to interpret or enforce the agreement."),
    CategoryMeta("liquidated_damages_penalties", "red", "Liquidated Damages / Penalty Fees", "Fixed penalties per breach may be disproportionate and punitive."),
    CategoryMeta("perpetual_restraint", "red", "Open-Ended Non-Compete / Survival", "Restrictive duties may survive termination without a clear time limit."),
    CategoryMeta("waiver_of_statutory_rights", "red", "Waiver of Statutory / Consumer Rights", "Language may try to waive rights under consumer or privacy laws."),
    CategoryMeta("device_exploitation", "red", "Device / Resource Exploitation", "The service may claim use of your device resources beyond core delivery."),
    CategoryMeta("data_selling", "red", "Explicit Sale of Personal Data", "The company may reserve the right to sell your personal information to third parties."),
    CategoryMeta("private_message_monitoring", "red", "Monitoring of Private Messages", "The provider may read, scan, or monitor private/direct messages."),
    CategoryMeta("content_copyright_transfer", "red", "Copyright Surrender", "You may be transferring copyright or ownership rights in user content."),
    CategoryMeta("moral_rights_waiver", "red", "Waiver of Moral Rights", "You may waive moral rights, including attribution and integrity protections."),
    CategoryMeta("shortened_limitation_period", "red", "Shortened Statute of Limitations", "The legal time window to bring claims may be reduced (e.g., one year)."),
    CategoryMeta("ai_training_license", "red", "AI / Machine Learning Training", "Your data or content may be used to train AI models without explicit opt-in."),
    CategoryMeta("biometric_harvesting", "red", "Biometric Data Collection", "Terms may allow collection or processing of sensitive biometric identifiers."),
    CategoryMeta("off_platform_tracking", "red", "Off-Platform / Browser Monitoring", "The service may monitor activity beyond its own app or website."),
    CategoryMeta("inactivity_fee_seizure", "red", "Inactivity Fees / Asset Seizure", "Dormant accounts may incur fees or lose balances/credits over time."),
    CategoryMeta("notice_of_breach_delay", "red", "Delayed Breach Notification", "Terms may allow unusually delayed notice after security incidents."),
    CategoryMeta("auto_renewal", "yellow", "Auto-Renewal Terms", "Billing may continue automatically; check notice and cancellation windows."),
    CategoryMeta("data_rights", "yellow", "Broad Data / IP Rights", "Broad licenses or sharing rights over your data or content."),
    CategoryMeta("cross_service_tracking", "yellow", "Cross-Service Data Use", "Data from one product may be combined or reused across other services."),
    CategoryMeta("retroactive_changes", "yellow", "Retroactive Policy Changes", "Changes may apply to data or conduct that already occurred."),
    CategoryMeta("unilateral_changes", "yellow", "Unilateral Term Changes", "The provider can change terms; continued use may count as acceptance."),
    CategoryMeta("fee_modification", "yellow", "Price / Fee Changes", "Fees or prices may change with limited notice or automatic tier jumps."),
    CategoryMeta("cancellation_friction", "yellow", "Hard-to-Cancel Terms", "Cancellation or refunds may be harder than signup or unfair."),
    CategoryMeta("one_way_attorneys_fees", "yellow", "One-Sided Attorneys' Fees", "Only the provider may recover legal fees if they prevail."),
    CategoryMeta("no_injunctive_relief", "yellow", "No Injunctive / Equitable Relief", "You may be limited to money damages and unable to stop ongoing harm."),
    CategoryMeta("mandatory_delay_tactics", "yellow", "Mandatory Pre-Suit Delays", "You may have to wait through mediation or informal steps before suing."),
    CategoryMeta("no_assignment_by_user", "yellow", "Assignment: You Can't, They Can", "You may not assign the contract while the provider can assign freely."),
    CategoryMeta("overbroad_ip_restrictions", "yellow", "Restrictive IP / Reverse Engineering", "Restrictions on reverse engineering or derivatives may be very broad."),
    CategoryMeta("shadow_profiling", "yellow", "Profiling Beyond Direct Users", "Data about non-users, contacts, or broker-augmented profiles may be collected."),
    CategoryMeta("english_language_supremacy", "yellow", "English-Only Binding Version", "Only the English version may be binding despite translations offered."),
    CategoryMeta("survival_of_termination_vague", "yellow", "Vague Post-Termination Survival", "Vague 'surviving provisions' clauses can leave important terms open-ended."),
    CategoryMeta("limitation_of_liability", "yellow", "Cap on Damages / Liability Limits", "Damages may be capped or consequential losses excluded, limiting recovery."),
    CategoryMeta("disclaimer_of_warranties", "yellow", "\u201cAs Is\u201d / No Warranties", "The service may be offered without meaningful warranties or merchantability."),
    CategoryMeta("broad_indemnity", "yellow", "Broad Indemnification", "You may have to pay the provider's losses, fees, or third-party claims."),
    CategoryMeta("forum_selection_exclusive", "yellow", "Exclusive Court / Venue", "Disputes may be forced into specific courts or jurisdictions far from you."),
    CategoryMeta("discretionary_termination", "yellow", "Discretionary Suspension / Termination", "The provider may cut off access with broad or unclear discretion."),
    CategoryMeta("children_data_collection", "yellow", "Children / Minors Data", "Terms may address under-13 or minor data in ways worth reviewing."),
    CategoryMeta("marketing_communications_burden", "yellow", "Marketing / Communications Opt-Out", "Promotional messages or SMS may be hard to opt out of or bundled with service notices."),
    CategoryMeta("device_fingerprinting", "yellow", "Advanced Device Tracking", "The service may use hard-to-block tracking methods like fingerprinting or tracking pixels."),
    CategoryMeta("continuous_location_tracking", "yellow", "Precise / Continuous Location Tracking", "Terms may allow precise or background location tracking."),
    CategoryMeta("no_refund_on_ban", "yellow", "Forfeiture of Purchases on Ban", "Account suspension/termination may forfeit purchases or wallet balances without refund."),
    CategoryMeta("payment_method_updating", "yellow", "Automatic Payment Method Updates", "Payment credentials may be auto-updated via card networks or banks."),
    CategoryMeta("beta_testing_waiver", "yellow", "Beta / Experimental Feature Immunity", "Experimental features may be offered with broad liability disclaimers."),
    CategoryMeta("consent_to_background_check", "yellow", "Hidden Background Checks", "Terms may permit background, credit, or criminal checks at provider discretion."),
    CategoryMeta("data_deletion_friction", "yellow", "Data Retention / Deletion Friction", "Deleting an account may not remove data, backups, or retained records."),
    CategoryMeta("third_party_disclaimer", "yellow", "Third-Party Harm Disclaimer", "The service may disclaim responsibility for third-party links, ads, or integrations."),
    CategoryMeta("force_majeure_broad", "yellow", "Overbroad Force Majeure", "Broad force majeure language may excuse provider failures too easily."),
)

ALL_CATEGORY_KEYS: frozenset[str] = frozenset(c.key for c in CATEGORY_REGISTRY)

RED_CATEGORIES: frozenset[str] = frozenset(c.key for c in CATEGORY_REGISTRY if c.severity == "red")

CATEGORY_BY_KEY: dict[str, CategoryMeta] = {c.key: c for c in CATEGORY_REGISTRY}


def get_label(key: str) -> str:
    return CATEGORY_BY_KEY[key].label if key in CATEGORY_BY_KEY else key.replace("_", " ").title()


def get_severity(key: str) -> str:
    return CATEGORY_BY_KEY[key].severity if key in CATEGORY_BY_KEY else "yellow"


def get_explanation(key: str) -> str:
    return CATEGORY_BY_KEY[key].explanation if key in CATEGORY_BY_KEY else "Flagged by automated review."
