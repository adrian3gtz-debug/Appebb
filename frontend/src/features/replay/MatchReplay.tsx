import { useEffect, useState } from 'react'
import { translations } from '../../i18n'
import type { Language } from '../../i18n'
import { fetchDemoMatch } from '../../services/matches'
import type { DemoMatchResponse } from '../../types/match'
import { formatClock, matchAt } from './playback'
import { usePlayback } from './usePlayback'

const buttonStyle = 'rounded-lg border border-[#c8d6c9] px-5 py-2.5 font-medium hover:bg-[#e8f0e8] disabled:cursor-not-allowed disabled:opacity-50'
type LoadState = { status: 'loading' } | { status: 'error' } | { status: 'ready'; data: DemoMatchResponse }

export function MatchReplay({ language }: { language: Language }) {
  const [load, setLoad] = useState<LoadState>({ status: 'loading' })
  const [attempt, setAttempt] = useState(0)
  const copy = translations[language]

  useEffect(() => {
    const controller = new AbortController()
    setLoad({ status: 'loading' })
    fetchDemoMatch(controller.signal).then(
      (data) => { if (!controller.signal.aborted) setLoad({ status: 'ready', data }) },
      () => { if (!controller.signal.aborted) setLoad({ status: 'error' }) },
    )
    return () => controller.abort()
  }, [attempt])

  if (load.status === 'loading') return <p role="status" className="py-12">{copy.loading}</p>
  if (load.status === 'error') return (
    <div className="mt-8 rounded-xl border border-red-200 bg-white p-6">
      <p role="alert" className="mb-4 text-red-800">{copy.loadError}</p>
      <button className={buttonStyle} onClick={() => setAttempt((value) => value + 1)}>{copy.retry}</button>
    </div>
  )
  return <Replay key={load.data.match.id} data={load.data} language={language} />
}

function Replay({ data, language }: { data: DemoMatchResponse; language: Language }) {
  const { match, duration_seconds: duration } = data
  const { second, playing, speed, dispatch } = usePlayback(duration)
  const copy = translations[language]
  const { homeScore, awayScore, recentEvents } = matchAt(match, second)
  const finished = second >= duration
  const teams = [match.home_team, match.away_team]
  const periodLabel = finished ? copy.finished : second < 2700 ? copy.firstHalf : copy.secondHalf

  return (
    <div className="mt-8 grid items-start gap-8 lg:grid-cols-[1.1fr_1fr]">
      <section aria-label={copy.replayTitle} className="rounded-2xl border border-[#dce5db] bg-white p-5 sm:p-8">
        <div className="flex justify-between gap-3 text-sm text-[#53675b]">
          <span>{periodLabel}</span>
          <span>{finished ? copy.finished : playing ? copy.playing : copy.paused}</span>
        </div>
        <div className="mt-10 grid grid-cols-[1fr_auto_1fr] items-center gap-3 text-center">
          <h2 className="break-words text-lg font-semibold">{match.home_team.name}</h2>
          <p className="whitespace-nowrap text-4xl font-semibold tabular-nums sm:text-5xl">{homeScore} – {awayScore}</p>
          <h2 className="break-words text-lg font-semibold">{match.away_team.name}</h2>
        </div>
        <p className="my-8 text-center text-3xl tabular-nums">{formatClock(second)}</p>
        <progress aria-label={copy.progress} max={duration} value={second} className="h-2 w-full accent-[#205c41]" />
        <div className="mt-7 flex flex-wrap items-center gap-3">
          <button className="rounded-lg bg-[#205c41] px-5 py-2.5 font-medium text-white hover:bg-[#184732] disabled:cursor-not-allowed disabled:opacity-50" disabled={finished} onClick={() => dispatch({ type: 'toggle', duration })}>{playing ? copy.pause : copy.play}</button>
          <button className={buttonStyle} onClick={() => dispatch({ type: 'reset' })}>{copy.reset}</button>
          <label className="flex items-center gap-2 text-sm">
            {copy.speed}
            <select className="rounded-lg border border-[#c8d6c9] bg-white px-2 py-2.5" value={speed} onChange={(event) => dispatch({ type: 'speed', speed: Number(event.target.value) })}>
              {[1, 10, 30, 60].map((value) => <option key={value} value={value}>{value}×</option>)}
            </select>
          </label>
        </div>
        <p className="mt-6 text-sm leading-6 text-[#53675b]">{copy.demoHelp}</p>
      </section>
      <section aria-label={copy.latestEvents} className="rounded-2xl border border-[#dce5db] bg-white p-5 sm:p-8">
        <h2 className="text-xl font-semibold">{copy.latestEvents}</h2>
        {recentEvents.length === 0 ? <p className="py-8 text-[#53675b]">{copy.noEvents}</p> : (
          <ol className="mt-4 divide-y divide-[#e5ebe3]">
            {recentEvents.map((event) => {
              const team = teams.find((item) => item.id === event.team_id)!
              const player = team.players.find((item) => item.id === event.player_id)!
              const outcome = event.type === 'pass' || event.type === 'shot' ? copy.outcomes[event.outcome] : null
              return (
                <li key={event.id} className="flex gap-4 py-3">
                  <span className="pt-0.5 text-sm tabular-nums text-[#53675b]">{formatClock(event.second)}</span>
                  <div>
                    <p className="font-medium">{copy.events[event.type]}{outcome && ` · ${outcome}`}</p>
                    <p className="mt-1 text-sm text-[#53675b]">{player.name} · {team.name}</p>
                  </div>
                </li>
              )
            })}
          </ol>
        )}
      </section>
    </div>
  )
}
