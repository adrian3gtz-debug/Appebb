import { useEffect, useReducer } from 'react'
import { initialPlayback, playbackReducer } from './playback'

export function usePlayback(duration: number) {
  const [state, dispatch] = useReducer(playbackReducer, initialPlayback)

  useEffect(() => {
    if (!state.playing) return
    let previous = performance.now()
    const timer = window.setInterval(() => {
      const now = performance.now()
      dispatch({ type: 'tick', elapsed: (now - previous) / 1000, duration })
      previous = now
    }, 100)
    return () => window.clearInterval(timer)
  }, [state.playing, state.speed, duration])

  return { ...state, dispatch }
}
