---
title: claimbounded
emoji: 🏥
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: "6.19.0"
app_file: app.py
pinned: false
license: mit
short_description: Claim-bounded monitoring of AI-enabled medical devices
---

# claimbounded

**Claim-Bounded Monitoring of AI-Enabled Medical Devices**

[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Schema](https://img.shields.io/badge/schema-v4__claimbounded-teal)](claimbounded/schema.py)
[![OSF Preregistration](https://img.shields.io/badge/OSF-10.17605%2FOSF.IO%2F74WAP-blue)](https://doi.org/10.17605/OSF.IO/74WAP)
[![HuggingFace Space](https://img.shields.io/badge/🤗%20HuggingFace-Live%20Demo-orange)](https://huggingface.co/spaces/yanisvdc/claimbounded)

## Try it now — no install required

**[→ Open the live app on HuggingFace Spaces](https://huggingface.co/spaces/yanisvdc/claimbounded)**

---

`claimbounded` is a regulatory science Python package grounded in a structured audit of **1,400 public FDA authorization summaries** for AI-enabled medical devices (510(k) and De Novo). It answers a foundational question in AI medical device oversight:

> **What is the strongest performance claim a health system can substantiate using only the data routine deployment naturally generates — and how far does that fall short of what the device was authorized on?**

The package classifies any device along five primary variables validated against human reviewers (all κ ≥ 0.75):

| Variable | What it captures |
|---|---|
| **Postmarket evaluability class** | What *kind* of correctness signal routine deployment produces (surrogate-only, correction-evaluable, delayed-evaluable, directly auditable) |
| **Authorization endpoint recoverability** | Whether the *specific* performance endpoint the device was cleared on can be recovered from routine data — and at what cost |
| **Strongest auditable postmarket claim** | The highest claim level routine evidence can support without a new study |
| **Postmarket audit burden** | The evidence work required to reconstruct the authorization endpoint |
| **Routine data claim type** | Whether routine data supports the same endpoint, a clinical proxy, a workflow proxy, or only technical monitoring |

**Key empirical findings from the 1,400-device corpus** (publicly available FDA summaries):
- **85%** of authorized AI devices produce only surrogate-only evidence in deployment — no natural correctness signal
- **62%** have a claim ceiling of *workflow performance* — alert rates and output volume, not clinical accuracy
- **51%** have *proxy-only* recoverability — the authorization endpoint cannot be recovered from routine data at all
- **Only 1 in 1,400** devices is directly auditable on its authorization endpoint from routine deployment data
- **96%** have no PCCP; **99%** have no device-specific postmarket monitoring plan

---

## Who Is This For?

| Audience | How `claimbounded` helps |
|---|---|
| **Regulators** | Assess whether a manufacturer's marketed postmarket monitoring claim is supportable from the evidence their routine deployment generates. Cross-reference real FDA submission numbers from the precedent table on `accessdata.fda.gov`. See what fraction of comparable authorized devices share the same recoverability class. |
| **Device manufacturers** | Know your claim ceiling before your device ships. The *Manufacturer Design Requirements* section tells you exactly which logging, export, and identifier features would raise that ceiling. The *Landscape Context* shows how your device compares to 1,400 authorized peers. |
| **Health systems** | Use the *Procurement Questions* as a vendor checklist before deployment. Know the strongest monitoring claim your routine data supports — and verify it before signing a contract. The package surfaces whether comparable authorized devices can substantiate their marketed claims. |

---

## Installation

```bash
pip install claimbounded
```

With interactive UI (adds Gradio + python-docx):
```bash
pip install "claimbounded[ui]"
```

From source:
```bash
git clone https://github.com/yanisvdc/claimbounded
cd claimbounded
pip install -e ".[ui]"
```

---

## Quick Start

### Launch the interactive UI
```bash
claimbounded ui
```
Opens at `http://localhost:7860`. All processing runs locally — no data leaves your machine.

### Python API
```python
from claimbounded import (
    profile_device,
    classify_evaluability_class,
    classify_recoverability,
    generate_monitoring_package,
)

profile = profile_device({
    "device_name": "Acme LVO Triage",
    "device_function": "triage_notification",
    "authorization_endpoint_type": "diagnostic_accuracy",
    "authorization_ground_truth_modality": "expert_reader_panel",
    "routine_postmarket_evidence_stream": "workflow_logs",
    "endpoint_linked_to_ai_output": "possible_but_not_described",
    "human_correction_available": "no",
})

# Primary V4 variables
print(classify_evaluability_class(profile))
# → "surrogate_only"  (85% of authorized AI devices)

print(classify_recoverability(profile))
# → "recoverable_with_chart_review"  (expert panel GT; images retained in PACS)

# Full monitoring package
pkg = generate_monitoring_package(profile, k=8)
print(pkg["claim_profile"]["routine_evidence_claim_ceiling"])
# → "workflow_performance"

print(pkg["claim_profile"]["recoverability_label"])
# → "Recoverable with chart/image review"

# Landscape context: how this device compares to the 1,400-device corpus
ctx = pkg["landscape_context"]
print(f"{ctx['ceiling_pct']}% of FDA-authorized AI devices share this claim ceiling")
# → "62.2% of FDA-authorized AI devices share this claim ceiling"
```

### CLI
```bash
claimbounded report examples/example_profiles/lvo_triage.json
claimbounded precedents examples/example_profiles/lvo_triage.json --mode hybrid -k 10
claimbounded lookup K192383
claimbounded search "large vessel occlusion"
claimbounded search "oncology"
```

---

## The Five Primary Variables

### Postmarket evaluability class
What *kind* of correctness signal routine deployment naturally produces — before any additional effort.

| Class | Description | Prevalence |
|---|---|---|
| `surrogate_only` | Deployment produces outputs and logs but no natural correctness signal | **85%** of corpus |
| `correction_evaluable` | Physician edits/confirmations explicitly captured and stored | 13% |
| `delayed_evaluable` | Clinical outcome accumulates naturally over time in EHR records | 1% |
| `workflow_endpoint_directly_auditable` | Authorization endpoint is itself a workflow metric, co-logged in deployment | <1% |
| `closed_loop_evaluable` | AI output and ground truth both automatically co-logged | <1% |

### Authorization endpoint recoverability
Whether the *specific* authorization endpoint can be recovered and re-measured.

| Class | Description | Prevalence |
|---|---|---|
| `proxy_only` | Endpoint NOT recoverable; only operational proxies available | **51%** of corpus |
| `recoverable_with_chart_review` | Endpoint recoverable but requires expert re-annotation (major effort) | 43% |
| `recoverable_with_linkage` | Endpoint recoverable via data engineering on structured records | 4% |
| `not_recoverable` | Endpoint not recoverable AND no operational proxy exists | 2% |
| `directly_auditable` | Endpoint re-measurable from routine deployment data | **<0.1%** (1 in 1,400) |

### The Claim Hierarchy
The strongest monitoring claim routine evidence can support:

| Level | Claim | Prevalence in corpus |
|---|---|---|
| 7 | **Clinical accuracy or calibration** | 0% (no device reaches this from routine data) |
| 6 | **Output quality / measurement agreement** | 2.5% |
| 5 | **Human–machine concordance** | 11% |
| 4 | **Workflow performance** | **62%** |
| 3 | **Technical pipeline stability** | 23% |
| 2 | **Utilization only** | — |
| 1 | **No performance claim auditable** | 1% |

---

## Precedent Retrieval

`claimbounded` retrieves comparable FDA-authorized devices using a hybrid scoring function:

| Signal | Weight | Fields |
|---|---|---|
| Regulatory identity | 35% | disease area, clinical domain, device function, submission pathway |
| Evidence structure | 30% | endpoint type, recoverability, ground truth, claim ceiling, evaluability class, audit burden |
| Text similarity (BM25) | 20% | authorization endpoint description, supporting quotes |
| Evidence-gap matching | 15% | audit burden, monitoring implication |

**Retrieval modes:**
- `hybrid` — weighted blend (recommended)
- `like_for_like` — same regulatory and clinical identity
- `adjacent` — same postmarket-evidence problem, any device type
- `claim_gap` — same divergence between authorization endpoint and ceiling

---

## Interactive UI

Launch with `claimbounded ui` and navigate three tabs:

### ① Profile & Report
Fill in a device description using structured dropdowns (V4 FDA-Panel vocabulary). Click **Generate Report** to receive:
- **Claim hierarchy** — visual ceiling and authorization gap
- **Postmarket evaluability class** — what correctness signal deployment produces, with full V4 codebook definition
- **Authorization endpoint recoverability** — whether/how the clearing endpoint can be recovered
- **Landscape context** — how this device compares to 1,400 authorized peers (% sharing same ceiling, recoverability, evaluability)
- **Minimum audit dataset**, **Manufacturer design requirements**, **Procurement questions**
- **Comparable FDA precedents** — up to 20 real 510(k)/De Novo submission numbers with scoring
- Downloadable HTML report and Word document (.docx)

### ② Corpus Search
Search the 1,400-device corpus by device name, manufacturer, authorization endpoint, disease area, or clinical domain. Results render as a full stakeholder report with evaluability class, recoverability, PCCP status, and monitoring plan notes.

### ③ Submission Lookup
Enter a 510(k) or De Novo submission number to retrieve the complete coded profile — including evaluability class, recoverability, claim ceiling, supporting quotes, and PCCP/monitoring plan context.

---

## Validation

Five primary variables validated against two independent human reviewers on a 200-record stratified sample (pre-registered before full extraction):

| Variable | κ (R1 vs R2) | 95% CI | Gate |
|---|---|---|---|
| `authorization_endpoint_recoverability` | 0.759 | [0.68, 0.83] | ✓ PASS |
| `routine_data_claim_type` | 0.837 | [0.76, 0.91] | ✓ PASS |
| `postmarket_evaluability_class` | 0.768 | [0.63, 0.88] | ✓ PASS |
| `strongest_auditable_postmarket_claim` | 0.821 | [0.74, 0.89] | ✓ PASS |
| `postmarket_audit_burden` | 0.832 | [0.76, 0.90] | ✓ PASS |

Pre-registration: [doi:10.17605/OSF.IO/74WAP](https://doi.org/10.17605/OSF.IO/74WAP)

---

## Public API Reference

```python
from claimbounded import (
    # Profile a device
    profile_device,               # dict → DeviceEvidenceProfile
    normalize_device_record,      # dict → dict (canonical field set)
    load_corpus,                  # → list[DeviceEvidenceProfile]
    find_in_corpus,               # submission_number → DeviceEvidenceProfile | None
    search_corpus,                # text → list[DeviceEvidenceProfile]
    corpus_stats,                 # profile → dict (corpus-level context percentages)

    # Classify (primary V4 variables)
    classify_evaluability_class,           # profile → str
    classify_recoverability,               # profile → str
    classify_claim_ceiling,                # profile → str
    classify_supportable_claims,           # profile → list[str]
    classify_audit_burden,                 # profile → dict
    estimate_authorization_remeasurement,  # profile → dict

    # Retrieve precedents
    retrieve_precedents,          # (profile, mode, k) → list[dict]
    build_bm25_index,
    structured_similarity,
    schema_similarity,
    explain_precedent_match,

    # Generate operational outputs
    generate_claim_support_matrix,
    generate_dashboard_claim_limits,
    generate_minimum_audit_dataset,
    generate_manufacturer_design_requirements,
    generate_procurement_questions,

    # Assemble complete reports
    generate_monitoring_package,          # (profile, mode, k) → dict
    generate_monitoring_profile_report,   # (profile, mode, k) → str (Markdown)
)
```

---

## Design Principles

**Zero runtime dependencies** — the core package uses only the Python standard library, including a dependency-free BM25 implementation. Gradio and python-docx are optional extras.

**Empirically grounded** — every classification rule mirrors the pre-registered V4 codebook used to extract and code 1,400 public FDA authorization summaries. Classifications for new devices follow the same logic as the published audit.

**Conservative** — the codebook errs on the side of requiring more evidence work rather than overstating what routine data supports. `proxy_only` is the conservative default for recoverability; `surrogate_only` is the conservative default for evaluability.

**Precedent-grounded** — every output cites real FDA submission numbers verifiable at `accessdata.fda.gov`. The package cannot generate a recommendation not tied to a public precedent.

**Schema-first retrieval** — structured matching over shared coded fields (endpoint type, recoverability, ground truth, evaluability class) outperforms free-text search for this regulatory science task.

---

## Disclaimer

This package does not determine whether a device is safe or effective and does not predict FDA decisions. It maps the evidentiary relationship between authorization claims, routine postmarket evidence, and supportable monitoring claims, grounded in public authorization precedents. All classifications are preliminary and generated from user-provided inputs under the study codebook (schema `v4_claimbounded`, pre-registered at [doi:10.17605/OSF.IO/74WAP](https://doi.org/10.17605/OSF.IO/74WAP)). Nothing in this package constitutes regulatory advice.

---

## Citation

```bibtex
@software{claimbounded2026,
  title   = {claimbounded: Claim-Bounded Monitoring of AI-Enabled Medical Devices},
  author  = {Yanis Vandecasteele and Sofiane Vandecasteele},
  year    = {2026},
  url     = {https://github.com/yanisvdc/claimbounded},
  note    = {Schema version v4\_claimbounded. Grounded in 1,400 public FDA authorization
             records. OSF Preregistration: doi:10.17605/OSF.IO/74WAP}
}
```

---

## License

MIT © 2026 Yanis Vandecasteele & Sofiane Vandecasteele
