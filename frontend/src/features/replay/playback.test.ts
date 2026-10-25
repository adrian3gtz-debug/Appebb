import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import type { Match } from '../../types/match'
import { formatClock, initialPlayback, matchAt, playbackReducer } from './playback'

const match: Match = JSON.parse(readFileSync(new URL('../../../../data/synthetic/circulation-vs-counterattack.json', import.meta.url), 'utf8'))

describe('playback clock', () => {
  it('starts paused and does not advance until started', () => {
    expect(playbackReducer(initialPlayback, { type: 'tick', elapsed: 10, duration: 5400 })).toEqual(initialPlayback)
    const playing = playbackReducer(initialPlayback, { type: 'toggle', duration: 5400 })
    expect(playbackReducer(playing, { type: 'tick', elapsed: 2, duration: 5400 }).second).toBe(120)
  })
  it('pauses, resumes and changes speed without resetting time', () => {
    let state = { second: 600, speed: 60, playing: true }
    state = playbackReducer(state, { type: 'toggle', duration: 5400 })
    state = playbackReducer(state, { type: 'tick', elapsed: 50, duration: 5400 })
    expect(state.second).toBe(600)
    state = playbackReducer(state, { type: 'speed', speed: 10 })
    state = playbackReducer(state, { type: 'toggle', duration: 5400 })
    state = playbackReducer(state, { type: 'tick', elapsed: 2, duration: 5400 })
    expect(state.second).toBe(620)
  })
  it('clamps at full time and cannot resume without resetting', () => {
    const ended = playbackReducer({ second: 5399, speed: 60, playing: true }, { type: 'tick', elapsed: 2, duration: 5400 })
    expect(ended).toEqual({ second: 5400, speed: 60, playing: false })
    expect(playbackReducer(ended, { type: 'toggle', duration: 5400 })).toEqual(ended)
    expect(playbackReducer(ended, { type: 'reset' })).toEqual(initialPlayback)
  })
  it('resets during play, preserving the chosen speed', () => {
    expect(playbackReducer({ second: 400, speed: 10, playing: true }, { type: 'reset' })).toEqual({ second: 0, speed: 10, playing: false })
  })
  it('seeks to a bounded time and pauses playback for inspection', () => {
    const playing = { second: 100, speed: 30, playing: true }
    expect(playbackReducer(playing, { type: 'seek', second: 1200, duration: 5400 })).toEqual({ second: 1200, speed: 30, playing: false })
    expect(playbackReducer(playing, { type: 'seek', second: -10, duration: 5400 }).second).toBe(0)
    expect(playbackReducer(playing, { type: 'seek', second: 6000, duration: 5400 }).second).toBe(5400)
  })
  it('formats period boundaries without restarting the match clock', () => {
    expect(formatClock(2699.9)).toBe('44:59')
    expect(formatClock(2700)).toBe('45:00')
    expect(formatClock(5400)).toBe('90:00')
  })
})

describe('visible match events', () => {
  it('hides each goal until its exact timestamp', () => {
    const goals = match.events.filter((event) => event.type === 'shot' && event.outcome === 'goal')
    expect(goals.length).toBe(2)
    goals.forEach((goal, index) => {
      expect(matchAt(match, goal.second - 0.01).awayScore).toBe(index)
      expect(matchAt(match, goal.second).awayScore).toBe(index + 1)
    })
  })
  it('shows only the latest eight past events in reverse order', () => {
    const visible = matchAt(match, 1200)
    expect(visible.recentEvents).toHaveLength(8)
    expect(visible.recentEvents.every((event) => event.second <= 1200)).toBe(true)
    expect(visible.recentEvents.map((event) => event.second)).toEqual(visible.recentEvents.map((event) => event.second).sort((a, b) => b - a))
  })
  it('starts at 0–0 and ends with the recorded result', () => {
    expect(matchAt(match, 0)).toMatchObject({ homeScore: 0, awayScore: 0 })
    expect(matchAt(match, 5400)).toMatchObject({ homeScore: 0, awayScore: 2 })
    expect(matchAt(match, 0).recentEvents).toEqual(match.events.filter((event) => event.second === 0).reverse().slice(0, 8))
  })
})
