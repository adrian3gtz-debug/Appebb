"""Read the checked-in demo independently of the process working directory."""

from pathlib import Path

from app.models.match import Match

DEMO_PATH = Path(__file__).resolve().parents[3] / "data/synthetic/circulation-vs-counterattack.json"


def load_demo_match() -> Match:
    return Match.model_validate_json(DEMO_PATH.read_text(encoding="utf-8"))
