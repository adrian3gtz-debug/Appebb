"""Structured evidence; narratives and field drawings are separate consumers."""

from typing import Literal

from pydantic import BaseModel, Field


class RecoveryRules(BaseModel):
    version: str = "recoveries-v1"
    window_seconds: int = Field(default=600, gt=0, le=1350)
    high_recovery_x: float = Field(default=200 / 3, ge=0, le=100)
    minimum_current: int = Field(default=4, gt=0)
    minimum_increase: int = Field(default=3, gt=0)
    minimum_ratio: float = Field(default=2, ge=1)


class RecoverySequence(BaseModel):
    recovery_event_id: str
    team_id: str
    period: int
    start_second: int
    possession_id: str
    event_ids: list[str]
    status: Literal["shot", "lost", "out_of_play", "period_end", "in_progress"]
    end_second: int | None
    shot_event_id: str | None
    seconds_to_shot: int | None


class RecoveryWindow(BaseModel):
    start_second: int
    end_second: int
    total_recoveries: int
    high_recoveries: int
    shot_sequences: int
    pending_sequences: int


class RecoveryComparison(BaseModel):
    team_id: str
    period: int
    previous: RecoveryWindow
    current: RecoveryWindow


class RecoveryInsight(RecoveryComparison):
    id: str
    type: Literal["high_recovery_increase"] = "high_recovery_increase"
    detected_second: int
    recovery_event_ids: list[str]


class RecoveryAnalysis(BaseModel):
    match_id: str
    as_of_second: int
    rules: RecoveryRules
    sequences: list[RecoverySequence]
    comparisons: list[RecoveryComparison]
    insights: list[RecoveryInsight]
