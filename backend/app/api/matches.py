"""Read-only access to the synthetic demo fixture."""

import logging
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.analytics.recoveries import analyze_recoveries
from app.analytics.statistics import calculate_statistics
from app.analytics.recap import build_recap
from app.models.statistics import MatchAnalysis
from app.models.match import Match
from app.models.recoveries import RecoveryAnalysis
from app.services.match_repository import DemoScenario, load_scenario
from app.models.explanation import ExplanationRequest, ExplanationResponse
from app.services.explanations import explain

router = APIRouter(prefix="/api/matches", tags=["matches"])
logger = logging.getLogger(__name__)


@router.post("/demo/explanation", response_model=ExplanationResponse)
async def match_explanation(request: ExplanationRequest) -> ExplanationResponse:
    return await explain(_available_match(request.scenario), request)


class DemoMatchResponse(BaseModel):
    source: Literal["synthetic"] = "synthetic"
    duration_seconds: int = 5400
    match: Match


def _available_match(scenario: DemoScenario) -> Match:
    try:
        match = load_scenario(scenario)
    except (OSError, ValueError):
        logger.exception("Could not load the synthetic demo")
        raise HTTPException(status_code=503, detail="Demo match unavailable") from None
    return match


@router.get("/demo", response_model=DemoMatchResponse)
def demo_match(scenario: DemoScenario = "original") -> DemoMatchResponse:
    return DemoMatchResponse(match=_available_match(scenario))


@router.get("/demo/recoveries", response_model=RecoveryAnalysis)
def recovery_analysis(
    second: int = Query(ge=0, le=5400), scenario: DemoScenario = "original",
) -> RecoveryAnalysis:
    return analyze_recoveries(_available_match(scenario), second)


@router.get("/demo/analysis", response_model=MatchAnalysis)
def match_analysis(
    second: int = Query(ge=0, le=5400), scenario: DemoScenario = "original",
) -> MatchAnalysis:
    match = _available_match(scenario)
    statistics = calculate_statistics(match, second)
    return MatchAnalysis(
        match_id=match.id, as_of_second=second,
        statistics=statistics,
        recoveries=analyze_recoveries(match, second),
        recap=build_recap(match, statistics),
    )
