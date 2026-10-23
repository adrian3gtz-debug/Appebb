"""Possession time is derived from complete ball-control intervals."""

import pytest
from pydantic import ValidationError

from app.analytics.possession import calculate_possession
from app.models import Match


def team(team_id: str) -> dict:
    return {
        "id": team_id,
        "name": team_id.title(),
        "players": [
            {
                "id": f"{team_id}-{number}",
                "name": f"Player {number}",
                "role": "goalkeeper" if number == 0 else "midfielder",
            }
            for number in range(11)
        ],
    }


def interval(start: int, end: int, state: str, team_id: str | None = None) -> dict:
    return {
        "start_second": start,
        "end_second": end,
        "state": state,
        "team_id": team_id,
    }


def match_payload(ball_states: list[dict]) -> dict:
    return {
        "id": "example",
        "home_team": team("home"),
        "away_team": team("away"),
        "ball_states": ball_states,
    }


def test_control_time_excludes_contested_and_out_of_play() -> None:
    match = Match.model_validate(match_payload([
        interval(0, 600, "controlled", "home"),
        interval(600, 900, "contested"),
        interval(900, 1800, "controlled", "away"),
        interval(1800, 2100, "out_of_play"),
        interval(2100, 5400, "controlled", "home"),
    ]))

    summary = calculate_possession(match)

    assert summary.home_seconds == 3900
    assert summary.away_seconds == 900
    assert summary.contested_seconds == 300
    assert summary.out_of_play_seconds == 300
    assert summary.home_share_percent == 81.25
    assert summary.away_share_percent == 18.75


@pytest.mark.parametrize(
    ("ball_states", "message"),
    [
        ([interval(0, 100, "controlled", "home"), interval(99, 5400, "controlled", "away")], "overlap"),
        ([interval(0, 100, "controlled", "home"), interval(101, 5400, "controlled", "away")], "gaps"),
        ([interval(1, 5400, "controlled", "home")], "gaps"),
        ([interval(0, 5399, "controlled", "home")], "full match clock"),
        ([interval(0, 5400, "controlled", "other")], "unknown team"),
        ([interval(0, 5400, "contested", "home")], "only controlled"),
        ([interval(0, 5400, "controlled")], "require a team_id"),
        ([interval(100, 100, "controlled", "home")], "positive duration"),
    ],
)
def test_invalid_timeline_is_rejected(ball_states: list[dict], message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        Match.model_validate(match_payload(ball_states))


def test_event_must_agree_with_ball_control() -> None:
    payload = match_payload([
        interval(0, 100, "controlled", "home"),
        interval(100, 5400, "controlled", "away"),
    ])
    payload["events"] = [{
        "id": "pass-1",
        "match_id": "example",
        "period": 1,
        "second": 100,
        "type": "pass",
        "team_id": "home",
        "player_id": "home-1",
        "possession_id": "home-possession",
        "possession_team_id": "home",
        "location": {"x": 20, "y": 40},
        "end_location": {"x": 30, "y": 40},
        "receiver_id": "home-2",
        "outcome": "complete",
    }]

    with pytest.raises(ValidationError, match="disagrees with ball control"):
        Match.model_validate(payload)


def test_uncontrolled_match_has_no_possession_percentage() -> None:
    match = Match.model_validate(match_payload([interval(0, 5400, "out_of_play")]))

    summary = calculate_possession(match)

    assert summary.home_seconds == summary.away_seconds == 0
    assert summary.home_share_percent is None
    assert summary.away_share_percent is None


def test_possession_requires_a_complete_timeline() -> None:
    match = Match.model_validate(match_payload([]))

    with pytest.raises(ValueError, match="complete ball-state timeline"):
        calculate_possession(match)
