"""Worked example: a new LVO stroke-triage device.

Run from the repository root:

    python examples/lvo_stroke_triage.py

This mirrors the worked example in the manuscript. Before a health system
deploys a new large-vessel-occlusion (LVO) triage tool, the package:

1. profiles the device into the study schema;
2. classifies the routine-evidence claim ceiling and audit burden;
3. retrieves comparable *real* FDA precedents (with submission numbers) so the
   team can study how adjacent devices were authorized and what claim their
   routine evidence could support;
4. emits dashboard claim limits and the minimum audit dataset to design up front.
"""

import json
import os

from claimbounded import (
    profile_device,
    classify_claim_ceiling,
    classify_supportable_claims,
    estimate_authorization_remeasurement,
    retrieve_precedents,
    generate_monitoring_package,
)

HERE = os.path.dirname(__file__)


def main() -> None:
    with open(os.path.join(HERE, "example_profiles", "lvo_triage.json")) as fh:
        record = json.load(fh)
    profile = profile_device(record)

    print("=" * 78)
    print("DEVICE:", profile.name)
    print("=" * 78)

    print("\nRoutine-evidence claim ceiling:", classify_claim_ceiling(profile))
    print("Supportable claims:", classify_supportable_claims(profile))

    rem = estimate_authorization_remeasurement(profile)
    print("\nCan re-measure authorization endpoint from routine data:",
          rem["can_audit_authorization_endpoint_with_routine_data"])
    print("Claim gap:", rem["claim_gap"])
    print("Audit burden:", rem["postmarket_audit_burden"])

    print("\n--- Like-for-like precedents (same regulatory identity) ---")
    for p in retrieve_precedents(profile, mode="like_for_like", k=5):
        print(f"  {p['submission_number']:>10}  {p['device_name'][:40]:40}  -> {p['strongest_auditable_postmarket_claim']}")

    print("\n--- Claim-gap precedents (same authorization->ceiling divergence) ---")
    for p in retrieve_precedents(profile, mode="claim_gap", k=5):
        print(f"  {p['submission_number']:>10}  {p['device_name'][:40]:40}  -> {p['strongest_auditable_postmarket_claim']}")

    print("\n--- Hybrid precedents ---")
    for p in retrieve_precedents(profile, mode="hybrid", k=5):
        print(f"  {p['score']:.3f}  {p['submission_number']:>10}  {p['device_name'][:38]:38}")
        print(f"          {p['match']}")

    pkg = generate_monitoring_package(profile, k=5)
    print("\n--- Dashboard claim limits ---")
    for key, value in pkg["dashboard_claim_limits"].items():
        print(f"  {key}: {value}")

    print("\n--- Minimum audit dataset ---")
    for item in pkg["minimum_audit_dataset"]:
        print(f"  - {item}")


if __name__ == "__main__":
    main()
