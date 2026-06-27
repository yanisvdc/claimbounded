"""High-level report assembly.

``generate_monitoring_package`` bundles the claim-bounded profile, precedents,
and operational outputs into a single dictionary.  ``generate_monitoring_profile_report``
renders that bundle as Markdown for humans.
"""

from __future__ import annotations

from typing import Any, Optional

from .claims import (
    classify_audit_burden,
    classify_claim_ceiling,
    classify_evaluability_class,
    classify_recoverability,
    classify_supportable_claims,
    estimate_authorization_remeasurement,
)
from .outputs import (
    generate_claim_support_matrix,
    generate_dashboard_claim_limits,
    generate_manufacturer_design_requirements,
    generate_minimum_audit_dataset,
    generate_procurement_questions,
)
from .precedents import retrieve_precedents
from .profiles import corpus_stats
from .schema import (
    CLAIM_LABELS,
    EVALUABILITY_CLASS_LABELS,
    EVALUABILITY_CLASS_DESCRIPTIONS,
    RECOVERABILITY_LABELS,
    RECOVERABILITY_DESCRIPTIONS,
    DeviceEvidenceProfile,
)

DISCLAIMER = (
    "This package does not determine whether a device is safe or effective and "
    "does not predict FDA decisions. It maps the evidentiary relationship between "
    "authorization claims, routine postmarket evidence, and supportable monitoring "
    "claims, grounded in public authorization precedents."
)


def generate_monitoring_package(
    profile: DeviceEvidenceProfile,
    precedents: Optional[list[dict[str, Any]]] = None,
    mode: str = "hybrid",
    k: int = 10,
) -> dict[str, Any]:
    """Assemble the full claim-bounded monitoring package for a device."""

    if precedents is None:
        precedents = retrieve_precedents(profile, mode=mode, k=k)

    evaluability = classify_evaluability_class(profile)
    recoverability = classify_recoverability(profile)
    ceiling = classify_claim_ceiling(profile)

    # Update profile with derived values so corpus_stats can read them
    if str(profile.get("strongest_auditable_postmarket_claim", "unclear")).strip().lower() in {"unclear", ""}:
        profile["strongest_auditable_postmarket_claim"] = ceiling
    if str(profile.get("postmarket_evaluability_class", "unclear")).strip().lower() in {"unclear", ""}:
        profile["postmarket_evaluability_class"] = evaluability
    if str(profile.get("authorization_endpoint_recoverability", "unclear")).strip().lower() in {"unclear", ""}:
        profile["authorization_endpoint_recoverability"] = recoverability

    return {
        "device": {
            "device_name": profile.get("device_name"),
            "applicant": profile.get("applicant"),
            "submission_number": profile.get("submission_number"),
            "clinical_domain": profile.get("clinical_domain"),
            "device_function": profile.get("device_function"),
            "authorization_endpoint_type": profile.get("authorization_endpoint_type"),
        },
        "claim_profile": {
            "routine_evidence_claim_ceiling": ceiling,
            "supportable_claims": classify_supportable_claims(profile),
            "audit_burden": classify_audit_burden(profile),
            "authorization_remeasurement": estimate_authorization_remeasurement(profile),
            "postmarket_evaluability_class": evaluability,
            "evaluability_label": EVALUABILITY_CLASS_LABELS.get(evaluability, evaluability),
            "evaluability_description": EVALUABILITY_CLASS_DESCRIPTIONS.get(evaluability, ""),
            "authorization_endpoint_recoverability": recoverability,
            "recoverability_label": RECOVERABILITY_LABELS.get(recoverability, recoverability),
            "recoverability_description": RECOVERABILITY_DESCRIPTIONS.get(recoverability, ""),
        },
        "landscape_context": corpus_stats(profile),
        "claim_support_matrix": generate_claim_support_matrix(profile),
        "dashboard_claim_limits": generate_dashboard_claim_limits(profile),
        "minimum_audit_dataset": generate_minimum_audit_dataset(profile),
        "manufacturer_design_requirements": generate_manufacturer_design_requirements(profile),
        "procurement_questions": generate_procurement_questions(profile),
        "precedents": precedents,
        "disclaimer": DISCLAIMER,
    }


def _md_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> str:
    header = "| " + " | ".join(label for _, label in columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for r in rows:
        body.append("| " + " | ".join(str(r.get(key, "")) for key, _ in columns) + " |")
    return "\n".join([header, sep, *body])


def generate_monitoring_profile_report(
    profile: DeviceEvidenceProfile,
    mode: str = "hybrid",
    k: int = 8,
) -> str:
    """Render a Markdown monitoring report for a device."""

    pkg = generate_monitoring_package(profile, mode=mode, k=k)
    cp = pkg["claim_profile"]
    rem = cp["authorization_remeasurement"]
    dash = pkg["dashboard_claim_limits"]

    lines: list[str] = []
    lines.append(f"# Claim-bounded monitoring profile: {profile.name}")
    lines.append("")
    lines.append(f"- Applicant: {profile.get('applicant')}")
    lines.append(f"- Submission: {profile.get('submission_number')}  |  Product code: {profile.get('product_code')}")
    lines.append(f"- Authorization endpoint type: {profile.get('authorization_endpoint_type')}")
    lines.append("")

    lines.append("## Claim profile")
    lines.append(f"- **Postmarket evaluability class:** {cp.get('evaluability_label', cp.get('postmarket_evaluability_class',''))}")
    lines.append(f"- **Authorization endpoint recoverability:** {cp.get('recoverability_label', cp.get('authorization_endpoint_recoverability',''))}")
    lines.append(f"- Routine-evidence claim ceiling: **{CLAIM_LABELS.get(cp['routine_evidence_claim_ceiling'], cp['routine_evidence_claim_ceiling'])}**")
    lines.append(f"- Supportable claims: {', '.join(CLAIM_LABELS.get(c, c) for c in cp['supportable_claims'])}")
    lines.append(f"- Audit burden: {cp['audit_burden']['label']}")
    lines.append(f"- Can re-measure authorization endpoint from routine data: **{rem['can_audit_authorization_endpoint_with_routine_data']}** ({rem['claim_gap']})")
    lines.append(f"- Extra evidence needed: {rem['extra_evidence_needed']}")
    lines.append("")

    ctx = pkg.get("landscape_context", {})
    if ctx.get("n_corpus"):
        lines.append("## Landscape context")
        lines.append(f"Among {ctx['n_corpus']:,} FDA-authorized AI devices (doi:10.17605/OSF.IO/74WAP):")
        for key, label in [("ceiling", "claim ceiling"), ("recoverability", "recoverability class"), ("evaluability", "evaluability class")]:
            pct = ctx.get(f"{key}_pct")
            peer_pct = ctx.get(f"{key}_peer_pct")
            n_peers = ctx.get("n_peers")
            if pct is not None:
                peer = f" · {peer_pct}% among {n_peers} same-function peers" if peer_pct is not None else ""
                lines.append(f"- {pct}% share this {label}{peer}")
        lines.append("")

    lines.append("## Claim-support matrix")
    lines.append(
        _md_table(
            pkg["claim_support_matrix"],
            [
                ("claim", "Claim"),
                ("supported_by_routine_evidence", "Routine evidence?"),
                ("evidence_needed", "Evidence needed"),
            ],
        )
    )
    lines.append("")

    lines.append("## Dashboard claim limits")
    lines.append(f"- Responsible claim: {dash['responsible_dashboard_claim']}")
    lines.append(f"- Not supported without extra evidence: {dash['not_supported_without_extra_evidence']}")
    lines.append(f"- To make the stronger claim: {dash['to_make_the_stronger_claim']}")
    lines.append("")

    lines.append("## Minimum audit dataset")
    for item in pkg["minimum_audit_dataset"]:
        lines.append(f"- {item}")
    lines.append("")

    lines.append("## Manufacturer design requirements")
    for item in pkg["manufacturer_design_requirements"]:
        lines.append(f"- {item}")
    lines.append("")

    lines.append("## Procurement questions")
    for item in pkg["procurement_questions"]:
        lines.append(f"- {item}")
    lines.append("")

    lines.append(f"## Comparable public precedents (mode={mode})")
    lines.append(
        _md_table(
            pkg["precedents"],
            [
                ("submission_number", "Submission"),
                ("device_name", "Device"),
                ("applicant", "Applicant"),
                ("authorization_endpoint_type", "Endpoint"),
                ("strongest_auditable_postmarket_claim", "Claim ceiling"),
                ("score", "Score"),
            ],
        )
    )
    lines.append("")
    lines.append(f"> {pkg['disclaimer']}")
    return "\n".join(lines)
