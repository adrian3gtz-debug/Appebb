"""Summaries must remain traceable, time-bounded and descriptive."""

from fastapi.testclient import TestClient
import pytest

from app.analytics.recap import build_recap
from app.analytics.statistics import calculate_statistics
from app.main import app
from app.models import Match, ShotEvent
from app.services.match_repository import load_scenario


def recap_at(match, second):
    return build_recap(match, calculate_statistics(match, second))


def test_goal_timeline_changes_at_the_observed_timestamp_only():
    match = load_scenario("original")
    goals = [event for event in match.events if isinstance(event, ShotEvent) and event.outcome == "goal"]
    assert goals
    for index, goal in enumerate(goals):
        assert len(recap_at(match, goal.second - 1).goals) == index
        at = recap_at(match, goal.second)
        assert at.goals[-1].event_id == goal.id
        assert at.goals[-1].player_id == goal.player_id
        assert at.goals[-1].home_score + at.goals[-1].away_score == index + 1


@pytest.mark.parametrize("second", [0, 1200, 2700, 5399, 5400])
def test_final_status_requires_the_full_match_clock(second):
    match = load_scenario("varied")
    recap = recap_at(match, second)
    assert recap.phase == ("full_time" if second == 5400 else "in_progress")
    assert all(goal.second <= second for goal in recap.goals)


def test_future_shot_changes_and_full_time_query_do_not_leak_on_rewind():
    match = load_scenario("original")
    cutoff = 1200
    expected = recap_at(match, cutoff)
    payload = match.model_dump()
    for event in payload["events"]:
        if event["second"] > cutoff and event["type"] == "shot":
            event["outcome"] = "goal"
    changed = Match.model_validate(payload)
    recap_at(changed, 5400)
    assert recap_at(changed, cutoff) == expected


def test_control_shots_contrast_uses_explicit_time_and_strict_comparison():
    match = load_scenario("original")
    stats = calculate_statistics(match, 5400)
    contrast = build_recap(match, stats).control_shots_contrast
    assert contrast.team_id == match.home_team.id
    assert contrast.controlled_seconds > contrast.opponent_controlled_seconds
    assert contrast.shots < contrast.opponent_shots
    event_only = Match.model_validate({**match.model_dump(), "ball_states": []})
    assert recap_at(event_only, 5400).control_shots_contrast is None


def test_empty_feed_has_no_goal_or_control_story():
    match = load_scenario("varied")
    empty = Match.model_validate({**match.model_dump(), "events": [], "ball_states": []})
    recap = recap_at(empty, 0)
    assert recap.goals == [] and recap.control_shots_contrast is None
    assert recap.phase == "in_progress"


def test_mismatched_match_or_goal_counts_fail():
    match = load_scenario("varied")
    stats = calculate_statistics(match, 0)
    with pytest.raises(ValueError, match="same match"):
        build_recap(match, stats.model_copy(update={"match_id": "another-match"}))
    incorrect = stats.model_copy(update={"home": stats.home.model_copy(update={"goals": 99})})
    with pytest.raises(ValueError, match="observed goals"):
        build_recap(match, incorrect)


@pytest.mark.parametrize("scenario", ["original", "varied", "stable", "higher_recoveries", "recoveries_without_shots"])
def test_api_shares_one_cutoff_for_summary_statistics_and_recoveries(scenario):
    client = TestClient(app)
    for second in [1200, 5400, 0]:
        response = client.get("/api/matches/demo/analysis", params={"scenario": scenario, "second": second})
        assert response.status_code == 200
        data = response.json()
        assert all(data[key]["as_of_second"] == second for key in ("recap", "statistics", "recoveries"))
        assert data["recap"]["match_id"] == data["match_id"]
        assert data["recap"]["generation"] == "rules"
        stats, goals = data["statistics"], data["recap"]["goals"]
        assert len(goals) == stats["home"]["goals"] + stats["away"]["goals"]
