"""Declared restart context must survive replay and preserve legacy uncertainty."""

from hashlib import sha256

from fastapi.testclient import TestClient
import pytest
from pydantic import ValidationError

from app.main import app
from app.models import Match, PassEvent, PressureEvent, ShotEvent
from app.reference.context_report import context_summary
from app.reference.observations import synthetic_observations
from app.reference.wyscout import read_observations
from app.services.synthetic_audit import audit_match
from app.services.varied_generator import generate_varied_match


def test_v1_reproduces_its_historical_seed_7_signature():
    # Recorded from the implementation in commit 5f919b1, excluding null fields.
    match = generate_varied_match(7, version="varied-v1")
    assert sha256(match.model_dump_json(exclude_none=True).encode()).hexdigest() == (
        "5b41f2b41f22c8d770bc9e584de3ac744a98c0fad0a3abacbf95d2dbdff519bc")
    assert all(event.pass_context is None for event in match.events if isinstance(event, PassEvent))


def test_v2_context_marks_only_first_pass_of_a_restart_possession():
    match = generate_varied_match(7)
    actions = [event for event in match.events if not isinstance(event, PressureEvent)]
    passes = [event for event in actions if isinstance(event, PassEvent)]
    assert {event.pass_context for event in passes} == {"open_play", "kickoff", "throw_in", "goal_kick"}
    for index, event in enumerate(actions):
        if not isinstance(event, PassEvent) or event.pass_context == "open_play":
            continue
        if index:
            previous = actions[index - 1]
            assert previous.possession_id != event.possession_id
            if event.pass_context == "goal_kick":
                assert isinstance(previous, ShotEvent) and previous.outcome == "off_target"
            if event.pass_context == "kickoff" and previous.period == event.period:
                assert isinstance(previous, ShotEvent) and previous.outcome == "goal"
        if event.pass_context == "kickoff":
            assert (event.location.x, event.location.y) == (50, 50)
        if event.pass_context == "throw_in":
            assert event.location.y in (0, 100)
    assert audit_match(match)["structural_issues"] == []


def test_context_validation_and_audit_reject_false_restart_declarations():
    payload = generate_varied_match(7).model_dump()
    event = next(e for e in payload["events"] if e["type"] == "pass" and e["pass_context"] == "open_play")
    event["pass_context"] = "not-a-restart"
    with pytest.raises(ValidationError):
        Match.model_validate(payload)
    event["pass_context"] = "kickoff"
    damaged = Match.model_validate(payload)
    assert any(issue["reason"] == "kickoff_not_at_centre" for issue in audit_match(damaged)["structural_issues"])


def test_context_report_does_not_misclassify_unmarked_wyscout_kickoff_as_open_play():
    raw = dict(id=1, matchId=10, teamId=20, playerId=1, eventId=8, subEventId=85,
               matchPeriod="1H", eventSec=0., positions=[dict(x=50, y=50)], tags=[dict(id=1801)])
    events = read_observations([raw], {"10": {"20", "30"}})
    assert events[0].restart is None and events[0].pass_context == "unmarked"
    summary = context_summary(events, ["10"])
    assert summary["pass_context_counts"] == {"unmarked": 1}


def test_record_adjacency_excludes_cross_half_and_opponent_pairs():
    from dataclasses import replace
    event = synthetic_observations(generate_varied_match(7))[0]
    event = replace(event, kind="pass", pass_context="open_play", pass_complete=True,
                    provider_type="pass", period=1, period_second=2699)
    second_half = replace(event, id="2", period=2, period_second=0)
    opposing = replace(second_half, id="3", period_second=2, team_id="other")
    summary = context_summary([event, second_half, opposing], [event.match_id])
    assert summary["per_match"]["adjacent_pass_pairs"]["median"] == 0
    assert summary["per_match"]["record_adjacent_pass_gap_median_seconds"]["count"] == 0


def test_api_insights_update_at_window_close_and_disappear_on_rewind():
    client = TestClient(app)
    def analysis(second):
        response = client.get("/api/matches/demo/analysis", params={"scenario": "higher_recoveries", "second": second})
        assert response.status_code == 200
        result = response.json()
        assert result["as_of_second"] == result["recoveries"]["as_of_second"] == second
        return result
    before = analysis(1199)
    closed = analysis(1200)
    assert not before["recoveries"]["insights"]
    assert closed["recoveries"]["insights"]
    assert analysis(1199) == before
    assert not analysis(0)["recoveries"]["insights"]


def test_v2_api_returns_restart_context_and_only_observed_evidence():
    client = TestClient(app)
    match = client.get("/api/matches/demo", params={"scenario": "varied"}).json()["match"]
    assert match["events"][0]["pass_context"] == "kickoff"
    for second in (0, 1200, 5400, 600):
        data = client.get("/api/matches/demo/analysis", params={"scenario": "varied", "second": second}).json()
        events = {event["id"]: event for event in match["events"]}
        assert all(events[event_id]["second"] <= second for sequence in data["recoveries"]["sequences"]
                   for event_id in sequence["event_ids"])


def test_cli_can_reproduce_legacy_version_explicitly(tmp_path):
    import json
    import subprocess
    import sys
    output = tmp_path / "legacy.json"
    result = subprocess.run([sys.executable, "-m", "app.services.generate_match", "--mode", "varied",
                             "--generator-version", "varied-v1", "--seed", "7", "--output", str(output)],
                            capture_output=True, text=True, check=True)
    assert json.loads(result.stdout)["generation"]["version"] == "varied-v1"
    assert Match.model_validate_json(output.read_bytes()) == generate_varied_match(7, version="varied-v1")
