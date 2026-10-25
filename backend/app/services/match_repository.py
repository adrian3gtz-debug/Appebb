"""Read the checked-in demo independently of the process working directory."""

from pathlib import Path
from typing import Literal

from app.models.match import Match
from app.services.recovery_scenarios import generate_recovery_scenario

DEMO_PATH = Path(__file__).resolve().parents[3] / "data/synthetic/circulation-vs-counterattack.json"


def load_demo_match() -> Match:
    return Match.model_validate_json(DEMO_PATH.read_text(encoding="utf-8"))


# Keep scenario selection at the repository boundary, never in the analytics engine.
DemoScenario = Literal["original", "stable", "higher_recoveries", "recoveries_without_shots"]


def load_scenario(scenario: DemoScenario) -> Match:
    if scenario == "original":
        return load_demo_match()
    return generate_recovery_scenario(scenario)
