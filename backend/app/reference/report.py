"""Reproduce the first Wyscout EPL 2017/18 comparison (no calibration).

Run from backend: python -m app.reference.report --events ... --matches ... --output ...
"""

import argparse
from collections import Counter
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from statistics import median, quantiles

from app.reference.observations import Observation, synthetic_observations
from app.reference.download import BASE_URL, SNAPSHOT
from app.reference.wyscout import read_observations
from app.services.varied_generator import generate_varied_match


SPLIT_VERSION = "wyscout-epl-2017-18-v1"


def split_matches(ids: list[str]) -> tuple[list[str], list[str]]:
    """Freeze a match-level 300/80 split without selecting on scores or metrics."""
    if len(ids) != 380 or len(set(ids)) != 380:
        raise ValueError("expected 380 unique EPL 2017/18 matches")
    ordered = sorted(ids, key=lambda value: sha256(f"{SPLIT_VERSION}:{value}".encode()).hexdigest())
    return ordered[:300], ordered[300:]


def distribution(values: list[int | float]) -> dict:
    if not values:
        return {"count": 0, "min": None, "p25": None, "median": None, "p75": None, "max": None}
    quartiles = quantiles(values, n=4, method="inclusive") if len(values) > 1 else [values[0]] * 3
    return dict(count=len(values), min=min(values), p25=quartiles[0], median=median(values), p75=quartiles[2], max=max(values))


def summarize(observations: list[Observation], match_ids: list[str], *, regulation_only: bool) -> dict:
    """Include zero-action matches and expose missing accuracy denominators."""
    grouped: dict[str, list[Observation]] = {key: [] for key in match_ids}
    for event in observations:
        if event.match_id in grouped and (not regulation_only or event.period_second < 2700):
            grouped[event.match_id].append(event)
    rows = []
    cells: Counter = Counter()
    for events in grouped.values():
        passes = [event for event in events if event.kind == "pass"]
        shots = [event for event in events if event.kind == "shot"]
        complete = sum(event.pass_complete is True for event in passes)
        unknown = sum(event.pass_complete is None for event in passes)
        known = len(passes) - unknown
        rows.append({
            "passes_including_pass_restarts": len(passes), "shots_including_shot_restarts": len(shots),
            "passes_with_unknown_outcome": unknown,
            "accuracy_among_known_pass_outcomes_pct": 100 * complete / known if known else None,
        })
        for event in shots:
            # Fixed grid in the attacking frame; x=100 and y=100 stay in bounds.
            cells[f"{min(5, int(event.attacking_x // (100 / 6)))}:{min(3, int(event.attacking_y // 25))}"] += 1
    fields = rows[0].keys() if rows else []
    return {
        "match_count": len(match_ids),
        "per_match": {field: distribution([row[field] for row in rows if row[field] is not None]) for field in fields},
        "shot_grid_6_by_4_counts": dict(sorted(cells.items())),
        "possession_seconds": None,
        "passes_per_possession": None,
    }


def reference_cohorts(raw_events: list[dict], matches: list[dict]) -> tuple:
    """Validate the selected season before exposing its frozen cohorts."""
    teams_by_match = {}
    team_counts: Counter = Counter()
    for match in matches:
        key = str(match["wyId"])
        if key in teams_by_match:
            raise ValueError("duplicate match metadata")
        if match["competitionId"] != 364 or match["seasonId"] != 181150 or match["status"] != "Played":
            raise ValueError("metadata is not played EPL 2017/18")
        teams = match["teamsData"]
        if len(teams) != 2 or {value["side"] for value in teams.values()} != {"home", "away"}:
            raise ValueError("expected one home team and one away team")
        teams_by_match[key] = set(teams)
        team_counts.update(teams.keys())
    tuning, holdout = split_matches(list(teams_by_match))
    if len(team_counts) != 20 or set(team_counts.values()) != {38}:
        raise ValueError("expected 20 clubs playing 38 matches each")
    observations = read_observations(raw_events, teams_by_match)
    if {event.match_id for event in observations} != set(teams_by_match):
        raise ValueError("missing event coverage for one or more matches")
    return observations, tuning, holdout, team_counts


def build_report(raw_events: list[dict], matches: list[dict], *, synthetic_count: int) -> dict:
    if synthetic_count < 1:
        raise ValueError("synthetic_count must be positive")
    observations, tuning, holdout, team_counts = reference_cohorts(raw_events, matches)
    synthetic = []
    synthetic_ids = []
    for seed in range(synthetic_count):
        # Keep stage 1 reproducible after the browser's generator advances.
        match = generate_varied_match(seed, version="varied-v1")
        # Seed-specific comparison keys even if a future generator reuses its demo ID.
        key = f"seed:{seed}"
        synthetic_ids.append(key)
        synthetic.extend(replace(event, match_id=key) for event in synthetic_observations(match))
    return {
        "methodology": "reference-comparison-v1", "calibrated": False,
        "reference": {"provider": "Wyscout", "competition": "Premier League", "season": "2017/18",
                      "source": "https://doi.org/10.6084/m9.figshare.c.4415000", "license": "CC BY 4.0",
                      "mirror_snapshot": SNAPSHOT, "mirror_base_url": BASE_URL},
        "split": {"version": SPLIT_VERSION, "tuning_ids": tuning, "held_out_ids": holdout,
                  "held_out_metrics_computed": False},
        "coverage": {"matches": len(matches), "events": len(observations),
                     "clubs": len(team_counts), "matches_per_club": dict(sorted(team_counts.items())),
                     "unknown_actor_events": sum(event.player_id is None for event in observations),
                     "events_at_or_after_45_minutes_in_either_half": sum(event.period_second >= 2700 for event in observations)},
        "reference_tuning_full_clock": summarize(observations, tuning, regulation_only=False),
        "reference_tuning_first_45_minutes_of_each_half": summarize(observations, tuning, regulation_only=True),
        "synthetic": {"version": "varied-v1", "seeds": list(range(synthetic_count)),
                      "summary": summarize(synthetic, synthetic_ids, regulation_only=True)},
        "limitations": [
            "Historical 2017/18 reference, not current Premier League validation.",
            "Pass counts include pass restarts; shots include penalties and direct free kicks.",
            "Goal kicks without accuracy tags remain unknown; accuracy uses known outcomes only.",
            "Two 45-minute observation windows omit real added-time actions; full-clock counts are also reported.",
            "No exact control time, receivers, carries, recoveries or possession sequences inferred from this release.",
            "Synthetic restart context is unavailable, so open-play-only comparison is not supported yet.",
            "No significance tests, learned parameters or automatic realism score.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--matches", type=Path, required=True)
    parser.add_argument("--synthetic-count", type=int, default=100)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output exists; choose a new path")
    paths = {"events": args.events, "matches": args.matches}
    contents = {key: path.read_bytes() for key, path in paths.items()}
    try:
        report = build_report(json.loads(contents["events"]), json.loads(contents["matches"]),
                              synthetic_count=args.synthetic_count)
    except (ValueError, KeyError, TypeError) as error:
        parser.error(str(error))
    report["input_sha256"] = {key: sha256(content).hexdigest() for key, content in contents.items()}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as output:
        json.dump(report, output, indent=2, allow_nan=False)
        output.write("\n")
    print(f"Report written to {args.output}")


if __name__ == "__main__":
    main()
