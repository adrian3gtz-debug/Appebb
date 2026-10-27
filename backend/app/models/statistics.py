"""Descriptive counts and denominators, without inferred chance quality."""

from typing import Literal

from pydantic import Field

from app.models.possession import PossessionSummary
from app.models.events import Schema
from app.models.recoveries import RecoveryAnalysis
from app.models.recap import MatchRecap


class TeamStatistics(Schema):
    team_id: str
    passes_attempted: int = Field(default=0, ge=0)
    passes_completed: int = Field(default=0, ge=0)
    pass_accuracy_percent: float | None = Field(default=None, ge=0, le=100)
    shots: int = Field(default=0, ge=0)
    goals: int = Field(default=0, ge=0)
    shots_saved: int = Field(default=0, ge=0)
    shots_off_target: int = Field(default=0, ge=0)
    shots_blocked: int = Field(default=0, ge=0)


class MatchStatistics(Schema):
    match_id: str
    as_of_second: int = Field(ge=0, le=5400)
    methodology_version: Literal["statistics-v1"] = "statistics-v1"
    home: TeamStatistics
    away: TeamStatistics
    possession: PossessionSummary | None


class MatchAnalysis(Schema):
    source: Literal["synthetic"] = "synthetic"
    match_id: str
    as_of_second: int = Field(ge=0, le=5400)
    statistics: MatchStatistics
    recoveries: RecoveryAnalysis
    recap: MatchRecap
