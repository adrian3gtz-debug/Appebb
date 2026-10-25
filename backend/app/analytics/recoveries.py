"""Observe recovery chains and compare closed windows, without scenario knowledge."""

from itertools import groupby

from app.models import Match, MatchEvent, PassEvent, RecoveryEvent, ShotEvent
from app.models.recoveries import (
    RecoveryAnalysis, RecoveryComparison, RecoveryInsight, RecoveryRules,
    RecoverySequence, RecoveryWindow,
)


def attacking_x(match: Match, event: MatchEvent) -> float:
    attacks_right = (event.team_id == match.home_team.id) == (event.period == 1)
    return event.location.x if attacks_right else 100 - event.location.x


def _control_end(match: Match, recovery: RecoveryEvent) -> tuple[int, str]:
    """Contested/dead-ball intervals terminate a chain even without another event."""
    half_end = 2700 if recovery.period == 1 else 5400
    for interval in match.ball_states:
        if interval.end_second <= recovery.second:
            continue
        if interval.start_second >= half_end:
            break
        if interval.state != "controlled" or interval.team_id != recovery.team_id:
            reason = "out_of_play" if interval.state == "out_of_play" else "lost"
            return min(interval.start_second, half_end), reason
    return half_end, "period_end"


def _sequences(match: Match, cutoff: int, rules: RecoveryRules) -> list[RecoverySequence]:
    visible = [event for event in match.events if event.second <= cutoff]
    result: list[RecoverySequence] = []
    possessions = [list(grouped) for _, grouped in groupby(visible, key=lambda event: event.possession_id)]
    for index, events in enumerate(possessions):
        recovery = events[0]
        if not isinstance(recovery, RecoveryEvent) or attacking_x(match, recovery) < rules.high_recovery_x:
            continue
        control_end, end_reason = _control_end(match, recovery)
        end = control_end
        # A new possession also terminates an event-only chain.
        next_event = possessions[index + 1][0] if index + 1 < len(possessions) else None
        if next_event is not None and next_event.second < end:
            end, end_reason = next_event.second, "lost"
        ids: list[str] = []
        status = "in_progress"
        ended: int | None = None
        shot: ShotEvent | None = None
        for event in events:
            # Group order disambiguates simultaneous actions before a new possession.
            if event.second >= control_end or event.period != recovery.period:
                break
            ids.append(event.id)
            if isinstance(event, ShotEvent):
                shot, status, ended = event, "shot", event.second
                break
            if isinstance(event, PassEvent) and event.outcome == "incomplete":
                status, ended = "lost", event.second
                break
        if status == "in_progress" and end <= cutoff:
            status, ended = end_reason, end
        result.append(RecoverySequence(
            recovery_event_id=recovery.id, team_id=recovery.team_id, period=recovery.period,
            start_second=recovery.second, possession_id=recovery.possession_id,
            event_ids=ids, status=status, end_second=ended,
            shot_event_id=shot.id if shot else None,
            seconds_to_shot=shot.second - recovery.second if shot else None,
        ))
    return result


def _window(match: Match, team_id: str, start: int, end: int,
            rules: RecoveryRules) -> tuple[RecoveryWindow, list[str]]:
    # Integer event times: end-1 enforces the half-open [start, end) window.
    sequences = [sequence for sequence in _sequences(match, end - 1, rules)
                 if sequence.team_id == team_id and start <= sequence.start_second < end]
    recoveries = [event for event in match.events if isinstance(event, RecoveryEvent)
                  and event.team_id == team_id and start <= event.second < end]
    return RecoveryWindow(
        start_second=start, end_second=end, total_recoveries=len(recoveries),
        high_recoveries=len(sequences),
        shot_sequences=sum(sequence.status == "shot" for sequence in sequences),
        pending_sequences=sum(sequence.status == "in_progress" for sequence in sequences),
    ), [sequence.recovery_event_id for sequence in sequences]


def analyze_recoveries(match: Match, as_of_second: int,
                       rules: RecoveryRules | None = None) -> RecoveryAnalysis:
    if not 0 <= as_of_second <= 5400:
        raise ValueError("analysis time must be between 0 and 5400")
    rules = rules or RecoveryRules()
    comparisons: list[RecoveryComparison] = []
    insights: list[RecoveryInsight] = []
    # Windows are anchored at each half's kickoff; never compare across halftime.
    for period, half_start in ((1, 0), (2, 2700)):
        half_end = half_start + 2700
        for end in range(half_start + 2 * rules.window_seconds,
                         min(half_end, as_of_second) + 1, rules.window_seconds):
            middle = end - rules.window_seconds
            start = middle - rules.window_seconds
            for team in (match.home_team, match.away_team):
                previous, _ = _window(match, team.id, start, middle, rules)
                current, ids = _window(match, team.id, middle, end, rules)
                comparison = RecoveryComparison(team_id=team.id, period=period,
                                                previous=previous, current=current)
                comparisons.append(comparison)
                before, after = previous.high_recoveries, current.high_recoveries
                if (after >= rules.minimum_current and after - before >= rules.minimum_increase
                        and (before == 0 or after >= before * rules.minimum_ratio)):
                    insights.append(RecoveryInsight(
                        **comparison.model_dump(),
                        id=f"{match.id}:{team.id}:high-recoveries:{end}",
                        detected_second=end, recovery_event_ids=ids,
                    ))
    return RecoveryAnalysis(
        match_id=match.id, as_of_second=as_of_second, rules=rules,
        sequences=_sequences(match, as_of_second, rules), comparisons=comparisons, insights=insights,
    )
