"""Behavior, counterexamples and time boundaries for recovery evidence."""

import pytest
from fastapi.testclient import TestClient

from app.analytics.recoveries import analyze_recoveries, attacking_x
from app.main import app
from app.models import Match
from app.services.recovery_scenarios import generate_recovery_scenario
from app.services.synthetic_common import make_team


def small_match(events: list[dict]) -> Match:
    """Event-only logs allow adversarial boundary tests without a scenario label."""
    return Match.model_validate({
        'id': 'test', 'home_team': make_team('red', 'Red').model_dump(),
        'away_team': make_team('blue', 'Blue').model_dump(), 'events': events,
    })


def event(kind: str, second: int, *, possession: str = 'p1', x: float = 75,
          team: str = 'red', **details) -> dict:
    return {
        'id': f'{kind}-{second}-{possession}', 'match_id': 'test', 'type': kind,
        'period': 1 if second < 2700 else 2, 'second': second,
        'team_id': team, 'player_id': f'{team}-06', 'possession_id': possession,
        'possession_team_id': team, 'location': {'x': x, 'y': 50}, **details,
    }


def recovery(second: int, **details) -> dict:
    return event('recovery', second, method='interception', **details)


@pytest.mark.parametrize('seed', [0, 7, 19])
def test_contrasting_scenarios_are_discovered_from_events(seed):
    fixtures = [generate_recovery_scenario(scenario, seed) for scenario in
                ['stable', 'higher_recoveries', 'recoveries_without_shots']]
    assert len({match.id for match in fixtures}) == 3
    assert all(label not in match.model_dump_json() for match in fixtures
               for label in ["higher_recoveries", "recoveries_without_shots", "stable"])
    assert all(Match.model_validate_json(match.model_dump_json()) == match for match in fixtures)
    stable, increase, no_shots = [analyze_recoveries(match, 1200) for match in fixtures]
    assert stable.insights == []
    for result, shots in [(increase, 3), (no_shots, 0)]:
        assert len(result.insights) == 1
        insight = result.insights[0]
        assert (insight.previous.high_recoveries, insight.current.high_recoveries) == (1, 6)
        assert insight.current.shot_sequences == shots
        assert len(insight.recovery_event_ids) == 6
        fixture = fixtures[1] if shots else fixtures[2]
        recorded_ids = {e.id for e in fixture.events}
        assert set(insight.recovery_event_ids) <= recorded_ids


def test_script_is_reproducible_and_new_seed_changes_locations():
    assert generate_recovery_scenario('stable', 7) == generate_recovery_scenario('stable', 7)
    assert generate_recovery_scenario('stable', 7) != generate_recovery_scenario('stable', 19)


def test_future_shot_and_comparison_are_hidden():
    match = generate_recovery_scenario('higher_recoveries')
    shot = next(e for e in match.events if e.type == 'shot' and 600 < e.second < 1200)
    before = analyze_recoveries(match, shot.second - 1)
    sequence = next(s for s in before.sequences if s.possession_id == shot.possession_id)
    assert sequence.status == 'in_progress'
    assert sequence.shot_event_id is None
    assert shot.id not in sequence.event_ids
    after = analyze_recoveries(match, shot.second)
    sequence = next(s for s in after.sequences if s.possession_id == shot.possession_id)
    assert sequence.status == 'shot'
    assert sequence.seconds_to_shot == 15
    assert analyze_recoveries(match, 1199).insights == []
    assert len(analyze_recoveries(match, 1200).insights) == 1
    assert analyze_recoveries(match, 0).sequences == []


def test_history_is_unchanged_by_future_outcomes():
    match = generate_recovery_scenario('higher_recoveries')
    payload = match.model_dump()
    for item in payload['events']:
        if item['second'] > 1200 and item['type'] == 'shot':
            item['outcome'] = 'goal'
    assert analyze_recoveries(match, 1200) == analyze_recoveries(Match.model_validate(payload), 1200)


def test_directions_for_both_teams_and_halves_use_roster_ids():
    match = small_match([
        recovery(10, x=70, possession='p1'), recovery(20, x=30, possession='p2', team='blue'),
        recovery(2710, x=30, possession='p3'), recovery(2720, x=70, possession='p4', team='blue'),
    ])
    assert [attacking_x(match, e) for e in match.events] == [70, 70, 70, 70]
    assert len(analyze_recoveries(match, 5400).sequences) == 4
    assert all(s.period == 2 for s in analyze_recoveries(generate_recovery_scenario('higher_recoveries'), 3900).sequences if s.start_second >= 2700)


def test_last_third_boundary_is_inclusive_and_deep_recovery_is_excluded():
    match = small_match([recovery(1, x=200/3, possession='a'), recovery(2, x=66.6, possession='b')])
    assert len(analyze_recoveries(match, 3).sequences) == 1


def test_incomplete_pass_ends_chain_before_later_shot():
    match = small_match([
        recovery(10), event('pass', 15, end_location={'x': 80, 'y': 50}, outcome='incomplete'),
        event('shot', 20, outcome='goal'),
    ])
    sequence = analyze_recoveries(match, 30).sequences[0]
    assert sequence.status == 'lost'
    assert len(sequence.event_ids) == 2
    assert sequence.shot_event_id is None


def test_other_possession_and_half_end_stop_chain():
    match = small_match([recovery(2695), event('shot', 2705, outcome='goal')])
    assert analyze_recoveries(match, 2710).sequences[0].status == 'period_end'
    match = small_match([recovery(10), event('shot', 15, possession='other', outcome='goal')])
    assert analyze_recoveries(match, 20).sequences[0].status == 'lost'


def test_first_shot_only_counts_once():
    match = small_match([recovery(10), event('shot', 15, outcome='blocked'), event('shot', 17, outcome='goal')])
    sequence = analyze_recoveries(match, 20).sequences[0]
    assert sequence.shot_event_id == match.events[1].id
    assert len(sequence.event_ids) == 2


def test_interval_counts_freeze_and_exact_boundary_belongs_to_next_window():
    match = small_match([
        recovery(599), event('shot', 600, outcome='off_target'), recovery(601, possession='p2'),
    ])
    result = analyze_recoveries(match, 1200)
    previous, current = result.comparisons[0].previous, result.comparisons[0].current
    assert (previous.high_recoveries, previous.shot_sequences, previous.pending_sequences) == (1, 0, 1)
    assert (current.high_recoveries, current.shot_sequences) == (1, 0)
    assert result.sequences[0].status == 'shot'
    assert result.comparisons == analyze_recoveries(match, 1299).comparisons


def test_dead_ball_ends_a_chain_even_without_a_later_event():
    match = small_match([recovery(10)])
    payload = match.model_dump()
    payload['ball_states'] = [
        {'start_second': 0, 'end_second': 20, 'state': 'controlled', 'team_id': 'red'},
        {'start_second': 20, 'end_second': 5400, 'state': 'out_of_play', 'team_id': None},
    ]
    match = Match.model_validate(payload)
    assert analyze_recoveries(match, 19).sequences[0].status == 'in_progress'
    assert analyze_recoveries(match, 20).sequences[0].status == 'out_of_play'


def test_no_halftime_comparison_and_no_small_sample_insight():
    match = generate_recovery_scenario('higher_recoveries')
    assert not [c for c in analyze_recoveries(match, 3899).comparisons if c.period == 2]
    result = analyze_recoveries(match, 3900)
    comparison = next(c for c in result.comparisons if c.period == 2)
    assert (comparison.previous.start_second, comparison.current.end_second) == (2700, 3900)
    sparse = small_match([recovery(610, possession='a'), recovery(650, possession='b'), recovery(690, possession='c')])
    assert analyze_recoveries(sparse, 1200).insights == []


@pytest.mark.parametrize('second', [-1, 5401])
def test_invalid_time_is_rejected(second):
    with pytest.raises(ValueError):
        analyze_recoveries(small_match([]), second)


def test_api_uses_same_analyzer_and_validates_query():
    client = TestClient(app)
    match = generate_recovery_scenario('higher_recoveries')
    response = client.get('/api/matches/demo/recoveries?second=1200&scenario=higher_recoveries')
    assert response.status_code == 200
    assert response.json() == analyze_recoveries(match, 1200).model_dump()
    assert client.get('/api/matches/demo?scenario=stable').json()['match']['id'] == generate_recovery_scenario('stable').id
    assert client.get('/api/matches/demo/recoveries?second=5401').status_code == 422
    assert client.get('/api/matches/demo?scenario=unknown').status_code == 422


@pytest.mark.parametrize('scenario', ['stable', 'higher_recoveries', 'recoveries_without_shots'])
def test_scenario_actions_keep_ball_and_receiver_continuity(scenario):
    from app.models import CarryEvent, PassEvent, RecoveryEvent
    from math import hypot

    match = generate_recovery_scenario(scenario)
    actions = [e for e in match.events if e.type != 'pressure']
    for previous, current in zip(actions, actions[1:]):
        if previous.possession_id == current.possession_id and isinstance(previous, RecoveryEvent):
            assert previous.location == current.location
            assert previous.player_id == current.player_id
        elif previous.possession_id == current.possession_id:
            assert isinstance(previous, (PassEvent, CarryEvent))
            assert previous.end_location == current.location
            assert current.player_id == (previous.receiver_id if isinstance(previous, PassEvent) else previous.player_id)
            distance = hypot((previous.end_location.x - previous.location.x) * 1.05,
                             (previous.end_location.y - previous.location.y) * 0.68)
            assert distance / (current.second - previous.second) < (9 if isinstance(previous, CarryEvent) else 35)
        elif isinstance(current, RecoveryEvent):
            assert isinstance(previous, PassEvent) and previous.outcome == 'incomplete'
            assert previous.end_location == current.location
            assert previous.team_id != current.team_id
        else:
            assert any(interval.state == 'out_of_play' and previous.second < interval.start_second
                       and interval.end_second <= current.second for interval in match.ball_states)
    assert all(match.events[i].second <= match.events[i+1].second for i in range(len(match.events)-1))
    assert sum(interval.end_second - interval.start_second for interval in match.ball_states) == 5400


def test_simultaneous_actions_keep_list_order_before_next_possession():
    match = small_match([recovery(10), event('shot', 10, outcome='saved'), recovery(10, possession='p2')])
    sequences = analyze_recoveries(match, 10).sequences
    assert sequences[0].status == 'shot'
    assert sequences[0].seconds_to_shot == 0
    assert sequences[1].status == 'in_progress'


def test_changing_match_identity_does_not_change_the_analysis():
    match = generate_recovery_scenario('higher_recoveries')
    payload = match.model_dump()
    payload['id'] = 'arbitrary-anonymous-match'
    for item in payload['events']:
        item['match_id'] = payload['id']
    original = analyze_recoveries(match, 1200)
    anonymous = analyze_recoveries(Match.model_validate(payload), 1200)
    assert original.comparisons == anonymous.comparisons
    assert original.sequences == anonymous.sequences
    assert original.insights[0].current == anonymous.insights[0].current
