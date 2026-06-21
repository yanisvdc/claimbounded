"""Command-line interface for claimbounded.

Examples
--------
    claimbounded report examples/example_profiles/lvo_triage.json
    claimbounded precedents examples/example_profiles/lvo_triage.json --mode hybrid -k 10
    claimbounded lookup K192383
    claimbounded search "large vessel occlusion"
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from .profiles import find_in_corpus, profile_device, search_corpus
from .reports import generate_monitoring_package, generate_monitoring_profile_report


def _load_profile(path: str):
    with open(path, encoding="utf-8") as fh:
        record = json.load(fh)
    return profile_device(record)


def _cmd_report(args: argparse.Namespace) -> int:
    profile = _load_profile(args.profile)
    if args.json:
        pkg = generate_monitoring_package(profile, mode=args.mode, k=args.k)
        print(json.dumps(pkg, indent=2))
    else:
        print(generate_monitoring_profile_report(profile, mode=args.mode, k=args.k))
    return 0


def _cmd_precedents(args: argparse.Namespace) -> int:
    from .precedents import retrieve_precedents

    profile = _load_profile(args.profile)
    precedents = retrieve_precedents(profile, mode=args.mode, k=args.k)
    if args.json:
        print(json.dumps(precedents, indent=2))
    else:
        for p in precedents:
            print(f"{p['score']:.3f}  {p['submission_number']:>10}  {p['device_name'][:42]:42}  "
                  f"-> {p['strongest_auditable_postmarket_claim']}")
            print(f"            {p['match']}")
    return 0


def _cmd_lookup(args: argparse.Namespace) -> int:
    profile = find_in_corpus(args.submission_number)
    if profile is None:
        print(f"No corpus record for {args.submission_number}", file=sys.stderr)
        return 1
    print(json.dumps(profile.to_dict(), indent=2))
    return 0


def _cmd_ui(args: argparse.Namespace) -> int:
    try:
        from .ui import launch
    except ImportError:
        print(
            "Gradio is not installed. Install the UI extra with:\n"
            "    pip install claimbounded[ui]",
            file=sys.stderr,
        )
        return 1
    launch(share=args.share, server_port=args.port)
    return 0


def _cmd_search(args: argparse.Namespace) -> int:
    hits = search_corpus(args.text)
    for h in hits[: args.k]:
        print(f"{h.get('submission_number'):>10}  {h.get('applicant')[:24]:24}  {h.name[:44]:44}  "
              f"-> {h.get('strongest_auditable_postmarket_claim')}")
    print(f"\n{len(hits)} match(es).", file=sys.stderr)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="claimbounded", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_report = sub.add_parser("report", help="full monitoring report from a profile JSON")
    p_report.add_argument("profile")
    p_report.add_argument("--mode", default="hybrid",
                          choices=["like_for_like", "adjacent", "claim_gap", "hybrid"])
    p_report.add_argument("-k", type=int, default=8)
    p_report.add_argument("--json", action="store_true")
    p_report.set_defaults(func=_cmd_report)

    p_prec = sub.add_parser("precedents", help="retrieve comparable precedents")
    p_prec.add_argument("profile")
    p_prec.add_argument("--mode", default="hybrid",
                        choices=["like_for_like", "adjacent", "claim_gap", "hybrid"])
    p_prec.add_argument("-k", type=int, default=10)
    p_prec.add_argument("--json", action="store_true")
    p_prec.set_defaults(func=_cmd_precedents)

    p_lookup = sub.add_parser("lookup", help="print a corpus record by submission number")
    p_lookup.add_argument("submission_number")
    p_lookup.set_defaults(func=_cmd_lookup)

    p_ui = sub.add_parser("ui", help="launch interactive browser UI (requires claimbounded[ui])")
    p_ui.add_argument("--share", action="store_true", help="create a public Gradio share link")
    p_ui.add_argument("--port", type=int, default=7860, metavar="PORT")
    p_ui.set_defaults(func=_cmd_ui)

    p_search = sub.add_parser("search", help="substring search over the corpus")
    p_search.add_argument("text")
    p_search.add_argument("-k", type=int, default=20)
    p_search.set_defaults(func=_cmd_search)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
