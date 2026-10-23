"""Event types shared by synthetic match generation and analysis."""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Schema(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Coordinate(Schema):
    """A fixed field location; both axes are normalized to 0–100."""

    x: float = Field(ge=0, le=100)
    y: float = Field(ge=0, le=100)


class BaseEvent(Schema):
    id: str = Field(min_length=1)
    match_id: str = Field(min_length=1)
    period: Literal[1, 2]
    second: int = Field(ge=0, le=5400)
    team_id: str = Field(min_length=1)
    player_id: str = Field(min_length=1)
    possession_id: str = Field(min_length=1)
    possession_team_id: str = Field(min_length=1)
    location: Coordinate

    @model_validator(mode="after")
    def check_period_clock(self) -> BaseEvent:
        if self.period == 1 and self.second >= 2700:
            raise ValueError("first-half events must occur before second 2700")
        if self.period == 2 and self.second < 2700:
            raise ValueError("second-half events must occur at or after second 2700")
        return self


class PassEvent(BaseEvent):
    type: Literal["pass"]
    end_location: Coordinate
    outcome: Literal["complete", "incomplete"]
    receiver_id: str | None = None

    @model_validator(mode="after")
    def check_receiver(self) -> PassEvent:
        if self.outcome == "complete" and not self.receiver_id:
            raise ValueError("completed passes need a receiver_id")
        return self


class CarryEvent(BaseEvent):
    type: Literal["carry"]
    end_location: Coordinate


class RecoveryEvent(BaseEvent):
    type: Literal["recovery"]
    method: Literal["interception", "tackle", "loose_ball", "goalkeeper_claim"]


class PressureEvent(BaseEvent):
    type: Literal["pressure"]
    target_player_id: str = Field(min_length=1)


class ShotEvent(BaseEvent):
    type: Literal["shot"]
    outcome: Literal["goal", "saved", "off_target", "blocked"]


MatchEvent = Annotated[
    Union[PassEvent, CarryEvent, RecoveryEvent, PressureEvent, ShotEvent],
    Field(discriminator="type"),
]
