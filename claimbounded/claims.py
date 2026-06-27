"""Claim-bounded classification.

Given a :class:`~claimbounded.schema.DeviceEvidenceProfile`, decide:

* ``classify_claim_ceiling``            -> the strongest claim routine evidence supports
* ``classify_supportable_claims``       -> the full multi-label set of supportable claims
* ``classify_audit_burden``             -> the evidence work needed to go higher
* ``classify_evaluability_class``       -> what kind of correctness signal routine
                                           deployment naturally produces
* ``classify_recoverability``           -> whether the authorization endpoint can be
                                           recovered from routine data
* ``estimate_authorization_remeasurement`` -> whether/how the authorization
  endpoint itself can be re-measured after deployment

The rules are transparent and conservative; they mirror the coding logic used
to build the empirical corpus.  When a profile is a corpus row (its coded
primary variables are already present and not "unclear"), the coded values are
trusted and returned directly so package output is consistent with the V4 audit.
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


_EVALUABILITY_CODED = {
    "closed_loop_evaluable", "workflow_endpoint_directly_auditable",
    "correction_evaluable", "delayed_evaluable",
    "surrogate_only", "not_evaluable",
}

_RECOVERABILITY_CODED = {
    "directly_auditable", "recoverable_with_linkage",
    "recoverable_with_chart_review", "proxy_only", "not_recoverable",
}

_STRUCTURED_GT = {
    "clinical_diagnosis", "laboratory_reference_method", "physiologic_reference_standard",
}

_EXPERT_REVIEW_GT = {
    "expert_reader_panel", "expert_annotation", "pathology_or_histology",
    "longitudinal_clinical_outcome",
}

_BENCH_GT = {
    "phantom_or_bench_reference", "predicate_device_comparison", "not_reported",
}

_NONCLINICAL_ENDPOINTS = {
    "nonclinical_technical_or_bench_performance",
    "no_device_specific_performance_data_in_public_summary",
    "technical_performance_only",
    "substantial_equivalence_only",
}


def classify_evaluability_class(profile: DeviceEvidenceProfile) -> str:
    """Classify the postmarket evaluability class — what correctness signal routine
    deployment naturally produces.

    Trusts coded value for corpus rows; derives from user inputs for new devices.
    Follows the V4 OSF codebook decision rules (conservative by default).
    """
    coded = _coded(profile, "postmarket_evaluability_class")
    if coded in _EVALUABILITY_CODED:
        return coded

    endpoint_type = _coded(profile, "authorization_endpoint_type")
    correction = _coded(profile, "human_correction_available")
    linked = _coded(profile, "endpoint_linked_to_ai_output")
    gt = _coded(profile, "authorization_ground_truth_modality")
    endpoint_occurs = _coded(profile, "endpoint_occurs_in_routine_care")

    # Bare clearance — no meaningful deployment description
    if endpoint_type in {"no_device_specific_performance_data_in_public_summary"}:
        return "not_evaluable"

    # Workflow device with co-logged metric: the authorized endpoint IS the log
    if endpoint_type in {"workflow_or_timeliness_performance"} and linked == "yes":
        return "workflow_endpoint_directly_auditable"

    # Physician edit/confirmation explicitly captured in accessible system
    if correction == "yes":
        return "correction_evaluable"

    # Future outcome accumulates naturally in clinical records over time
    if gt == "longitudinal_clinical_outcome" and endpoint_occurs in {"yes", "sometimes"}:
        return "delayed_evaluable"

    return "surrogate_only"


def classify_recoverability(profile: DeviceEvidenceProfile) -> str:
    """Classify whether the authorization endpoint can be recovered from routine data.

    Trusts coded value for corpus rows; derives for new devices.
    The overwhelming empirical finding: 51% proxy_only, 43% requires chart review,
    only 1 in 1,400 devices is directly_auditable.
    """
    coded = _coded(profile, "authorization_endpoint_recoverability")
    if coded in _RECOVERABILITY_CODED:
        return coded

    endpoint_type = _coded(profile, "authorization_endpoint_type")
    gt = _coded(profile, "authorization_ground_truth_modality")
    linked = _coded(profile, "endpoint_linked_to_ai_output")
    endpoint_occurs = _coded(profile, "endpoint_occurs_in_routine_care")

    # Nonclinical/bench — no clinical correctness signal possible
    if endpoint_type in _NONCLINICAL_ENDPOINTS:
        return "not_recoverable"

    # Workflow: authorized metric IS co-logged in deployment
    if endpoint_type in {"workflow_or_timeliness_performance"} and linked == "yes":
        return "directly_auditable"

    # Explicit case-level linkage + reference occurs in routine care
    if linked == "yes" and endpoint_occurs == "yes":
        return "directly_auditable"

    # Structured EHR records (ICD codes, lab, physiologic ref) — data engineering only
    if gt in _STRUCTURED_GT and endpoint_occurs in {"yes", "sometimes"}:
        return "recoverable_with_linkage"

    # Expert panel / annotation / pathology / longitudinal — human effort required
    if gt in _EXPERT_REVIEW_GT:
        return "recoverable_with_chart_review"

    # Phantom / bench / predicate — no clinical analogue in deployment
    if gt in _BENCH_GT:
        return "proxy_only"

    # Conservative default: most AI devices cannot recover their authorization endpoint
    return "proxy_only"


def _derive_audit_burden(profile: DeviceEvidenceProfile) -> str:
    gt = _coded(profile, "authorization_ground_truth_modality")
    linked = _coded(profile, "endpoint_linked_to_ai_output")
    endpoint_type = _coded(profile, "authorization_endpoint_type")

    if endpoint_type == "risk_prediction_or_prognosis":
        return "requires_longitudinal_registry"
    if endpoint_type in {"nonclinical_technical_or_bench_performance",
                          "no_device_specific_performance_data_in_public_summary",
                          "technical_performance_only", "substantial_equivalence_only"}:
        return "requires_new_validation_study"
    if endpoint_type == "workflow_or_timeliness_performance":
        return "routine_data_only"
    if gt in {"longitudinal_clinical_outcome"}:
        return "requires_longitudinal_registry"
    if gt in {"expert_annotation", "expert_reader_panel",
              "pathology_or_histology", "phantom_or_bench_reference"}:
        return "requires_sampling_or_chart_review"
    if gt in {"clinical_diagnosis", "laboratory_reference_method",
              "physiologic_reference_standard", "predicate_device_comparison"}:
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
        # V4 endpoint type names (locked OSF codebook)
        "diagnostic_accuracy": "clinical_accuracy_or_calibration",
        "risk_prediction_or_prognosis": "clinical_accuracy_or_calibration",
        "therapy_planning_or_control_performance": "clinical_accuracy_or_calibration",
        "quantitative_measurement_agreement": "output_quality_or_measurement_agreement",
        "segmentation_geometric_accuracy": "output_quality_or_measurement_agreement",
        "data_generation_or_acquisition_quality": "output_quality_or_measurement_agreement",
        "workflow_or_timeliness_performance": "workflow_performance",
        "nonclinical_technical_or_bench_performance": "technical_pipeline_stability",
        "no_device_specific_performance_data_in_public_summary": "technical_pipeline_stability",
        # V3 legacy names (backward compat for any old corpus rows)
        "triage_sensitivity_specificity": "clinical_accuracy_or_calibration",
        "physiologic_event_detection": "clinical_accuracy_or_calibration",
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
        "requires_data_linkage": "Join AI output log to structured clinical records (ICD codes, lab results, report fields) by patient/study identifier.",
        "requires_sampling_or_chart_review": "Draw a sampling frame and perform chart/image review against an expert-adjudicated reference.",
        "requires_longitudinal_registry": "Establish longitudinal EHR follow-up or registry linkage for outcome ascertainment.",
        "requires_new_validation_study": "Run a new validation study — existing clinical data cannot reconstruct the authorized endpoint.",
    }.get(burden, "Additional evidence linkage required.")
