import { useMemo, useState } from 'react'
import { translations } from '../../i18n'
import type { Language } from '../../i18n'
import type { Match } from '../../types/match'
import type { RecoveryAnalysis } from '../../types/recoveries'
import { formatClock } from '../replay/playback'
import { playerLabel, teamLabel } from '../replay/displayNames'
import { recoveryCopy } from './copy'
import { RecoveryPitch } from './RecoveryPitch'

interface Props { match: Match; second: number; data: RecoveryAnalysis; language: Language; onSeek: (second: number) => void }

export function RecoveryPanel({ match, second, data, language, onSeek }: Props) {
  const copy = recoveryCopy[language]
  const eventCopy = translations[language]
  const [teamId, setTeamId] = useState(match.home_team.id)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const events = useMemo(() => new Map(match.events.map((event) => [event.id, event])), [match])
  const period = second < 2700 ? 1 : 2
  const comparison = data.comparisons.filter((item) => item.team_id === teamId && item.period === period).at(-1)
  const insight = comparison && data.insights.find((item) => item.team_id === teamId && item.detected_second === comparison.current.end_second)
  const sequences = data.sequences.filter((item) => item.team_id === teamId && item.period === period)
  const selected = sequences.find((item) => item.recovery_event_id === selectedId) ?? sequences.at(-1)
  const chain = selected?.event_ids.map((id) => events.get(id)!).filter(Boolean) ?? []
  const attacksRight = (teamId === match.home_team.id) === (period === 1)
  const windowLabel = (start: number, end: number) => `${formatClock(start)}–${formatClock(end)}`
  const firstComparison = (period === 1 ? 0 : 2700) + 2 * data.rules.window_seconds

  return <section className="mt-5 rounded-2xl border border-[#dce5db] bg-white p-4 sm:p-6" aria-label={copy.title}>
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h2 className="text-xl font-semibold tracking-tight sm:text-2xl">{copy.title}</h2>
        <p className="mt-1 text-sm text-[#53675b]">{copy.introduction}</p>
      </div>
      <label className="flex items-center gap-2 text-sm font-medium">{copy.team}
        <select className="min-h-11 max-w-full rounded-lg border border-[#c8d6c9] bg-white px-2" value={teamId} onChange={(event) => { setTeamId(event.target.value); setSelectedId(null) }}>
          {[match.home_team, match.away_team].map((item) => <option key={item.id} value={item.id}>{teamLabel(item.name)}</option>)}
        </select>
      </label>
    </div>
    <p className="mt-3 text-xs tabular-nums text-[#53675b] sm:text-sm">{copy.through} {formatClock(data.as_of_second)}</p>
    <div className="mt-4 grid items-start gap-6 lg:grid-cols-[0.9fr_1.1fr]">
      <div>
        <div className={`rounded-xl p-4 sm:p-5 ${insight ? 'bg-[#e8f0e8]' : 'bg-[#f7f8f5]'}`}>
          <h3 className="text-lg font-semibold">{!comparison ? copy.waitingTitle : insight ? copy.increase : copy.noChangeTitle}</h3>
          {!comparison ? <>
            <p className="mt-2 text-sm leading-6 text-[#53675b]">{copy.waitingUntil(formatClock(firstComparison))}</p>
            <button className="mt-4 min-h-11 rounded-lg bg-[#205c41] px-4 py-2 text-sm font-medium text-white hover:bg-[#184732]" onClick={() => onSeek(firstComparison)}>{copy.jumpTo(formatClock(firstComparison))}</button>
          </> : insight ? <>
            <p className="mt-3 leading-7">{copy.increaseText(insight.previous.high_recoveries, insight.current.high_recoveries)}</p>
            <p className="mt-2 text-sm leading-6 text-[#53675b]">{copy.shotText(insight.current.shot_sequences, insight.current.high_recoveries)}</p>
            <p className="mt-3 text-xs tabular-nums text-[#53675b]">{windowLabel(comparison.previous.start_second, comparison.previous.end_second)} / {windowLabel(comparison.current.start_second, comparison.current.end_second)}</p>
          </> : <p className="mt-2 text-sm leading-6 text-[#53675b]">{copy.noSignal}</p>}
        </div>
        <details className="mt-4 border-t border-[#dce5db] pt-4 text-sm leading-6 text-[#53675b]">
          <summary className="cursor-pointer font-semibold text-[#19332a]">{copy.evidence}</summary>
          {comparison && <div className="mt-3 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <caption className="mb-2 text-left font-medium">{copy.comparison}</caption>
              <thead><tr className="border-b border-[#dce5db]"><th scope="col" className="py-2 pr-2 font-medium">{copy.metric}</th><th scope="col" className="px-1 font-medium">{windowLabel(comparison.previous.start_second, comparison.previous.end_second)}</th><th scope="col" className="px-1 font-medium">{windowLabel(comparison.current.start_second, comparison.current.end_second)}</th></tr></thead>
              <tbody>{([
                [copy.total, 'total_recoveries'], [copy.high, 'high_recoveries'],
                [copy.shots, 'shot_sequences'], [copy.pending, 'pending_sequences'],
              ] as const).map(([label, key]) => <tr key={key} className="border-b border-[#edf1eb]"><th scope="row" className="py-2 pr-2 font-medium">{label}</th><td className="px-1 tabular-nums">{comparison.previous[key]}</td><td className="px-1 tabular-nums">{comparison.current[key]}</td></tr>)}</tbody>
            </table>
          </div>}
          <p className="mt-3">{copy.limitation}</p>
          <p className="mt-3">{copy.boundaryNote}</p>
          <p className="mt-3">{copy.definition}</p>
          <p className="mt-3">{copy.rule(data.rules.minimum_current, data.rules.minimum_increase, data.rules.minimum_ratio)}</p>
          <p className="mt-3">{copy.templates}</p>
        </details>
      </div>
      <div>
        <RecoveryPitch sequences={sequences} events={events} selected={selected} attacksRight={attacksRight} language={language} onSelect={setSelectedId} />
        {selected && <div className="mt-4 rounded-xl border border-[#dce5db] p-4">
          <h3 className="font-semibold">{copy.selected} · {formatClock(selected.start_second)}</h3>
          <p className="mt-1 text-sm font-medium text-[#205c41]">{selected.seconds_to_shot !== null ? copy.shotAfter(selected.seconds_to_shot) : copy.statuses[selected.status]}</p>
          <ol className="mt-2 divide-y divide-[#edf1eb]">{chain.map((event) => {
            const actorTeam = event.team_id === match.home_team.id ? match.home_team : match.away_team
            const player = actorTeam.players.find((item) => item.id === event.player_id)!
            const outcome = event.type === 'pass' || event.type === 'shot' ? eventCopy.outcomes[event.outcome] : null
            return <li key={event.id} className="flex gap-3 py-2 text-sm"><span className="tabular-nums text-[#53675b]">{formatClock(event.second)}</span><div><span className="font-medium">{eventCopy.events[event.type]}{outcome && ` · ${outcome}`}</span><p className="mt-1 text-[#53675b]">{teamLabel(actorTeam.name)} · {playerLabel(player.name, actorTeam.name)}</p></div></li>
          })}</ol>
        </div>}
        <h3 className="mt-5 text-base font-semibold">{copy.sequences}</h3>
        {sequences.length === 0 ? <p className="mt-2 text-sm leading-6 text-[#53675b]">{copy.empty}</p> : <div className="mt-3 grid max-h-52 gap-2 overflow-y-auto sm:grid-cols-2">
          {[...sequences].reverse().map((item) => <button key={item.recovery_event_id} onClick={() => setSelectedId(item.recovery_event_id)} aria-pressed={selected?.recovery_event_id === item.recovery_event_id} className={`min-h-11 rounded-lg border p-3 text-left text-sm ${selected?.recovery_event_id === item.recovery_event_id ? 'border-[#205c41] bg-[#e8f0e8]' : 'border-[#dce5db] hover:bg-[#f7f8f5]'}`}>
            <span className="font-semibold tabular-nums">{formatClock(item.start_second)}</span><span className="mt-1 block text-[#53675b]">{item.seconds_to_shot !== null ? copy.shotAfter(item.seconds_to_shot) : copy.statuses[item.status]}</span>
          </button>)}
        </div>}
      </div>
    </div>
  </section>
}
