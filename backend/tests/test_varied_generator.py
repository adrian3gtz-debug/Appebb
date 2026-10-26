"""Structural invariants, diverse outcomes and diagnostics without generator labels."""

from collections import Counter
import json
import subprocess
import sys

from fastapi.testclient import TestClient
import pytest

from app.analytics.recoveries import analyze_recoveries
from app.analytics.statistics import calculate_statistics
from app.main import app
from app.models import Match, PassEvent, PressureEvent, ShotEvent
from app.services.synthetic_audit import audit_match
from app.services.varied_generator import generate_varied_match


def test_reproducibility_and_seed_affects_more_than_coordinates():
    assert generate_varied_match(7) == generate_varied_match(7)
    matches = [generate_varied_match(seed) for seed in [0, 7, 19, 99]]
    assert len({tuple((e.type, e.second) for e in match.events) for match in matches}) > 1
    assert len({tuple(calculate_statistics(match, 5400).model_dump()[side]['goals']
                      for side in ['home', 'away']) for match in matches}) > 1


@pytest.mark.parametrize('seed', range(20))
def test_clock_continuity_restart_physics_and_variation(seed):
    match = generate_varied_match(seed)
    assert Match.model_validate_json(match.model_dump_json()) == match
    report = audit_match(match)
    assert report['structural_issues'] == []
    assert report['calibrated_to_real_data'] is False
    assert report['controlled_spell_seconds']['min'] < report['controlled_spell_seconds']['max']
    assert report['passes_per_recorded_possession']['min'] < report['passes_per_recorded_possession']['max']
    assert report['pass_directions']['forward'] > 0
    assert report['pass_directions']['backward'] > 0
    # No block schedule: possession lengths must have several distinct observed values.
    durations = {s.end_second - s.start_second for s in match.ball_states if s.state == 'controlled'}
    assert len(durations) > 10
    assert sum(s.end_second - s.start_second for s in match.ball_states) == 5400
    assert {'controlled', 'contested', 'out_of_play'} <= {s.state for s in match.ball_states}
    actions = [e for e in match.events if not isinstance(e, PressureEvent)]
    for kickoff_second, owner in [(0, 'home'), (2700, 'away')]:
        kickoff = next(e for e in actions if e.second == kickoff_second)
        assert isinstance(kickoff, PassEvent)
        assert kickoff.team_id == owner
        assert (kickoff.location.x, kickoff.location.y) == (50, 50)
    for shot in (e for e in actions if isinstance(e, ShotEvent)):
        progress = shot.location.x if (shot.team_id == 'home') == (shot.period == 1) else 100 - shot.location.x
        assert progress >= 68
    stats = report['statistics']
    for side in ['home', 'away']:
        assert stats[side]['goals'] == sum(isinstance(e, ShotEvent) and e.outcome == 'goal'
                                         and e.team_id == stats[side]['team_id'] for e in actions)


def test_patterns_and_outcomes_appear_across_seeds_without_forced_winner():
    outcomes = Counter()
    winners = set()
    for seed in range(12):
        match = generate_varied_match(seed)
        stats = calculate_statistics(match, 5400)
        winners.add('home' if stats.home.goals > stats.away.goals else
                    'away' if stats.away.goals > stats.home.goals else 'draw')
        outcomes.update(e.outcome for e in match.events if isinstance(e, ShotEvent))
    assert {'goal', 'saved', 'blocked', 'off_target'} <= outcomes.keys()
    assert winners == {'home', 'away', 'draw'}


def test_analysis_uses_events_not_generator_identity_or_future():
    match = generate_varied_match(7)
    payload = match.model_dump()
    payload['id'] = 'anonymous'
    for event in payload['events']:
        event['match_id'] = 'anonymous'
        if event['second'] > 1200 and event['type'] == 'shot':
            event['outcome'] = 'goal'
    anonymous = Match.model_validate(payload)
    before = calculate_statistics(match, 1200)
    after = calculate_statistics(anonymous, 1200)
    assert before.home == after.home and before.away == after.away
    observed = analyze_recoveries(anonymous, 1200)
    assert all(s.start_second <= 1200 for s in observed.sequences)
    assert all(anonymous.events[int(event_id.split('-')[1]) - 1].second <= 1200
               for s in observed.sequences for event_id in s.event_ids)


def test_audit_detects_injected_spatial_and_speed_error():
    payload = generate_varied_match(7).model_dump()
    event = next(e for e in payload['events'] if e['type'] == 'carry')
    event['end_location'] = {'x': 0.0 if event['location']['x'] > 50 else 100.0, 'y': 0.0}
    damaged = Match.model_validate(payload)
    problems = audit_match(damaged)['structural_issues']
    assert any(p['event_id'] == event['id'] and p['reason'] == 'movement_exceeds_assumed_speed_bound' for p in problems)
    assert any(p['reason'] in ('ball_endpoint_discontinuity', 'recovery_not_at_previous_endpoint') for p in problems)


def test_audit_reports_missing_timing_and_bad_goal_restart():
    match = generate_varied_match(7)
    without_time = Match.model_validate({**match.model_dump(), 'ball_states': []})
    assert any(p['reason'] == 'missing_control_timeline' for p in audit_match(without_time)['structural_issues'])
    payload = match.model_dump()
    index = next(i for i, e in enumerate(payload['events']) if e['type'] == 'shot' and e['outcome'] == 'goal')
    next_action = next(e for e in payload['events'][index + 1:] if e['type'] != 'pressure')
    next_action['location']['x'] = 49.0
    damaged = Match.model_validate(payload)
    assert any(p['reason'] == 'invalid_restart_after_goal' for p in audit_match(damaged)['structural_issues'])


def test_varied_api_has_one_reproducible_match_and_cutoff():
    client = TestClient(app)
    response = client.get('/api/matches/demo?scenario=varied')
    assert response.status_code == 200
    match = Match.model_validate(response.json()['match'])
    assert match == generate_varied_match(7)
    result = client.get('/api/matches/demo/analysis?scenario=varied&second=1200').json()
    assert result['source'] == 'synthetic'
    assert result['statistics'] == calculate_statistics(match, 1200).model_dump()
    assert result['recoveries']['as_of_second'] == 1200


def test_cli_generates_varied_fixture_and_reports_diagnostics_without_overwriting(tmp_path):
    output = tmp_path / 'varied.json'
    command = [sys.executable, '-m', 'app.services.generate_match', '--mode', 'varied',
               '--seed', '7', '--audit', '--output', str(output)]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    assert Match.model_validate_json(output.read_bytes()) == generate_varied_match(7)
    summary = json.loads(result.stdout)
    assert summary['generation'] == {'version': 'varied-v1', 'seed': 7, 'calibrated': False}
    assert summary['diagnostics']['structural_issues'] == []
    original = output.read_bytes()
    assert subprocess.run(command, capture_output=True).returncode != 0
    assert output.read_bytes() == original
