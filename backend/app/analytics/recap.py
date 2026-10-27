"""Summarize observed goals and a descriptive control/shot-volume contrast."""

from app.models.events import ShotEvent
from app.models.match import Match
from app.models.recap import ControlShotsContrast, GoalMoment, MatchRecap
from app.models.statistics import MatchStatistics


def build_recap(match: Match, statistics: MatchStatistics) -> MatchRecap:
    if (statistics.match_id != match.id or statistics.home.team_id != match.home_team.id
            or statistics.away.team_id != match.away_team.id):
        raise ValueError("summary statistics must belong to the same match and teams")
    cutoff = statistics.as_of_second
    home_score = away_score = 0
    goals = []
    for event in match.events:
        if event.second > cutoff:
            break
        if isinstance(event, ShotEvent) and event.outcome == "goal":
            home_score += int(event.team_id == match.home_team.id)
            away_score += int(event.team_id == match.away_team.id)
            goals.append(GoalMoment(
                event_id=event.id, team_id=event.team_id, player_id=event.player_id,
                second=event.second, home_score=home_score, away_score=away_score,
            ))
    if (home_score, away_score) != (statistics.home.goals, statistics.away.goals):
        raise ValueError("summary score disagrees with observed goals")

    contrast = None
    possession = statistics.possession
    if possession is not None:
        for team, opponent, seconds, opponent_seconds in (
            (statistics.home, statistics.away, possession.home_seconds, possession.away_seconds),
            (statistics.away, statistics.home, possession.away_seconds, possession.home_seconds),
        ):
            if seconds > opponent_seconds and team.shots < opponent.shots:
                contrast = ControlShotsContrast(
                    team_id=team.team_id, opponent_team_id=opponent.team_id,
                    controlled_seconds=seconds, opponent_controlled_seconds=opponent_seconds,
                    shots=team.shots, opponent_shots=opponent.shots,
                )
                break
    return MatchRecap(
        match_id=match.id, as_of_second=cutoff,
        phase="full_time" if cutoff == 5400 else "in_progress",
        goals=goals, control_shots_contrast=contrast,
    )
