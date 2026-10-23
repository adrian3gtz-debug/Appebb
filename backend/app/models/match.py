"""Rosters and relationships between the events of one match."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from app.models.events import MatchEvent, PassEvent, PressureEvent, RecoveryEvent, Schema


class Player(Schema):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    role: Literal["goalkeeper", "defender", "midfielder", "forward"]


class Team(Schema):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    players: list[Player] = Field(min_length=11, max_length=11)

    @model_validator(mode="after")
    def check_lineup(self) -> Team:
        if len({player.id for player in self.players}) != 11:
            raise ValueError("player ids must be unique within a team")
        if sum(player.role == "goalkeeper" for player in self.players) != 1:
            raise ValueError("each team must have exactly one goalkeeper")
        return self


class Match(Schema):
    id: str = Field(min_length=1)
    home_team: Team
    away_team: Team
    events: list[MatchEvent] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_relationships(self) -> Match:
        if self.home_team.id == self.away_team.id:
            raise ValueError("the teams must have different ids")

        rosters = {
            team.id: {player.id for player in team.players}
            for team in (self.home_team, self.away_team)
        }
        if rosters[self.home_team.id] & rosters[self.away_team.id]:
            raise ValueError("player ids must be unique across both teams")

        seen_ids: set[str] = set()
        possession_owners: dict[str, str] = {}
        previous_second = -1
        previous_possession_id: str | None = None

        for event in self.events:
            if event.id in seen_ids:
                raise ValueError(f"duplicate event id: {event.id}")
            seen_ids.add(event.id)
            if event.match_id != self.id:
                raise ValueError(f"event {event.id} belongs to another match")
            if event.second < previous_second:
                raise ValueError("events must be ordered by second")
            previous_second = event.second
            if event.team_id not in rosters or event.possession_team_id not in rosters:
                raise ValueError(f"event {event.id} refers to an unknown team")
            if event.player_id not in rosters[event.team_id]:
                raise ValueError(f"event {event.id} refers to a player outside its team")

            if event.possession_id != previous_possession_id and event.possession_id in possession_owners:
                raise ValueError("a possession cannot resume after another possession")
            if isinstance(event, RecoveryEvent) and event.possession_id in possession_owners:
                raise ValueError("a recovery must start a new possession")
            owner = possession_owners.setdefault(event.possession_id, event.possession_team_id)
            if owner != event.possession_team_id:
                raise ValueError(f"possession {event.possession_id} changes owner")
            previous_possession_id = event.possession_id

            if isinstance(event, PressureEvent):
                if event.team_id == event.possession_team_id:
                    raise ValueError("the pressing team cannot own the ball")
                if event.target_player_id not in rosters[event.possession_team_id]:
                    raise ValueError("pressure target must belong to the team in possession")
            elif event.team_id != event.possession_team_id:
                raise ValueError(f"event {event.id} must be performed by the team in possession")

            if isinstance(event, PassEvent) and event.receiver_id is not None:
                if event.receiver_id not in rosters[event.team_id]:
                    raise ValueError("pass receiver must belong to the passing team")
                if event.receiver_id == event.player_id:
                    raise ValueError("a player cannot pass to themselves")

        return self
