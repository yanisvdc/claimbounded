"""Operational outputs for health systems and manufacturers.

These functions turn a claim-bounded profile into the artifacts a stakeholder
actually uses: a claim-support matrix, responsible dashboard claim limits, the
minimum dataset needed to audit the authorization endpoint, manufacturer design
requirements, and procurement questions.
"""

from __future__ import annotations

from typing import Any

from .claims import (
    classify_audit_burden,
    classify_claim_ceiling,
    classify_supportable_claims,
    estimate_authorization_remeasurement,
)
from .schema import (
    CLAIM_EVIDENCE_REQUIREMENTS,
    CLAIM_HIERARCHY,
    CLAIM_LABELS,
    CLAIM_RANK,
    DeviceEvidenceProfile,
)


def generate_claim_support_matrix(profile: DeviceEvidenceProfile) -> list[dict[str, str]]:
    """One row per claim level: is it supported, and what evidence is needed.

    Verdicts: ``yes`` (supportable from routine evidence), ``requires linkage``
    (needs case-level linkage), ``requires additional audit work`` (needs
    sampling/adjudication/study), ``no``.
    """

    supportable = set(classify_supportable_claims(profile))
    ceiling_rank = CLAIM_RANK[classify_claim_ceiling(profile)]

    matrix = []
    for claim in reversed(CLAIM_HIERARCHY):
        if claim in {"no_performance_claim_auditable", "utilization_only"}:
            continue
        rank = CLAIM_RANK[claim]
        if claim in supportable:
            verdict = "Yes"
        elif rank == ceiling_rank + 1:
            verdict = "Requires linkage"
        else:
            verdict = "Requires additional audit work"
        matrix.append(
            {
                "claim": CLAIM_LABELS[claim],
                "supported_by_routine_evidence": verdict,
                "evidence_needed": CLAIM_EVIDENCE_REQUIREMENTS.get(claim, ""),
            }
        )
    return matrix


def generate_dashboard_claim_limits(profile: DeviceEvidenceProfile) -> dict[str, Any]:
    """Responsible vs unsupported dashboard claims."""

    ceiling = classify_claim_ceiling(profile)
    remeasure = estimate_authorization_remeasurement(profile)

    responsible = {
        "workflow_performance": "The device is operating and delivering outputs within expected workflow parameters.",
        "human_machine_concordance": "Clinicians accept, edit, or override device outputs at observed rates.",
        "output_quality_or_measurement_agreement": "Device outputs agree with the linked final measurement or report.",
        "technical_pipeline_stability": "The device pipeline is running, versioned, and within expected technical tolerances.",
        "utilization_only": "The device is being used at the observed volume.",
        "clinical_accuracy_or_calibration": "Device clinical accuracy/calibration is maintained (auditable from routine evidence).",
        "no_performance_claim_auditable": "Device is deployed (no performance claim auditable from routine evidence).",
    }

    unsupported = (
        f"The device maintains its authorized "
        f"{str(profile.get('authorization_endpoint_type')).replace('_', ' ')} after deployment"
    )

    return {
        "routine_evidence_claim_ceiling": ceiling,
        "responsible_dashboard_claim": responsible.get(ceiling, responsible["workflow_performance"]),
        "not_supported_without_extra_evidence": unsupported,
        "to_make_the_stronger_claim": remeasure["extra_evidence_needed"],
    }


def generate_minimum_audit_dataset(profile: DeviceEvidenceProfile) -> list[str]:
    """Minimum fields to assemble to re-measure the authorization endpoint."""

    burden = classify_audit_burden(profile)["postmarket_audit_burden"]
    base = [
        "Case-level AI output export (score/label/contour/measurement)",
        "Model and software version per inference",
        "Timestamped workflow events (delivery, acknowledgement, action)",
        "Stable case identifier (accession / order / encounter / specimen)",
    ]
    extra = {
        "requires_data_linkage": [
            "Linkage of each AI output to the final report or reference label",
            "Denominator of eligible cases, including non-flagged / non-alerted cases",
        ],
        "requires_sampling_or_chart_review": [
            "Denominator of eligible cases, including non-flagged cases",
            "Sampling frame for review",
            "Chart/image review protocol against an adjudicated reference",
        ],
        "requires_longitudinal_registry": [
            "Longitudinal EHR follow-up or registry linkage for outcome ascertainment",
            "Endpoint ascertainment window and censoring rules",
        ],
        "requires_new_validation_study": [
            "New validation study protocol — existing clinical data cannot reconstruct the authorized endpoint",
            "Independent reference standard generation or reader study design",
        ],
        "routine_data_only": [],
    }
    return base + extra.get(burden, ["Linkage of AI output to reference evidence"])


def generate_manufacturer_design_requirements(profile: DeviceEvidenceProfile) -> list[str]:
    """Logging/identifier/linkage features that would raise the claim ceiling."""

    reqs = [
        "Case-level output export (not just alert/notification)",
        "Logging of non-flagged / non-alerted cases (eligible denominator)",
        "Model and software version stamped on every inference",
        "Timestamped workflow events (acquisition, inference, delivery, acknowledgement)",
        "Stable identifiers (accession / order / specimen / encounter)",
        "Capture of user accept / edit / reject / override on each output",
        "Auditable data dictionary for exported fields",
        "Documentation of the intended postmarket monitoring claim(s) and their evidence chain",
    ]
    return reqs


def generate_procurement_questions(profile: DeviceEvidenceProfile) -> list[str]:
    """Questions a health system should ask before deployment."""

    endpoint = str(profile.get("authorization_endpoint_type")).replace("_", " ")
    return [
        f"What was the device authorized to show ({endpoint}), and against what reference standard?",
        "Which monitoring claims can our routine data support without new evidence work?",
        "Can the device export case-level outputs, versions, and identifiers for audit?",
        "Are non-flagged / non-alerted cases logged so we can estimate false negatives?",
        "What linkage (EHR / PACS / LIS / pathology / registry) is required to re-measure the authorized endpoint?",
        "Who is responsible for the chart review / adjudication if endpoint-level audit is needed?",
    ]
