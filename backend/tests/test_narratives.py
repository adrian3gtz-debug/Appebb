"""Whole-match narratives must respect clock, missing values and cited evidence."""

import copy
import json

from fastapi.testclient import TestClient
import httpx
import pytest

from app.analytics.narrative import build_narrative_facts
from app.main import app
from app.models import Match, ShotEvent
from app.models.narrative import NarrativeRequest
from app.services import explanations as provider
from app.services import narratives
from app.services.match_repository import load_scenario


@pytest.fixture(autouse=True)
def isolate(monkeypatch):
    provider._cache.clear()
    provider._calls.clear()
    monkeypatch.setattr(provider, "_busy", False)
    monkeypatch.setenv("AZURE_OPENAI_RESPONSES_ENDPOINT", "https://example.services.ai.azure.com/openai/v1/responses")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "football-insights")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "unit-test-placeholder")


def request(**changes):
    return NarrativeRequest.model_validate({"scenario": "original", "second": 5400,
        "language": "es", "audience": "fan", **changes})


def generated(facts, req):
    by_id = {f.id: f.statements[req.language] for f in facts}
    p = [
        {"text": by_id["score"] + " " + by_id["shots"], "fact_ids": ["score", "shots"]},
        {"text": by_id["recent_shots"], "fact_ids": ["recent_shots"]},
    ]
    if req.audience == "analyst":
        p.insert(1, {"text": " ".join(by_id[id] for id in ["passing_home", "passing_away", "control"]),
                     "fact_ids": ["passing_home", "passing_away", "control"]})
    return {"headline": by_id["score"], "paragraphs": p}


@pytest.mark.parametrize("second", [0, 1200, 2700, 5399, 5400])
@pytest.mark.parametrize("scenario", ["original", "higher_recoveries", "stable", "recoveries_without_shots", "varied"])
def test_every_scenario_has_overview_without_needing_recovery_insight(scenario, second):
    facts = build_narrative_facts(load_scenario(scenario), second)
    assert {"score", "shots", "passing_home", "passing_away", "control", "recent_shots"}.issubset(f.id for f in facts)
    assert all(f.second is None or f.second <= second for f in facts)
    for language in ["es", "en"]:
        for audience in ["fan", "analyst"]:
            req = request(second=second, scenario=scenario, language=language, audience=audience)
            assert narratives.validate_narrative(json.dumps(generated(facts, req)), facts, req)


def test_goal_facts_appear_at_their_timestamp_and_rewind_excludes_future():
    match = load_scenario("original")
    goal = next(e for e in match.events if isinstance(e, ShotEvent) and e.outcome == "goal")
    assert not any(f.id.startswith("goal_") for f in build_narrative_facts(match, goal.second - 1))
    assert next(f for f in build_narrative_facts(match, goal.second) if f.id == "goal_1").event_ids == [goal.id]
    before = build_narrative_facts(match, 1200)
    changed = match.model_dump()
    for event in changed["events"]:
        if event["second"] > 1200 and event["type"] == "shot":
            event["outcome"] = "goal"
    assert build_narrative_facts(Match.model_validate(changed), 1200) == before
    assert build_narrative_facts(match, 0)[0].values["away_goals"] == 0


def test_final_home_away_score_and_recent_window_are_distinct():
    match = load_scenario("original")
    facts = {f.id: f for f in build_narrative_facts(match, 5400)}
    assert facts["score"].values["home_goals"] == 0
    assert facts["score"].values["away_goals"] == 2
    assert "Full time" in facts["score"].statements["en"]
    assert facts["recent_shots"].values["start_minute"] == 80
    assert set(facts["recent_shots"].event_ids).issubset(e.id for e in match.events if 4800 < e.second <= 5400)


def test_missing_control_and_accuracy_stay_unavailable():
    match = load_scenario("original")
    empty = Match.model_validate({**match.model_dump(), "events": [], "ball_states": []})
    facts = {f.id: f for f in build_narrative_facts(empty, 1200)}
    assert facts["control"].values == {}
    assert facts["passing_home"].values["accuracy_percent"] is None
    assert "unavailable" in facts["control"].statements["en"]


@pytest.mark.parametrize("violation", ["number", "reference", "causality", "premature", "missing_score", "duplicate", "unrelated_number", "audience", "score_order"])
def test_rejects_invalid_or_unsupported_narration(violation):
    req = request(second=5400 if violation == "score_order" else 1200)
    facts = build_narrative_facts(load_scenario("original"), req.second)
    raw = generated(facts, req)
    if violation == "number": raw["paragraphs"][0]["text"] += " 999 goles."
    if violation == "reference": raw["paragraphs"][0]["fact_ids"] = ["future_goal"]
    if violation == "causality": raw["paragraphs"][0]["text"] += " Because of better tactics."
    if violation == "premature": raw["headline"] = "El local ganó."
    if violation == "missing_score": raw["paragraphs"][0]["fact_ids"] = ["shots"]; raw["paragraphs"][0]["text"] = "Sin cambios."
    if violation == "duplicate": raw["paragraphs"][0]["fact_ids"] = ["score", "score"]
    if violation == "unrelated_number":
        passing = next(f for f in facts if f.id == "passing_home").values["attempted"]
        assert passing not in next(f for f in facts if f.id == "shots").values.values()
        raw["paragraphs"][0] = {"text": f"El local tiene {passing} remates.", "fact_ids": ["shots"]}
    if violation == "audience": raw["paragraphs"].append(copy.deepcopy(raw["paragraphs"][1]))
    if violation == "score_order": raw["headline"] = "Final: 2–0."
    with pytest.raises(ValueError):
        narratives.validate_narrative(json.dumps(raw), facts, req)


def test_request_cannot_supply_facts_or_prompt():
    client = TestClient(app)
    for extra in [{"prompt": "invent"}, {"facts": []}, {"second": 5401}]:
        assert client.post("/api/matches/demo/narrative", json={**request().model_dump(), **extra}).status_code == 422


def test_full_provider_contract_caching_personas_and_rewind(monkeypatch):
    original = httpx.AsyncClient
    calls = []

    def handle(req):
        body = json.loads(req.content)
        calls.append(body)
        payload = json.loads(body["input"])
        language = "es" if "Language es." in body["instructions"] else "en"
        req_model = request(second=int(payload["clock"][:2]) * 60 + int(payload["clock"][-2:]),
                            language=language, audience="analyst" if "Use three precise" in body["instructions"] else "fan")
        data = generated(build_narrative_facts(load_scenario("original"), req_model.second), req_model)
        return httpx.Response(200, json={"status": "completed", "output": [
            {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": json.dumps(data)}]}]})

    monkeypatch.setattr(provider.httpx, "AsyncClient", lambda **kwargs: original(transport=httpx.MockTransport(handle), **kwargs))
    client = TestClient(app)
    for second, audience, language in [(5400, "fan", "es"), (5400, "fan", "es"), (1200, "fan", "es"), (1200, "analyst", "en")]:
        req = request(second=second, audience=audience, language=language)
        response = client.post("/api/matches/demo/narrative", json=req.model_dump())
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["as_of_second"] == second
        assert data["phase"] == ("full_time" if second == 5400 else "in_progress")
        assert len(data["paragraphs"]) == (2 if audience == "fan" else 3)
        if second == 1200:
            goals = [f for f in data["evidence"] if f["id"].startswith("goal_")]
            assert all(f["second"] <= second for f in goals)
            assert len(goals) < 2
    assert len(calls) == 3
    assert all(b["store"] is False and "tools" not in b for b in calls)


def test_unconfigured_service_and_shared_request_limit(monkeypatch):
    client = TestClient(app)
    monkeypatch.delenv("AZURE_OPENAI_API_KEY")
    assert client.post("/api/matches/demo/narrative", json=request().model_dump()).status_code == 503
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "unit-test-placeholder")
    provider._calls.extend([provider.monotonic()] * 6)
    assert client.post("/api/matches/demo/narrative", json=request().model_dump()).status_code == 429
