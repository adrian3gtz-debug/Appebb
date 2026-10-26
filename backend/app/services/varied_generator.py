"""Seeded, state-dependent synthetic play. Parameters are assumptions, not fitted rates."""

from dataclasses import dataclass
from hashlib import sha256
from math import ceil, hypot
from random import Random
from typing import Any, Literal

from pydantic import TypeAdapter

from app.models import BallStateInterval, Coordinate, Match, MatchEvent
from app.services.synthetic_common import field_point, make_team

GENERATOR_VERSION = "varied-v1"
Pattern = Literal["circulation", "progression", "wide", "transition"]


@dataclass(frozen=True)
class Start:
    team: str
    point: Coordinate
    player: int
    recovery: str | None = None


def opponent(team: str) -> str:
    return "away" if team == "home" else "home"


def distance(start: Coordinate, end: Coordinate) -> float:
    # Assumed 105 x 68 m pitch. These are synthetic plausibility checks, not measurements.
    return hypot((end.x - start.x) * 1.05, (end.y - start.y) * .68)


class _Builder:
    def __init__(self, seed: int):
        self.rng = Random(seed)
        self.match_id = "synthetic-" + sha256(f"{GENERATOR_VERSION}:{seed}".encode()).hexdigest()[:12]
        self.events: list[MatchEvent] = []
        self.states: list[BallStateInterval] = []
        self.adapter = TypeAdapter(MatchEvent)
        self.possessions = 0
        self.pending_dead = 0
        self.pending_contest = 0
        # Independent, modest team tendencies; neither side is assigned a winner.
        self.directness = {team: self.rng.uniform(.35, .65) for team in ("home", "away")}
        self.pressure = {team: self.rng.uniform(.12, .30) for team in ("home", "away")}

    def emit(self, kind: str, second: int, start: Start, possession: str,
             player: int, point: Coordinate, **details: Any) -> None:
        actor = details.pop("actor_team", start.team)
        self.events.append(self.adapter.validate_python(dict(
            id=f"event-{len(self.events) + 1:04}", match_id=self.match_id, type=kind,
            second=second, period=1 if second < 2700 else 2, team_id=actor,
            player_id=f"{actor}-{player:02}", possession_team_id=start.team,
            possession_id=possession, location=point, **details,
        )))

    def state(self, start: int, end: int, state: str, team: str | None = None) -> None:
        if end > start:
            self.states.append(BallStateInterval(start_second=start, end_second=end,
                                               state=state, team_id=team))

    def progress(self, point: Coordinate, team: str, period: int) -> float:
        return point.x if (team == "home") == (period == 1) else 100 - point.x

    def receiver(self, x: float, y: float, current: int = 0) -> int:
        candidates = [2, 3, 4, 5] if x < 35 else [6, 7, 8] if x < 70 else [9, 10, 11]
        if y < 22:
            candidates += [2, 6, 9]
        elif y > 78:
            candidates += [5, 8, 11]
        return self.rng.choice([number for number in candidates if number != current])

    def pattern(self, start: Start, period: int) -> Pattern:
        x = self.progress(start.point, start.team, period)
        if start.recovery and x >= 30 and self.rng.random() < .55:
            return "transition"
        return self.rng.choices(
            ["circulation", "progression", "wide"],
            weights=[.55 if x < 35 else .25, self.directness[start.team], .30],
        )[0]

    def destination(self, point: Coordinate, team: str, period: int,
                    pattern: Pattern, carry: bool) -> Coordinate:
        x = self.progress(point, team, period)
        forward_probability = .40 if pattern == "circulation" else .78 if pattern == "transition" else .66
        if x < 12:
            forward_probability = .85
        elif x > 90:
            forward_probability = .25
        forward = self.rng.random() < forward_probability
        step = self.rng.uniform(4, 12) if carry else self.rng.uniform(6, 20)
        if pattern == "transition":
            step *= 1.25
        next_x = max(3, min(97, x + (step if forward else -step)))
        if not carry and self.rng.random() < (.28 if pattern == "circulation" else .12):
            next_x = max(3, min(97, x + self.rng.uniform(-2, 2)))
        if pattern == "wide" and x < 75:
            target_y = 12 if point.y < 50 else 88
            next_y = point.y + max(-18, min(18, target_y - point.y))
        elif x > 72:
            # Cutbacks/central combinations can follow wide progression.
            next_y = point.y + max(-15, min(15, 50 - point.y)) + self.rng.uniform(-5, 5)
        else:
            next_y = point.y + self.rng.uniform(-12 if carry else -25, 12 if carry else 25)
        return field_point(next_x, max(3, min(97, next_y)), team, period)

    def turnover(self, team: str, point: Coordinate, period: int, method: str) -> Start:
        other = opponent(team)
        return Start(other, point, self.receiver(self.progress(point, other, period), point.y), method)

    def possession(self, t: int, half_end: int, start: Start) -> tuple[int, Start]:
        self.possessions += 1
        possession = f"possession-{self.possessions:04}"
        period = 1 if t < 2700 else 2
        beginning = t
        point, player = start.point, start.player
        pattern = self.pattern(start, period)
        pace = self.rng.lognormvariate(0, .25)
        if start.recovery:
            self.emit("recovery", t, start, possession, player, point, method=start.recovery)
            t += 2
        age = 0
        while t < half_end:
            age += 1
            x = self.progress(point, start.team, period)
            pressured = self.rng.random() < self.pressure[opponent(start.team)] + (.1 if x < 40 else 0)
            # Choice to shoot depends on position, not the requested scenario or final result.
            shot_chance = .025 if x < 80 else .10 if x < 90 else .24
            can_shoot = age > 1 and x >= 68 and abs(point.y - 50) < 32
            if can_shoot and self.rng.random() < shot_chance:
                t, following = self.shot(t, half_end, start, possession, player, point, period)
                self.state(beginning, t, "controlled", start.team)
                return t, following

            # Restarts are represented by the first pass, as in the existing schema.
            carry = age > 1 and player != 1 and self.rng.random() < .24
            destination = self.destination(point, start.team, period, pattern, carry)
            failure_chance = (.04 + distance(point, destination) / 260 + (.10 if pressured else 0)
                              + (.05 if self.progress(destination, start.team, period) > 65 else 0))
            failed = self.rng.random() < (failure_chance if not carry else .06 + .08 * pressured)
            out = failed and not carry and self.rng.random() < .27
            if out:
                destination = Coordinate(x=destination.x, y=0 if destination.y < 50 else 100)
            speed = self.rng.uniform(3.5, 6.5) if carry else self.rng.uniform(12, 23)
            duration = max(2, ceil(distance(point, destination) / speed))
            decision = max(1, round(self.rng.lognormvariate(1.1, .45) * pace))
            if pattern == "transition":
                decision = max(1, decision // 2)
            next_t = t + duration + decision
            # Do not publish an action with an unobserved endpoint across halftime.
            if next_t >= half_end:
                self.state(beginning, half_end, "controlled", start.team)
                return half_end, start
            if pressured:
                self.emit("pressure", t, start, possession, self.rng.randint(2, 11), point,
                          actor_team=opponent(start.team), target_player_id=f"{start.team}-{player:02}")
            receiver = self.receiver(self.progress(destination, start.team, period), destination.y, player)
            if carry:
                self.emit("carry", t, start, possession, player, point, end_location=destination)
            else:
                self.emit("pass", t, start, possession, player, point, end_location=destination,
                          outcome="incomplete" if failed else "complete",
                          receiver_id=None if failed else f"{start.team}-{receiver:02}")
            t = next_t
            if failed:
                self.state(beginning, t, "controlled", start.team)
                if out:
                    end = min(half_end, t + self.rng.randint(9, 26))
                    self.state(t, end, "out_of_play")
                    return end, Start(opponent(start.team), destination, 2 if destination.y == 0 else 5)
                contested = self.rng.random() < .23
                following = self.turnover(start.team, destination, period,
                                          "loose_ball" if contested else "tackle" if carry else "interception")
                if contested:
                    end = min(half_end, t + self.rng.randint(2, 5))
                    self.state(t, end, "contested")
                    t = end
                return t, following
            point = destination
            if not carry:
                player = receiver
        self.state(beginning, half_end, "controlled", start.team)
        return half_end, start

    def shot(self, t: int, half_end: int, start: Start, possession: str,
             player: int, point: Coordinate, period: int) -> tuple[int, Start]:
        x = self.progress(point, start.team, period)
        # Heuristic outcome weights only. This is NOT a trained or calibrated xG model.
        goal_weight = max(.025, min(.14, .03 + (x - 68) * .003 - abs(point.y - 50) * .0015))
        outcome = self.rng.choices(["goal", "saved", "blocked", "off_target"],
                                  [goal_weight, .32, .25, .43 - goal_weight])[0]
        self.emit("shot", t, start, possession, player, point, outcome=outcome)
        other = opponent(start.team)
        if outcome in ("goal", "off_target"):
            restart = field_point(50 if outcome == "goal" else 5, 50, other, period)
            arrival = min(half_end, t + max(1, ceil(distance(point, field_point(100, 50, start.team, period)) / 25)))
            # The caller closes control through ball flight; the outer loop records dead time.
            self.pending_dead = self.rng.randint(30, 65) if outcome == "goal" else self.rng.randint(12, 30)
            return arrival, Start(other, restart, 9 if outcome == "goal" else 1)
        if outcome == "saved":
            restart = field_point(4, self.rng.uniform(43, 57), other, period)
            arrival = min(half_end, t + max(1, ceil(distance(point, restart) / 25)))
            return arrival, Start(other, restart, 1, "goalkeeper_claim")
        blocked = field_point(min(98, x + self.rng.uniform(1, 4)), point.y, start.team, period)
        arrival = min(half_end, t + 1)
        self.pending_contest = self.rng.randint(2, 5)
        return arrival, self.turnover(start.team, blocked, period, "loose_ball")

    def build(self) -> Match:
        for half_start in (0, 2700):
            t, half_end = half_start, half_start + 2700
            start = Start("home" if half_start == 0 else "away", Coordinate(x=50, y=50), 9)
            while t < half_end:
                self.pending_dead = self.pending_contest = 0
                t, start = self.possession(t, half_end, start)
                if self.pending_dead or self.pending_contest:
                    end = min(half_end, t + self.pending_dead + self.pending_contest)
                    self.state(t, end, "out_of_play" if self.pending_dead else "contested")
                    t = end
        return Match(id=self.match_id, home_team=make_team("home", "Harbor FC (synthetic)"),
                     away_team=make_team("away", "Ridge United (synthetic)"),
                     events=self.events, ball_states=self.states)


def generate_varied_match(seed: int = 7) -> Match:
    """Same seed and version reproduce a match; outcomes are sampled from its actions."""
    return _Builder(seed).build()
