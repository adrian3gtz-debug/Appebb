"""Groq transport, provider isolation and shared evidence validation, without live calls."""

import json

from fastapi import HTTPException
from fastapi.testclient import TestClient
import httpx
import pytest

from app.analytics.narrative import build_narrative_facts
from app.analytics.recoveries import analyze_recoveries
from app.main import app
from app.services import ai_providers, explanations
from app.services.match_repository import load_scenario


@pytest.fixture(autouse=True)
def isolate(monkeypatch):
    explanations._cache.clear()
    explanations._calls.clear()
    monkeypatch.setattr(explanations, "_busy", False)
    monkeypatch.setenv("AI_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "groq-test-private")
    monkeypatch.setenv("GROQ_MODEL", "openai/gpt-oss-120b")
    # Even with both configured, only the selected provider may receive a request.
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "azure-test-private")
    monkeypatch.setenv("AZURE_OPENAI_RESPONSES_ENDPOINT", "https://example.services.ai.azure.com/openai/v1/responses")


def completion(content, **message):
    return {"choices": [{"finish_reason": "stop", "message": {
        "role": "assistant", "content": json.dumps(content), **message}}]}


def recovery_request():
    insight = analyze_recoveries(load_scenario("higher_recoveries"), 1200).insights[0]
    return {"scenario": "higher_recoveries", "second": 1200,
            "insight_id": insight.id, "language": "es", "audience": "fan"}


def recovery_text():
    return {"text": "El local pasó de 1 recuperación entre 0–10 a 6 entre 10–20; 3 posesiones acabaron en remate.",
            "fact_ids": ["recovery_increase", "subsequent_shots"]}


def mock_transport(monkeypatch, handler):
    original = httpx.AsyncClient
    monkeypatch.setattr(ai_providers.httpx, "AsyncClient",
        lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs))


@pytest.mark.parametrize("second,language,audience", [(0, "es", "fan"), (1200, "en", "analyst"), (5400, "es", "fan")])
def test_groq_narration_contract_cutoffs_and_personas(monkeypatch, second, language, audience):
    facts = build_narrative_facts(load_scenario("original"), second)
    by_id = {f.id: f.statements[language] for f in facts}
    paragraphs = [{"text": by_id["score"] + " " + by_id["shots"], "fact_ids": ["score", "shots"]},
                  {"text": by_id["recent_shots"], "fact_ids": ["recent_shots"]}]
    if audience == "analyst":
        paragraphs.insert(1, {"text": " ".join(by_id[i] for i in ["passing_home", "passing_away", "control"]),
                              "fact_ids": ["passing_home", "passing_away", "control"]})
    calls = []

    def handle(req):
        calls.append(req)
        body = json.loads(req.content)
        assert str(req.url) == ai_providers.GROQ_ENDPOINT
        assert req.headers["authorization"] == "Bearer groq-test-private"
        assert "api-key" not in req.headers
        assert "azure-test-private" not in str(req.headers) + req.content.decode()
        assert body["model"] == "openai/gpt-oss-120b"
        assert body["reasoning_effort"] == "low" and body["include_reasoning"] is False
        assert body["max_completion_tokens"] == 4096
        assert not {"input", "instructions", "store", "text", "tools"} & body.keys()
        assert body["messages"][0]["role"] == "system"
        supplied = json.loads(body["messages"][1]["content"])
        assert supplied["facts"] == [{"id": f.id, "statement": f.statements[language], "values": f.values} for f in facts]
        schema = body["response_format"]["json_schema"]
        assert schema["strict"] is True and schema["schema"]["additionalProperties"] is False
        return httpx.Response(200, json=completion({"headline": by_id["score"], "paragraphs": paragraphs},
                                                  reasoning="private reasoning must never enter output"))

    mock_transport(monkeypatch, handle)
    request = {"scenario": "original", "second": second, "language": language, "audience": audience}
    client = TestClient(app)
    response = client.post("/api/matches/demo/narrative", json=request)
    assert response.status_code == 200, response.text
    assert response.json()["generation"] == "groq"
    assert response.json()["as_of_second"] == second
    assert "private reasoning" not in response.text
    assert client.post("/api/matches/demo/narrative", json=request).json() == response.json()
    assert len(calls) == 1


def test_cache_separates_providers_and_models_and_preserves_metadata(monkeypatch):
    calls = []

    def handle(req):
        body = json.loads(req.content)
        calls.append((str(req.url), body["model"]))
        if str(req.url) == ai_providers.GROQ_ENDPOINT:
            # Metadata must describe this request, even if configuration changes in flight.
            monkeypatch.setenv("AI_PROVIDER", "azure_openai")
            return httpx.Response(200, json=completion(recovery_text()))
        assert req.headers["api-key"] == "azure-test-private"
        assert "authorization" not in req.headers
        return httpx.Response(200, json={"status": "completed", "output": [{"type": "message", "role": "assistant",
            "content": [{"type": "output_text", "text": json.dumps(recovery_text())}]}]})

    mock_transport(monkeypatch, handle)
    client = TestClient(app)
    request = recovery_request()
    assert client.post("/api/matches/demo/explanation", json=request).json()["generation"] == "groq"
    assert client.post("/api/matches/demo/explanation", json=request).json()["generation"] == "azure_openai"
    monkeypatch.setenv("AI_PROVIDER", "groq")
    assert client.post("/api/matches/demo/explanation", json=request).json()["generation"] == "groq"
    assert len(calls) == 2
    monkeypatch.setenv("GROQ_MODEL", "openai/gpt-oss-20b")
    assert client.post("/api/matches/demo/explanation", json=request).json()["generation"] == "groq"
    assert len(calls) == 3 and calls[-1][1] == "openai/gpt-oss-20b"


@pytest.mark.parametrize("failure", ["truncated", "refusal", "missing", "bad_shape", "unsupported_fact", "unknown_reference", "http", "quota", "timeout"])
def test_groq_failures_do_not_bypass_validation_or_leak_credentials(monkeypatch, caplog, failure):
    def handle(req):
        if failure == "timeout":
            raise httpx.ReadTimeout("groq-test-private", request=req)
        if failure in ("http", "quota"):
            return httpx.Response(429 if failure == "quota" else 401, json={"error": "groq-test-private"})
        raw = recovery_text()
        if failure == "unsupported_fact": raw["text"] = "99 remates"
        if failure == "unknown_reference": raw["fact_ids"] = ["fake", "subsequent_shots"]
        payload = completion(raw)
        if failure == "truncated": payload["choices"][0]["finish_reason"] = "length"
        if failure == "refusal": payload["choices"][0]["message"]["refusal"] = "unavailable"
        if failure == "missing": payload["choices"][0]["message"]["content"] = None
        if failure == "bad_shape": payload = {"choices": []}
        return httpx.Response(200, json=payload)

    mock_transport(monkeypatch, handle)
    response = TestClient(app).post("/api/matches/demo/explanation", json=recovery_request())
    assert response.status_code == (429 if failure == "quota" else 502)
    assert "groq-test-private" not in response.text + caplog.text
    assert not explanations._busy and not explanations._cache


def test_selection_is_explicit_and_never_falls_back_to_azure(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY")
    with pytest.raises(HTTPException) as error:
        ai_providers.settings()
    assert error.value.status_code == 503
    monkeypatch.setenv("AI_PROVIDER", "unknown")
    with pytest.raises(HTTPException): ai_providers.settings()
    monkeypatch.setenv("AI_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "groq-test-private")
    monkeypatch.setenv("GROQ_MODEL", "unsupported")
    with pytest.raises(HTTPException): ai_providers.settings()
    monkeypatch.delenv("AI_PROVIDER")
    assert ai_providers.settings().generation == "azure_openai"
    assert "azure-test-private" not in repr(ai_providers.settings())
