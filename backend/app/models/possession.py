"""Time accounting for recorded ball-control intervals."""

from pydantic import Field

from app.models.events import Schema


class PossessionSummary(Schema):
    home_seconds: int = Field(ge=0)
    away_seconds: int = Field(ge=0)
    contested_seconds: int = Field(ge=0)
    out_of_play_seconds: int = Field(ge=0)
    home_share_percent: float | None = Field(default=None, ge=0, le=100)
    away_share_percent: float | None = Field(default=None, ge=0, le=100)
