"""Explicit, bounded requests for language generation from closed evidence."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.services.match_repository import DemoScenario


class ExplanationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scenario: DemoScenario
    second: int = Field(ge=1200, le=5400)
    insight_id: str = Field(min_length=1, max_length=200)
    language: Literal["es", "en"]
    audience: Literal["fan", "analyst"]


class ExplanationResponse(BaseModel):
    generation: Literal["azure_openai", "groq"] = "azure_openai"
    match_id: str
    insight_id: str
    evidence_second: int
    language: Literal["es", "en"]
    audience: Literal["fan", "analyst"]
    text: str
    fact_ids: list[str]
    recovery_event_ids: list[str]
