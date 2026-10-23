"""Time intervals describing who controls the ball."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from app.models.events import Schema


class BallStateInterval(Schema):
    """A half-open [start_second, end_second) interval on the match clock."""

    start_second: int = Field(ge=0, lt=5400)
    end_second: int = Field(gt=0, le=5400)
    state: Literal["controlled", "contested", "out_of_play"]
    team_id: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def check_state(self) -> BallStateInterval:
        if self.end_second <= self.start_second:
            raise ValueError("ball-state interval must have positive duration")
        if self.state == "controlled" and self.team_id is None:
            raise ValueError("controlled intervals require a team_id")
        if self.state != "controlled" and self.team_id is not None:
            raise ValueError("only controlled intervals may have a team_id")
        return self
