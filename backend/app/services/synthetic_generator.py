"""An authored synthetic scenario with seeded variations, not a calibrated simulator."""

from __future__ import annotations

from random import Random
from typing import Any

from pydantic import TypeAdapter

from app.models import BallStateInterval, Coordinate, Match, MatchEvent, Player, Team


def _player(team: str, number: int) -> str:
    return f"{team}-{number:02}"


def _team(team_id: str, name: str) -> Team:
    roles = ["goalkeeper"] + ["defender"] * 4 + ["midfielder"] * 3 + ["forward"] * 3
    return Team.model_validate({
        "id": team_id,
        "name": name,
        "players": [
            Player(id=_player(team_id, number), name=f"{name} {number}", role=role)
            for number, role in enumerate(roles, start=1)
        ],
    })


def _point(x: float, y: float, team: str, period: int) -> Coordinate:
    """Convert attacking-relative x to the fixed field convention; y stays fixed."""
    attacks_right = (team == "home") == (period == 1)
    return Coordinate(x=round(x if attacks_right else 100 - x, 2), y=round(y, 2))


def _progress(location: Coordinate, team: str, period: int) -> float:
    attacks_right = (team == "home") == (period == 1)
    return location.x if attacks_right else 100 - location.x


class _ScenarioBuilder:
    def __init__(self, seed: int) -> None:
        self.rng = Random(seed)
        self.match_id = f"synthetic-{seed}"
        self.events: list[MatchEvent] = []
        self.states: list[BallStateInterval] = []
        self.adapter = TypeAdapter(MatchEvent)

    def emit(
        self, kind: str, second: int, owner: str, possession: str,
        player: int, location: Coordinate, *, actor_team: str | None = None,
        **details: Any,
    ) -> None:
        actor = actor_team or owner
        self.events.append(self.adapter.validate_python({
            "id": f"event-{len(self.events) + 1:04}",
            "match_id": self.match_id,
            "period": 1 if second < 2700 else 2,
            "second": second,
            "type": kind,
            "team_id": actor,
            "player_id": _player(actor, player),
            "possession_id": possession,
            "possession_team_id": owner,
            "location": location,
            **details,
        }))

    def state(self, start: int, end: int, team: str | None = None) -> None:
        self.states.append(BallStateInterval(
            start_second=start,
            end_second=end,
            state="controlled" if team else "out_of_play",
            team_id=team,
        ))

    def receiver(self, progress: float, current_player: int) -> int:
        candidates = list(range(2, 6) if progress < 45 else
                          range(6, 9) if progress < 70 else range(9, 12))
        return self.rng.choice([number for number in candidates if number != current_player])

    def home_possession(
        self, cycle: int, start: int, end: int, location: Coordinate, player: int,
    ) -> Coordinate:
        """Circulate, occasionally shoot, otherwise lose an attempted forward pass."""
        period = 1 if start < 2700 else 2
        possession = f"possession-{cycle * 2 + 1:03}"
        shot = cycle % 6 == 3
        final_second = end - 3
        times = list(range(start, final_second - 5, self.rng.randint(5, 7)))

        for index, second in enumerate(times):
            # Occasional attacks reach a shooting location; most circulation stays deeper.
            approaching_shot = shot and index >= len(times) - 2
            if approaching_shot:
                x = 68 if index == len(times) - 2 else 82
                y = self.rng.uniform(40, 60)
            else:
                x = (35, 47, 37, 51, 41, 55)[index % 6] + self.rng.uniform(-2, 2)
                y = self.rng.choice((25, 50, 75)) + self.rng.uniform(-3, 3)

            if index % 5 == 4 and not approaching_shot:
                destination = _point(
                    _progress(location, "home", period) + 3,
                    location.y + self.rng.uniform(-2, 2), "home", period,
                )
                self.emit("carry", second, "home", possession, player, location,
                          end_location=destination)
            else:
                destination = _point(x, y, "home", period)
                receiver = self.receiver(x, player)
                self.emit("pass", second, "home", possession, player, location,
                          end_location=destination, receiver_id=_player("home", receiver),
                          outcome="complete")
                player = receiver
            location = destination

        if shot:
            self.emit("shot", final_second, "home", possession, player, location,
                      outcome="off_target")
            return location

        self.emit("pressure", final_second - 1, "home", possession, 6, location,
                  actor_team="away", target_player_id=_player("home", player))
        destination = _point(
            _progress(location, "home", period) + self.rng.uniform(6, 12),
            location.y + self.rng.uniform(-3, 3), "home", period,
        )
        self.emit("pass", final_second, "home", possession, player, location,
                  end_location=destination, outcome="incomplete")
        return destination

    def away_possession(
        self, cycle: int, start: int, end: int, location: Coordinate, recovered: bool,
    ) -> tuple[Coordinate, int]:
        """Advance quickly, then shoot or put the ball out for a home throw-in."""
        period = 1 if start < 2700 else 2
        possession = f"possession-{cycle * 2 + 2:03}"
        player = 6 if recovered else 1
        if recovered:
            self.emit("recovery", start, "away", possession, player, location,
                      method="interception")

        shot = cycle % 3 == 1
        final_second = end - 3
        times = list(range(start + (4 if recovered else 0), final_second - 3, 5))
        initial_x = _progress(location, "away", period)
        initial_y = location.y
        target_x = 86 if shot else 73
        target_y = self.rng.uniform(42, 58) if shot else self.rng.choice((18, 82))

        for index, second in enumerate(times):
            fraction = (index + 1) / len(times)
            x = initial_x + (target_x - initial_x) * fraction
            y = initial_y + (target_y - initial_y) * fraction
            destination = _point(x, y, "away", period)
            if index % 3 == 2:
                self.emit("carry", second, "away", possession, player, location,
                          end_location=destination)
            else:
                receiver = self.receiver(x, player)
                self.emit("pass", second, "away", possession, player, location,
                          end_location=destination, receiver_id=_player("away", receiver),
                          outcome="complete")
                player = receiver
            location = destination

        if shot:
            # These authored goals define the test scenario, not a probability or xG model.
            goal = cycle in (7, 25)
            self.emit("shot", final_second, "away", possession, player, location,
                      outcome="goal" if goal else "off_target")
            restart = _point(50 if goal else 5, 50, "home", period)
            return restart, 9 if goal else 1

        destination = _point(78, 0 if location.y < 50 else 100, "away", period)
        self.emit("pass", final_second, "away", possession, player, location,
                  end_location=destination, outcome="incomplete")
        return destination, 4


def generate_match(seed: int = 7) -> Match:
    """Produce a complete authored fixture with deterministic timing/coordinate variation."""
    builder = _ScenarioBuilder(seed)
    restart = Coordinate(x=50, y=50)
    restart_player = 9

    # Each 150-second block contains both possessions and their stoppages.
    for cycle in range(36):
        start = cycle * 150
        period = 1 if start < 2700 else 2
        if cycle == 18:
            # The away team takes the second-half kickoff below.
            restart = Coordinate(x=50, y=50)
            kickoff_end = start + 12
            builder.state(start, kickoff_end, "away")
            kickoff_possession = "possession-half2-kickoff"
            destination = _point(43, 50, "away", period)
            builder.emit("pass", start, "away", kickoff_possession, 9, restart,
                         end_location=destination, receiver_id=_player("away", 6),
                         outcome="complete")
            restart = _point(40, 35, "away", period)
            builder.emit("pass", kickoff_end - 3, "away", kickoff_possession, 6, destination,
                         end_location=restart, outcome="incomplete")
            start = kickoff_end
            restart_player = 6
            builder.emit("recovery", start, "home", f"possession-{cycle * 2 + 1:03}",
                         restart_player, restart, method="interception")
            # Let the recovery precede the next ball action.
            first_action = start + 4
        else:
            first_action = start

        home_end = start + builder.rng.randint(60, 74)
        builder.state(start, home_end, "home")
        lost_at = builder.home_possession(cycle, first_action, home_end, restart, restart_player)
        home_shot = cycle % 6 == 3
        away_start = home_end
        if home_shot:
            away_start += builder.rng.randint(10, 18)
            builder.state(home_end, away_start)
            lost_at = _point(5, 50, "away", period)
        away_end = away_start + builder.rng.randint(27, 39)
        builder.state(away_start, away_end, "away")
        restart, restart_player = builder.away_possession(
            cycle, away_start, away_end, lost_at, recovered=not home_shot,
        )
        builder.state(away_end, (cycle + 1) * 150)

    return Match(
        id=builder.match_id,
        home_team=_team("home", "Harbor FC (synthetic)"),
        away_team=_team("away", "Ridge United (synthetic)"),
        events=builder.events,
        ball_states=builder.states,
    )
