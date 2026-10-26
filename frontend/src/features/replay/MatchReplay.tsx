import { useEffect, useState } from 'react'
import { translations } from '../../i18n'
import type { Language } from '../../i18n'
import { fetchDemoMatch } from '../../services/matches'
import type { DemoMatchResponse } from '../../types/match'
import { formatClock, matchAt } from './playback'
import { usePlayback } from './usePlayback'
import { MatchAnalysisPanel } from '../statistics/MatchAnalysisPanel'
import { teamLabel } from './displayNames'
import { recoveryCopy } from '../recoveries/copy'
import type { DemoScenario } from '../../types/recoveries'

const buttonStyle = 'rounded-lg border border-[#c8d6c9] px-5 py-2.5 font-medium hover:bg-[#e8f0e8] disabled:cursor-not-allowed disabled:opacity-50'
type LoadState = { status: 'loading' } | { status: 'error' } | { status: 'ready'; data: DemoMatchResponse }

export function MatchReplay({ language }: { language: Language }) {
  const [scenario, setScenario] = useState<DemoScenario>('higher_recoveries')
  const copy = recoveryCopy[language]
  return <>
    <label className="mt-4 flex flex-wrap items-center gap-2 text-sm font-medium">
      {copy.scenario}
      <select className="min-w-0 max-w-full rounded-lg border border-[#c8d6c9] bg-white px-3 py-2" value={scenario} onChange={(event) => setScenario(event.target.value as DemoScenario)}>
        {(Object.keys(copy.scenarios) as DemoScenario[]).map((option) => <option key={option} value={option}>{copy.scenarios[option]}</option>)}
      </select>
    </label>
    <LoadReplay key={scenario} scenario={scenario} language={language} />
  </>
}

function LoadReplay({ language, scenario }: { language: Language; scenario: DemoScenario }) {
  const [load, setLoad] = useState<LoadState>({ status: 'loading' })
  const [attempt, setAttempt] = useState(0)
  const copy = translations[language]

  useEffect(() => {
    const controller = new AbortController()
    setLoad({ status: 'loading' })
    fetchDemoMatch(controller.signal, scenario).then(
      (data) => { if (!controller.signal.aborted) setLoad({ status: 'ready', data }) },
      () => { if (!controller.signal.aborted) setLoad({ status: 'error' }) },
    )
    return () => controller.abort()
  }, [attempt, scenario])

  if (load.status === 'loading') return <p role="status" className="py-12">{copy.loading}</p>
  if (load.status === 'error') return (
    <div className="mt-8 rounded-xl border border-red-200 bg-white p-6">
      <p role="alert" className="mb-4 text-red-800">{copy.loadError}</p>
      <button className={buttonStyle} onClick={() => setAttempt((value) => value + 1)}>{copy.retry}</button>
    </div>
  )
  return <Replay data={load.data} language={language} scenario={scenario} />
}

function Replay({ data, language, scenario }: { data: DemoMatchResponse; language: Language; scenario: DemoScenario }) {
  const { match, duration_seconds: duration } = data
  const { second, playing, speed, dispatch } = usePlayback(duration)
  const copy = translations[language]
  const { homeScore, awayScore, recentEvents } = matchAt(match, second)
  const finished = second >= duration
  const periodLabel = finished ? copy.finished : second < 2700 ? copy.firstHalf : copy.secondHalf

  return <>
    <section aria-label={copy.replayTitle} className="mt-4 rounded-t-2xl border border-b-0 border-[#dce5db] bg-white px-4 py-4 sm:px-6">
      <div className="mb-3 flex items-center justify-between text-xs text-[#53675b] sm:text-sm">
        <span>{periodLabel}</span><span>{finished ? copy.finished : playing ? copy.playing : copy.paused}</span>
      </div>
      <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3 text-center">
        <h2 className="break-words text-base font-semibold sm:text-xl">{teamLabel(match.home_team.name)}</h2>
        <p className="whitespace-nowrap text-3xl font-semibold tabular-nums sm:text-4xl">{homeScore} – {awayScore}</p>
        <h2 className="break-words text-base font-semibold sm:text-xl">{teamLabel(match.away_team.name)}</h2>
      </div>
    </section>
    <div className="sticky top-0 z-20 rounded-b-2xl border border-[#dce5db] bg-white px-3 py-3 shadow-sm sm:px-6" role="group" aria-label={copy.progress}>
      <div className="flex items-center gap-2 sm:gap-3">
        <button className="min-h-11 rounded-lg bg-[#205c41] px-3 text-sm font-medium text-white hover:bg-[#184732] disabled:opacity-50 sm:px-5" disabled={finished} onClick={() => dispatch({ type: 'toggle', duration })}>{playing ? copy.pause : copy.play}</button>
        <button className="min-h-11 rounded-lg border border-[#c8d6c9] px-3 text-sm font-medium hover:bg-[#e8f0e8]" onClick={() => dispatch({ type: 'reset' })}>{copy.reset}</button>
        <label className="flex min-w-0 items-center gap-2 text-sm">
          <span className="sr-only sm:not-sr-only">{copy.speed}</span>
          <select className="min-h-11 rounded-lg border border-[#c8d6c9] bg-white px-1.5" value={speed} onChange={(event) => dispatch({ type: 'speed', speed: Number(event.target.value) })}>
            {[1, 10, 30, 60].map((value) => <option key={value} value={value}>{value}×</option>)}
          </select>
        </label>
        <p className="ml-auto text-lg font-semibold tabular-nums sm:text-xl">{formatClock(second)}</p>
      </div>
      <label className="mt-2 block">
        <span className="sr-only">{copy.progress}</span>
        <input type="range" min={0} max={duration} step={1} value={Math.floor(second)} aria-valuetext={formatClock(second)} onChange={(event) => dispatch({ type: 'seek', second: Number(event.target.value), duration })} className="block h-6 w-full accent-[#205c41]" />
      </label>
    </div>
    <MatchAnalysisPanel match={match} second={second} playing={playing} scenario={scenario} language={language} recentEvents={recentEvents} onSeek={(target) => dispatch({ type: 'seek', second: target, duration })} />
  </>
}
