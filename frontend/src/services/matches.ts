import type { DemoMatchResponse } from '../types/match'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? ''

export async function fetchDemoMatch(signal: AbortSignal): Promise<DemoMatchResponse> {
  const response = await fetch(`${apiBaseUrl}/api/matches/demo`, { signal })
  if (!response.ok) throw new Error(`Match request failed: ${response.status}`)
  // The API validates this payload against its Pydantic response model.
  const data: DemoMatchResponse = await response.json()
  if (data.source !== 'synthetic' || data.duration_seconds <= 0 || !Array.isArray(data.match?.events)) {
    throw new Error('Unexpected match response')
  }
  return data
}
