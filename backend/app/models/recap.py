"""Time-bounded facts for match summaries; language and audience are presentation."""

from typing import Literal

from pydantic import Field

from app.models.events import Schema


class GoalMoment(Schema):
    event_id: str
    team_id: str
    player_id: str
    second: int = Field(ge=0, lt=5400)
    home_score: int = Field(ge=0)
    away_score: int = Field(ge=0)


class ControlShotsContrast(Schema):
    team_id: str
    opponent_team_id: str
    controlled_seconds: int = Field(ge=0)
    opponent_controlled_seconds: int = Field(ge=0)
    shots: int = Field(ge=0)
    opponent_shots: int = Field(ge=0)


class MatchRecap(Schema):
    methodology_version: Literal["recap-v1"] = "recap-v1"
    generation: Literal["rules"] = "rules"
    match_id: str
    as_of_second: int = Field(ge=0, le=5400)
    phase: Literal["in_progress", "full_time"]
    goals: list[GoalMoment]
    control_shots_contrast: ControlShotsContrast | None
