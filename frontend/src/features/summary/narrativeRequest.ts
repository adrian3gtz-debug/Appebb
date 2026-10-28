import { isAIProvider } from '../../types/ai'
import type { Match } from '../../types/match'
import type { MatchNarrativeResponse, NarrativeRequest } from '../../types/narrative'
import { apiBaseUrl } from '../../services/api'

// Stable milestones, independent of the UI's 100 ms replay ticks.
export function narrativeCheckpoint(match: Match, second: number): number {
  const cutoff = Math.floor(second)
  let checkpoint = Math.max(Math.floor(cutoff / 600) * 600, cutoff >= 2700 ? 2700 : 0)
  for (const event of match.events) {
    if (event.second > cutoff) break
    if (event.type === 'shot' && event.outcome === 'goal') checkpoint = Math.max(checkpoint, event.second)
  }
  return checkpoint
}

function object(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === 'object'
}

export function parseNarrative(value: unknown, request: NarrativeRequest, matchId: string): MatchNarrativeResponse {
  if (!object(value) || value.source !== 'synthetic' || !isAIProvider(value.generation)
    || value.methodology_version !== 'narrative-v1' || value.match_id !== matchId
    || value.as_of_second !== request.second || value.language !== request.language || value.audience !== request.audience
    || value.phase !== (request.second === 5400 ? 'full_time' : 'in_progress')
    || typeof value.headline !== 'string' || !value.headline.trim()
    || !Array.isArray(value.paragraphs) || value.paragraphs.length !== (request.audience === 'fan' ? 2 : 3)
    || !Array.isArray(value.evidence) || value.evidence.length === 0) throw new Error('Mismatched narrative')
  const ids = new Set<string>()
  for (const fact of value.evidence) {
    if (!object(fact) || typeof fact.id !== 'string' || ids.has(fact.id)
      || !object(fact.statements) || typeof fact.statements.es !== 'string' || typeof fact.statements.en !== 'string'
      || !object(fact.values) || Object.values(fact.values).some(v => v !== null && (typeof v !== 'number' || !Number.isFinite(v)))
      || !Array.isArray(fact.event_ids) || fact.event_ids.some(id => typeof id !== 'string')
      || (fact.second !== null && (typeof fact.second !== 'number' || !Number.isInteger(fact.second) || fact.second < 0 || fact.second > request.second))) throw new Error('Invalid evidence')
    ids.add(fact.id)
  }
  for (const paragraph of value.paragraphs) {
    if (!object(paragraph) || typeof paragraph.text !== 'string' || !paragraph.text.trim()
      || !Array.isArray(paragraph.fact_ids) || paragraph.fact_ids.length === 0
      || paragraph.fact_ids.some(id => typeof id !== 'string' || !ids.has(id))) throw new Error('Uncited narrative')
  }
  return value as unknown as MatchNarrativeResponse
}

export async function fetchNarrative(request: NarrativeRequest, matchId: string, signal: AbortSignal) {
  // Bound the whole fetch + body read, including a stalled proxy connection.
  const controller = new AbortController()
  const abort = () => controller.abort()
  if (signal.aborted) abort()
  signal.addEventListener('abort', abort, { once: true })
  const timer = window.setTimeout(abort, 35000)
  try {
    const response = await fetch(`${apiBaseUrl}/api/matches/demo/narrative`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request), signal: controller.signal,
    })
    if (!response.ok) throw new Error(response.status === 429 ? 'rate_limit' : 'unavailable')
    return parseNarrative(await response.json(), request, matchId)
  } finally {
    window.clearTimeout(timer)
    signal.removeEventListener('abort', abort)
  }
}
