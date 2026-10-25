"""Calculate possession from control intervals, not pass counts."""

from __future__ import annotations

from app.models.match import Match
from app.models.possession import PossessionSummary


def calculate_possession(match: Match, second: int = 5400) -> PossessionSummary:
    """Share of controlled time; contested and out-of-play time stay separate."""

    if not 0 <= second <= 5400:
        raise ValueError("second must be between 0 and 5400")
    if not match.ball_states:
        raise ValueError("a complete ball-state timeline is required")

    home_seconds = 0
    away_seconds = 0
    contested_seconds = 0
    out_of_play_seconds = 0

    for interval in match.ball_states:
        if interval.start_second >= second:
            break
        duration = min(interval.end_second, second) - interval.start_second
        if interval.state == "contested":
            contested_seconds += duration
        elif interval.state == "out_of_play":
            out_of_play_seconds += duration
        elif interval.team_id == match.home_team.id:
            home_seconds += duration
        else:
            away_seconds += duration

    controlled_seconds = home_seconds + away_seconds
    return PossessionSummary(
        home_seconds=home_seconds,
        away_seconds=away_seconds,
        contested_seconds=contested_seconds,
        out_of_play_seconds=out_of_play_seconds,
        home_share_percent=(100 * home_seconds / controlled_seconds if controlled_seconds else None),
        away_share_percent=(100 * away_seconds / controlled_seconds if controlled_seconds else None),
    )
