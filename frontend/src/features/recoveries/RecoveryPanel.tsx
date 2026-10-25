import { useMemo, useState } from 'react'
import { translations } from '../../i18n'
import type { Language } from '../../i18n'
import type { Match } from '../../types/match'
import type { DemoScenario } from '../../types/recoveries'
import { formatClock } from '../replay/playback'
import { recoveryCopy } from './copy'
import { RecoveryPitch } from './RecoveryPitch'
import { useRecoveryAnalysis } from './useRecoveryAnalysis'

interface Props { match: Match; second: number; playing: boolean; scenario: DemoScenario; language: Language }

export function RecoveryPanel({ match, second, playing, scenario, language }: Props) {
  const copy = recoveryCopy[language]
  const eventCopy = translations[language]
  const { data, error, retry } = useRecoveryAnalysis(scenario, second, playing)
  const [teamId, setTeamId] = useState(match.home_team.id)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const events = useMemo(() => new Map(match.events.map((event) => [event.id, event])), [match])
  const period = second < 2700 ? 1 : 2
  const comparisons = data?.comparisons.filter((item) => item.team_id === teamId && item.period === period) ?? []
  const comparison = comparisons.at(-1)
  const insight = comparison && data?.insights.find((item) => item.team_id === teamId && item.detected_second === comparison.current.end_second)
  const sequences = data?.sequences.filter((item) => item.team_id === teamId && item.period === period) ?? []
  const selected = sequences.find((item) => item.recovery_event_id === selectedId) ?? sequences.at(-1)
  const chain = selected?.event_ids.map((id) => events.get(id)!).filter(Boolean) ?? []
  const attacksRight = (teamId === match.home_team.id) === (period === 1)
  const windowLabel = (start: number, end: number) => `${formatClock(start)}–${formatClock(end)}`

  return <section className="my-10 rounded-2xl border border-[#dce5db] bg-white p-5 sm:p-8" aria-label={copy.title}>
    <div className="flex flex-wrap items-start justify-between gap-5">
      <div><h2 className="text-2xl font-semibold tracking-tight">{copy.title}</h2><p className="mt-2 max-w-2xl leading-7 text-[#53675b]">{copy.introduction}</p></div>
      <label className="flex flex-col gap-2 text-sm font-medium">{copy.team}
        <select className="max-w-full rounded-lg border border-[#c8d6c9] bg-white px-3 py-2.5" value={teamId} onChange={(event) => { setTeamId(event.target.value); setSelectedId(null) }}>
          {[match.home_team, match.away_team].map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
        </select>
      </label>
    </div>
    {error && <div role="alert" className="mt-5 rounded-lg bg-red-50 p-4 text-red-800">{copy.error} <button onClick={retry} className="ml-2 font-semibold underline">{copy.retry}</button></div>}
    {!data ? <p role="status" className="py-8">{copy.loading}</p> : <>
      <p className="mt-5 text-sm tabular-nums text-[#53675b]">{copy.through} {formatClock(data.as_of_second)}</p>
      <div className="mt-6 grid items-start gap-8 xl:grid-cols-2">
        <div>
          <h3 className="text-lg font-semibold">{copy.comparison}</h3>
          {!comparison ? <p className="mt-3 leading-7 text-[#53675b]">{copy.waiting}</p> : <>
            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead><tr className="border-b border-[#dce5db] text-[#53675b]"><th scope="col" className="py-3 pr-3 font-medium">{copy.metric}</th><th scope="col" className="px-2 py-3 font-medium">{windowLabel(comparison.previous.start_second, comparison.previous.end_second)}</th><th scope="col" className="px-2 py-3 font-medium">{windowLabel(comparison.current.start_second, comparison.current.end_second)}</th></tr></thead>
                <tbody>{([
                  [copy.total, 'total_recoveries'], [copy.high, 'high_recoveries'],
                  [copy.shots, 'shot_sequences'], [copy.pending, 'pending_sequences'],
                ] as const).map(([label, key]) => <tr key={key} className="border-b border-[#edf1eb]"><th scope="row" className="py-3 pr-3 font-medium">{label}</th><td className="px-2 tabular-nums">{comparison.previous[key]}</td><td className="px-2 tabular-nums">{comparison.current[key]}</td></tr>)}</tbody>
              </table>
            </div>
            <div className={`mt-5 rounded-xl p-5 ${insight ? 'bg-[#e8f0e8]' : 'bg-[#f7f8f5]'}`}>
              {insight ? <>
                <h4 className="font-semibold">{copy.increase}</h4>
                <p className="mt-2 leading-7">{copy.increaseText(insight.previous.high_recoveries, insight.current.high_recoveries)}</p>
                <p className="mt-2 leading-7">{copy.shotText(insight.current.shot_sequences, insight.current.high_recoveries)}</p>
              </> : <p className="leading-7">{copy.noSignal}</p>}
              <p className="mt-3 text-sm leading-6 text-[#53675b]">{copy.limitation}</p>
            </div>
            <p className="mt-3 text-sm leading-6 text-[#53675b]">{copy.boundaryNote}</p>
          </>}
          <details className="mt-5 border-t border-[#dce5db] pt-4 text-sm leading-6 text-[#53675b]">
            <summary className="cursor-pointer font-semibold text-[#19332a]">{copy.methodology}</summary>
            <p className="mt-3">{copy.definition}</p>
            <p className="mt-3">{copy.rule(data.rules.minimum_current, data.rules.minimum_increase, data.rules.minimum_ratio)}</p>
            <p className="mt-3">{copy.templates}</p>
          </details>
        </div>
        <div>
          <RecoveryPitch sequences={sequences} events={events} selected={selected} attacksRight={attacksRight} language={language} onSelect={setSelectedId} />
          <h3 className="mt-6 text-lg font-semibold">{copy.sequences}</h3>
          {sequences.length === 0 ? <p className="mt-3 leading-7 text-[#53675b]">{copy.empty}</p> : <>
            <div className="mt-3 grid max-h-52 gap-2 overflow-y-auto sm:grid-cols-2">
              {[...sequences].reverse().map((item) => <button key={item.recovery_event_id} onClick={() => setSelectedId(item.recovery_event_id)} aria-pressed={selected?.recovery_event_id === item.recovery_event_id} className={`rounded-lg border p-3 text-left text-sm ${selected?.recovery_event_id === item.recovery_event_id ? 'border-[#205c41] bg-[#e8f0e8]' : 'border-[#dce5db] hover:bg-[#f7f8f5]'}`}>
                <span className="font-semibold tabular-nums">{formatClock(item.start_second)}</span><span className="mt-1 block text-[#53675b]">{item.seconds_to_shot !== null ? copy.shotAfter(item.seconds_to_shot) : copy.statuses[item.status]}</span>
              </button>)}
            </div>
            {selected && <div className="mt-5">
              <h4 className="font-semibold">{copy.selected} · {formatClock(selected.start_second)}</h4>
              <ol className="mt-2 divide-y divide-[#edf1eb]">{chain.map((event) => {
                const actorTeam = event.team_id === match.home_team.id ? match.home_team : match.away_team
                const player = actorTeam.players.find((item) => item.id === event.player_id)!
                const outcome = event.type === 'pass' || event.type === 'shot' ? eventCopy.outcomes[event.outcome] : null
                return <li key={event.id} className="flex gap-3 py-2 text-sm"><span className="tabular-nums text-[#53675b]">{formatClock(event.second)}</span><div><span className="font-medium">{eventCopy.events[event.type]}{outcome && ` · ${outcome}`}</span><p className="mt-1 text-[#53675b]">{player.name}</p></div></li>
              })}</ol>
              <p className="mt-2 text-sm font-medium text-[#205c41]">{copy.statuses[selected.status]}</p>
            </div>}
          </>}
        </div>
      </div>
    </>}
  </section>
}
