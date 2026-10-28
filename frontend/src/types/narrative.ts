import type { AIProvider } from './ai'
import type { Language } from '../i18n'
import type { Audience } from '../features/summary/audience'
import type { DemoScenario } from './recoveries'

export interface NarrativeRequest {
  scenario: DemoScenario
  second: number
  language: Language
  audience: Audience
}

export interface NarrativeFact {
  id: string
  statements: { es: string; en: string }
  values: Record<string, number | null>
  event_ids: string[]
  second: number | null
}

export interface MatchNarrativeResponse {
  source: 'synthetic'
  generation: AIProvider
  methodology_version: 'narrative-v1'
  match_id: string
  as_of_second: number
  phase: 'in_progress' | 'full_time'
  language: Language
  audience: Audience
  headline: string
  paragraphs: { text: string; fact_ids: string[] }[]
  evidence: NarrativeFact[]
}
