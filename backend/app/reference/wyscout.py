"""Read the Pappalardo/Wyscout release without forcing it into synthetic Match."""

from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

from app.reference.observations import Observation


class _Record(BaseModel):
    model_config = ConfigDict(strict=True, extra="ignore", allow_inf_nan=False)


class _Position(_Record):
    x: float = Field(ge=0, le=100)
    y: float = Field(ge=0, le=100)


class _Tag(_Record):
    id: int


class RawEvent(_Record):
    id: int
    matchId: int
    teamId: int
    playerId: int = Field(ge=0)
    eventId: int
    subEventId: int | Literal[""]
    matchPeriod: Literal["1H", "2H"]
    eventSec: float = Field(ge=0)
    positions: list[_Position] = Field(min_length=1)
    tags: list[_Tag]


# Wyscout v2: corners, free kicks/crosses, goal kicks and throw-ins.
# Direct free-kick shots (33) and penalties (35) are shots, not passes.
PASS_RESTARTS = {30, 31, 32, 34, 36}
SHOT_RESTARTS = {33, 35}
PASS_CONTEXT = {30: "corner", 31: "free_kick", 32: "free_kick", 34: "goal_kick", 36: "throw_in"}


def read_observations(records: list[dict], teams_by_match: dict[str, set[str]]) -> list[Observation]:
    observations = []
    seen: set[int] = set()
    for record in records:
        event = RawEvent.model_validate(record)
        if event.id in seen:
            raise ValueError(f"duplicate Wyscout event id: {event.id}")
        seen.add(event.id)
        match_id, team_id = str(event.matchId), str(event.teamId)
        if match_id not in teams_by_match or team_id not in teams_by_match[match_id]:
            raise ValueError(f"event {event.id}: unknown match or team")
        tags = tuple(tag.id for tag in event.tags)
        if 1801 in tags and 1802 in tags:
            raise ValueError(f"event {event.id}: conflicting accuracy tags")
        kind = "other"
        if event.eventId == 8 or event.eventId == 3 and event.subEventId in PASS_RESTARTS:
            kind = "pass"
        elif event.eventId == 10 or event.eventId == 3 and event.subEventId in SHOT_RESTARTS:
            kind = "shot"
        observations.append(Observation(
            source="wyscout", id=str(event.id), match_id=match_id, team_id=team_id,
            player_id=str(event.playerId) if event.playerId else None,
            period=1 if event.matchPeriod == "1H" else 2, period_second=event.eventSec,
            kind=kind, attacking_x=event.positions[0].x, attacking_y=event.positions[0].y,
            pass_complete=(True if 1801 in tags else False if 1802 in tags else None) if kind == "pass" else None,
            # Type 8 has no restart marker, including recorded kickoffs.
            restart=True if event.eventId == 3 else None, provider_type=str(event.eventId),
            provider_subtype=str(event.subEventId), tags=tags,
            end_attacking_x=event.positions[1].x if len(event.positions) > 1 else None,
            end_attacking_y=event.positions[1].y if len(event.positions) > 1 else None,
            pass_context=(PASS_CONTEXT.get(event.subEventId) if event.eventId == 3 else "unmarked")
                         if kind == "pass" else None,
        ))
    # Provider arrays can contain paired duels and equal timestamps. Stable sorting
    # retains source order for ties; no continuous ownership is inferred.
    return sorted(observations, key=lambda e: (e.match_id, e.period, e.period_second))
