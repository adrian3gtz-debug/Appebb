"""Compare restart contexts and recorded action timing on the frozen cohorts."""

import argparse
from collections import Counter
from dataclasses import asdict, replace
from hashlib import sha256
import json
from pathlib import Path
from statistics import median

from app.reference.observations import Observation, synthetic_observations
from app.reference.download import SNAPSHOT
from app.reference.report import distribution, reference_cohorts, SPLIT_VERSION
from app.services.synthetic_audit import audit_match
from app.services.varied_generator import _Builder, GenerationRules, VERSION_RULES


# A small, predeclared sensitivity experiment. No outcome quotas or shot-rule changes.
CANDIDATES = {
    "annotation_only": GenerationRules(),
    "travel_floor_1": GenerationRules(minimum_travel_seconds=1),
    "failure_075": GenerationRules(pass_failure_base=.075),
    "travel_1_failure_075": GenerationRules(pass_failure_base=.075, minimum_travel_seconds=1),
    "decision_085_travel_1_failure_075": GenerationRules(.075, .85, 1),
    "decision_065_travel_1_failure_075": GenerationRules(.075, .65, 1),
}

REFERENCE = {
    "provider": "Wyscout", "authors": ["Luca Pappalardo", "Emanuele Massucco"],
    "competition": "Premier League", "season": "2017/18",
    "source": "https://doi.org/10.6084/m9.figshare.c.4415000",
    "license": "CC BY 4.0", "license_url": "https://creativecommons.org/licenses/by/4.0/",
    "mirror_snapshot": SNAPSHOT,
    "transformations": "Attacking-frame observations; period-relative first-45-minute windows; match-level aggregates.",
}


def context_summary(observations: list[Observation], ids: list[str]) -> dict:
    grouped: dict[str, list[Observation]] = {key: [] for key in ids}
    for event in observations:
        if event.match_id in grouped and event.period_second < 2700:
            # Synthetic pressure is an annotation simultaneous with an action.
            # Real duels, touches, interruptions and other records still break adjacency.
            if event.source == "synthetic" and event.provider_type == "pressure":
                continue
            grouped[event.match_id].append(event)
    per_match = []
    contexts: Counter = Counter()
    zones: Counter = Counter()
    for events in grouped.values():
        passes = [event for event in events if event.kind == "pass"]
        ordinary = [event for event in passes if event.pass_context in {"open_play", "unmarked"}]
        known = [event for event in ordinary if event.pass_complete is not None]
        shots = [event for event in events if event.kind == "shot"]
        contexts.update(event.pass_context or "unknown" for event in passes)
        directions: Counter = Counter()
        for event in ordinary:
            if event.end_attacking_x is None or event.end_attacking_y is None:
                directions["unknown_endpoint"] += 1
                continue
            dx = (event.end_attacking_x - event.attacking_x) * 1.05
            dy = abs(event.end_attacking_y - event.attacking_y) * .68
            directions["forward" if dx > dy else "backward" if dx < -dy else "lateral"] += 1
        gaps = []
        for previous, following in zip(events, events[1:]):
            if (previous.kind == following.kind == "pass"
                    and previous.pass_context in {"open_play", "unmarked"}
                    and following.pass_context in {"open_play", "unmarked"}
                    and previous.pass_complete is True
                    and previous.team_id == following.team_id and previous.period == following.period):
                gaps.append(following.period_second - previous.period_second)
        per_match.append({
            "ordinary_or_unmarked_passes": len(ordinary),
            "pass_restarts_marked": sum(event.restart is True for event in passes),
            "ordinary_pass_accuracy_known_pct": 100 * sum(event.pass_complete is True for event in known) / len(known) if known else None,
            "record_adjacent_pass_gap_median_seconds": median(gaps) if gaps else None,
            "adjacent_pass_pairs": len(gaps),
            "shots": len(shots),
            "ordinary_pass_forward_pct": 100 * directions["forward"] / len(ordinary) if ordinary else None,
            "ordinary_pass_backward_pct": 100 * directions["backward"] / len(ordinary) if ordinary else None,
            "ordinary_pass_lateral_pct": 100 * directions["lateral"] / len(ordinary) if ordinary else None,
        })
        zones.update("own_third" if event.attacking_x < 100 / 3 else "middle_third"
                     if event.attacking_x < 200 / 3 else "final_third" for event in shots)
    return {"matches": len(ids), "pass_context_counts": dict(sorted(contexts.items())),
            "shot_zones_counts": dict(sorted(zones.items())),
            "per_match": {key: distribution([row[key] for row in per_match if row[key] is not None])
                          for key in per_match[0]} if per_match else {}}


def synthetic_cohort(rules: GenerationRules, count: int) -> dict:
    observations = []
    ids = []
    issue_count = 0
    for seed in range(count):
        match = _Builder(seed, version="varied-v2", rules=rules).build()
        issue_count += len(audit_match(match)["structural_issues"])
        key = f"seed:{seed}"
        ids.append(key)
        observations.extend(replace(event, match_id=key) for event in synthetic_observations(match))
    return {"rules": asdict(rules), "seeds": list(range(count)), "structural_issue_count": issue_count,
            "summary": context_summary(observations, ids)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--matches", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--experiment", action="store_true", help="Compare the declared candidate rules on seeds 0–19")
    parser.add_argument("--evaluate-held-out", action="store_true", help="Final evaluation only after rules and metrics are frozen")
    args = parser.parse_args()
    if args.experiment and args.evaluate_held_out:
        parser.error("candidate experiments cannot read held-out outcome metrics")
    if args.output.exists():
        parser.error("output exists; choose a new path")
    contents = {"events": args.events.read_bytes(), "matches": args.matches.read_bytes()}
    observations, tuning, holdout, _ = reference_cohorts(json.loads(contents["events"]), json.loads(contents["matches"]))
    report = {
        "methodology": "reference-context-v1", "calibrated": False,
        "reference": REFERENCE,
        "input_sha256": {key: sha256(value).hexdigest() for key, value in contents.items()},
        "split_version": SPLIT_VERSION, "held_out_metrics_computed": args.evaluate_held_out,
        "tuning": context_summary(observations, tuning),
        "limitations": [
            "Wyscout unmarked type-8 passes include kickoffs; synthetic open_play excludes explicit kickoffs.",
            "First 2700 seconds of each half only; no compression of added time.",
            "Adjacent-record gaps include decision and travel, not measured ball flight or possession duration.",
            "Synthetic pressure annotations are excluded before adjacency; real duels/touches/interruptions break pairs.",
            "Direction sectors assume a 105x68m pitch and are diagnostics, not progressive-pass labels.",
            "Missing fouls, corners and same-team rebounds still limit representation.",
        ],
    }
    if args.experiment:
        report["candidates"] = {name: synthetic_cohort(rules, 20) for name, rules in CANDIDATES.items()}
    else:
        report["before_annotation_only"] = synthetic_cohort(VERSION_RULES["varied-v1"], 100)
        report["after_varied_v2"] = synthetic_cohort(VERSION_RULES["varied-v2"], 100)
        if args.evaluate_held_out:
            report["held_out"] = context_summary(observations, holdout)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as output:
        json.dump(report, output, indent=2, allow_nan=False)
        output.write("\n")
    print(f"Report written to {args.output}")


if __name__ == "__main__":
    main()
