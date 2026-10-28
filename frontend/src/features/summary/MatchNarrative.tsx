import { useCallback, useEffect, useRef, useState } from 'react'
import { providerLabel } from '../../types/ai'
import type { Language } from '../../i18n'
import type { Match } from '../../types/match'
import type { DemoScenario } from '../../types/recoveries'
import type { MatchNarrativeResponse } from '../../types/narrative'
import type { Audience } from './audience'
import { formatClock } from '../replay/playback'
import { narrativeCopy } from './narrativeCopy'
import { fetchNarrative, narrativeCheckpoint } from './narrativeRequest'

interface Props { match: Match; scenario: DemoScenario; second: number; language: Language; audience: Audience; onSeek: (second: number) => void }

export function MatchNarrative(props: Props) {
  const [automatic, setAutomatic] = useState(false)
  const [enabled, setEnabled] = useState(false)
  return <NarrativeView key={`${props.scenario}:${props.match.id}:${props.language}:${props.audience}`}
    {...props} automatic={automatic} enabled={enabled} enable={() => setEnabled(true)}
    setAutomatic={value => { setAutomatic(value); if (value) setEnabled(true) }} />
}

function NarrativeView({ match, scenario, second, language, audience, onSeek, automatic, enabled, enable, setAutomatic }:
  Props & { automatic: boolean; enabled: boolean; enable: () => void; setAutomatic: (value: boolean) => void }) {
  const c = narrativeCopy[language]
  const cutoff = Math.floor(second)
  const final = cutoff === 5400
  const [result, setResult] = useState<MatchNarrativeResponse | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<'rate_limit' | 'unavailable' | null>(null)
  const pending = useRef<{ controller: AbortController; second: number } | null>(null)
  const lastAutomatic = useRef<number | null>(null)
  const nextAutomatic = useRef(0)
  const checkpoint = narrativeCheckpoint(match, cutoff)

  useEffect(() => () => pending.current?.controller.abort(), [])
  useEffect(() => {
    if (pending.current && pending.current.second > cutoff) {
      pending.current.controller.abort(); pending.current = null; setBusy(false); setError(null)
    }
    if (result && result.as_of_second > cutoff) setResult(null)
    if (lastAutomatic.current !== null && lastAutomatic.current > cutoff) lastAutomatic.current = null
  }, [cutoff, result])

  const generate = useCallback(async (target: number) => {
    if (pending.current) return
    const request = { controller: new AbortController(), second: target }
    pending.current = request
    lastAutomatic.current = narrativeCheckpoint(match, target)
    nextAutomatic.current = Date.now() + 30000
    setBusy(true); setError(null)
    try {
      const response = await fetchNarrative({ scenario, second: target, language, audience }, match.id, request.controller.signal)
      if (!request.controller.signal.aborted) setResult(response)
    } catch (failure) {
      if (!request.controller.signal.aborted) setError(failure instanceof Error && failure.message === 'rate_limit' ? 'rate_limit' : 'unavailable')
    } finally {
      if (pending.current === request) { pending.current = null; setBusy(false) }
    }
  }, [scenario, language, audience, match])

  useEffect(() => {
    if (busy || (!automatic && !(enabled && final))) return
    const target = final ? 5400 : checkpoint
    if (lastAutomatic.current === target || (result && result.as_of_second >= target)) return
    const timer = window.setTimeout(() => { void generate(target) }, final ? 0 : Math.max(600, nextAutomatic.current - Date.now()))
    return () => window.clearTimeout(timer)
  }, [automatic, enabled, final, checkpoint, busy, result, generate])

  const visible = result && result.as_of_second <= cutoff && (!final || result.phase === 'full_time') ? result : null
  const evidence = visible ? new Map(visible.evidence.map(f => [f.id, f])) : null
  return <section className="mt-5 rounded-2xl border border-[#b7cdbd] bg-white p-4 sm:p-6" aria-label={final ? c.final : c.title}>
    <h2 className="text-lg font-semibold">{final ? c.final : c.title}</h2>
    <p className="mt-2 max-w-3xl text-sm leading-6 text-[#53675b]">{c.intro}</p>
    <div className="mt-3 flex flex-wrap items-center gap-3">
      <button type="button" disabled={busy} onClick={() => { enable(); void generate(cutoff) }} className="min-h-11 rounded-lg bg-[#205c41] px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">{final ? c.finalAction : visible ? c.update : c.action}</button>
      <label className="flex min-h-11 cursor-pointer items-center gap-2 text-sm font-medium">
        <input type="checkbox" checked={automatic} onChange={e => setAutomatic(e.target.checked)} className="size-4 accent-[#205c41]" />{c.follow}
      </label>
    </div>
    <p className="mt-2 text-xs leading-5 text-[#53675b]">{automatic ? c.followHelp : c.finalHelp}</p>
    <div aria-live="polite">
      {busy && <p role="status" className="mt-4 text-sm">{c.loading}</p>}
      {error && <p role="alert" className="mt-4 text-sm text-red-800">{error === 'rate_limit' ? c.limit : c.error}</p>}
    </div>
    {visible && <div className="mt-4 border-t border-[#dce5db] pt-4">
      <p className="text-xs font-medium tabular-nums text-[#53675b]">{c.through} {formatClock(visible.as_of_second)}</p>
      <h3 className="mt-2 text-xl font-semibold">{visible.headline}</h3>
      {visible.paragraphs.map((p, index) => <div key={`${visible.as_of_second}:${index}`} className="mt-3 max-w-3xl">
        <p className="text-sm leading-6">{p.text}</p>
        <details className="mt-2 text-sm">
          <summary className="min-h-6 cursor-pointer font-medium text-[#205c41]">{c.evidence} · {index + 1}</summary>
          <ul className="mt-2 space-y-2 border-l-2 border-[#c8d6c9] pl-3">
            {p.fact_ids.map(id => {
              const fact = evidence!.get(id)!
              return <li key={id} className="text-xs leading-5 text-[#53675b]">{fact.statements[language]}
                {fact.second !== null && <button type="button" onClick={() => onSeek(fact.second!)} className="ml-2 min-h-11 font-semibold underline">{c.inspect} {formatClock(fact.second)}</button>}
              </li>
            })}
          </ul>
        </details>
      </div>)}
      {visible.as_of_second < cutoff && <p className="mt-3 text-xs text-[#53675b]">{c.snapshot}</p>}
      <p className="mt-3 max-w-3xl text-xs leading-5 text-[#53675b]">{c.note(providerLabel(visible.generation))}</p>
    </div>}
  </section>
}
