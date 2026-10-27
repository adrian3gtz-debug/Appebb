"""Write a synthetic fixture and print statistics derived from its events."""

import argparse
import json
from pathlib import Path

from app.analytics.possession import calculate_possession
from app.models import Match, ShotEvent
from app.services.synthetic_generator import generate_match
from app.services.varied_generator import GENERATOR_VERSION, generate_varied_match
from app.services.synthetic_audit import audit_match


def summarize_match(match: Match) -> dict:
    return {
        "match_id": match.id,
        "synthetic": True,
        "event_count": len(match.events),
        "teams": [
            {
                "team_id": team.id,
                "name": team.name,
                "shots": sum(isinstance(e, ShotEvent) and e.team_id == team.id for e in match.events),
                "goals": sum(
                    isinstance(e, ShotEvent) and e.team_id == team.id and e.outcome == "goal"
                    for e in match.events
                ),
            }
            for team in (match.home_team, match.away_team)
        ],
        "possession": calculate_possession(match).model_dump(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--mode", choices=["authored", "varied"], default="authored")
    parser.add_argument("--generator-version", choices=["varied-v1", "varied-v2"],
                        help="Varied mode only; defaults to the current version")
    parser.add_argument("--audit", action="store_true", help="Include diagnostics; not a realism rating")
    parser.add_argument("--output", type=Path, required=True, help="New JSON file; existing files are not overwritten")
    args = parser.parse_args()
    if args.generator_version and args.mode != "varied":
        parser.error("--generator-version requires --mode varied")
    version = args.generator_version or GENERATOR_VERSION
    match = generate_varied_match(args.seed, version=version) if args.mode == "varied" else generate_match(args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with args.output.open("x", encoding="utf-8") as output:
            output.write(match.model_dump_json(indent=2) + "\n")
    except FileExistsError:
        parser.error(f"file already exists: {args.output}; choose another output path")
    summary = summarize_match(match)
    if args.mode == "varied":
        summary["generation"] = {"version": version, "seed": args.seed, "calibrated": False}
    if args.audit:
        summary["diagnostics"] = audit_match(match)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
