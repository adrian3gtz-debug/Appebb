"""Whole-match narration and the evidence behind each paragraph."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.services.match_repository import DemoScenario


class NarrativeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scenario: DemoScenario
    second: int = Field(ge=0, le=5400)
    language: Literal["es", "en"]
    audience: Literal["fan", "analyst"]


class NarrativeFact(BaseModel):
    id: str
    statements: dict[Literal["es", "en"], str]
    values: dict[str, int | float | None]
    event_ids: list[str] = Field(default_factory=list)
    second: int | None = None


class NarrativeParagraph(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=700)
    fact_ids: list[str] = Field(min_length=1, max_length=8)


class GeneratedNarrative(BaseModel):
    model_config = ConfigDict(extra="forbid")
    headline: str = Field(min_length=1, max_length=160)
    paragraphs: list[NarrativeParagraph] = Field(min_length=2, max_length=3)


class NarrativeResponse(GeneratedNarrative):
    source: Literal["synthetic"] = "synthetic"
    generation: Literal["azure_openai"] = "azure_openai"
    methodology_version: Literal["narrative-v1"] = "narrative-v1"
    match_id: str
    as_of_second: int
    phase: Literal["in_progress", "full_time"]
    language: Literal["es", "en"]
    audience: Literal["fan", "analyst"]
    evidence: list[NarrativeFact]
