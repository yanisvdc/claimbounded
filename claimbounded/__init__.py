"""claimbounded: claim-bounded monitoring of AI-enabled medical devices.

Translate a device into the study schema, classify the strongest postmarket
claim its routine evidence can support, estimate the work needed to re-measure
the authorization endpoint, retrieve comparable public FDA precedents, and
generate operational outputs for health systems and manufacturers.

Quick start
-----------
>>> from claimbounded import profile_device, generate_monitoring_package
>>> profile = profile_device({
...     "device_name": "Acme LVO Triage",
...     "device_function": "triage_notification",
...     "authorization_endpoint_type": "diagnostic_accuracy",
...     "routine_postmarket_evidence_stream": "workflow_logs",
... })
>>> pkg = generate_monitoring_package(profile, k=5)
>>> pkg["claim_profile"]["routine_evidence_claim_ceiling"]
'workflow_performance'
"""

from .schema import (
    CLAIM_HIERARCHY,
    CLAIM_LABELS,
    SCHEMA_VERSION,
    DeviceEvidenceProfile,
)
from .profiles import (
    corpus_stats,
    find_in_corpus,
    load_corpus,
    normalize_device_record,
    profile_device,
    search_corpus,
)
from .claims import (
    classify_audit_burden,
    classify_claim_ceiling,
    classify_evaluability_class,
    classify_recoverability,
    classify_supportable_claims,
    estimate_authorization_remeasurement,
)
from .precedents import (
    build_bm25_index,
    explain_precedent_match,
    retrieve_precedents,
    schema_similarity,
    structured_similarity,
)
from .outputs import (
    generate_claim_support_matrix,
    generate_dashboard_claim_limits,
    generate_manufacturer_design_requirements,
    generate_minimum_audit_dataset,
    generate_procurement_questions,
)
from .reports import (
    generate_monitoring_package,
    generate_monitoring_profile_report,
)

__version__ = "0.2.0"

__all__ = [
    "DeviceEvidenceProfile",
    "CLAIM_HIERARCHY",
    "CLAIM_LABELS",
    "SCHEMA_VERSION",
    "profile_device",
    "normalize_device_record",
    "load_corpus",
    "find_in_corpus",
    "search_corpus",
    "corpus_stats",
    "classify_claim_ceiling",
    "classify_evaluability_class",
    "classify_recoverability",
    "classify_supportable_claims",
    "classify_audit_burden",
    "estimate_authorization_remeasurement",
    "retrieve_precedents",
    "build_bm25_index",
    "structured_similarity",
    "schema_similarity",
    "explain_precedent_match",
    "generate_claim_support_matrix",
    "generate_dashboard_claim_limits",
    "generate_minimum_audit_dataset",
    "generate_manufacturer_design_requirements",
    "generate_procurement_questions",
    "generate_monitoring_package",
    "generate_monitoring_profile_report",
]
