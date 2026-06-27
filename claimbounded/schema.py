"""Schema definitions for claim-bounded monitoring.

This module defines the controlled vocabulary, the ordered claim hierarchy,
and the :class:`DeviceEvidenceProfile` dataclass that every other module in
the package consumes.  The vocabulary mirrors the coded variables used in the
empirical evidence audit of 1,400 public FDA authorization summaries, so that
a newly profiled device is described in exactly the same terms as the
precedent corpus shipped with the package.

Nothing in this package is a regulatory determination.  The classifications
describe the *evidentiary relationship* between an authorization claim, the
evidence routine deployment generates, and the strongest postmarket claim
that evidence can support.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Optional

SCHEMA_VERSION = "v4_claimbounded"

# ---------------------------------------------------------------------------
# Ordered claim hierarchy
# ---------------------------------------------------------------------------
# A "claim ceiling" is the *strongest* performance-related statement routine
# deployment evidence can support without launching a new validation study.
# Claims are ordered from weakest (index 0) to strongest (index -1).  A device
# that can support a claim at level k can, in general, support every claim
# below k as well (see ``supportable_claims`` in ``claims.py``).

CLAIM_HIERARCHY: list[str] = [
    "no_performance_claim_auditable",
    "utilization_only",
    "technical_pipeline_stability",
    "workflow_performance",
    "human_machine_concordance",
    "output_quality_or_measurement_agreement",
    "clinical_accuracy_or_calibration",
]

CLAIM_RANK: dict[str, int] = {c: i for i, c in enumerate(CLAIM_HIERARCHY)}

CLAIM_LABELS: dict[str, str] = {
    "no_performance_claim_auditable": "No performance claim auditable",
    "utilization_only": "Utilization only",
    "technical_pipeline_stability": "Technical pipeline stability",
    "workflow_performance": "Workflow performance",
    "human_machine_concordance": "Human-machine concordance",
    "output_quality_or_measurement_agreement": "Output quality or measurement agreement",
    "clinical_accuracy_or_calibration": "Clinical accuracy or calibration",
}

# Plain-language description of what evidence each claim level requires.
CLAIM_EVIDENCE_REQUIREMENTS: dict[str, str] = {
    "technical_pipeline_stability": "Device logs, failures, uptime, software/model version per inference",
    "workflow_performance": "Alert/output delivery, timestamps, acknowledgement, turnaround",
    "human_machine_concordance": "User accept / reject / edit / override events on AI output",
    "output_quality_or_measurement_agreement": "Final measurement or report linked case-level to the AI output",
    "clinical_accuracy_or_calibration": "Independent reference standard, outcome, adjudication, or new study",
    "utilization_only": "Counts of device use; no output-level evidence",
    "no_performance_claim_auditable": "No routine evidence that re-touches device performance",
}

# ---------------------------------------------------------------------------
# Audit burden vocabulary (mirrors postmarket_audit_burden in the corpus)
# ---------------------------------------------------------------------------
AUDIT_BURDEN_ORDER: list[str] = [
    "routine_data_only",
    "requires_data_linkage",
    "requires_sampling_or_chart_review",
    "requires_expert_adjudication",
    "requires_longitudinal_registry",
    "requires_new_clinical_study",
    "unclear",
]

AUDIT_BURDEN_LABELS: dict[str, str] = {
    "routine_data_only": "Auditable from routine data only",
    "requires_data_linkage": "Requires linkage of AI output to reference evidence",
    "requires_sampling_or_chart_review": "Requires sampling and chart/image review",
    "requires_expert_adjudication": "Requires expert adjudication of a reference label",
    "requires_longitudinal_registry": "Requires a longitudinal registry or follow-up",
    "requires_new_clinical_study": "Requires a new prospective clinical study",
    "unclear": "Unclear from available description",
}

# ---------------------------------------------------------------------------
# Fields used in structured / schema / evidence-gap similarity
# ---------------------------------------------------------------------------
STRUCTURED_REGULATORY_FIELDS = [
    "product_code",
    "panel",
    "submission_pathway",
    "clinical_domain",
    "device_function",
]

CLAIM_SCHEMA_FIELDS = [
    "authorization_endpoint_type",
    "authorization_ground_truth_modality",
    "routine_data_claim_type",
    "strongest_auditable_postmarket_claim",
    "postmarket_audit_burden",
    "postmarket_evaluability_class",
]

BM25_TEXT_FIELDS = [
    "authorization_endpoint",
    "supporting_quote_authorization",
    "supporting_quote_deployment",
    "supporting_quote_evaluability",
    # also searched when provided by users profiling new devices
    "intended_use_summary",
    "authorization_performance_claim",
    "deployment_output",
    "routine_deployment_evidence",
    "extra_evidence_needed",
]

EVIDENCE_GAP_FIELDS = [
    "authorization_endpoint_recoverability",
    "extra_evidence_needed",
    "reason_authorization_endpoint_not_auditable",
    "monitoring_implication",
]

# Every column carried on a profile.  Anything not supplied defaults to "unclear".
PROFILE_FIELDS = [
    # regulatory identity
    "submission_number",
    "submission_pathway",
    "device_name",
    "year",
    "applicant",
    "panel",
    "product_code",
    "regulation_number",
    "clinical_domain",
    "disease_area",
    "device_function",
    "device_role",
    "input_data_type",
    "primary_ai_task",
    "ai_ml_explicitly_described",
    "intended_use_summary",
    "intended_user",
    "intended_setting",
    # authorization evidence
    "authorization_performance_claim",
    "authorization_endpoint",
    "authorization_endpoint_type",
    "authorization_ground_truth_modality",
    "authorization_validation_design",
    "validation_type",
    # deployment evidence
    "deployment_output",
    "routine_deployment_evidence",
    "routine_feedback_available",
    "routine_postmarket_evidence_stream",
    "routine_data_claim_type",
    "feedback_type",
    "endpoint_occurs_in_routine_care",
    "endpoint_routinely_recorded",
    "endpoint_linked_to_ai_output",
    "endpoint_ascertainment_window",
    "endpoint_latency_category",
    "feedback_latency",
    "human_correction_available",
    "human_overread_or_confirmation_required",
    "clinical_outcome_required_to_verify",
    # coded outcomes (present for corpus rows; derived for new devices)
    "postmarket_audit_burden",
    "authorization_endpoint_recoverability",
    "can_audit_authorization_endpoint_with_routine_data",
    "reason_authorization_endpoint_not_auditable",
    "postmarket_evaluability_class",
    "strongest_auditable_postmarket_claim",
    "immediate_postmarket_claim",
    "mature_postmarket_claim",
    "extra_evidence_needed",
    "monitoring_implication",
    "evidence_explicitness",
    "confidence",
    "final_verification_status",
    # new V4 policy flags
    "pccp_present",
    "postmarket_monitoring_plan_mentioned",
    "subgroup_performance_reported",
    # free text used by retrieval
    "supporting_quote_authorization",
    "supporting_quote_deployment",
    "supporting_quote_evaluability",
]

DEFAULT_VALUE = "unclear"


@dataclass
class DeviceEvidenceProfile:
    """Normalized description of one device's evidence relationship.

    All fields default to ``"unclear"``.  Build one with
    :func:`claimbounded.profiles.profile_device`, which accepts a partial
    dictionary and fills the rest.
    """

    fields: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for f in PROFILE_FIELDS:
            self.fields.setdefault(f, DEFAULT_VALUE)

    def get(self, key: str, default: Any = DEFAULT_VALUE) -> Any:
        return self.fields.get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self.fields[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.fields[key] = value

    def to_dict(self) -> dict[str, Any]:
        return dict(self.fields)

    @property
    def name(self) -> str:
        return str(self.get("device_name") or "unnamed device")

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return (
            f"DeviceEvidenceProfile(name={self.name!r}, "
            f"endpoint_type={self.get('authorization_endpoint_type')!r}, "
            f"ceiling={self.get('strongest_auditable_postmarket_claim')!r})"
        )
