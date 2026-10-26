"""Read the checked-in demo independently of the process working directory."""

from pathlib import Path
from typing import Literal
from functools import lru_cache

from app.models.match import Match
from app.services.recovery_scenarios import generate_recovery_scenario
from app.services.varied_generator import generate_varied_match

DEMO_PATH = Path(__file__).resolve().parents[3] / "data/synthetic/circulation-vs-counterattack.json"


def load_demo_match() -> Match:
    return Match.model_validate_json(DEMO_PATH.read_text(encoding="utf-8"))


# Keep scenario selection at the repository boundary, never in the analytics engine.
DemoScenario = Literal["original", "stable", "higher_recoveries", "recoveries_without_shots", "varied"]


@lru_cache(maxsize=1)
def _varied_demo() -> Match:
    # Analytics consumers are read-only. Avoid regenerating the fixed demo on each poll.
    return generate_varied_match(seed=7)


def load_scenario(scenario: DemoScenario) -> Match:
    if scenario == "varied":
        return _varied_demo()
    if scenario == "original":
        return load_demo_match()
    return generate_recovery_scenario(scenario)
