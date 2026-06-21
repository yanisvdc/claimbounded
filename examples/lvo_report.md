# Claim-bounded monitoring profile: Acme LVO Triage (hypothetical new device)

- Applicant: Acme AI, Inc.
- Submission: unclear  |  Product code: QAS
- Authorization endpoint type: diagnostic_accuracy

## Claim profile
- Routine-evidence claim ceiling: **Workflow performance**
- Supportable claims: Technical pipeline stability, Workflow performance
- Audit burden: Requires sampling and chart/image review
- Can re-measure authorization endpoint from routine data: **no** (routine evidence is 3 levels below the authorization claim)
- Extra evidence needed: Draw a sampling frame and perform chart/image review against an adjudicated reference.

## Claim-support matrix
| Claim | Routine evidence? | Evidence needed |
| --- | --- | --- |
| Clinical accuracy or calibration | Requires additional audit work | Independent reference standard, outcome, adjudication, or new study |
| Output quality or measurement agreement | Requires additional audit work | Final measurement or report linked case-level to the AI output |
| Human-machine concordance | Requires linkage | User accept / reject / edit / override events on AI output |
| Workflow performance | Yes | Alert/output delivery, timestamps, acknowledgement, turnaround |
| Technical pipeline stability | Yes | Device logs, failures, uptime, software/model version per inference |
| Utilization only | Requires additional audit work | Counts of device use; no output-level evidence |

## Dashboard claim limits
- Responsible claim: The device is operating and delivering outputs within expected workflow parameters.
- Not supported without extra evidence: The device maintains its authorized diagnostic accuracy after deployment
- To make the stronger claim: Draw a sampling frame and perform chart/image review against an adjudicated reference.

## Minimum audit dataset
- Case-level AI output export (score/label/contour/measurement)
- Model and software version per inference
- Timestamped workflow events (delivery, acknowledgement, action)
- Stable case identifier (accession / order / encounter / specimen)
- Denominator of eligible cases, including non-flagged cases
- Sampling frame for review
- Chart/image review protocol against an adjudicated reference

## Manufacturer design requirements
- Case-level output export (not just alert/notification)
- Logging of non-flagged / non-alerted cases (eligible denominator)
- Model and software version stamped on every inference
- Timestamped workflow events (acquisition, inference, delivery, acknowledgement)
- Stable identifiers (accession / order / specimen / encounter)
- Capture of user accept / edit / reject / override on each output
- Auditable data dictionary for exported fields
- Documentation of the intended postmarket monitoring claim(s) and their evidence chain

## Procurement questions
- What was the device authorized to show (diagnostic accuracy), and against what reference standard?
- Which monitoring claims can our routine data support without new evidence work?
- Can the device export case-level outputs, versions, and identifiers for audit?
- Are non-flagged / non-alerted cases logged so we can estimate false negatives?
- What linkage (EHR / PACS / LIS / pathology / registry) is required to re-measure the authorized endpoint?
- Who is responsible for the chart review / adjudication if endpoint-level audit is needed?

## Comparable public precedents (mode=hybrid)
| Submission | Device | Applicant | Endpoint | Claim ceiling | Score |
| --- | --- | --- | --- | --- | --- |
| K251610 | qER-CTA (v1.0) | Qure.ai Technologies Pvt. Ltd. | diagnostic_accuracy | workflow_performance | 0.7433 |
| K251590 | Methinks CTA Stroke | Methinks Software S.L. | diagnostic_accuracy | workflow_performance | 0.7337 |
| K200873 | HALO | NiCo-Lab B.V. | diagnostic_accuracy | workflow_performance | 0.7246 |
| K221314 | BriefCase | Aidoc Medical, Ltd. | diagnostic_accuracy | workflow_performance | 0.7128 |
| K250685 | Methinks NCCT Stroke | Methinks Software, SL | diagnostic_accuracy | workflow_performance | 0.704 |
| K220709 | BriefCase | Aidoc Medical, Ltd. | diagnostic_accuracy | workflow_performance | 0.6991 |

> This package does not determine whether a device is safe or effective and does not predict FDA decisions. It maps the evidentiary relationship between authorization claims, routine postmarket evidence, and supportable monitoring claims, grounded in public authorization precedents.