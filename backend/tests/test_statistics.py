"""Hand-counted boundaries, missing information and football counterexamples."""

import pytest
from fastapi.testclient import TestClient

from app.analytics.statistics import calculate_statistics
from app.main import app
from app.models.match import Match
from app.services.match_repository import load_scenario
from app.services.synthetic_common import make_team


def fixture() -> Match:
    events = []
    for second, outcome in [(10, 'complete'), (20, 'incomplete'), (30, 'complete')]:
        events.append(dict(
            id=f'pass-{second}', match_id='hand-counted', type='pass', period=1, second=second,
            team_id='red', player_id='red-06', possession_id='red-p1', possession_team_id='red',
            location={'x': 40, 'y': 50}, end_location={'x': 20, 'y': 50},
            outcome=outcome, receiver_id='red-07' if outcome == 'complete' else None,
        ))
    for second, outcome in [(100, 'blocked'), (120, 'saved'), (150, 'off_target'), (2700, 'goal')]:
        events.append(dict(
            id=f'shot-{second}', match_id='hand-counted', type='shot',
            period=1 if second < 2700 else 2, second=second,
            team_id='blue', player_id='blue-09', possession_id='blue-p2', possession_team_id='blue',
            location={'x': 10, 'y': 50}, outcome=outcome,
        ))
    return Match.model_validate(dict(
        id='hand-counted', home_team=make_team('red', 'Red'), away_team=make_team('blue', 'Blue'),
        events=events,
        ball_states=[
            dict(start_second=0, end_second=60, state='controlled', team_id='red'),
            dict(start_second=60, end_second=90, state='contested'),
            dict(start_second=90, end_second=3000, state='controlled', team_id='blue'),
            dict(start_second=3000, end_second=5400, state='out_of_play'),
        ],
    ))


def test_partial_control_intervals_and_exact_event_boundaries():
    match = fixture()
    before = calculate_statistics(match, 19)
    assert (before.home.passes_attempted, before.home.passes_completed) == (1, 1)
    assert before.possession.home_seconds == 19
    at = calculate_statistics(match, 20)
    assert (at.home.passes_attempted, at.home.passes_completed, at.home.pass_accuracy_percent) == (2, 1, 50)
    later = calculate_statistics(match, 120)
    assert later.home.pass_accuracy_percent == pytest.approx(200 / 3)
    assert (later.possession.home_seconds, later.possession.away_seconds, later.possession.contested_seconds) == (60, 30, 30)
    assert later.possession.home_share_percent == pytest.approx(200 / 3)
    assert (later.away.shots, later.away.shots_blocked, later.away.shots_saved) == (2, 1, 1)


def test_zero_and_unknown_are_distinct():
    match = fixture()
    start = calculate_statistics(match, 0)
    assert start.home.passes_attempted == 0
    assert start.home.pass_accuracy_percent is None
    assert start.possession.home_seconds == 0
    assert start.possession.home_share_percent is None
    # A valid event-only feed can count passes, but cannot supply possession time.
    event_only = Match.model_validate({**match.model_dump(), 'ball_states': []})
    assert calculate_statistics(event_only, 20).possession is None
    assert calculate_statistics(event_only, 20).home.pass_accuracy_percent == 50


def test_halftime_goal_and_final_shot_partition():
    match = fixture()
    assert calculate_statistics(match, 2699).away.goals == 0
    assert calculate_statistics(match, 2700).away.goals == 1
    final = calculate_statistics(match, 5400)
    assert final.away.shots == 4
    assert final.away.goals == final.away.shots_saved == final.away.shots_off_target == final.away.shots_blocked == 1
    p = final.possession
    assert p.home_seconds + p.away_seconds + p.contested_seconds + p.out_of_play_seconds == 5400


def test_future_changes_and_rewinding_cannot_change_past_statistics():
    match = fixture()
    expected = calculate_statistics(match, 120)
    payload = match.model_dump()
    payload['events'][-1]['outcome'] = 'off_target'
    payload['ball_states'][-1] = dict(start_second=3000, end_second=5400, state='controlled', team_id='red')
    changed_future = Match.model_validate(payload)
    calculate_statistics(changed_future, 5400)
    assert calculate_statistics(changed_future, 120) == expected


def test_possession_and_accuracy_do_not_imply_attacking_success():
    match = load_scenario('original')
    result = calculate_statistics(match, 5400)
    assert result.possession.home_share_percent > result.possession.away_share_percent
    assert result.home.passes_attempted > result.away.passes_attempted
    assert result.home.shots < result.away.shots
    assert result.home.goals < result.away.goals
    # Two completed backward passes still count as completed, without a danger score.
    simple = calculate_statistics(fixture(), 30)
    assert simple.home.passes_completed == 2
    assert simple.home.shots == 0


@pytest.mark.parametrize('second', [-1, 5401])
def test_invalid_cutoffs(second):
    with pytest.raises(ValueError):
        calculate_statistics(fixture(), second)


@pytest.mark.parametrize('scenario', ['original', 'stable', 'higher_recoveries', 'recoveries_without_shots'])
def test_api_returns_statistics_and_recoveries_at_one_cutoff(scenario):
    response = TestClient(app).get('/api/matches/demo/analysis', params={'scenario': scenario, 'second': 1200})
    assert response.status_code == 200
    result = response.json()
    assert result['source'] == 'synthetic'
    assert result['as_of_second'] == result['statistics']['as_of_second'] == result['recoveries']['as_of_second'] == 1200
    assert result['match_id'] == result['statistics']['match_id'] == result['recoveries']['match_id']
    for side in ['home', 'away']:
        team = result['statistics'][side]
        assert team['shots'] == sum(team[key] for key in ['goals', 'shots_saved', 'shots_off_target', 'shots_blocked'])


@pytest.mark.parametrize('query', ['second=-1', 'second=5401', 'second=1.5', 'second=10&scenario=unknown', ''])
def test_api_rejects_invalid_query(query):
    assert TestClient(app).get(f'/api/matches/demo/analysis?{query}').status_code == 422
