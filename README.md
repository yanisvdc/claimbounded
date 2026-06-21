---
title: claimbounded
emoji: 🏥
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: "5.29.0"
app_file: app.py
pinned: false
license: mit
short_description: Claim-bounded monitoring of AI-enabled medical devices
---

# claimbounded

**Claim-Bounded Monitoring of AI-Enabled Medical Devices**

[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Schema](https://img.shields.io/badge/schema-v3__auditability-teal)](claimbounded/schema.py)
[![HuggingFace Space](https://img.shields.io/badge/🤗%20HuggingFace-Live%20Demo-orange)](https://huggingface.co/spaces/yanisvdc/claimbounded)

## Try it now — no install required

**[→ Open the live app on HuggingFace Spaces](https://huggingface.co/spaces/yanisvdc/claimbounded)**

Run the full tool in your browser with zero setup.

`claimbounded` is a regulatory science Python package that answers a foundational question in AI medical device oversight:

> **What is the strongest performance claim that a health system can substantiate using only the data routine deployment naturally generates?**

The package applies a transparent, rule-based codebook to a device description and returns:
- The **claim ceiling** — the highest monitoring claim routine evidence can support
- The **evidence gap** — how far that ceiling sits below the original authorization claim
- The **audit burden** — what additional evidence work closing that gap requires
- **Comparable FDA precedents** — real 510(k) and De Novo submission numbers from a corpus of 1,400 publicly authorized AI medical devices

All outputs are grounded in public FDA authorization records. No external APIs, no cloud, no LLMs — fully reproducible and offline.

---

## Who Is This For?

| Audience | How `claimbounded` helps |
|---|---|
| **Regulators** | Assess whether a manufacturer's marketed postmarket monitoring claim is supportable from the evidence their routine deployment generates. Cross-reference real FDA submission numbers from the precedent table on `accessdata.fda.gov`. |
| **Device manufacturers** | Get a concrete roadmap: the *Manufacturer Design Requirements* section tells you exactly which logging, export, and identifier features would raise your claim ceiling and enable stronger postmarket evidence. |
| **Health systems** | Use the *Procurement Questions* as a vendor checklist before deployment. Know the strongest monitoring claim your routine data supports — and verify it before signing a contract. |

---

## Installation

### Core package (zero runtime dependencies)
```bash
pip install claimbounded
```

### With interactive UI (adds Gradio + python-docx)
```bash
pip install "claimbounded[ui]"
```

### From source
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
from claimbounded import profile_device, generate_monitoring_package

profile = profile_device({
    "device_name": "Acme LVO Triage",
    "device_function": "triage_notification",
    "authorization_endpoint_type": "diagnostic_accuracy",
    "authorization_ground_truth_modality": "expert_reader_panel",
    "routine_postmarket_evidence_stream": "workflow_logs",
    "endpoint_linked_to_ai_output": "no",
    "human_correction_available": "no",
})

pkg = generate_monitoring_package(profile, mode="hybrid", k=8)

print(pkg["claim_profile"]["routine_evidence_claim_ceiling"])
# → "workflow_performance"

print(pkg["claim_profile"]["authorization_remeasurement"]["claim_gap"])
# → "routine evidence is 3 levels below the authorization claim"

for p in pkg["precedents"][:3]:
    print(p["submission_number"], p["device_name"], p["score"])
# → K223504  Ceribell Status Epilepticus Monitor  0.357
# → K231068  autoSCORE                           0.357
# → K242094  Dreem 3S                            0.357
```

### CLI
```bash
# Full monitoring report from a device profile JSON
claimbounded report examples/example_profiles/lvo_triage.json

# Find comparable FDA precedents
claimbounded precedents examples/example_profiles/lvo_triage.json --mode hybrid -k 10

# Look up a specific FDA submission by number
claimbounded lookup K192383

# Search the corpus by keyword
claimbounded search "large vessel occlusion"
```

---

## The Claim Hierarchy

`claimbounded` maps devices onto a 7-level ordered claim hierarchy. A device's **claim ceiling** is the highest level its routine deployment evidence can support without additional evidence work.

| Level | Claim | Evidence required from routine data |
|---|---|---|
| 7 | **Clinical accuracy or calibration** | Independent reference standard, outcome, adjudication, or new study |
| 6 | **Output quality / measurement agreement** | Final measurement or report linked case-level to the AI output |
| 5 | **Human–machine concordance** | User accept / reject / edit / override events captured on AI output |
| 4 | **Workflow performance** | Alert delivery, timestamps, acknowledgement, turnaround time |
| 3 | **Technical pipeline stability** | Device logs, failures, uptime, software/model version per inference |
| 2 | **Utilization only** | Counts of device use; no output-level evidence |
| 1 | **No performance claim auditable** | No routine evidence that re-touches device performance |

The **evidence gap** is the number of levels between the authorization endpoint (e.g., *diagnostic accuracy* → level 7) and the claim ceiling (e.g., *workflow performance* → level 4). A gap of 3 means the device cannot re-measure its authorization claim from routine deployment data alone.

---

## The Corpus

The package ships with a structured dataset of **1,400 FDA-authorized AI medical devices**, extracted from public 510(k) and De Novo authorization summaries. Each record contains:

- Authorization endpoint type and ground-truth modality
- Routine postmarket evidence stream (as described in the public summary)
- Coded claim ceiling and audit burden
- Supporting quotes extracted from the public FDA summary
- Submission number, applicant, year, clinical domain, device function, product code

The dataset is bundled inside the package — no external database or internet connection required.

---

## Precedent Retrieval

`claimbounded` retrieves comparable FDA-authorized devices using a hybrid scoring function:

| Signal | Weight | Fields |
|---|---|---|
| Regulatory identity | 35% | product code, device function, submission pathway, clinical domain |
| Evidence structure | 30% | endpoint type, ground truth, evidence stream, claim ceiling, audit burden |
| Text similarity (BM25) | 20% | intended use, authorization performance claim, supporting quotes |
| Evidence-gap matching | 15% | audit burden, monitoring implication, extra evidence needed |

**Retrieval modes** (`--mode` flag):
- `hybrid` — weighted blend of all signals (recommended)
- `like_for_like` — same regulatory and clinical identity
- `adjacent` — same postmarket-evidence problem, any product code
- `claim_gap` — same divergence between authorization endpoint and ceiling

The BM25 implementation is dependency-free (no external library required).

---

## Interactive UI

Launch with `claimbounded ui` and navigate three tabs:

### ① Profile & Report
Fill in a device description using structured dropdowns (controlled vocabulary matching the corpus). Click **Generate Report** to receive:
- A visual **claim hierarchy** showing the ceiling and authorization gap
- A **downloadable HTML report** with full analysis and stakeholder guidance
- A **downloadable Word document (.docx)** ready for regulatory submission
- Up to 20 **comparable FDA precedents** with scoring explanations and full intended use text

The form is pre-filled with a worked example (large vessel occlusion triage device). Hit **Auto-complete Example** to reset, or **Clear All Fields** to start from scratch.

### ② Corpus Search
Search the 1,400-device corpus by device name, manufacturer, or intended use. Results render as a full stakeholder HTML report (downloadable as HTML or Word) showing all matching devices with complete intended use text and authorization details.

### ③ Submission Lookup
Enter a 510(k) or De Novo submission number (e.g. `K192383`) to retrieve the complete coded profile — including the full intended use text, authorization performance claim, claim ceiling, and supporting quotes from the public FDA authorization summary.

---

## Live Demo

A hosted version is available at no cost, with no installation required:

**[https://huggingface.co/spaces/yanisvdc/claimbounded](https://huggingface.co/spaces/yanisvdc/claimbounded)**

Open the link in any browser to use the full tool — form, report generation, corpus search, and submission lookup all run on HuggingFace's servers. No Python, no setup.

---

## Package Structure

```
claimbounded/
├── claimbounded/
│   ├── schema.py          # Claim hierarchy, controlled vocabulary, DeviceEvidenceProfile
│   ├── profiles.py        # Device intake, normalization, corpus loading and search
│   ├── claims.py          # Claim-ceiling classification (decision tree over deployment fields)
│   ├── precedents.py      # BM25 index, structured/schema/evidence-gap similarity, retrieval
│   ├── outputs.py         # Claim-support matrix, audit dataset, procurement questions
│   ├── reports.py         # Report assembly and Markdown rendering
│   ├── cli.py             # CLI entry point (report, precedents, lookup, search, ui)
│   ├── ui.py              # Gradio interactive UI (requires claimbounded[ui])
│   └── data/
│       └── fda_ai_device_claims.csv   # 1,400 FDA-authorized AI device records
├── examples/
│   ├── lvo_stroke_triage.py           # Worked example: LVO triage device
│   ├── lvo_report.md                  # Sample report output
│   └── example_profiles/
│       └── lvo_triage.json            # Example device profile (JSON)
├── tests/
│   └── test_claimbounded.py
├── app.py                 # HuggingFace Spaces entry point
├── requirements.txt       # HuggingFace Spaces dependencies
└── pyproject.toml
```

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

    # Classify
    classify_claim_ceiling,               # profile → str
    classify_supportable_claims,          # profile → list[str]
    classify_audit_burden,                # profile → dict
    estimate_authorization_remeasurement, # profile → dict

    # Retrieve precedents
    retrieve_precedents,          # (profile, mode, k) → list[dict]
    build_bm25_index,             # → (BM25Index, list[dict])
    structured_similarity,        # (profile, rec) → float
    schema_similarity,            # (profile, rec) → float
    explain_precedent_match,      # (profile, rec, components) → str

    # Generate operational outputs
    generate_claim_support_matrix,           # profile → list[dict]
    generate_dashboard_claim_limits,         # profile → dict
    generate_minimum_audit_dataset,          # profile → list[str]
    generate_manufacturer_design_requirements, # profile → list[str]
    generate_procurement_questions,          # profile → list[str]

    # Assemble complete reports
    generate_monitoring_package,             # (profile, mode, k) → dict
    generate_monitoring_profile_report,      # (profile, mode, k) → str (Markdown)

    # Core types and constants
    DeviceEvidenceProfile,
    CLAIM_HIERARCHY,
    CLAIM_LABELS,
    SCHEMA_VERSION,
)
```

---

## Running Tests

```bash
pip install "claimbounded[test]"
pytest -q
```

CI runs on Python 3.9, 3.10, 3.11, and 3.12 via GitHub Actions.

---

## Design Principles

**Zero runtime dependencies** — the core package uses only the Python standard library, including a dependency-free BM25 implementation. Gradio and python-docx are optional extras (`claimbounded[ui]`).

**Transparency** — the classification rules are fully explicit and auditable; they mirror the coding logic used to build the empirical corpus. Nothing is hidden in model weights.

**Precedent-grounded** — every output cites real FDA submission numbers verifiable at `accessdata.fda.gov`. The package cannot generate a recommendation that is not tied to a public precedent.

**Conservative** — the codebook errs on the side of requiring more evidence work rather than overstating what routine data can support.

**Schema-first retrieval** — structured matching over shared coded fields (endpoint type, ground truth, evidence stream) outperforms free-text search for this regulatory science task. BM25 is a supplement, not the primary signal.

---

## Disclaimer

This package does not determine whether a device is safe or effective and does not predict FDA decisions. It maps the evidentiary relationship between authorization claims, routine postmarket evidence, and supportable monitoring claims, grounded in public authorization precedents. All classifications are preliminary and generated from user-provided inputs under the study codebook (schema `v3_auditability`). Nothing in this package constitutes regulatory advice.

---

## Citation

If you use `claimbounded` in your research, please cite:

```bibtex
@software{claimbounded2026,
  title   = {claimbounded: Claim-Bounded Monitoring of AI-Enabled Medical Devices},
  author  = {Yanis Vandecasteele},
  year    = {2026},
  url     = {https://github.com/yanisvdc/claimbounded},
  note    = {Schema version v3\_auditability. Grounded in 1,400 public FDA authorization records.}
}
```

---

## License

MIT © 2026 Yanis Vandecasteele
