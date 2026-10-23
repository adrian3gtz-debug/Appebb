"""Read-only access to the synthetic demo fixture."""

import logging
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.match import Match
from app.services.match_repository import load_demo_match

router = APIRouter(prefix="/api/matches", tags=["matches"])
logger = logging.getLogger(__name__)


class DemoMatchResponse(BaseModel):
    source: Literal["synthetic"] = "synthetic"
    duration_seconds: int = 5400
    match: Match


@router.get("/demo", response_model=DemoMatchResponse)
def demo_match() -> DemoMatchResponse:
    try:
        match = load_demo_match()
    except (OSError, ValueError):
        logger.exception("Could not load the synthetic demo")
        raise HTTPException(status_code=503, detail="Demo match unavailable") from None
    return DemoMatchResponse(match=match)
