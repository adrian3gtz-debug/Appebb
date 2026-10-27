import { translations } from '../../i18n'
import type { Language } from '../../i18n'
import type { Match, MatchEvent } from '../../types/match'
import { playerLabel, teamLabel } from './displayNames'
import { formatClock } from './playback'
import { eventLabel } from './eventLabel'

export function EventList({ match, events, language }: { match: Match; events: MatchEvent[]; language: Language }) {
  const copy = translations[language]
  const teams = [match.home_team, match.away_team]
  return events.length === 0 ? <p className="py-5 text-[#53675b]">{copy.noEvents}</p> : <ol className="mt-3 divide-y divide-[#e5ebe3]">
    {events.map((event) => {
      const team = teams.find((item) => item.id === event.team_id)!
      const player = team.players.find((item) => item.id === event.player_id)!
      const outcome = event.type === 'pass' || event.type === 'shot' ? copy.outcomes[event.outcome] : null
      return <li key={event.id} className="flex gap-4 py-3 text-sm">
        <span className="tabular-nums text-[#53675b]">{formatClock(event.second)}</span>
        <div><p className="font-medium">{eventLabel(event, language)}{outcome && ` · ${outcome}`}</p>
          <p className="mt-1 text-[#53675b]">{teamLabel(team.name)} · {playerLabel(player.name, team.name)}</p>
        </div>
      </li>
    })}
  </ol>
}
