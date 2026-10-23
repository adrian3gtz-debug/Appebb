"""Behavioral checks for the first authored synthetic match."""

import json
from math import hypot
from pathlib import Path
import subprocess
import sys

import pytest

from app.analytics.possession import calculate_possession
from app.models import CarryEvent, Match, PassEvent, PressureEvent, RecoveryEvent, ShotEvent
from app.services.generate_match import summarize_match
from app.services.synthetic_generator import generate_match


def test_seed_is_reproducible_and_changes_the_fixture() -> None:
    assert generate_match(7).model_dump_json() == generate_match(7).model_dump_json()
    assert generate_match(7).model_dump_json() != generate_match(19).model_dump_json()


@pytest.mark.parametrize("seed", [0, 7, 19, 99])
def test_generated_match_has_continuous_actions_and_valid_clock(seed: int) -> None:
    match = generate_match(seed)
    assert Match.model_validate_json(match.model_dump_json()) == match
    assert len(match.home_team.players) == len(match.away_team.players) == 11
    assert sum(s.end_second - s.start_second for s in match.ball_states) == 5400

    actions = [event for event in match.events if not isinstance(event, PressureEvent)]
    for previous, current in zip(actions, actions[1:]):
        same_possession = previous.possession_id == current.possession_id
        if same_possession and isinstance(previous, (PassEvent, CarryEvent)):
            assert previous.end_location == current.location
            if isinstance(previous, PassEvent):
                assert previous.outcome == "complete"
                assert current.player_id == previous.receiver_id
            else:
                assert current.player_id == previous.player_id

            # Only a plausibility bound under a hypothetical 105 x 68 m field.
            distance = hypot(
                (previous.end_location.x - previous.location.x) * 1.05,
                (previous.end_location.y - previous.location.y) * 0.68,
            )
            elapsed = current.second - previous.second
            assert elapsed > 0
            assert distance / elapsed <= (9 if isinstance(previous, CarryEvent) else 35)

        if not same_possession:
            if isinstance(current, RecoveryEvent):
                assert isinstance(previous, PassEvent)
                assert previous.outcome == "incomplete"
                assert previous.end_location == current.location
                assert current.team_id != previous.team_id
            else:
                assert any(
                    state.state == "out_of_play"
                    and previous.second < state.start_second
                    and state.end_second <= current.second
                    for state in match.ball_states
                ), "a restart needs an explicit dead-ball interval"


@pytest.mark.parametrize("seed", [0, 7, 19, 99])
def test_more_possession_does_not_mean_more_shots_or_a_win(seed: int) -> None:
    match = generate_match(seed)
    possession = calculate_possession(match)
    home, away = summarize_match(match)["teams"]
    assert possession.home_seconds > possession.away_seconds
    assert home["shots"] < away["shots"]
    assert home["goals"] < away["goals"]

    # Evaluate direction using observed coordinates, including the halftime switch.
    for team in ("home", "away"):
        passes = [e for e in match.events if isinstance(e, PassEvent) and e.team_id == team]
        backwards = sum(
            (e.end_location.x - e.location.x) * (1 if (team == "home") == (e.period == 1) else -1) < 0
            for e in passes
        )
        assert backwards / len(passes) > 0.3 if team == "home" else backwards / len(passes) < 0.15


def test_score_is_derived_from_recorded_goals() -> None:
    payload = generate_match(7).model_dump()
    for event in payload["events"]:
        if event["type"] == "shot" and event["outcome"] == "goal":
            event["outcome"] = "off_target"
    changed = Match.model_validate(payload)

    assert [team["goals"] for team in summarize_match(changed)["teams"]] == [0, 0]


def test_kickoffs_and_goals_use_the_expected_restarts() -> None:
    match = generate_match(7)
    actions = [e for e in match.events if not isinstance(e, PressureEvent)]
    kickoffs = [e for e in actions if e.second in (0, 2700)]
    assert [e.team_id for e in kickoffs] == ["home", "away"]
    for kickoff in kickoffs:
        assert (kickoff.location.x, kickoff.location.y) == (50, 50)
    for index, event in enumerate(actions[:-1]):
        if isinstance(event, ShotEvent) and event.outcome == "goal":
            restart = actions[index + 1]
            assert restart.team_id != event.team_id
            assert (restart.location.x, restart.location.y) == (50, 50)


def test_checked_in_fixture_matches_the_generator() -> None:
    fixture = Path(__file__).resolve().parents[2] / "data/synthetic/circulation-vs-counterattack.json"
    assert Match.model_validate_json(fixture.read_text(encoding="utf-8")) == generate_match(7)


def test_cli_writes_valid_json_and_refuses_to_overwrite(tmp_path: Path) -> None:
    output = tmp_path / "match.json"
    command = [sys.executable, "-m", "app.services.generate_match", "--seed", "7", "--output", str(output)]
    first = subprocess.run(command, capture_output=True, text=True, check=True)
    original = output.read_bytes()
    assert json.loads(first.stdout)["synthetic"] is True
    Match.model_validate_json(original)
    second = subprocess.run(command, capture_output=True, text=True)
    assert second.returncode != 0
    assert "already exists" in second.stderr
    assert output.read_bytes() == original
