"""Claim-bounded classification.

Given a :class:`~claimbounded.schema.DeviceEvidenceProfile`, decide:

* ``classify_claim_ceiling``      -> the strongest claim routine evidence supports
* ``classify_supportable_claims`` -> the full multi-label set of supportable claims
* ``classify_audit_burden``       -> the evidence work needed to go higher
* ``estimate_authorization_remeasurement`` -> whether/how the authorization
  endpoint itself can be re-measured after deployment

The rules are transparent and conservative; they mirror the coding logic used
to build the empirical corpus.  When a profile is a corpus row (its
``strongest_auditable_postmarket_claim`` is already coded and not "unclear"),
the coded value is trusted and returned directly so package output is
consistent with the published audit.
"""

from __future__ import annotations

from typing import Any

from .schema import (
    AUDIT_BURDEN_LABELS,
    CLAIM_EVIDENCE_REQUIREMENTS,
    CLAIM_HIERARCHY,
    CLAIM_RANK,
    DeviceEvidenceProfile,
)

_TECHNICAL_FUNCTIONS = {
    "image_reconstruction_enhancement",
    "acquisition_guidance",
}

_YES = {"yes", "true", "structured"}


def _coded(profile: DeviceEvidenceProfile, field: str) -> str:
    return str(profile.get(field, "unclear")).strip().lower()


def classify_claim_ceiling(profile: DeviceEvidenceProfile) -> str:
    """Return the strongest auditable postmarket claim for this device.

    If the profile already carries a coded ceiling (corpus row), trust it.
    Otherwise apply a conservative decision tree over the deployment-evidence
    fields.
    """

    coded = _coded(profile, "strongest_auditable_postmarket_claim")
    if coded in CLAIM_RANK:
        return coded

    linked = _coded(profile, "endpoint_linked_to_ai_output")
    recorded = _coded(profile, "endpoint_routinely_recorded")
    correction = _coded(profile, "human_correction_available")
    overread = _coded(profile, "human_overread_or_confirmation_required")
    stream = _coded(profile, "routine_postmarket_evidence_stream")
    function = _coded(profile, "device_function")

    # No usable routine evidence at all.
    if stream in {"none", "no_routine_evidence"}:
        return "no_performance_claim_auditable"
    if stream in {"utilization", "utilization_only"}:
        return "utilization_only"

    # Output-level reference evidence is linked case-to-case -> measurement.
    if linked == "yes" and (recorded in _YES or correction == "yes"):
        return "output_quality_or_measurement_agreement"

    # Clinician edits / accept / reject / override CAPTURED on the AI output.
    # Note: an overread merely being *required* does not, by itself, mean the
    # accept/reject decision is captured as routine evidence; concordance
    # requires that the human action is actually recorded.
    if correction == "yes":
        return "human_machine_concordance"
    if overread == "yes" and stream in {"clinician_edits", "structured_report", "accept_reject_log"}:
        return "human_machine_concordance"

    # Purely technical pipelines (reconstruction, acquisition) with only logs.
    if function in _TECHNICAL_FUNCTIONS and stream in {"device_logs", "technical_logs", "workflow_logs"}:
        return "technical_pipeline_stability"

    # Default: outputs flow through a workflow but nothing re-touches accuracy.
    return "workflow_performance"


def classify_supportable_claims(profile: DeviceEvidenceProfile) -> list[str]:
    """Return every claim level at or below the ceiling the evidence supports.

    More operationally honest than a single ceiling: a device may support
    several lower-level claims while topping out at one ceiling.  Technical
    pipeline stability and workflow performance are treated as supportable
    whenever the device produces any routine output stream.
    """

    ceiling = classify_claim_ceiling(profile)
    ceiling_rank = CLAIM_RANK[ceiling]
    supportable: list[str] = []

    stream = _coded(profile, "routine_postmarket_evidence_stream")
    has_stream = stream not in {"none", "no_routine_evidence", "unclear"}

    for claim in CLAIM_HIERARCHY:
        rank = CLAIM_RANK[claim]
        if claim in {"no_performance_claim_auditable", "utilization_only"}:
            continue
        if rank <= ceiling_rank:
            if claim in {"technical_pipeline_stability", "workflow_performance"} and not has_stream:
                continue
            supportable.append(claim)
    if not supportable:
        supportable = [ceiling]
    return supportable


def classify_audit_burden(profile: DeviceEvidenceProfile) -> dict[str, Any]:
    """Classify the work needed to audit the authorization endpoint.

    Trusts the coded ``postmarket_audit_burden`` when present; otherwise derives
    it from the authorization ground-truth modality and linkage.
    """

    coded = _coded(profile, "postmarket_audit_burden")
    if coded in AUDIT_BURDEN_LABELS and coded != "unclear":
        burden = coded
    else:
        burden = _derive_audit_burden(profile)

    return {
        "postmarket_audit_burden": burden,
        "label": AUDIT_BURDEN_LABELS.get(burden, burden),
        "driven_by_ground_truth": _coded(profile, "authorization_ground_truth_modality"),
    }


def _derive_audit_burden(profile: DeviceEvidenceProfile) -> str:
    gt = _coded(profile, "authorization_ground_truth_modality")
    linked = _coded(profile, "endpoint_linked_to_ai_output")
    endpoint_type = _coded(profile, "authorization_endpoint_type")

    if endpoint_type == "risk_prediction_or_prognosis":
        return "requires_longitudinal_registry"
    if gt in {"longitudinal_outcome", "clinical_outcome"}:
        return "requires_longitudinal_registry"
    if gt in {"expert_annotation", "expert_reader_panel", "expert_consensus"}:
        return "requires_sampling_or_chart_review"
    if gt in {"clinical_diagnosis", "laboratory_reference", "pathology"}:
        return "requires_data_linkage"
    if linked == "yes":
        return "routine_data_only"
    return "requires_data_linkage"


def estimate_authorization_remeasurement(profile: DeviceEvidenceProfile) -> dict[str, Any]:
    """Estimate whether the authorization endpoint can be re-measured.

    Compares the authorization endpoint type to the routine-evidence ceiling
    and reports the gap, the auditability verdict, and the extra evidence work.
    """

    endpoint_type = _coded(profile, "authorization_endpoint_type")
    ceiling = classify_claim_ceiling(profile)
    burden = classify_audit_burden(profile)

    endpoint_claim = _endpoint_type_to_claim(endpoint_type)
    gap = CLAIM_RANK.get(endpoint_claim, len(CLAIM_HIERARCHY) - 1) - CLAIM_RANK[ceiling]

    coded_audit = _coded(profile, "can_audit_authorization_endpoint_with_routine_data")
    if coded_audit in {"yes", "partially", "no"}:
        can_audit = coded_audit
    else:
        can_audit = "no" if gap >= 2 else ("partially" if gap == 1 else "yes")

    extra = profile.get("extra_evidence_needed")
    if not extra or str(extra).strip().lower() == "unclear":
        extra = _default_extra_evidence(burden["postmarket_audit_burden"])

    return {
        "authorization_endpoint_type": endpoint_type,
        "authorization_claim_level": endpoint_claim,
        "routine_evidence_claim_ceiling": ceiling,
        "claim_gap_levels": gap,
        "claim_gap": _describe_gap(gap),
        "can_audit_authorization_endpoint_with_routine_data": can_audit,
        "postmarket_audit_burden": burden["postmarket_audit_burden"],
        "extra_evidence_needed": extra,
    }


def _endpoint_type_to_claim(endpoint_type: str) -> str:
    mapping = {
        "diagnostic_accuracy": "clinical_accuracy_or_calibration",
        "triage_sensitivity_specificity": "clinical_accuracy_or_calibration",
        "risk_prediction_or_prognosis": "clinical_accuracy_or_calibration",
        "physiologic_event_detection": "clinical_accuracy_or_calibration",
        "quantitative_measurement_agreement": "output_quality_or_measurement_agreement",
        "segmentation_geometric_accuracy": "output_quality_or_measurement_agreement",
        "image_quality_or_reconstruction_fidelity": "output_quality_or_measurement_agreement",
        "technical_performance_only": "technical_pipeline_stability",
        "substantial_equivalence_only": "technical_pipeline_stability",
        "workflow_or_time_to_notification": "workflow_performance",
    }
    return mapping.get(endpoint_type, "clinical_accuracy_or_calibration")


def _describe_gap(gap: int) -> str:
    if gap <= 0:
        return "routine evidence reaches the authorization claim level"
    if gap == 1:
        return "routine evidence is one level below the authorization claim"
    return f"routine evidence is {gap} levels below the authorization claim"


def _default_extra_evidence(burden: str) -> str:
    return {
        "routine_data_only": "No additional linkage required; confirm denominator and version capture.",
        "requires_data_linkage": "Link each AI output to the downstream reference report or label.",
        "requires_sampling_or_chart_review": "Draw a sampling frame and perform chart/image review against an adjudicated reference.",
        "requires_expert_adjudication": "Convene expert adjudication of a reference label for sampled cases.",
        "requires_longitudinal_registry": "Establish longitudinal follow-up or registry linkage for outcome ascertainment.",
        "requires_new_clinical_study": "Run a new prospective study to re-measure the authorized endpoint.",
    }.get(burden, "Additional evidence linkage required.")
