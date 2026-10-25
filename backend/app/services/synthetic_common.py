"""Shared field convention and fictional rosters for authored scenarios."""

from app.models import Coordinate, Player, Team


def make_team(team_id: str, name: str) -> Team:
    roles = ["goalkeeper"] + ["defender"] * 4 + ["midfielder"] * 3 + ["forward"] * 3
    return Team(
        id=team_id, name=name,
        players=[Player(id=f"{team_id}-{number:02}", name=f"{name} {number}", role=role)
                 for number, role in enumerate(roles, start=1)],
    )


def field_point(x: float, y: float, team: str, period: int) -> Coordinate:
    """Attacking-relative x to fixed coordinates; keep the fixed y axis."""
    attacks_right = (team == "home") == (period == 1)
    return Coordinate(x=round(x if attacks_right else 100 - x, 2), y=round(y, 2))
