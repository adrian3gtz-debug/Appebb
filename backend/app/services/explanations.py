"""Validated language generation. Facts come from Python, never from client text."""

from collections import OrderedDict, deque
from collections.abc import Callable
from dataclasses import dataclass
import asyncio
import hashlib
import json
import logging
import re
from time import monotonic

import httpx
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.analytics.recoveries import analyze_recoveries
from app.services.ai_providers import AIProvider, request_completion, settings
from app.models.explanation import ExplanationRequest, ExplanationResponse
from app.models.match import Match

logger = logging.getLogger(__name__)


class ModelText(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=800)
    fact_ids: list[str] = Field(min_length=2, max_length=2)


def evidence(match: Match, request: ExplanationRequest) -> tuple[dict, list[str], int]:
    analysis = analyze_recoveries(match, request.second)
    insight = next((item for item in analysis.insights if item.id == request.insight_id), None)
    if insight is None:
        raise HTTPException(422, "Insight is not available at this clock")
    # Recompute at detection: later events must never change this closed-window story.
    closed = analyze_recoveries(match, insight.detected_second)
    insight = next(item for item in closed.insights if item.id == insight.id)
    facts = {
        "source": "synthetic", "match_id": match.id,
        "team": "home" if insight.team_id == match.home_team.id else "away",
        "recovery_increase": {
            "previous_start_minute": insight.previous.start_second // 60,
            "previous_end_minute": insight.previous.end_second // 60,
            "previous_count": insight.previous.high_recoveries,
            "current_start_minute": insight.current.start_second // 60,
            "current_end_minute": insight.current.end_second // 60,
            "current_count": insight.current.high_recoveries,
        },
        "subsequent_shots": {"shot_sequences": insight.current.shot_sequences},
    }
    return facts, insight.recovery_event_ids, insight.detected_second


def validate_text(raw: str, facts: dict) -> ModelText:
    result = ModelText.model_validate_json(raw)
    if set(result.fact_ids) != {"recovery_increase", "subsequent_shots"}:
        raise ValueError("Unrecognized evidence reference")
    allowed = set(re.findall(r"\d+", json.dumps([facts["recovery_increase"], facts["subsequent_shots"]])))
    if not set(re.findall(r"\d+(?:[.,]\d+)?", result.text)).issubset(allowed):
        raise ValueError("Unsupported number")
    # Conservative lexical guard; not a semantic proof of factual grounding.
    if re.search(r"presi[oó]n|press(?:ing|ure)?|t[aá]ctic|tactic|gol(?:es)?\b|goals?\b|xg\b|formation|formaci[oó]n|coach|entrenador|caus|provoc|debido|because|domin|mejor|better|superior|https?://", result.text, re.I):
        raise ValueError("Unsupported interpretation")
    return result


async def request_model(endpoint: str, key: str, deployment: str, facts: dict,
                        language: str, audience: str, *, instructions: str | None = None,
                        schema: dict | None = None, max_output_tokens: int = 1000) -> str:
    instructions = instructions or (
        "Explain only the supplied synthetic football facts. Do not use tools or outside knowledge. "
        "Write at most 65 words, plain text, using digits for counts. Refer to the home/away team, "
        "using 'equipo local'/'equipo visitante' in Spanish and 'home team'/'away team' in English. "
        "Never invent names. Report both the recovery counts with their minute intervals and the "
        "number of subsequent possessions ending in a shot in the current interval. "
        "Do not derive percentages, ratios or new numbers. Do not infer pressure, tactics, dominance, "
        "quality, goals, coaching decisions or causality. No advice or predictions. "
        f"Language: {language}. Audience: {audience}; fan uses everyday language; analyst is precise about windows. "
        "Return JSON matching the schema. Cite exactly recovery_increase and subsequent_shots."
    )
    schema = schema or {
        "type": "object", "properties": {
            "text": {"type": "string"},
            "fact_ids": {"type": "array", "items": {"type": "string", "enum": ["recovery_increase", "subsequent_shots"]}},
        }, "required": ["text", "fact_ids"], "additionalProperties": False,
    }
    return await request_completion(endpoint, key, deployment, json.dumps(facts),
                                    instructions, schema, max_output_tokens)


@dataclass(frozen=True)
class CheckedGeneration:
    value: BaseModel
    generation: AIProvider

    def copy(self):
        return CheckedGeneration(self.value.model_copy(deep=True), self.generation)


# Best-effort limits per worker; serverless replicas do not share this state.
_cache: OrderedDict[str, CheckedGeneration] = OrderedDict()
_calls: deque[float] = deque()
_busy = False


async def generate_checked(facts: dict, language: str, audience: str, *, version: str,
                           validate: Callable[[str], BaseModel], instructions: str | None = None,
                           schema: dict | None = None, max_output_tokens: int = 1000) -> CheckedGeneration:
    """Shared cache and request budget for recovery and whole-match narration."""
    global _busy
    config = settings()
    endpoint, key, deployment = config.endpoint, config.key, config.model
    cache_key = hashlib.sha256(json.dumps([version, config.generation, endpoint, deployment, facts,
        language, audience], sort_keys=True).encode()).hexdigest()
    if cache_key in _cache:
        _cache.move_to_end(cache_key)
        return _cache[cache_key].copy()
    now = monotonic()
    while _calls and now - _calls[0] >= 60:
        _calls.popleft()
    # No await between checking and reserving capacity on the async worker.
    if _busy or len(_calls) >= 6:
        raise HTTPException(429, "AI request limit reached; try again later")
    _busy = True
    _calls.append(now)
    try:
        args = (endpoint, key, deployment, facts, language, audience)
        call = request_model(*args) if instructions is None else request_model(
            *args, instructions=instructions, schema=schema, max_output_tokens=max_output_tokens)
        raw = await asyncio.wait_for(call, timeout=30)
        result = CheckedGeneration(validate(raw), config.generation)
    except httpx.HTTPStatusError as error:
        status = 429 if error.response.status_code == 429 else 502
        # Do not expose provider bodies, URLs, request headers or exception strings.
        logger.warning("AI failure category=provider_http_error provider_status=%d", error.response.status_code)
        raise HTTPException(status, {"code": "provider_http_error", "provider_status": error.response.status_code,
            "message": "AI provider rejected the request; deterministic evidence remains available"}) from None
    except (httpx.TimeoutException, TimeoutError):
        logger.warning("AI failure category=provider_timeout")
        raise HTTPException(502, {"code": "provider_timeout", "message": "AI provider timed out"}) from None
    except httpx.RequestError:
        logger.warning("AI failure category=provider_connection_error")
        raise HTTPException(502, {"code": "provider_connection_error", "message": "AI provider could not be reached"}) from None
    except (ValueError, KeyError, TypeError):
        logger.warning("AI failure category=response_rejected")
        raise HTTPException(502, {"code": "response_rejected",
            "message": "AI response incomplete or rejected by evidence validation"}) from None
    finally:
        _busy = False
    _cache[cache_key] = result
    if len(_cache) > 96:
        _cache.popitem(last=False)
    return result.copy()


async def explain(match: Match, request: ExplanationRequest) -> ExplanationResponse:
    facts, event_ids, second = evidence(match, request)
    result = await generate_checked(facts, request.language, request.audience,
        version="explanation-v2", validate=lambda raw: validate_text(raw, facts))
    return ExplanationResponse(generation=result.generation, match_id=match.id, insight_id=request.insight_id,
        evidence_second=second, language=request.language, audience=request.audience,
        text=result.value.text, fact_ids=result.value.fact_ids, recovery_event_ids=event_ids)
