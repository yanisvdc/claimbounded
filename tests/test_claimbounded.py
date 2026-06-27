"""Test suite for claimbounded (V4 schema). Run with: pytest -q"""

from claimbounded import (
    CLAIM_HIERARCHY,
    classify_audit_burden,
    classify_claim_ceiling,
    classify_evaluability_class,
    classify_recoverability,
    classify_supportable_claims,
    corpus_stats,
    estimate_authorization_remeasurement,
    find_in_corpus,
    generate_claim_support_matrix,
    generate_monitoring_package,
    load_corpus,
    profile_device,
    retrieve_precedents,
    search_corpus,
)
from claimbounded.precedents import build_bm25_index


# ---------------------------------------------------------------------------
# Corpus loading
# ---------------------------------------------------------------------------

def test_corpus_loads_full_cohort():
    corpus = load_corpus()
    assert len(corpus) == 1400


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
    p = find_in_corpus("DEN170073")
    assert p is not None
    assert "viz" in str(p.get("applicant", "")).lower() or p.get("device_name")


def test_lookup_missing_returns_none():
    assert find_in_corpus("K000000") is None


def test_search_by_device_name():
    hits = search_corpus("vessel occlusion")
    assert len(hits) >= 1


def test_search_by_disease_area():
    hits = search_corpus("oncology")
    assert len(hits) >= 1


def test_search_by_clinical_domain():
    hits = search_corpus("cardiovascular")
    assert len(hits) >= 1


# ---------------------------------------------------------------------------
# Claim ceiling
# ---------------------------------------------------------------------------

def test_corpus_ceiling_is_trusted():
    p = find_in_corpus("DEN170073")
    assert classify_claim_ceiling(p) == p.get("strongest_auditable_postmarket_claim")


def test_workflow_device_ceilings_at_workflow():
    p = profile_device({
        "device_function": "triage_notification",
        "authorization_endpoint_type": "diagnostic_accuracy",
        "routine_postmarket_evidence_stream": "workflow_logs",
        "human_correction_available": "no",
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


def test_supportable_claims_are_subset_of_hierarchy():
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


# ---------------------------------------------------------------------------
# V4 endpoint type names
# ---------------------------------------------------------------------------

def test_v4_endpoint_data_generation_maps_to_measurement():
    p = profile_device({"authorization_endpoint_type": "data_generation_or_acquisition_quality"})
    rem = estimate_authorization_remeasurement(p)
    assert rem["authorization_claim_level"] == "output_quality_or_measurement_agreement"


def test_v4_endpoint_workflow_timeliness_maps_to_workflow():
    p = profile_device({"authorization_endpoint_type": "workflow_or_timeliness_performance"})
    rem = estimate_authorization_remeasurement(p)
    assert rem["authorization_claim_level"] == "workflow_performance"


def test_v4_endpoint_nonclinical_maps_to_technical():
    p = profile_device({"authorization_endpoint_type": "nonclinical_technical_or_bench_performance"})
    rem = estimate_authorization_remeasurement(p)
    assert rem["authorization_claim_level"] == "technical_pipeline_stability"


def test_v4_endpoint_therapy_planning_maps_to_clinical():
    p = profile_device({"authorization_endpoint_type": "therapy_planning_or_control_performance"})
    rem = estimate_authorization_remeasurement(p)
    assert rem["authorization_claim_level"] == "clinical_accuracy_or_calibration"


# ---------------------------------------------------------------------------
# Audit burden (V4 vocabulary)
# ---------------------------------------------------------------------------

def test_audit_burden_returns_label():
    p = find_in_corpus("DEN170073")
    burden = classify_audit_burden(p)
    assert "postmarket_audit_burden" in burden
    assert burden["label"]


def test_audit_burden_expert_panel_chart_review():
    p = profile_device({
        "authorization_endpoint_type": "diagnostic_accuracy",
        "authorization_ground_truth_modality": "expert_reader_panel",
    })
    burden = classify_audit_burden(p)
    assert burden["postmarket_audit_burden"] == "requires_sampling_or_chart_review"


def test_audit_burden_clinical_diagnosis_linkage():
    p = profile_device({
        "authorization_endpoint_type": "diagnostic_accuracy",
        "authorization_ground_truth_modality": "clinical_diagnosis",
        "endpoint_occurs_in_routine_care": "yes",
    })
    burden = classify_audit_burden(p)
    assert burden["postmarket_audit_burden"] == "requires_data_linkage"


def test_audit_burden_nonclinical_new_study():
    p = profile_device({
        "authorization_endpoint_type": "nonclinical_technical_or_bench_performance",
    })
    burden = classify_audit_burden(p)
    assert burden["postmarket_audit_burden"] == "requires_new_validation_study"


def test_audit_burden_no_requires_expert_adjudication():
    # requires_expert_adjudication was removed in V4
    from claimbounded.schema import AUDIT_BURDEN_LABELS
    assert "requires_expert_adjudication" not in AUDIT_BURDEN_LABELS
    assert "requires_new_validation_study" in AUDIT_BURDEN_LABELS


# ---------------------------------------------------------------------------
# Evaluability class (new V4 primary variable)
# ---------------------------------------------------------------------------

def test_corpus_evaluability_is_trusted():
    p = find_in_corpus("DEN170073")
    coded = p.get("postmarket_evaluability_class")
    if coded and coded != "unclear":
        assert classify_evaluability_class(p) == coded


def test_bare_clearance_is_not_evaluable():
    p = profile_device({
        "authorization_endpoint_type": "no_device_specific_performance_data_in_public_summary",
    })
    assert classify_evaluability_class(p) == "not_evaluable"


def test_workflow_device_with_linkage_is_directly_auditable():
    p = profile_device({
        "authorization_endpoint_type": "workflow_or_timeliness_performance",
        "endpoint_linked_to_ai_output": "yes",
    })
    assert classify_evaluability_class(p) == "workflow_endpoint_directly_auditable"


def test_correction_captured_is_correction_evaluable():
    p = profile_device({
        "authorization_endpoint_type": "diagnostic_accuracy",
        "human_correction_available": "yes",
    })
    assert classify_evaluability_class(p) == "correction_evaluable"


def test_longitudinal_outcome_with_routine_care_is_delayed():
    p = profile_device({
        "authorization_endpoint_type": "risk_prediction_or_prognosis",
        "authorization_ground_truth_modality": "longitudinal_clinical_outcome",
        "endpoint_occurs_in_routine_care": "yes",
    })
    assert classify_evaluability_class(p) == "delayed_evaluable"


def test_default_evaluability_is_surrogate_only():
    p = profile_device({
        "authorization_endpoint_type": "diagnostic_accuracy",
        "authorization_ground_truth_modality": "expert_reader_panel",
        "human_correction_available": "no",
    })
    assert classify_evaluability_class(p) == "surrogate_only"


# ---------------------------------------------------------------------------
# Recoverability (new V4 primary variable)
# ---------------------------------------------------------------------------

def test_corpus_recoverability_is_trusted():
    p = find_in_corpus("DEN170073")
    coded = p.get("authorization_endpoint_recoverability")
    if coded and coded != "unclear":
        assert classify_recoverability(p) == coded


def test_nonclinical_endpoint_not_recoverable():
    p = profile_device({
        "authorization_endpoint_type": "nonclinical_technical_or_bench_performance",
    })
    assert classify_recoverability(p) == "not_recoverable"


def test_workflow_with_linkage_directly_auditable():
    p = profile_device({
        "authorization_endpoint_type": "workflow_or_timeliness_performance",
        "endpoint_linked_to_ai_output": "yes",
    })
    assert classify_recoverability(p) == "directly_auditable"


def test_explicit_linkage_and_routine_care_directly_auditable():
    p = profile_device({
        "authorization_endpoint_type": "diagnostic_accuracy",
        "endpoint_linked_to_ai_output": "yes",
        "endpoint_occurs_in_routine_care": "yes",
    })
    assert classify_recoverability(p) == "directly_auditable"


def test_clinical_diagnosis_gt_with_routine_care_recoverable_linkage():
    p = profile_device({
        "authorization_endpoint_type": "diagnostic_accuracy",
        "authorization_ground_truth_modality": "clinical_diagnosis",
        "endpoint_occurs_in_routine_care": "yes",
        "endpoint_linked_to_ai_output": "possible_but_not_described",
    })
    assert classify_recoverability(p) == "recoverable_with_linkage"


def test_expert_panel_gt_recoverable_chart_review():
    p = profile_device({
        "authorization_endpoint_type": "diagnostic_accuracy",
        "authorization_ground_truth_modality": "expert_reader_panel",
    })
    assert classify_recoverability(p) == "recoverable_with_chart_review"


def test_phantom_bench_gt_proxy_only():
    p = profile_device({
        "authorization_endpoint_type": "data_generation_or_acquisition_quality",
        "authorization_ground_truth_modality": "phantom_or_bench_reference",
    })
    assert classify_recoverability(p) == "proxy_only"


def test_default_recoverability_is_proxy_only():
    p = profile_device({
        "authorization_endpoint_type": "diagnostic_accuracy",
        "authorization_ground_truth_modality": "not_reported",
    })
    assert classify_recoverability(p) == "proxy_only"


# ---------------------------------------------------------------------------
# Corpus stats
# ---------------------------------------------------------------------------

def test_corpus_stats_returns_corpus_size():
    p = profile_device({
        "strongest_auditable_postmarket_claim": "workflow_performance",
        "authorization_endpoint_recoverability": "proxy_only",
        "postmarket_evaluability_class": "surrogate_only",
        "device_function": "triage_notification",
    })
    stats = corpus_stats(p)
    assert stats["n_corpus"] == 1400


def test_corpus_stats_ceiling_pct_in_range():
    p = profile_device({
        "strongest_auditable_postmarket_claim": "workflow_performance",
        "authorization_endpoint_recoverability": "proxy_only",
        "postmarket_evaluability_class": "surrogate_only",
        "device_function": "triage_notification",
    })
    stats = corpus_stats(p)
    # workflow_performance is 62.2% of corpus — should be between 55 and 70
    assert 55 <= stats["ceiling_pct"] <= 70


def test_corpus_stats_recoverability_proxy_majority():
    p = profile_device({
        "strongest_auditable_postmarket_claim": "workflow_performance",
        "authorization_endpoint_recoverability": "proxy_only",
        "postmarket_evaluability_class": "surrogate_only",
    })
    stats = corpus_stats(p)
    # proxy_only is 51% — should be between 45 and 60
    assert 45 <= stats["recoverability_pct"] <= 60


# ---------------------------------------------------------------------------
# Precedent retrieval
# ---------------------------------------------------------------------------

def test_bm25_index_builds():
    index, records = build_bm25_index()
    assert index.N == len(records) == 1400
    assert index.avgdl > 0


def test_retrieve_returns_k_sorted():
    p = profile_device({
        "device_function": "triage_notification",
        "authorization_endpoint_type": "diagnostic_accuracy",
        "clinical_domain": "neurology",
        "disease_area": "neurological_disease",
    })
    for mode in ["like_for_like", "adjacent", "claim_gap", "hybrid"]:
        res = retrieve_precedents(p, mode=mode, k=8)
        assert 1 <= len(res) <= 8
        scores = [r["score"] for r in res]
        assert scores == sorted(scores, reverse=True)


def test_retrieve_excludes_self_by_submission_number():
    p = find_in_corpus("K192383")
    if p is not None:
        res = retrieve_precedents(p, mode="hybrid", k=10)
        assert all(r["submission_number"] != "K192383" for r in res)


def test_retrieve_does_not_exclude_unclear_submission():
    # Devices with unclear submission number should NOT all be excluded
    p = profile_device({
        "device_function": "diagnostic_classification",
        "authorization_endpoint_type": "diagnostic_accuracy",
        "clinical_domain": "radiology",
    })
    res = retrieve_precedents(p, mode="hybrid", k=5)
    assert len(res) == 5


def test_invalid_mode_raises():
    p = profile_device({"device_name": "x"})
    try:
        retrieve_precedents(p, mode="nope")
    except ValueError:
        return
    raise AssertionError("expected ValueError")


# ---------------------------------------------------------------------------
# Full monitoring package
# ---------------------------------------------------------------------------

def test_claim_support_matrix_shape():
    p = profile_device({
        "authorization_endpoint_type": "diagnostic_accuracy",
        "routine_postmarket_evidence_stream": "workflow_logs",
    })
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
        "procurement_questions", "precedents", "disclaimer", "landscape_context",
    ]:
        assert key in pkg, f"missing key: {key}"
    assert len(pkg["precedents"]) == 5


def test_monitoring_package_claim_profile_has_v4_fields():
    p = profile_device({
        "device_function": "triage_notification",
        "authorization_endpoint_type": "diagnostic_accuracy",
        "authorization_ground_truth_modality": "expert_reader_panel",
        "routine_postmarket_evidence_stream": "workflow_logs",
    })
    pkg = generate_monitoring_package(p, k=3)
    cp = pkg["claim_profile"]
    assert "postmarket_evaluability_class" in cp
    assert "authorization_endpoint_recoverability" in cp
    assert "evaluability_label" in cp
    assert "recoverability_label" in cp
    assert cp["postmarket_evaluability_class"] in {
        "closed_loop_evaluable", "workflow_endpoint_directly_auditable",
        "correction_evaluable", "delayed_evaluable", "surrogate_only", "not_evaluable",
    }
    assert cp["authorization_endpoint_recoverability"] in {
        "directly_auditable", "recoverable_with_linkage",
        "recoverable_with_chart_review", "proxy_only", "not_recoverable", "unclear",
    }
