"""Research imports must preserve uncertainty and provider clock semantics."""

import math

import pytest
from pydantic import ValidationError

from app.reference.observations import synthetic_observations
from app.reference.download import extract_england
from app.reference.report import build_report, split_matches, summarize
from app.reference.wyscout import read_observations
from app.services.varied_generator import generate_varied_match
from app.analytics.statistics import calculate_statistics


def record(**changes):
    return {**dict(id=1, matchId=10, teamId=20, playerId=0, eventId=8, subEventId=85,
                matchPeriod="1H", eventSec=2.75, positions=[dict(x=75, y=40)],
                tags=[dict(id=1801)]), **changes}


def read(*records):
    return read_observations(list(records), {"10": {"20", "30"}})


def test_real_clocks_keep_added_time_and_second_half_independent():
    first, second = read(record(eventSec=2800.5), record(id=2, matchPeriod="2H", eventSec=1.25))
    assert (first.period, first.period_second) == (1, 2800.5)
    assert (second.period, second.period_second) == (2, 1.25)
    full = summarize([first, second], ["10"], regulation_only=False)
    cut = summarize([first, second], ["10"], regulation_only=True)
    field = "passes_including_pass_restarts"
    assert full["per_match"][field]["median"] == 2
    assert cut["per_match"][field]["median"] == 1


def test_unknown_actor_accuracy_and_receiver_are_not_invented():
    event = read(record(eventId=3, subEventId=34, tags=[]))[0]
    assert event.player_id is None and event.pass_complete is None
    assert event.receiver_id is None and event.end_attacking_x is None
    assert event.kind == "pass" and event.restart
    report = summarize([event], ["10"], regulation_only=True)
    assert report["per_match"]["passes_with_unknown_outcome"]["median"] == 1
    assert report["per_match"]["accuracy_among_known_pass_outcomes_pct"]["count"] == 0
    assert report["possession_seconds"] is None


@pytest.mark.parametrize("subtype", [30, 31, 32, 34, 36])
def test_passing_restarts_count_as_passes(subtype):
    assert read(record(eventId=3, subEventId=subtype))[0].kind == "pass"


@pytest.mark.parametrize("subtype", [33, 35])
def test_penalties_and_free_kick_shots_are_shots(subtype):
    event = read(record(eventId=3, subEventId=subtype))[0]
    assert event.kind == "shot" and event.pass_complete is None


def test_duels_are_not_automatically_recoveries():
    event = read(record(eventId=1, subEventId=12, tags=[dict(id=703)]))[0]
    assert event.kind == "other" and event.tags == (703,)


@pytest.mark.parametrize("changes", [dict(eventSec=math.nan), dict(eventSec=-1),
                                         dict(positions=[dict(x=101, y=20)]), dict(matchPeriod="E1")])
def test_invalid_or_unsupported_data_fails_explicitly(changes):
    with pytest.raises(ValidationError):
        read(record(**changes))


def test_duplicate_unknown_team_and_conflicting_outcomes_fail():
    for records in [(record(), record()), (record(teamId=99),),
                    (record(tags=[dict(id=1801), dict(id=1802)]),)]:
        with pytest.raises(ValueError):
            read(*records)


def test_sorting_keeps_equal_time_source_order_and_offside_empty_subtype():
    events = read(record(id=3, eventSec=10), record(id=2, eventSec=5, eventId=6, subEventId=""),
                  record(id=1, eventSec=5))
    assert [event.id for event in events] == ["2", "1", "3"]


def test_zero_matches_and_shot_grid_boundaries_count_correctly():
    event = read(record(eventId=10, positions=[dict(x=100, y=100)]))[0]
    result = summarize([event], ["10", "11"], regulation_only=True)
    assert result["per_match"]["shots_including_shot_restarts"]["median"] == .5
    assert result["shot_grid_6_by_4_counts"] == {"5:3": 1}


def test_split_is_disjoint_complete_and_independent_of_input_order():
    ids = list(map(str, range(380)))
    tuning, holdout = split_matches(ids)
    assert (tuning, holdout) == split_matches(ids[::-1])
    assert len(tuning) == 300 and len(holdout) == 80
    assert not set(tuning) & set(holdout)
    assert set(tuning + holdout) == set(ids)
    with pytest.raises(ValueError):
        split_matches(ids[:-1] + [ids[0]])


def test_common_observations_match_existing_synthetic_statistics():
    match = generate_varied_match(7)
    observations = synthetic_observations(match)
    summary = summarize(observations, [match.id], regulation_only=True)
    stats = calculate_statistics(match, 5400).model_dump()
    # Check actual analytics contract rather than hard-coded generator counts.
    assert summary["per_match"]["passes_including_pass_restarts"]["median"] == (
        stats["home"]["passes_attempted"] + stats["away"]["passes_attempted"])
    assert summary["per_match"]["shots_including_shot_restarts"]["median"] == (
        stats["home"]["shots"] + stats["away"]["shots"])
    assert stats["match_id"] == match.id
    away_first = next(e for e in match.events if e.team_id == match.away_team.id and e.period == 1)
    normalized = next(e for e in observations if e.id == away_first.id)
    assert normalized.attacking_x == 100 - away_first.location.x
    assert normalized.attacking_y == 100 - away_first.location.y
    assert all(e.restart is not None for e in observations if e.kind == "pass")
    legacy = synthetic_observations(generate_varied_match(7, version="varied-v1"))
    assert all(e.restart is None for e in legacy)


def test_corrupt_download_fails_before_extracting():
    with pytest.raises(ValueError, match="checksum mismatch"):
        extract_england(b"not the pinned archive", "events")


def test_known_outcomes_use_explicit_denominator_and_raw_endpoints_survive():
    events = read(record(tags=[]), record(id=2, tags=[dict(id=1801)],
                  positions=[dict(x=30, y=40), dict(x=60, y=50)]),
                  record(id=3, tags=[dict(id=1802)]))
    summary = summarize(events, ["10"], regulation_only=True)
    assert summary["per_match"]["accuracy_among_known_pass_outcomes_pct"]["median"] == 50
    assert events[1].end_attacking_x == 60
    assert events[1].receiver_id is None


def season_fixture():
    matches, events = [], []
    for home in range(1, 21):
        for away in range(1, 21):
            if home == away:
                continue
            key = 1000 + len(matches)
            matches.append(dict(wyId=key, competitionId=364, seasonId=181150, status="Played",
                                teamsData={str(home): {"side": "home"}, str(away): {"side": "away"}}))
            events.append(record(id=key, matchId=key, teamId=home))
    return matches, events


def test_report_excludes_held_out_outcomes_from_distribution():
    matches, events = season_fixture()
    _, held_out = split_matches([str(match["wyId"]) for match in matches])
    # Artificially put every shot into held-out games. None should reach tuning metrics.
    for event in events:
        if str(event["matchId"]) in held_out:
            event.update(eventId=10, subEventId=100)
    report = build_report(events, matches, synthetic_count=1)
    assert report["split"]["held_out_metrics_computed"] is False
    assert report["reference_tuning_full_clock"]["per_match"]["shots_including_shot_restarts"]["max"] == 0
    assert report["reference_tuning_full_clock"]["match_count"] == 300


def test_incomplete_season_event_coverage_fails_before_comparing():
    matches, events = season_fixture()
    with pytest.raises(ValueError, match="missing event coverage"):
        build_report(events[:-1], matches, synthetic_count=1)
