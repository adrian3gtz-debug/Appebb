"""Exercise the provider boundary without credentials, network or billable calls."""

import asyncio
import json

from fastapi.testclient import TestClient
import httpx
import pytest

from app.analytics.recoveries import analyze_recoveries
from app.main import app
from app.models.explanation import ExplanationRequest
from app.services import explanations as service
from app.services.match_repository import load_scenario


@pytest.fixture(autouse=True)
def isolated(monkeypatch):
    service._cache.clear()
    service._calls.clear()
    monkeypatch.setattr(service, "_busy", False)
    monkeypatch.setenv("AZURE_OPENAI_RESPONSES_ENDPOINT", "https://example.services.ai.azure.com/openai/v1/responses")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "football-insights")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "unit-test-placeholder")


def request_at(second=1200, **changes):
    match = load_scenario("higher_recoveries")
    insight = analyze_recoveries(match, 1200).insights[0]
    return match, ExplanationRequest.model_validate({
        "scenario": "higher_recoveries", "second": second, "insight_id": insight.id,
        "language": "es", "audience": "fan", **changes,
    })


def valid():
    return json.dumps({"text": "El local pasó de 1 recuperación entre 0–10 a 6 entre 10–20; 3 posesiones acabaron en remate.",
                       "fact_ids": ["recovery_increase", "subsequent_shots"]})


def test_facts_are_frozen_at_detection_and_exclude_future_events():
    match, request = request_at()
    late = request.model_copy(update={"second": 5400})
    assert service.evidence(match, request) == service.evidence(match, late)
    facts, ids, second = service.evidence(match, late)
    assert facts["recovery_increase"]["current_count"] == 6
    assert facts["subsequent_shots"]["shot_sequences"] == 3
    assert second == 1200 and ids
    with pytest.raises(Exception) as error:
        service.evidence(match, request.model_copy(update={"second": 1199}))
    assert error.value.status_code == 422


@pytest.mark.parametrize("mutation", [
    {"text": "99 remates"}, {"text": "Mejor presión y 3 remates"},
    {"text": "Better tactics caused 3 shots"}, {"text": "Tres goles"},
    {"fact_ids": ["invented", "subsequent_shots"]},
    {"fact_ids": ["recovery_increase", "recovery_increase"]}, {"extra": "unexpected"},
    {"text": ""},
])
def test_rejects_unknown_numbers_references_and_unsupported_interpretation(mutation):
    match, request = request_at()
    raw = {**json.loads(valid()), **mutation}
    with pytest.raises(ValueError):
        service.validate_text(json.dumps(raw), service.evidence(match, request)[0])


def test_api_calls_only_on_explicit_post_and_caches_closed_context(monkeypatch):
    calls = []

    async def fake(*args):
        calls.append(args)
        return valid()

    monkeypatch.setattr(service, "request_model", fake)
    client = TestClient(app)
    _, request = request_at()
    for second in [1200, 1500]:
        assert client.get("/api/matches/demo/analysis", params={"scenario": "higher_recoveries", "second": second}).status_code == 200
    assert calls == []
    first = client.post("/api/matches/demo/explanation", json=request.model_dump())
    assert first.status_code == 200
    assert first.json()["generation"] == "azure_openai"
    assert first.json()["evidence_second"] == 1200
    later = client.post("/api/matches/demo/explanation", json=request.model_copy(update={"second": 5400}).model_dump())
    assert later.json() == first.json() and len(calls) == 1
    client.post("/api/matches/demo/explanation", json=request.model_copy(update={"language": "en"}).model_dump())
    assert len(calls) == 2


def test_missing_key_and_invalid_insight_do_not_call_provider(monkeypatch):
    monkeypatch.delenv("AZURE_OPENAI_API_KEY")
    _, request = request_at()
    client = TestClient(app)
    assert client.post("/api/matches/demo/explanation", json=request.model_dump()).status_code == 503
    assert client.post("/api/matches/demo/explanation", json=request.model_copy(update={"insight_id": "fake"}).model_dump()).status_code == 422
    assert not service._calls


@pytest.mark.parametrize("endpoint", ["http://example.services.ai.azure.com/openai/v1/responses", "https://attacker.invalid/openai/v1/responses", "https://example.services.ai.azure.com/openai/v1/responses?key=x"])
def test_configuration_rejects_wrong_hosts_paths_and_plain_http(monkeypatch, endpoint):
    monkeypatch.setenv("AZURE_OPENAI_RESPONSES_ENDPOINT", endpoint)
    with pytest.raises(Exception) as error:
        service.settings()
    assert error.value.status_code == 503


def test_http_adapter_uses_responses_contract_and_reads_assistant_text(monkeypatch):
    original_client = httpx.AsyncClient
    captured = []

    def handler(request):
        captured.append(request)
        return httpx.Response(200, json={"status": "completed", "output": [
            {"type": "reasoning", "summary": []},
            {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": valid()}]},
        ]})

    monkeypatch.setattr(service.httpx, "AsyncClient", lambda **kwargs: original_client(transport=httpx.MockTransport(handler), **kwargs))
    match, request = request_at()
    result = asyncio.run(service.explain(match, request))
    assert result.text == json.loads(valid())["text"]
    body = json.loads(captured[0].content)
    assert body["model"] == "football-insights" and body["store"] is False
    assert body["text"]["format"]["strict"] is True
    assert "tools" not in body and "previous_response_id" not in body
    assert captured[0].headers["api-key"] == "unit-test-placeholder"


@pytest.mark.parametrize("failure,expected", [("malformed", 502), ("timeout", 502), ("upstream", 502), ("quota", 429)])
def test_provider_failures_are_sanitized_and_release_capacity(monkeypatch, failure, expected):
    async def fake(*args):
        if failure == "malformed":
            return "invalid-json"
        if failure == "timeout":
            raise httpx.ReadTimeout("secret error detail")
        response = httpx.Response(429 if failure == "quota" else 401, request=httpx.Request("POST", "https://example.invalid"))
        raise httpx.HTTPStatusError("secret error detail", request=response.request, response=response)

    monkeypatch.setattr(service, "request_model", fake)
    _, request = request_at()
    response = TestClient(app).post("/api/matches/demo/explanation", json=request.model_dump())
    assert response.status_code == expected
    assert "secret" not in response.text and "unit-test" not in response.text
    assert service._busy is False and not service._cache


def test_rate_limit_and_cors_post(monkeypatch):
    service._calls.extend([service.monotonic()] * 6)
    _, request = request_at()
    client = TestClient(app)
    assert client.post("/api/matches/demo/explanation", json=request.model_dump()).status_code == 429
    preflight = client.options("/api/matches/demo/explanation", headers={
        "Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type"})
    assert preflight.status_code == 200 and "POST" in preflight.headers["access-control-allow-methods"]
