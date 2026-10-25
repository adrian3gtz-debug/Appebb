"""Aggregate only recorded events and control time available at the cutoff."""

from app.analytics.possession import calculate_possession
from app.models.events import PassEvent, ShotEvent
from app.models.match import Match
from app.models.statistics import MatchStatistics, TeamStatistics


def calculate_statistics(match: Match, second: int) -> MatchStatistics:
    if not 0 <= second <= 5400:
        raise ValueError("second must be between 0 and 5400")

    home = TeamStatistics(team_id=match.home_team.id)
    away = TeamStatistics(team_id=match.away_team.id)
    teams = {home.team_id: home, away.team_id: away}
    for event in match.events:
        if event.second > second:
            break
        team = teams[event.team_id]
        if isinstance(event, PassEvent):
            team.passes_attempted += 1
            team.passes_completed += int(event.outcome == "complete")
        elif isinstance(event, ShotEvent):
            team.shots += 1
            if event.outcome == "goal":
                team.goals += 1
            elif event.outcome == "saved":
                team.shots_saved += 1
            elif event.outcome == "off_target":
                team.shots_off_target += 1
            else:
                team.shots_blocked += 1

    for team in teams.values():
        if team.passes_attempted:
            team.pass_accuracy_percent = 100 * team.passes_completed / team.passes_attempted

    return MatchStatistics(
        match_id=match.id, as_of_second=second, home=home, away=away,
        possession=calculate_possession(match, second) if match.ball_states else None,
    )
