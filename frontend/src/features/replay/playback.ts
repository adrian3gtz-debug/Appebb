import type { Match } from '../../types/match'

export interface PlaybackState { second: number; playing: boolean; speed: number }
export const initialPlayback: PlaybackState = { second: 0, playing: false, speed: 60 }
export type PlaybackAction =
  | { type: 'toggle'; duration: number }
  | { type: 'tick'; elapsed: number; duration: number }
  | { type: 'speed'; speed: number }
  | { type: 'reset' }

export function playbackReducer(state: PlaybackState, action: PlaybackAction): PlaybackState {
  switch (action.type) {
    case 'toggle':
      return state.second >= action.duration ? state : { ...state, playing: !state.playing }
    case 'speed':
      return { ...state, speed: action.speed }
    case 'reset':
      return { ...state, second: 0, playing: false }
    case 'tick': {
      if (!state.playing) return state
      const second = Math.min(action.duration, state.second + Math.max(0, action.elapsed) * state.speed)
      return { ...state, second, playing: second < action.duration }
    }
  }
}

export function matchAt(match: Match, second: number) {
  const events = match.events.filter((event) => event.second <= second)
  const goals = events.filter((event) => event.type === 'shot' && event.outcome === 'goal')
  return {
    homeScore: goals.filter((event) => event.team_id === match.home_team.id).length,
    awayScore: goals.filter((event) => event.team_id === match.away_team.id).length,
    recentEvents: events.slice(-8).reverse(),
  }
}

export function formatClock(second: number): string {
  const whole = Math.floor(second)
  return `${String(Math.floor(whole / 60)).padStart(2, '0')}:${String(whole % 60).padStart(2, '0')}`
}
