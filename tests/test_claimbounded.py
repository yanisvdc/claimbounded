"""Test suite for claimbounded. Run with: pytest -q"""

from claimbounded import (
    CLAIM_HIERARCHY,
    classify_audit_burden,
    classify_claim_ceiling,
    classify_supportable_claims,
    estimate_authorization_remeasurement,
    find_in_corpus,
    generate_claim_support_matrix,
    generate_monitoring_package,
    load_corpus,
    profile_device,
    retrieve_precedents,
)
from claimbounded.precedents import build_bm25_index


# --------------------------------------------------------------------------- #
# Profiles & corpus                                                           #
# --------------------------------------------------------------------------- #
def test_corpus_loads_full_cohort():
    corpus = load_corpus()
    assert len(corpus) == 1404


def test_profile_fills_defaults():
    p = profile_device({"device_name": "X"})
    assert p.get("device_name") == "X"
    assert p.get("authorization_endpoint_type") == "unclear"


def test_alias_normalization():
    p = profile_device({"name": "Y", "manufacturer": "Z", "endpoint_type": "diagnostic_accuracy"})
    assert p.get("device_name") == "Y"
    assert p.get("applicant") == "Z"
    assert p.get("authorization_endpoint_type") == "diagnostic_accuracy"


def test_lookup_known_submission():
    p = find_in_corpus("DEN170073")  # Viz.ai ContaCT
    assert p is not None
    assert "viz" in str(p.get("applicant")).lower()


# --------------------------------------------------------------------------- #
# Claim classification                                                        #
# --------------------------------------------------------------------------- #
def test_corpus_ceiling_is_trusted():
    p = find_in_corpus("DEN170073")
    assert classify_claim_ceiling(p) == p.get("strongest_auditable_postmarket_claim")


def test_workflow_only_device_ceilings_at_workflow():
    p = profile_device({
        "device_function": "triage_notification",
        "authorization_endpoint_type": "diagnostic_accuracy",
        "routine_postmarket_evidence_stream": "workflow_logs",
        "human_correction_available": "no",
        "human_overread_or_confirmation_required": "no",
        "endpoint_linked_to_ai_output": "possible_but_not_described",
    })
    assert classify_claim_ceiling(p) == "workflow_performance"


def test_correction_device_reaches_concordance():
    p = profile_device({
        "device_function": "segmentation_quantification",
        "authorization_endpoint_type": "segmentation_geometric_accuracy",
        "routine_postmarket_evidence_stream": "clinician_edits",
        "human_correction_available": "yes",
    })
    assert classify_claim_ceiling(p) == "human_machine_concordance"


def test_linked_output_reaches_measurement():
    p = profile_device({
        "authorization_endpoint_type": "quantitative_measurement_agreement",
        "routine_postmarket_evidence_stream": "structured_report",
        "endpoint_linked_to_ai_output": "yes",
        "endpoint_routinely_recorded": "structured",
    })
    assert classify_claim_ceiling(p) == "output_quality_or_measurement_agreement"


def test_supportable_claims_are_ordered_subset():
    p = find_in_corpus("DEN170073")
    claims = classify_supportable_claims(p)
    assert all(c in CLAIM_HIERARCHY for c in claims)
    assert len(claims) >= 1


def test_remeasurement_reports_gap_for_diagnostic_workflow():
    p = profile_device({
        "device_function": "triage_notification",
        "authorization_endpoint_type": "diagnostic_accuracy",
        "routine_postmarket_evidence_stream": "workflow_logs",
    })
    rem = estimate_authorization_remeasurement(p)
    assert rem["claim_gap_levels"] >= 1
    assert rem["can_audit_authorization_endpoint_with_routine_data"] in {"no", "partially"}


def test_audit_burden_returns_label():
    p = find_in_corpus("DEN170073")
    burden = classify_audit_burden(p)
    assert "postmarket_audit_burden" in burden
    assert burden["label"]


# --------------------------------------------------------------------------- #
# Precedent retrieval                                                         #
# --------------------------------------------------------------------------- #
def test_bm25_index_builds():
    index, records = build_bm25_index()
    assert index.N == len(records) == 1404
    assert index.avgdl > 0


def test_retrieve_returns_k_with_submission_numbers():
    p = profile_device({
        "device_function": "triage_notification",
        "authorization_endpoint_type": "diagnostic_accuracy",
        "clinical_domain": "neurology",
        "product_code": "QAS",
        "intended_use_summary": "large vessel occlusion triage notification on CT angiography",
    })
    for mode in ["like_for_like", "adjacent", "claim_gap", "hybrid"]:
        res = retrieve_precedents(p, mode=mode, k=8)
        assert 1 <= len(res) <= 8
        assert all(r["submission_number"] for r in res)
        scores = [r["score"] for r in res]
        assert scores == sorted(scores, reverse=True)


def test_retrieve_excludes_self():
    p = find_in_corpus("K192383")  # Aidoc BriefCase
    res = retrieve_precedents(p, mode="hybrid", k=10)
    assert all(r["submission_number"] != "K192383" for r in res)


def test_invalid_mode_raises():
    p = profile_device({"device_name": "x"})
    try:
        retrieve_precedents(p, mode="nope")
    except ValueError:
        return
    raise AssertionError("expected ValueError")


# --------------------------------------------------------------------------- #
# Outputs & package                                                           #
# --------------------------------------------------------------------------- #
def test_claim_support_matrix_shape():
    p = profile_device({"authorization_endpoint_type": "diagnostic_accuracy",
                        "routine_postmarket_evidence_stream": "workflow_logs"})
    matrix = generate_claim_support_matrix(p)
    assert matrix and all("claim" in row for row in matrix)


def test_monitoring_package_has_all_sections():
    p = profile_device({
        "device_function": "triage_notification",
        "authorization_endpoint_type": "diagnostic_accuracy",
        "routine_postmarket_evidence_stream": "workflow_logs",
    })
    pkg = generate_monitoring_package(p, k=5)
    for key in [
        "device", "claim_profile", "claim_support_matrix", "dashboard_claim_limits",
        "minimum_audit_dataset", "manufacturer_design_requirements",
        "procurement_questions", "precedents", "disclaimer",
    ]:
        assert key in pkg
    assert len(pkg["precedents"]) == 5
