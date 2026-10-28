import { afterEach, describe, expect, it, vi } from 'vitest'
import type { Match } from '../../types/match'
import type { NarrativeRequest } from '../../types/narrative'
import { fetchNarrative, narrativeCheckpoint, parseNarrative } from './narrativeRequest'
import { providerLabel } from '../../types/ai'
import { narrativeCopy } from './narrativeCopy'

const request: NarrativeRequest = { scenario: 'original', second: 1200, language: 'es', audience: 'fan' }
const response = {
  source: 'synthetic', generation: 'azure_openai', methodology_version: 'narrative-v1',
  match_id: 'match', as_of_second: 1200, phase: 'in_progress', language: 'es', audience: 'fan',
  headline: 'Partido en juego', paragraphs: [
    { text: 'Marcador observado.', fact_ids: ['score'] }, { text: 'Remates observados.', fact_ids: ['shots'] },
  ], evidence: ['score', 'shots'].map(id => ({ id, statements: { es: 'Hecho', en: 'Fact' }, values: {}, event_ids: [], second: null })),
}

afterEach(() => { vi.unstubAllGlobals(); vi.useRealTimers() })

describe('narrative evidence boundary', () => {
  it('accepts Groq and labels the provider that actually generated the response', () => {
    for (const generation of ['groq', 'azure_openai'] as const) {
      const parsed = parseNarrative({ ...response, generation }, request, 'match')
      const note = narrativeCopy.es.note(providerLabel(parsed.generation))
      expect(note).toContain(generation === 'groq' ? 'Groq' : 'Microsoft Foundry')
      if (generation === 'groq') expect(note).not.toContain('Microsoft Foundry')
    }
    expect(() => parseNarrative({ ...response, generation: 'unknown' }, request, 'match')).toThrow()
  })
  it('accepts the requested context and rejects a final/future or unrelated response', () => {
    expect(parseNarrative(response, request, 'match').as_of_second).toBe(1200)
    for (const mutation of [{ match_id: 'other' }, { as_of_second: 5400 }, { phase: 'full_time' }, { language: 'en' }, { audience: 'analyst' }, { generation: 'rules' }]) {
      expect(() => parseNarrative({ ...response, ...mutation }, request, 'match')).toThrow()
    }
  })
  it('rejects unknown citations and future goal references', () => {
    expect(() => parseNarrative({ ...response, paragraphs: [{ text: 'Invented', fact_ids: ['future'] }, response.paragraphs[1]] }, request, 'match')).toThrow()
    expect(() => parseNarrative({ ...response, evidence: [{ ...response.evidence[0], second: 1500 }] }, request, 'match')).toThrow()
  })
  it('updates only at closed ten-minute boundaries, goals, half-time and full time', () => {
    const match = { events: [{ type: 'shot', outcome: 'goal', second: 705 }, { type: 'shot', outcome: 'goal', second: 3000 }] } as unknown as Match
    expect(narrativeCheckpoint(match, 599)).toBe(0)
    expect(narrativeCheckpoint(match, 600)).toBe(600)
    expect(narrativeCheckpoint(match, 704)).toBe(600)
    expect(narrativeCheckpoint(match, 705)).toBe(705)
    expect(narrativeCheckpoint(match, 1200)).toBe(1200)
    expect(narrativeCheckpoint(match, 2700)).toBe(2700)
    expect(narrativeCheckpoint(match, 3000)).toBe(3000)
    expect(narrativeCheckpoint(match, 5400)).toBe(5400)
    expect(narrativeCheckpoint(match, 704)).toBe(600)
  })
})

describe('bounded narrative fetch', () => {
  function hangingFetch() {
    vi.stubGlobal('window', globalThis)
    vi.stubGlobal('fetch', vi.fn((_url, options) => new Promise((_resolve, reject) => {
      if (options.signal.aborted) reject(new DOMException('Aborted', 'AbortError'))
      options.signal.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')), { once: true })
    })))
  }
  it('ends a hung request instead of loading forever', async () => {
    vi.useFakeTimers(); hangingFetch()
    const promise = fetchNarrative(request, 'match', new AbortController().signal)
    const failed = expect(promise).rejects.toThrow('Aborted')
    await vi.advanceTimersByTimeAsync(35000)
    await failed
    expect(vi.getTimerCount()).toBe(0)
  })
  it('aborts on rewind/unmount and clears its timeout', async () => {
    vi.useFakeTimers(); hangingFetch()
    const controller = new AbortController()
    const failed = expect(fetchNarrative(request, 'match', controller.signal)).rejects.toThrow('Aborted')
    controller.abort(); await failed
    expect(vi.getTimerCount()).toBe(0)
  })
})
