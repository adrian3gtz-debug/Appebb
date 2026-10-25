import { useEffect, useRef, useState } from 'react'
import { fetchRecoveryAnalysis } from '../../services/matches'
import type { DemoScenario, RecoveryAnalysis } from '../../types/recoveries'

// Poll at most twice per second of wall time, including during accelerated playback.
export function useRecoveryAnalysis(scenario: DemoScenario, second: number, playing: boolean) {
  const clock = useRef(second)
  clock.current = second
  const [data, setData] = useState<RecoveryAnalysis | null>(null)
  const [error, setError] = useState(false)
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let controller: AbortController | null = null
    let requested = -1
    function update() {
      const cutoff = Math.floor(clock.current)
      if (requested === cutoff) return
      requested = cutoff
      controller?.abort()
      const request = new AbortController()
      controller = request
      fetchRecoveryAnalysis(scenario, cutoff, request.signal).then(
        (result) => { if (!request.signal.aborted) { setData(result); setError(false) } },
        () => { if (!request.signal.aborted) { setError(true); requested = -1 } },
      )
    }
    update()
    const timer = window.setInterval(update, 500)
    return () => { window.clearInterval(timer); controller?.abort() }
  }, [scenario, playing, attempt])

  // A seek backwards/reset must hide future evidence immediately, before the next request.
  return { data: data && data.as_of_second <= second ? data : null, error, retry: () => setAttempt((value) => value + 1) }
}
