import type { DemoMatchResponse } from '../types/match'
import type { DemoScenario, RecoveryAnalysis } from '../types/recoveries'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? ''

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


export async function fetchRecoveryAnalysis(scenario: DemoScenario, second: number, signal: AbortSignal): Promise<RecoveryAnalysis> {
  const response = await fetch(`${apiBaseUrl}/api/matches/demo/recoveries?scenario=${scenario}&second=${second}`, { signal })
  if (!response.ok) throw new Error(`Analysis request failed: ${response.status}`)
  return response.json()
}
