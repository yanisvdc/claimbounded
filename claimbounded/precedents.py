"""Precedent retrieval over the public FDA corpus.

The core asset of this package is the *coded* corpus: every device carries an
authorization endpoint type, ground-truth modality, routine evidence stream,
claim ceiling, and audit burden.  Structured retrieval over those fields is
more reliable than free-text similarity, so it is the primary method; BM25 over
the free-text fields is a transparent supplement.

Each returned precedent includes the real FDA submission number, so a user can
look the device up and study how an adjacent problem was actually handled.

Retrieval modes
---------------
* ``like_for_like`` - same regulatory and clinical identity
* ``adjacent``      - same postmarket-evidence problem, any product code
* ``claim_gap``     - same divergence between authorization endpoint and ceiling
* ``hybrid``        - weighted blend of all signals (default)
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any, Optional

from .profiles import corpus_records
from .schema import (
    BM25_TEXT_FIELDS,
    CLAIM_SCHEMA_FIELDS,
    EVIDENCE_GAP_FIELDS,
    STRUCTURED_REGULATORY_FIELDS,
    DeviceEvidenceProfile,
)

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOP = {
    "the", "a", "an", "of", "and", "or", "to", "for", "in", "on", "with",
    "is", "are", "be", "by", "as", "that", "this", "from", "at", "it", "not",
    "device", "ai", "system", "software", "patient", "patients", "clinical",
}

HYBRID_WEIGHTS = {
    "structured": 0.35,
    "schema": 0.30,
    "bm25": 0.20,
    "evidence_gap": 0.15,
}


def _tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN_RE.findall(str(text).lower()) if t not in _STOP and len(t) > 2]


def _doc_text(rec: dict[str, Any], fields: list[str]) -> list[str]:
    parts = [str(rec.get(f, "")) for f in fields]
    return _tokenize(" ".join(parts))


# ---------------------------------------------------------------------------
# BM25 index (dependency-free implementation of the Okapi BM25 model)
# ---------------------------------------------------------------------------
@dataclass
class BM25Index:
    docs: list[list[str]]
    fields: list[str]
    k1: float = 1.5
    b: float = 0.75

    def __post_init__(self) -> None:
        self.N = len(self.docs)
        self.doc_len = [len(d) for d in self.docs]
        self.avgdl = (sum(self.doc_len) / self.N) if self.N else 0.0
        df: Counter = Counter()
        for d in self.docs:
            for term in set(d):
                df[term] += 1
        self.idf = {
            term: math.log(1 + (self.N - n + 0.5) / (n + 0.5)) for term, n in df.items()
        }
        self._tf = [Counter(d) for d in self.docs]

    def score(self, query_tokens: list[str], doc_idx: int) -> float:
        tf = self._tf[doc_idx]
        dl = self.doc_len[doc_idx]
        score = 0.0
        for term in query_tokens:
            if term not in tf:
                continue
            idf = self.idf.get(term, 0.0)
            freq = tf[term]
            denom = freq + self.k1 * (1 - self.b + self.b * dl / (self.avgdl or 1))
            score += idf * (freq * (self.k1 + 1)) / (denom or 1)
        return score


def build_bm25_index(fields: Optional[list[str]] = None) -> tuple[BM25Index, list[dict[str, Any]]]:
    """Build a BM25 index over the corpus free-text fields."""

    fields = fields or BM25_TEXT_FIELDS
    records = corpus_records()
    docs = [_doc_text(r, fields) for r in records]
    return BM25Index(docs=docs, fields=fields), records


# ---------------------------------------------------------------------------
# Structured similarity
# ---------------------------------------------------------------------------
def _field_match(a: Any, b: Any) -> float:
    a, b = str(a).strip().lower(), str(b).strip().lower()
    if a in {"", "unclear"} or b in {"", "unclear"}:
        return 0.0
    return 1.0 if a == b else 0.0


def _weighted_field_similarity(
    profile: DeviceEvidenceProfile, rec: dict[str, Any], fields: list[str]
) -> float:
    scores, weights = [], []
    for i, f in enumerate(fields):
        # earlier fields weighted slightly higher
        w = len(fields) - i
        scores.append(_field_match(profile.get(f), rec.get(f)) * w)
        weights.append(w)
    return sum(scores) / sum(weights) if weights else 0.0


def structured_similarity(profile: DeviceEvidenceProfile, rec: dict[str, Any]) -> float:
    """Regulatory/clinical identity similarity in [0, 1]."""

    return _weighted_field_similarity(profile, rec, STRUCTURED_REGULATORY_FIELDS)


def schema_similarity(profile: DeviceEvidenceProfile, rec: dict[str, Any]) -> float:
    """Claim-bounded schema similarity (endpoint / GT / stream / ceiling / burden)."""

    return _weighted_field_similarity(profile, rec, CLAIM_SCHEMA_FIELDS)


def evidence_gap_similarity(profile: DeviceEvidenceProfile, rec: dict[str, Any]) -> float:
    """Similarity of the evidence-gap / monitoring-implication fields."""

    # monitoring_implication and reason are categorical; extra_evidence is text.
    cat = 0.0
    for f in ("reason_authorization_endpoint_not_auditable", "monitoring_implication"):
        cat += _field_match(profile.get(f), rec.get(f))
    cat /= 2.0
    # token overlap on extra_evidence_needed
    a = set(_tokenize(profile.get("extra_evidence_needed", "")))
    b = set(_tokenize(rec.get("extra_evidence_needed", "")))
    jac = len(a & b) / len(a | b) if (a | b) else 0.0
    return 0.6 * cat + 0.4 * jac


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------
_PRECEDENT_SUMMARY_FIELDS = [
    "submission_number",
    "submission_pathway",
    "device_name",
    "applicant",
    "year",
    "product_code",
    "panel",
    "clinical_domain",
    "device_function",
    "intended_use_summary",
    "authorization_endpoint_type",
    "authorization_ground_truth_modality",
    "routine_postmarket_evidence_stream",
    "strongest_auditable_postmarket_claim",
    "postmarket_audit_burden",
    "extra_evidence_needed",
    "authorization_performance_claim",
    "supporting_quote_authorization",
]


def _normalize(scores: list[float]) -> list[float]:
    if not scores:
        return scores
    hi = max(scores)
    return [s / hi if hi > 0 else 0.0 for s in scores]


def retrieve_precedents(
    profile: DeviceEvidenceProfile,
    mode: str = "hybrid",
    k: int = 10,
    exclude_self: bool = True,
) -> list[dict[str, Any]]:
    """Retrieve the ``k`` most relevant precedents for ``profile``.

    Returns a list of dicts: a precedent summary plus ``score`` and a
    ``match`` explanation of which signals fired.
    """

    if mode not in {"like_for_like", "adjacent", "claim_gap", "hybrid"}:
        raise ValueError(f"unknown mode: {mode}")

    index, records = build_bm25_index()
    query_tokens = _doc_text(profile.to_dict(), BM25_TEXT_FIELDS)
    bm25_raw = [index.score(query_tokens, i) for i in range(len(records))]
    bm25_norm = _normalize(bm25_raw)

    self_sub = str(profile.get("submission_number", "")).strip().upper()

    scored: list[tuple[float, dict[str, Any], dict[str, Any]]] = []
    for i, rec in enumerate(records):
        if exclude_self and self_sub and str(rec.get("submission_number", "")).strip().upper() == self_sub:
            continue

        struct = structured_similarity(profile, rec)
        schema = schema_similarity(profile, rec)
        gap = evidence_gap_similarity(profile, rec)
        bm = bm25_norm[i]

        if mode == "like_for_like":
            score = struct
        elif mode == "adjacent":
            score = schema
        elif mode == "claim_gap":
            score = _claim_gap_score(profile, rec)
        else:  # hybrid
            score = (
                HYBRID_WEIGHTS["structured"] * struct
                + HYBRID_WEIGHTS["schema"] * schema
                + HYBRID_WEIGHTS["bm25"] * bm
                + HYBRID_WEIGHTS["evidence_gap"] * gap
            )

        components = {
            "structured": round(struct, 3),
            "schema": round(schema, 3),
            "bm25": round(bm, 3),
            "evidence_gap": round(gap, 3),
        }
        scored.append((score, rec, components))

    scored.sort(key=lambda t: t[0], reverse=True)
    out = []
    for score, rec, components in scored[:k]:
        summary = {f: rec.get(f) for f in _PRECEDENT_SUMMARY_FIELDS}
        summary["score"] = round(score, 4)
        summary["match"] = explain_precedent_match(profile, rec, components)
        out.append(summary)
    return out


def _claim_gap_score(profile: DeviceEvidenceProfile, rec: dict[str, Any]) -> float:
    """Score precedents that share the same authorization->ceiling divergence."""

    fields = [
        "authorization_endpoint_type",
        "strongest_auditable_postmarket_claim",
        "postmarket_audit_burden",
    ]
    matches = sum(_field_match(profile.get(f), rec.get(f)) for f in fields)
    return matches / len(fields)


def explain_precedent_match(
    profile: DeviceEvidenceProfile, rec: dict[str, Any], components: dict[str, Any]
) -> str:
    """Human-readable explanation of why a precedent matched."""

    shared = []
    for f, label in [
        ("product_code", "product code"),
        ("device_function", "device function"),
        ("authorization_endpoint_type", "authorization endpoint"),
        ("authorization_ground_truth_modality", "ground truth"),
        ("routine_postmarket_evidence_stream", "evidence stream"),
        ("strongest_auditable_postmarket_claim", "claim ceiling"),
        ("postmarket_audit_burden", "audit burden"),
    ]:
        if _field_match(profile.get(f), rec.get(f)) == 1.0:
            shared.append(f"{label}={rec.get(f)}")
    if not shared:
        return "text similarity only"
    return "shares " + "; ".join(shared)
