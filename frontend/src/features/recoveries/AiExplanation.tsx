import { useEffect, useRef, useState } from 'react'
import { isAIProvider, providerLabel } from '../../types/ai'
import type { AIProvider } from '../../types/ai'
import type { Language } from '../../i18n'
import type { DemoScenario, RecoveryInsight } from '../../types/recoveries'
import { apiBaseUrl } from '../../services/api'
import type { Audience } from '../summary/audience'
import { formatClock } from '../replay/playback'

interface Props {
  scenario: DemoScenario; matchId: string; insight: RecoveryInsight;
  language: Language; audience: Audience; onSeek: (second: number) => void
}

const copy = {
  es: { title: 'Explicación con IA', button: 'Explicar con IA', loading: 'Generando explicación…',
    error: 'La explicación con IA no está disponible. Puedes consultar la evidencia y el texto calculado del insight.',
    evidence: 'Revisar evidencia', note: (provider: string) => `Generada con ${provider} a partir de este insight sintético. Contrasta la redacción con la evidencia.` },
  en: { title: 'AI explanation', button: 'Explain with AI', loading: 'Generating explanation…',
    error: 'The AI explanation is unavailable. You can still inspect the evidence and the insight’s calculated text.',
    evidence: 'Inspect evidence', note: (provider: string) => `Generated with ${provider} from this synthetic insight. Check the wording against the evidence.` },
}

export function AiExplanation({ scenario, matchId, insight, language, audience, onSeek }: Props) {
  const c = copy[language]
  const [generated, setGenerated] = useState<{ text: string; generation: AIProvider } | null>(null)
  const text = generated?.text
  const [busy, setBusy] = useState(false)
  const [failed, setFailed] = useState(false)
  const controller = useRef<AbortController | null>(null)
  useEffect(() => () => controller.current?.abort(), [])

  async function generate() {
    if (controller.current && !controller.current.signal.aborted) return
    const pending = new AbortController()
    controller.current = pending
    setBusy(true)
    setFailed(false)
    try {
      const response = await fetch(`${apiBaseUrl}/api/matches/demo/explanation`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, signal: pending.signal,
        body: JSON.stringify({ scenario, second: insight.detected_second, insight_id: insight.id, language, audience }),
      })
      if (!response.ok) throw new Error('Explanation unavailable')
      const result: unknown = await response.json()
      if (!result || typeof result !== 'object' || !('text' in result) || typeof result.text !== 'string'
        || !('match_id' in result) || result.match_id !== matchId
        || !('insight_id' in result) || result.insight_id !== insight.id
        || !('evidence_second' in result) || result.evidence_second !== insight.detected_second
        || !('language' in result) || result.language !== language
        || !('audience' in result) || result.audience !== audience
        || !('generation' in result) || !isAIProvider(result.generation)) throw new Error('Mismatched explanation')
      if (!pending.signal.aborted) setGenerated({ text: result.text, generation: result.generation })
    } catch {
      if (!pending.signal.aborted) setFailed(true)
    } finally {
      if (!pending.signal.aborted) { setBusy(false); controller.current = null }
    }
  }

  return <section className="mt-5 rounded-xl border border-[#c8d6c9] bg-white p-4 sm:p-6" aria-label={c.title}>
    <h2 className="text-lg font-semibold">{c.title} · {formatClock(insight.detected_second)}</h2>
    <div aria-live="polite">
      {text && <p className="mt-3 max-w-3xl text-sm leading-6">{text}</p>}
      {failed && <p role="alert" className="mt-3 text-sm text-[#53675b]">{c.error}</p>}
      {busy && <p role="status" className="mt-3 text-sm">{c.loading}</p>}
    </div>
    <div className="mt-3 flex flex-wrap gap-3">
      {!text && <button type="button" disabled={busy} onClick={() => { void generate() }} className="min-h-11 rounded-lg bg-[#205c41] px-4 text-sm font-semibold text-white disabled:opacity-50">{c.button}</button>}
      <button type="button" onClick={() => onSeek(insight.detected_second)} className="min-h-11 text-sm font-medium underline">{c.evidence}</button>
    </div>
    {generated && <p className="mt-3 text-xs leading-5 text-[#53675b]">{c.note(providerLabel(generated.generation))}</p>}
  </section>
}
