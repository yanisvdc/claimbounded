"""Device intake, normalization, and corpus loading.

``profile_device`` translates any partial device record into the study schema
(:class:`~claimbounded.schema.DeviceEvidenceProfile`).  ``load_corpus`` reads
the shipped FDA dataset; ``find_in_corpus`` lets a user pull an exact
precedent by submission number.
"""

from __future__ import annotations

import csv
import os
from functools import lru_cache
from typing import Any, Iterable, Optional

from .schema import DEFAULT_VALUE, PROFILE_FIELDS, DeviceEvidenceProfile

_DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "fda_ai_device_claims.csv")


def _clean(value: Any) -> Any:
    if value is None:
        return DEFAULT_VALUE
    if isinstance(value, str):
        v = value.strip()
        return v if v else DEFAULT_VALUE
    return value


def normalize_device_record(record: dict[str, Any]) -> dict[str, Any]:
    """Coerce an arbitrary dict into the canonical field set.

    Unknown keys are dropped; missing keys default to ``"unclear"``; values are
    whitespace-stripped.  Lightweight aliases are accepted so callers do not
    have to memorize the exact column names.
    """

    aliases = {
        "name": "device_name",
        "device": "device_name",
        "manufacturer": "applicant",
        "vendor": "applicant",
        "pathway": "submission_pathway",
        "endpoint_type": "authorization_endpoint_type",
        "ground_truth": "authorization_ground_truth_modality",
        "evidence_stream": "routine_postmarket_evidence_stream",
        "intended_use": "intended_use_summary",
        "ai_task": "primary_ai_task",
    }
    out: dict[str, Any] = {}
    for key, value in record.items():
        canonical = aliases.get(key, key)
        if canonical in PROFILE_FIELDS:
            out[canonical] = _clean(value)
    for f in PROFILE_FIELDS:
        out.setdefault(f, DEFAULT_VALUE)
    return out


def profile_device(device_record: dict[str, Any]) -> DeviceEvidenceProfile:
    """Build a :class:`DeviceEvidenceProfile` from a partial device record.

    This is the package entry point.  Supply whatever you know about a device
    (a few fields are enough); the profile fills the rest with ``"unclear"``.
    """

    return DeviceEvidenceProfile(fields=normalize_device_record(device_record))


@lru_cache(maxsize=1)
def _read_rows() -> tuple[dict[str, Any], ...]:
    with open(_DATA_FILE, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        return tuple(normalize_device_record(row) for row in reader)


def load_corpus() -> list[DeviceEvidenceProfile]:
    """Return the shipped corpus as a list of profiles (one per FDA record)."""

    return [DeviceEvidenceProfile(fields=dict(r)) for r in _read_rows()]


def corpus_records() -> list[dict[str, Any]]:
    """Return the raw corpus rows as dictionaries."""

    return [dict(r) for r in _read_rows()]


def find_in_corpus(submission_number: str) -> Optional[DeviceEvidenceProfile]:
    """Look up an exact precedent by FDA submission number (e.g. ``K192383``)."""

    target = submission_number.strip().upper()
    for r in _read_rows():
        if str(r.get("submission_number", "")).strip().upper() == target:
            return DeviceEvidenceProfile(fields=dict(r))
    return None


def corpus_stats(profile: "DeviceEvidenceProfile") -> dict:
    """Return corpus-level percentages contextualizing a device profile.

    Computes what fraction of the 1,400-device corpus shares the same
    claim ceiling, recoverability class, and evaluability class — and
    provides the same statistics filtered to the same device_function peer group.
    Uses the cached corpus so repeated calls are fast.
    """
    records = corpus_records()
    n_total = len(records)
    if n_total == 0:
        return {}

    ceiling = str(profile.get("strongest_auditable_postmarket_claim", "")).strip().lower()
    recov = str(profile.get("authorization_endpoint_recoverability", "")).strip().lower()
    evaluability = str(profile.get("postmarket_evaluability_class", "")).strip().lower()
    fn = str(profile.get("device_function", "")).strip().lower()

    def _pct(field: str, value: str, subset=None) -> tuple[int, int]:
        pool = subset if subset is not None else records
        n_match = sum(1 for r in pool if str(r.get(field, "")).strip().lower() == value)
        return n_match, len(pool)

    result: dict = {"n_corpus": n_total}

    peers = [r for r in records if str(r.get("device_function", "")).strip().lower() == fn] if fn and fn != "unclear" else []

    for key, field in [
        ("ceiling", "strongest_auditable_postmarket_claim"),
        ("recoverability", "authorization_endpoint_recoverability"),
        ("evaluability", "postmarket_evaluability_class"),
    ]:
        value = {"ceiling": ceiling, "recoverability": recov, "evaluability": evaluability}[key]
        if value and value not in {"unclear", ""}:
            n_match, denom = _pct(field, value)
            result[f"{key}_n"] = n_match
            result[f"{key}_pct"] = round(n_match / denom * 100, 1) if denom else None
            if peers:
                pn, pdenom = _pct(field, value, peers)
                result[f"{key}_peer_n"] = pn
                result[f"{key}_peer_pct"] = round(pn / pdenom * 100, 1) if pdenom else None
                result[f"n_peers"] = len(peers)

    return result


def search_corpus(text: str) -> list[DeviceEvidenceProfile]:
    """Case-insensitive substring search over device name, applicant, and excerpts."""

    needle = text.strip().lower()
    hits = []
    for r in _read_rows():
        haystack = " ".join(
            str(r.get(k, "")) for k in (
                "device_name", "applicant", "intended_use_summary",
                "authorization_endpoint", "supporting_quote_authorization",
                "clinical_domain", "device_function", "disease_area",
            )
        ).lower()
        if needle in haystack:
            hits.append(DeviceEvidenceProfile(fields=dict(r)))
    return hits
