import { useEffect, useRef, useState } from 'react'
import { fetchMatchAnalysis } from '../../services/matches'
import type { DemoScenario } from '../../types/recoveries'
import type { MatchAnalysis } from '../../types/statistics'

export function useMatchAnalysis(scenario: DemoScenario, second: number, playing: boolean) {
  const clock = useRef(second)
  clock.current = second
  const [snapshot, setSnapshot] = useState<{ scenario: DemoScenario; data: MatchAnalysis } | null>(null)
  const [error, setError] = useState(false)
  const [attempt, setAttempt] = useState(0)
  const pausedSecond = playing ? null : Math.floor(second)

  useEffect(() => {
    const controller = new AbortController()
    let requested = -1
    let inFlight = false
    setError(false)
    async function update() {
      const cutoff = Math.floor(clock.current)
      if (inFlight || requested === cutoff) return
      requested = cutoff
      inFlight = true
      try {
        const data = await fetchMatchAnalysis(scenario, cutoff, controller.signal)
        if (!controller.signal.aborted) {
          setSnapshot({ scenario, data })
          setError(false)
        }
      } catch {
        if (!controller.signal.aborted) { setError(true); requested = -1 }
      } finally {
        inFlight = false
      }
    }
    void update()
    // One request feeds both panels. Let slow responses finish instead of repeatedly aborting them.
    const timer = window.setInterval(() => { void update() }, 500)
    return () => { window.clearInterval(timer); controller.abort() }
  }, [scenario, playing, pausedSecond, attempt])

  const data = snapshot?.scenario === scenario && snapshot.data.as_of_second <= second ? snapshot.data : null
  return { data, error, retry: () => setAttempt((value) => value + 1) }
}
