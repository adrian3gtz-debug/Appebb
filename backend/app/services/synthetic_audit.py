"""Independent diagnostics from events/intervals; not a professional-realism score."""

from collections import Counter
from itertools import groupby
from math import hypot
from statistics import median

from app.analytics.statistics import calculate_statistics
from app.models import CarryEvent, Match, PassEvent, PressureEvent, RecoveryEvent, ShotEvent


def _distribution(values: list[float]) -> dict:
    return {"count": len(values), "min": min(values) if values else None,
            "median": median(values) if values else None, "max": max(values) if values else None}


def audit_match(match: Match) -> dict:
    """Audit observations only: no generator scenario, intent or expected scores are inputs."""
    actions = [event for event in match.events if not isinstance(event, PressureEvent)]
    problems: list[dict] = []
    if not match.ball_states:
        problems.append({"event_id": None, "reason": "missing_control_timeline"})

    def issue(event_id: str, reason: str) -> None:
        problems.append({"event_id": event_id, "reason": reason})

    for index, event in enumerate(actions):
        following = actions[index + 1] if index + 1 < len(actions) else None
        if isinstance(event, (PassEvent, CarryEvent)):
            end = following.second if following and following.period == event.period else event.period * 2700
            elapsed = end - event.second
            distance = hypot((event.end_location.x - event.location.x) * 1.05,
                             (event.end_location.y - event.location.y) * .68)
            if elapsed <= 0 or distance / elapsed > (9 if isinstance(event, CarryEvent) else 35):
                issue(event.id, "movement_exceeds_assumed_speed_bound")
            if following and following.possession_id == event.possession_id:
                if event.end_location != following.location:
                    issue(event.id, "ball_endpoint_discontinuity")
                expected_player = event.receiver_id if isinstance(event, PassEvent) else event.player_id
                if following.player_id != expected_player:
                    issue(event.id, "next_actor_disagrees_with_ball_holder")
                if isinstance(event, PassEvent) and event.outcome != "complete":
                    issue(event.id, "incomplete_pass_continues_possession")
        if not following or following.period != event.period:
            continue
        if following.possession_id != event.possession_id:
            dead = any(state.state == "out_of_play" and event.second < state.start_second
                       and state.end_second <= following.second for state in match.ball_states)
            if not isinstance(following, RecoveryEvent) and not dead:
                issue(following.id, "new_possession_without_recovery_or_restart")
            if isinstance(following, RecoveryEvent) and isinstance(event, (PassEvent, CarryEvent)):
                if event.end_location != following.location:
                    issue(following.id, "recovery_not_at_previous_endpoint")
            if isinstance(event, ShotEvent) and event.outcome == "goal":
                if (following.team_id == event.team_id or not dead
                        or (following.location.x, following.location.y) != (50, 50)):
                    issue(following.id, "invalid_restart_after_goal")
            if isinstance(event, ShotEvent) and event.outcome == "off_target":
                team = match.away_team if following.team_id == match.away_team.id else match.home_team
                keeper = next(player for player in team.players if player.role == 'goalkeeper')
                if following.team_id == event.team_id or following.player_id != keeper.id or not dead:
                    issue(following.id, "invalid_restart_after_off_target_shot")
            if isinstance(event, ShotEvent) and event.outcome == "saved":
                if (not isinstance(following, RecoveryEvent) or following.method != "goalkeeper_claim"
                        or following.team_id == event.team_id):
                    issue(following.id, "save_without_opposing_goalkeeper_control")

    durations = [state.end_second - state.start_second for state in match.ball_states if state.state == "controlled"]
    pass_counts = [sum(isinstance(event, PassEvent) for event in group)
                   for _, group in groupby(actions, key=lambda event: event.possession_id)]
    recovery_zones: Counter = Counter()
    shot_zones: Counter = Counter()
    shot_cells: Counter = Counter()
    turnover_zones: Counter = Counter()
    directions: Counter = Counter()
    for event in actions:
        sign = 1 if (event.team_id == match.home_team.id) == (event.period == 1) else -1
        x = event.location.x if sign == 1 else 100 - event.location.x
        zone = "own_third" if x < 100 / 3 else "middle_third" if x < 200 / 3 else "final_third"
        if isinstance(event, RecoveryEvent):
            recovery_zones[zone] += 1
        if isinstance(event, ShotEvent):
            shot_zones[zone] += 1
            shot_cells[f"x{int(x // 10)}:y{min(2, int(event.location.y // (100 / 3)))}"] += 1
        if isinstance(event, PassEvent) and event.outcome == "incomplete":
            end_x = event.end_location.x if sign == 1 else 100 - event.end_location.x
            turnover_zones["own_third" if end_x < 100 / 3 else "middle_third" if end_x < 200 / 3 else "final_third"] += 1
        if isinstance(event, PassEvent):
            dx = sign * (event.end_location.x - event.location.x) * 1.05
            dy = abs(event.end_location.y - event.location.y) * .68
            # Diagnostic sectors on the assumed pitch: +/-45 degrees around the goal axis.
            directions["forward" if dx > dy else "backward" if dx < -dy else "lateral"] += 1
    summary = calculate_statistics(match, 5400)
    return {
        "match_id": match.id, "calibrated_to_real_data": False,
        "assumed_pitch_metres": {"length": 105, "width": 68},
        "structural_issues": problems,
        "controlled_spell_seconds": _distribution(durations),
        "passes_per_recorded_possession": _distribution(pass_counts),
        "event_types": dict(Counter(event.type for event in match.events)),
        "recovery_zones": dict(recovery_zones), "shot_zones": dict(shot_zones),
        "shot_location_cells": dict(shot_cells), "incomplete_pass_end_zones": dict(turnover_zones),
        "pass_directions": dict(directions),
        "statistics": summary.model_dump(),
    }
