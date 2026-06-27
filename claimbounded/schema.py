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
    "requires_longitudinal_registry",
    "requires_new_validation_study",
    "unclear",
]

AUDIT_BURDEN_LABELS: dict[str, str] = {
    "routine_data_only": "Auditable from routine data only",
    "requires_data_linkage": "Requires data linkage (structured records exist; needs join)",
    "requires_sampling_or_chart_review": "Requires sampling and chart/image review",
    "requires_longitudinal_registry": "Requires longitudinal follow-up or registry linkage",
    "requires_new_validation_study": "Requires a new validation study",
    "unclear": "Unclear from available description",
}

# ---------------------------------------------------------------------------
# Fields used in structured / schema / evidence-gap similarity
# ---------------------------------------------------------------------------
STRUCTURED_REGULATORY_FIELDS = [
    "disease_area",
    "clinical_domain",
    "device_function",
    "submission_pathway",
    "panel",
]

CLAIM_SCHEMA_FIELDS = [
    "authorization_endpoint_type",
    "authorization_endpoint_recoverability",
    "authorization_ground_truth_modality",
    "strongest_auditable_postmarket_claim",
    "postmarket_evaluability_class",
    "postmarket_audit_burden",
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

# ---------------------------------------------------------------------------
# Evaluability class vocabulary
# ---------------------------------------------------------------------------
EVALUABILITY_CLASS_LABELS: dict[str, str] = {
    "closed_loop_evaluable": "Closed-loop evaluable",
    "workflow_endpoint_directly_auditable": "Workflow endpoint directly auditable",
    "correction_evaluable": "Correction-evaluable (edit/override captured)",
    "delayed_evaluable": "Delayed-evaluable (outcome accumulates over time)",
    "surrogate_only": "Surrogate-only (no natural correctness signal)",
    "not_evaluable": "Not evaluable (bare clearance / no deployment description)",
}

EVALUABILITY_CLASS_DESCRIPTIONS: dict[str, str] = {
    "closed_loop_evaluable": "Deployment automatically co-logs both the AI output and clinical ground truth — correctness can be measured without extra work.",
    "workflow_endpoint_directly_auditable": "The authorized endpoint is itself a workflow/timeliness metric (e.g., time-to-notification) and the deployment system logs that metric automatically.",
    "correction_evaluable": "Clinicians are required to explicitly edit, confirm, or override AI outputs as clinical sign-off, and those decisions are stored in an accessible system.",
    "delayed_evaluable": "The ground truth outcome will naturally accumulate in routine clinical records over time (e.g., ICD-coded diagnosis at follow-up), enabling eventual linkage without a new study.",
    "surrogate_only": "Deployment produces outputs and logs, but no natural correctness signal is generated. Workflow monitoring (alert rates, output volume) is possible, but clinical accuracy cannot be re-measured from routine data alone. This is the modal class: 85% of FDA-authorized AI devices.",
    "not_evaluable": "The public summary contains no deployment description — typically a bare clearance letter. No performance data of any kind is available from routine deployment.",
}

# ---------------------------------------------------------------------------
# Recoverability vocabulary
# ---------------------------------------------------------------------------
RECOVERABILITY_LABELS: dict[str, str] = {
    "directly_auditable": "Directly auditable",
    "recoverable_with_linkage": "Recoverable with data linkage",
    "recoverable_with_chart_review": "Recoverable with chart/image review",
    "proxy_only": "Proxy only (authorization endpoint not recoverable)",
    "not_recoverable": "Not recoverable",
    "unclear": "Unclear",
}

RECOVERABILITY_DESCRIPTIONS: dict[str, str] = {
    "directly_auditable": "The authorization endpoint can be re-measured from existing routine deployment data — both AI output and ground truth are already co-collected and linked. Empirically rare: 1 in 1,400 devices.",
    "recoverable_with_linkage": "The ground truth exists in structured electronic records (ICD codes, lab results, structured report fields) and can be joined to AI output logs by patient/study identifier — no manual reading required. Requires data engineering. 3.6% of devices.",
    "recoverable_with_chart_review": "The authorization endpoint ground truth exists in clinical records but requires a human expert to manually review, re-annotate, or adjudicate cases — equivalent effort to a new validation substudy. 42.8% of devices.",
    "proxy_only": "The authorization endpoint cannot be recovered from routine data. Deployment produces operational proxies (workflow metrics, output rates) but these are weaker than what the device was cleared on. The modal outcome: 51.1% of devices.",
    "not_recoverable": "The authorization endpoint cannot be recovered AND routine deployment produces no meaningful operational proxy. Typically bare clearance letters or pure bench-tested devices. 2.4% of devices.",
    "unclear": "Insufficient information to determine recoverability.",
}

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
