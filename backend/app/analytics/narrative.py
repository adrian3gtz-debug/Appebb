"""Build a bounded account of what is observed, including recent activity."""

from app.analytics.recap import build_recap
from app.analytics.recoveries import analyze_recoveries
from app.analytics.statistics import calculate_statistics
from app.models.events import ShotEvent
from app.models.match import Match
from app.models.narrative import NarrativeFact


def clock(second: int) -> str:
    return f"{second // 60:02}:{second % 60:02}"


def build_narrative_facts(match: Match, second: int) -> list[NarrativeFact]:
    if not 0 <= second <= 5400:
        raise ValueError("Clock outside match")
    stats = calculate_statistics(match, second)
    recap = build_recap(match, stats)
    facts: list[NarrativeFact] = []

    def add(id: str, es: str, en: str, values: dict, event_ids=None, at=None):
        facts.append(NarrativeFact(id=id, statements={"es": es, "en": en},
            values=values, event_ids=event_ids or [], second=at))

    h, a = stats.home, stats.away
    phase_es, phase_en = ("Final", "Full time") if second == 5400 else ("En juego", "In progress")
    add("score", f"{phase_es}, corte {clock(second)}: marcador local–visitante {h.goals}–{a.goals}.",
        f"{phase_en}, through {clock(second)}: home–away score {h.goals}–{a.goals}.",
        {"minute": second // 60, "clock_second": second % 60, "home_goals": h.goals, "away_goals": a.goals})
    add("shots", f"Remates acumulados: local {h.shots}, visitante {a.shots}.",
        f"Cumulative shots: home {h.shots}, away {a.shots}.", {"home": h.shots, "away": a.shots})
    for side, team, es in (("home", h, "local"), ("away", a, "visitante")):
        accuracy = None if team.pass_accuracy_percent is None else round(team.pass_accuracy_percent, 1)
        es_accuracy = "Sin precisión disponible." if accuracy is None else f"Precisión {accuracy}%."
        en_accuracy = "Accuracy unavailable." if accuracy is None else f"Accuracy {accuracy}%."
        add(f"passing_{side}", f"Equipo {es}: {team.passes_completed} pases completos de {team.passes_attempted}. {es_accuracy}",
            f"{side.capitalize()} team: {team.passes_completed} completed passes from {team.passes_attempted}. {en_accuracy}",
            {"completed": team.passes_completed, "attempted": team.passes_attempted, "accuracy_percent": accuracy})
    control = stats.possession
    if control is not None and control.home_share_percent is not None:
        home, away = round(control.home_share_percent, 1), round(control.away_share_percent, 1)
        add("control", f"Del tiempo controlado por los equipos: local {home}%, visitante {away}%. No incluye balón disputado ni fuera de juego.",
            f"Share of team-controlled time: home {home}%, away {away}%. Contested and out-of-play time excluded.",
            {"home_percent": home, "away_percent": away})
    else:
        add("control", "Reparto de tiempo controlado no disponible; no inferirlo de los pases.",
            "Controlled-time shares unavailable; do not infer them from passes.", {})
    start = max(0, second - 600)
    recent = [event for event in match.events if isinstance(event, ShotEvent)
              and event.second <= second and (event.second > start or start == 0)]
    rh = sum(event.team_id == match.home_team.id for event in recent)
    ra = sum(event.team_id == match.away_team.id for event in recent)
    add("recent_shots", f"Entre {clock(start)} y {clock(second)}, remates: local {rh}, visitante {ra}. La ventana excluye su inicio, salvo al comienzo del partido.",
        f"Between {clock(start)} and {clock(second)}, shots: home {rh}, away {ra}. The window excludes its start except at the beginning of the match.",
        {"start_minute": start // 60, "start_second": start % 60, "end_minute": second // 60,
         "end_second": second % 60, "home": rh, "away": ra}, [event.id for event in recent])
    for index, goal in enumerate(recap.goals):
        home = goal.team_id == match.home_team.id
        add(f"goal_{index + 1}", f"Gol del equipo {'local' if home else 'visitante'} a {clock(goal.second)}: marcador local–visitante {goal.home_score}–{goal.away_score}.",
            f"{'Home' if home else 'Away'} goal at {clock(goal.second)}: home–away score {goal.home_score}–{goal.away_score}.",
            {"minute": goal.second // 60, "clock_second": goal.second % 60, "home": goal.home_score, "away": goal.away_score},
            [goal.event_id], goal.second)
    # Latest highlighted window per team is enough for a concise overview.
    latest = {}
    for insight in analyze_recoveries(match, second).insights:
        latest[insight.team_id] = insight
    for side, team_id, es in (("home", match.home_team.id, "local"), ("away", match.away_team.id, "visitante")):
        if team_id not in latest:
            continue
        i = latest[team_id]
        # Counts and subsequent shots belong to this closed comparison, not all later play.
        add(f"recoveries_{side}",
            f"Equipo {es}: recuperaciones en último tercio {i.previous.high_recoveries} entre {clock(i.previous.start_second)}–{clock(i.previous.end_second)} y {i.current.high_recoveries} entre {clock(i.current.start_second)}–{clock(i.current.end_second)}; {i.current.shot_sequences} posesiones del segundo intervalo terminaron en remate dentro de ese intervalo.",
            f"{side.capitalize()} team: final-third recoveries {i.previous.high_recoveries} in {clock(i.previous.start_second)}–{clock(i.previous.end_second)} and {i.current.high_recoveries} in {clock(i.current.start_second)}–{clock(i.current.end_second)}; {i.current.shot_sequences} possessions from the second window ended in a shot within that window.",
            {"previous": i.previous.high_recoveries, "current": i.current.high_recoveries, "shots": i.current.shot_sequences,
             "previous_start": i.previous.start_second // 60, "previous_end": i.previous.end_second // 60,
             "current_start": i.current.start_second // 60, "current_end": i.current.end_second // 60}, i.recovery_event_ids, i.detected_second)
    return facts
