import type { DemoMatchResponse } from '../types/match'
import type { DemoScenario } from '../types/recoveries'
import type { MatchAnalysis } from '../types/statistics'
import { apiBaseUrl } from './api'

export async function fetchDemoMatch(signal: AbortSignal, scenario: DemoScenario = 'original'): Promise<DemoMatchResponse> {
  const response = await fetch(`${apiBaseUrl}/api/matches/demo?scenario=${scenario}`, { signal })
  if (!response.ok) throw new Error(`Match request failed: ${response.status}`)
  // The API validates this payload against its Pydantic response model.
  const data: DemoMatchResponse = await response.json()
  if (data.source !== 'synthetic' || data.duration_seconds <= 0 || !Array.isArray(data.match?.events)) {
    throw new Error('Unexpected match response')
  }
  return data
}


export async function fetchMatchAnalysis(scenario: DemoScenario, second: number, signal: AbortSignal): Promise<MatchAnalysis> {
  const response = await fetch(`${apiBaseUrl}/api/matches/demo/analysis?scenario=${scenario}&second=${second}`, { signal })
  if (!response.ok) throw new Error(`Analysis request failed: ${response.status}`)
  return response.json()
}
