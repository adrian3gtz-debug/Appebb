"""Common observations for comparing provider records and synthetic actions.

Period-relative clocks preserve added time without overlapping the next half.
Locations face the attacking goal for both sources; they are not replay positions.
"""

from dataclasses import dataclass
from typing import Literal

from app.models import Match, PassEvent, ShotEvent


@dataclass(frozen=True)
class Observation:
    source: Literal["wyscout", "synthetic"]
    id: str
    match_id: str
    team_id: str
    player_id: str | None
    period: int
    period_second: float
    kind: Literal["pass", "shot", "other"]
    attacking_x: float
    attacking_y: float
    pass_complete: bool | None = None
    restart: bool | None = None
    provider_type: str | None = None
    provider_subtype: str | None = None
    tags: tuple[int, ...] = ()
    end_attacking_x: float | None = None
    end_attacking_y: float | None = None
    receiver_id: str | None = None
    pass_context: str | None = None


def synthetic_observations(match: Match) -> list[Observation]:
    observations = []
    for event in match.events:
        forward = (event.team_id == match.home_team.id) == (event.period == 1)
        end = getattr(event, "end_location", None)
        observations.append(Observation(
            source="synthetic", id=event.id, match_id=match.id,
            team_id=event.team_id, player_id=event.player_id,
            period=event.period, period_second=event.second - (event.period - 1) * 2700,
            kind="pass" if isinstance(event, PassEvent) else "shot" if isinstance(event, ShotEvent) else "other",
            attacking_x=event.location.x if forward else 100 - event.location.x,
            attacking_y=event.location.y if forward else 100 - event.location.y,
            pass_complete=event.outcome == "complete" if isinstance(event, PassEvent) else None,
            restart=(None if event.pass_context is None else event.pass_context != "open_play")
                    if isinstance(event, PassEvent) else None, provider_type=event.type,
            end_attacking_x=(end.x if forward else 100 - end.x) if end else None,
            end_attacking_y=(end.y if forward else 100 - end.y) if end else None,
            receiver_id=event.receiver_id if isinstance(event, PassEvent) else None,
            pass_context=event.pass_context if isinstance(event, PassEvent) else None,
        ))
    return observations
