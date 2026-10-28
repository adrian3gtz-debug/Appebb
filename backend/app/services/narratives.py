"""Whole-match generation with paragraph-level evidence checks."""

from decimal import Decimal
import re

from app.analytics.narrative import build_narrative_facts
from app.models.match import Match
from app.models.narrative import GeneratedNarrative, NarrativeFact, NarrativeRequest, NarrativeResponse
from app.services.explanations import generate_checked


def numbers(text: str) -> set[Decimal]:
    return {Decimal(value.replace(",", ".")) for value in re.findall(r"\d+(?:[.,]\d+)?", text)}


def validate_narrative(raw: str, facts: list[NarrativeFact], request: NarrativeRequest) -> GeneratedNarrative:
    result = GeneratedNarrative.model_validate_json(raw)
    lookup = {fact.id: fact for fact in facts}
    if len(result.paragraphs) != (2 if request.audience == "fan" else 3):
        raise ValueError("Wrong audience structure")
    def check(text: str, ids: list[str]):
        if len(set(ids)) != len(ids) or not set(ids).issubset(lookup):
            raise ValueError("Unknown or duplicated evidence")
        allowed = set()
        for id in ids:
            for value in lookup[id].values.values():
                if value is not None:
                    allowed.add(Decimal(str(value)))
        if not numbers(text).issubset(allowed):
            raise ValueError("Number absent from cited facts")
        if re.search(r"presi[oó]n|press(?:ing|ure)?|t[aá]ctic|tactic|xg\b|formation|formaci[oó]n|coach|entrenador|caus|provoc|debido|because|domin|merec|deserv|superior|https?://", text, re.I):
            raise ValueError("Unsupported interpretation")
        if request.second < 5400 and re.search(r"(?:^final\b(?![- ]third)|\b(?:full[- ]time|final (?:score|result)|resultado final|marcador final|won|wins|gan[oó]|ganaron|termin[oó] el partido)\b)", text, re.I):
            raise ValueError("Premature final result")
    check(result.headline, ["score"])
    score = lookup["score"].values
    pairs = re.findall(r"(?<!\d)(\d+)\s*[–—-]\s*(\d+)(?!\d)", result.headline)
    expected = (int(score["home_goals"]), int(score["away_goals"]))
    if not pairs or any((int(h), int(a)) != expected for h, a in pairs):
        raise ValueError("Headline must preserve the home-away score")
    cited = set()
    for paragraph in result.paragraphs:
        check(paragraph.text, paragraph.fact_ids)
        cited.update(paragraph.fact_ids)
    if not {"score", "shots"}.issubset(cited):
        raise ValueError("Missing score or shots")
    if request.audience == "analyst" and not {"passing_home", "passing_away", "control", "recent_shots"}.issubset(cited):
        raise ValueError("Missing analyst context")
    return result


async def narrate(match: Match, request: NarrativeRequest) -> NarrativeResponse:
    facts = build_narrative_facts(match, request.second)
    phase = "full_time" if request.second == 5400 else "in_progress"
    audience = ("Use two short paragraphs, at most 100 words total. Tell an accessible story: score and shots, "
                "then a useful contrast or recent activity. Avoid statistical jargon.") if request.audience == "fan" else (
                "Use three precise paragraphs, at most 180 words total. Include score and shot totals; "
                "compare both teams' completed/attempted passes and known accuracy and controlled-time shares; "
                "then describe the recent shots window and any relevant recorded goal or recovery change. "
                "Cite passing_home, passing_away, control and recent_shots somewhere in the paragraphs.")
    instructions = (
        "Write an evidence-grounded account of a synthetic football match using ONLY supplied facts. "
        f"Language {request.language}. Phase {phase}; the only full-time cutoff is 90:00. "
        "Use 'equipo local'/'equipo visitante' in Spanish, 'home team'/'away team' in English; no invented names. "
        "Headline: describe only score/status and ALWAYS include the exact home-away score as H–A. "
        "Preserve home-away order; do not reverse the score to put the winning team first. "
        "When in progress, never present a winner or final result. At full time, describe the actual result. "
        "Use digits for quantities, reproduce only supplied numbers and rounded percentages; derive no new metrics. "
        "Each paragraph cites all facts needed for its numbers. Cite score and shots at least once. "
        "Missing control/accuracy is unavailable, never zero. Possession means team-controlled time, not pass count. "
        "Separate cumulative totals from the recent window and closed recovery windows. Shots are not chance quality. "
        "Do not infer tactics, pressure, formations, dominance, causality, deserving winners, xG, advice or predictions. "
        "Do not use external knowledge, tools, markdown or URLs. Return only the requested JSON. " + audience
    )
    schema = {
        "type": "object", "properties": {
            "headline": {"type": "string"},
            # Azure's schema subset excludes minItems/maxItems. Enforce lengths in Python.
            "paragraphs": {"type": "array", "items": {
                "type": "object", "properties": {"text": {"type": "string"}, "fact_ids": {
                    "type": "array",
                    "items": {"type": "string", "enum": [f.id for f in facts]},
                }}, "required": ["text", "fact_ids"], "additionalProperties": False,
            }},
        }, "required": ["headline", "paragraphs"], "additionalProperties": False,
    }
    payload = {"source": "synthetic", "phase": phase, "clock": f"{request.second // 60:02}:{request.second % 60:02}",
        "facts": [{"id": f.id, "statement": f.statements[request.language], "values": f.values} for f in facts]}
    result = await generate_checked(payload, request.language, request.audience,
        version="narrative-v2", validate=lambda raw: validate_narrative(raw, facts, request),
        instructions=instructions, schema=schema, max_output_tokens=1800)
    return NarrativeResponse(**result.value.model_dump(), generation=result.generation, match_id=match.id, as_of_second=request.second,
        phase=phase, language=request.language, audience=request.audience, evidence=facts)
