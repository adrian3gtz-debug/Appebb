"""Foundry Responses adapter. Facts come from Python, never from client text."""

from collections import OrderedDict, deque
import hashlib
import json
import os
import re
from time import monotonic
from urllib.parse import urlsplit

import httpx
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.analytics.recoveries import analyze_recoveries
from app.models.explanation import ExplanationRequest, ExplanationResponse
from app.models.match import Match


class ModelText(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=800)
    fact_ids: list[str] = Field(min_length=2, max_length=2)


def settings() -> tuple[str, str, str]:
    endpoint = os.getenv("AZURE_OPENAI_RESPONSES_ENDPOINT", "").strip()
    key = os.getenv("AZURE_OPENAI_API_KEY", "").strip()
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "football-insights").strip()
    if not endpoint or not key or not deployment:
        raise HTTPException(503, "AI is not configured")
    url = urlsplit(endpoint)
    if (url.scheme != "https" or not url.hostname
            or not url.hostname.endswith((".services.ai.azure.com", ".openai.azure.com"))
            or url.path != "/openai/v1/responses" or url.query or url.fragment
            or url.username or url.password or url.port not in (None, 443)):
        raise HTTPException(503, "AI configuration is invalid")
    return endpoint, key, deployment


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
                        language: str, audience: str) -> str:
    instructions = (
        "Explain only the supplied synthetic football facts. Do not use tools or outside knowledge. "
        "Write at most 65 words, plain text, using digits for counts. Refer to the home/away team, "
        "never invent names. Report both the recovery counts with their minute intervals and the "
        "number of subsequent possessions ending in a shot in the current interval. "
        "Do not derive percentages, ratios or new numbers. Do not infer pressure, tactics, dominance, "
        "quality, goals, coaching decisions or causality. No advice or predictions. "
        f"Language: {language}. Audience: {audience}; fan uses everyday language; analyst is precise about windows. "
        "Return JSON matching the schema. Cite exactly recovery_increase and subsequent_shots."
    )
    async with httpx.AsyncClient(timeout=httpx.Timeout(25, connect=5), follow_redirects=False) as client:
        response = await client.post(endpoint, headers={"api-key": key}, json={
            "model": deployment, "store": False, "instructions": instructions,
            "input": json.dumps(facts), "max_output_tokens": 1000,
            "reasoning": {"effort": "minimal"},
            "text": {"format": {"type": "json_schema", "name": "explanation",
                "strict": True, "schema": {
                    "type": "object", "properties": {
                        "text": {"type": "string"},
                        "fact_ids": {"type": "array", "items": {"type": "string", "enum": ["recovery_increase", "subsequent_shots"]}},
                    }, "required": ["text", "fact_ids"], "additionalProperties": False,
                }}},
        })
    response.raise_for_status()
    payload = response.json()
    if payload.get("status") != "completed":
        raise ValueError("Incomplete response")
    return "".join(part["text"] for item in payload.get("output", [])
                   if item.get("type") == "message" and item.get("role") == "assistant"
                   for part in item.get("content", []) if part.get("type") == "output_text")


# Best-effort limits per worker; serverless replicas do not share this state.
_cache: OrderedDict[str, ExplanationResponse] = OrderedDict()
_calls: deque[float] = deque()
_busy = False


async def explain(match: Match, request: ExplanationRequest) -> ExplanationResponse:
    global _busy
    facts, event_ids, second = evidence(match, request)
    endpoint, key, deployment = settings()
    cache_key = hashlib.sha256(json.dumps(["explanation-v1", endpoint, deployment, facts,
        request.language, request.audience], sort_keys=True).encode()).hexdigest()
    if cache_key in _cache:
        _cache.move_to_end(cache_key)
        return _cache[cache_key].model_copy(deep=True)
    now = monotonic()
    while _calls and now - _calls[0] >= 60:
        _calls.popleft()
    # No await between checking and reserving capacity on the async worker.
    if _busy or len(_calls) >= 6:
        raise HTTPException(429, "AI request limit reached; try again later")
    _busy = True
    _calls.append(now)
    try:
        raw = await request_model(endpoint, key, deployment, facts, request.language, request.audience)
        result = validate_text(raw, facts)
    except httpx.HTTPStatusError as error:
        status = 429 if error.response.status_code == 429 else 502
        raise HTTPException(status, "AI provider unavailable; deterministic evidence remains available") from None
    except (httpx.RequestError, ValueError, KeyError, TypeError):
        raise HTTPException(502, "AI response unavailable or rejected; deterministic evidence remains available") from None
    finally:
        _busy = False
    response = ExplanationResponse(match_id=match.id, insight_id=request.insight_id,
        evidence_second=second, language=request.language, audience=request.audience,
        text=result.text, fact_ids=result.fact_ids, recovery_event_ids=event_ids)
    _cache[cache_key] = response
    if len(_cache) > 96:
        _cache.popitem(last=False)
    return response.model_copy(deep=True)
