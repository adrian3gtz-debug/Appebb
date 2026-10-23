"""Domain checks that keep synthetic sequences internally consistent."""

from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.models import Match


def team(team_id: str) -> dict:
    roles = ["goalkeeper"] + ["defender"] * 4 + ["midfielder"] * 3 + ["forward"] * 3
    return {
        "id": team_id,
        "name": f"{team_id.title()} FC",
        "players": [
            {"id": f"{team_id}-{number:02}", "name": f"Player {number}", "role": role}
            for number, role in enumerate(roles)
        ],
    }


def event(event_id: str, event_type: str, second: int, **fields: object) -> dict:
    return {
        "id": event_id,
        "match_id": "demo-match",
        "period": 1,
        "second": second,
        "type": event_type,
        "team_id": "home",
        "player_id": "home-06",
        "possession_id": "home-02",
        "possession_team_id": "home",
        "location": {"x": 68, "y": 30},
        **fields,
    }


def sample_match() -> dict:
    pressure = event(
        "e-01", "pressure", 1389,
        possession_id="away-01",
        possession_team_id="away",
        target_player_id="away-04",
    )
    recovery = event("e-02", "recovery", 1391, method="interception")
    completed_pass = event(
        "e-03", "pass", 1394,
        end_location={"x": 78, "y": 32},
        receiver_id="home-08",
        outcome="complete",
    )
    carry = event(
        "e-04", "carry", 1398,
        player_id="home-08",
        location={"x": 78, "y": 32},
        end_location={"x": 84, "y": 38},
    )
    shot = event(
        "e-05", "shot", 1402,
        player_id="home-08",
        location={"x": 84, "y": 38},
        outcome="saved",
    )
    return {
        "id": "demo-match",
        "home_team": team("home"),
        "away_team": team("away"),
        "events": [pressure, recovery, completed_pass, carry, shot],
    }


def test_example_possession_is_valid() -> None:
    match = Match.model_validate(sample_match())

    assert len(match.events) == 5
    assert match.events[1].possession_id == match.events[-1].possession_id
    assert match.events[0].possession_id != match.events[1].possession_id


@pytest.mark.parametrize(
    ("event_index", "changes"),
    [
        (2, {"end_location": {"x": 101, "y": 32}}),
        (2, {"receiver_id": "away-08"}),
        (2, {"receiver_id": None}),
        (0, {"target_player_id": "home-04"}),
        (0, {"possession_team_id": "home"}),
        (4, {"second": 2700}),
        (4, {"period": 2, "second": 5400}),
    ],
)
def test_invalid_event_or_relationship_is_rejected(event_index: int, changes: dict) -> None:
    payload = sample_match()
    payload["events"][event_index].update(changes)

    with pytest.raises(ValidationError):
        Match.model_validate(payload)


def test_events_must_be_chronological() -> None:
    payload = sample_match()
    payload["events"][2], payload["events"][3] = payload["events"][3], payload["events"][2]

    with pytest.raises(ValidationError, match="ordered by second"):
        Match.model_validate(payload)


def test_possession_cannot_change_owner() -> None:
    payload = sample_match()
    payload["events"][1]["possession_id"] = "away-01"

    with pytest.raises(ValidationError):
        Match.model_validate(payload)


def test_possession_cannot_resume_after_another_possession() -> None:
    payload = sample_match()
    payload["events"][4]["possession_id"] = "away-01"
    payload["events"][4]["possession_team_id"] = "away"
    payload["events"][4]["team_id"] = "away"
    payload["events"][4]["player_id"] = "away-08"

    with pytest.raises(ValidationError, match="cannot resume"):
        Match.model_validate(payload)


def test_roster_ids_must_be_unique_across_teams() -> None:
    payload = sample_match()
    payload["away_team"]["players"][1]["id"] = "home-01"

    with pytest.raises(ValidationError, match="unique across both teams"):
        Match.model_validate(payload)


def test_input_does_not_change_during_validation() -> None:
    payload = sample_match()
    original = deepcopy(payload)

    Match.model_validate(payload)

    assert payload == original
