"""Three authored counterexamples for recovery analysis, without analyzer labels."""

from hashlib import sha256
from random import Random
from typing import Literal

from pydantic import TypeAdapter

from app.models import BallStateInterval, Coordinate, Match, MatchEvent
from app.services.synthetic_common import field_point, make_team

RecoveryScenario = Literal["stable", "higher_recoveries", "recoveries_without_shots"]


def generate_recovery_scenario(scenario: RecoveryScenario, seed: int = 7) -> Match:
    """Vary locations/timing within coherent possessions; never pass scenario to analytics."""
    if scenario not in ("stable", "higher_recoveries", "recoveries_without_shots"):
        raise ValueError("Unknown recovery scenario")
    rng = Random(seed)
    # Opaque, deterministic identity; no scenario label enters the match payload.
    identity = sha256(f"{scenario}:{seed}".encode()).hexdigest()[:12]
    match_id = f"synthetic-recoveries-{identity}"
    events: list[MatchEvent] = []
    states: list[BallStateInterval] = []
    adapter = TypeAdapter(MatchEvent)

    def emit(kind: str, second: int, owner: str, possession: str,
             player: int, point: Coordinate, **details: object) -> None:
        actor = details.pop("actor_team", owner)
        events.append(adapter.validate_python({
            "id": f"event-{len(events) + 1:04}", "match_id": match_id,
            "period": 1 if second < 2700 else 2, "second": second, "type": kind,
            "team_id": actor, "player_id": f"{actor}-{player:02}",
            "possession_id": possession, "possession_team_id": owner,
            "location": point, **details,
        }))

    def state(start: int, end: int, team: str | None = None) -> None:
        states.append(BallStateInterval(start_second=start, end_second=end,
                      state="controlled" if team else "out_of_play", team_id=team))

    restart = Coordinate(x=50, y=50)
    for cycle in range(90):
        start = cycle * 60
        period = 1 if start < 2700 else 2
        half_cycle = cycle if period == 1 else cycle - 45
        high = half_cycle % 10 == 5
        if scenario != "stable" and 10 <= half_cycle < 20:
            high = half_cycle % 10 in (1, 2, 3, 4, 5, 6)
        shot = high and cycle % 2 == 0 and scenario != "recoveries_without_shots"
        recovery_x = rng.uniform(70, 79) if high else rng.uniform(38, 48)
        recovery_at = field_point(recovery_x, rng.uniform(22, 78), "home", period)
        away_possession = f"possession-{cycle}-away-start"
        home_possession = f"possession-{cycle}-home"
        away_end_possession = f"possession-{cycle}-away-end"
        away_player = 6
        if cycle == 0:
            # Home kickoff, interrupted by an away interception.
            kickoff = "possession-kickoff"
            middle = field_point(43, 50, "home", period)
            lost = field_point(42, 45, "home", period)
            emit("pass", 0, "home", kickoff, 9, restart,
                 end_location=middle, receiver_id="home-06", outcome="complete")
            emit("pass", 4, "home", kickoff, 6, middle,
                 end_location=lost, outcome="incomplete")
            emit("recovery", 8, "away", away_possession, 6, lost, method="interception")
            state(0, 8, "home")
            restart = lost
            away_start = 8
        else:
            if cycle == 45:
                restart = Coordinate(x=50, y=50)
            middle = field_point(50, 50, "away", period)
            emit("pass", start, "away", away_possession, 9 if cycle == 45 else 4, restart,
                 end_location=middle, receiver_id="away-06", outcome="complete")
            restart = middle
            away_start = start
        emit("pressure", start + 11, "away", away_possession, 6, restart,
             actor_team="home", target_player_id="away-06")
        emit("pass", start + 12, "away", away_possession, away_player, restart,
             end_location=recovery_at, outcome="incomplete")
        emit("recovery", start + 15, "home", home_possession, 6, recovery_at,
             method="interception")
        state(away_start, start + 15, "away")
        destination = field_point(recovery_x + 5, recovery_at.y, "home", period)
        emit("pass", start + 20, "home", home_possession, 6, recovery_at,
             end_location=destination, receiver_id="home-09", outcome="complete")
        carried = field_point(recovery_x + 10, recovery_at.y, "home", period)
        emit("carry", start + 25, "home", home_possession, 9, destination,
             end_location=carried)
        if shot:
            emit("shot", start + 30, "home", home_possession, 9, carried, outcome="off_target")
            state(start + 15, start + 32, "home")
            state(start + 32, start + 40)
            away_start = start + 40
            restart = field_point(5, 50, "away", period)
            away_player = 1
        else:
            lost = field_point(recovery_x + 13, carried.y + rng.uniform(-3, 3), "home", period)
            emit("pass", start + 32, "home", home_possession, 9, carried,
                 end_location=lost, outcome="incomplete")
            emit("recovery", start + 35, "away", away_end_possession, 6, lost,
                 method="interception")
            state(start + 15, start + 35, "home")
            away_start = start + 35
            restart = lost
            away_player = 6
        destination = field_point(48, 50, "away", period)
        emit("pass", away_start + 3, "away", away_end_possession, away_player, restart,
             end_location=destination, receiver_id="away-08", outcome="complete")
        restart = field_point(50, 0, "away", period)
        emit("pass", start + 52, "away", away_end_possession, 8, destination,
             end_location=restart, outcome="incomplete")
        state(away_start, start + 54, "away")
        state(start + 54, start + 60)

    return Match(id=match_id, home_team=make_team("home", "Harbor FC (synthetic)"),
                 away_team=make_team("away", "Ridge United (synthetic)"),
                 events=events, ball_states=states)
