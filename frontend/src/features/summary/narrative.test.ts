import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import type { Match } from '../../types/match'
import type { MatchStatistics } from '../../types/statistics'
import type { MatchRecap } from '../../types/recap'
import { summaryNarrative } from './narrative'

const match: Match = JSON.parse(readFileSync(new URL('../../../../data/synthetic/circulation-vs-counterattack.json', import.meta.url), 'utf8'))
const stats: MatchStatistics = {
  match_id: match.id, as_of_second: 5400, methodology_version: 'statistics-v1', possession: null,
  home: { team_id: match.home_team.id, passes_attempted: 100, passes_completed: 80, pass_accuracy_percent: 80, goals: 0, shots: 3, shots_saved: 1, shots_off_target: 1, shots_blocked: 1 },
  away: { team_id: match.away_team.id, passes_attempted: 50, passes_completed: 30, pass_accuracy_percent: 60, goals: 2, shots: 5, shots_saved: 1, shots_off_target: 1, shots_blocked: 1 },
}
const recap: MatchRecap = { methodology_version: 'recap-v1', generation: 'rules', match_id: match.id, as_of_second: 5400, phase: 'full_time', goals: [], control_shots_contrast: null }

describe('time-bounded match narrative', () => {
  it('uses winner-relative score for an away win and distinguishes live from final', () => {
    const final = summaryNarrative(match, stats, recap, 'en', 'fan')
    expect(final.headline).toContain('won 2–0')
    const live = summaryNarrative(match, stats, { ...recap, phase: 'in_progress' }, 'en', 'fan')
    expect(live.headline).toContain('lead 2–0')
    expect(live.headline).not.toContain('won')
  })
  it('handles draws without declaring a winner', () => {
    const tied = { ...stats, away: { ...stats.away, goals: 0 } }
    expect(summaryNarrative(match, tied, recap, 'es', 'fan').headline).toBe('El partido terminó empatado 0–0.')
    expect(summaryNarrative(match, tied, { ...recap, phase: 'in_progress' }, 'es', 'analyst').headline).toBe('El partido está empatado 0–0.')
  })
  it('changes detail for audiences while retaining the same score and shot facts', () => {
    const evidence = { ...recap, control_shots_contrast: { team_id: match.home_team.id, opponent_team_id: match.away_team.id, controlled_seconds: 3000, opponent_controlled_seconds: 1000, shots: 3, opponent_shots: 5 } }
    const fan = summaryNarrative(match, stats, evidence, 'es', 'fan')
    const analyst = summaryNarrative(match, stats, evidence, 'es', 'analyst')
    expect(fan.headline).toBe(analyst.headline)
    expect(fan.shots).toBe(analyst.shots)
    expect(fan.observation).toContain('ha tenido el balón')
    expect(fan.observation).not.toContain('3000')
    expect(analyst.observation).toContain('3000s de control y 3 tiros')
  })
  it('emits no control observation when the API supplies none', () => {
    expect(summaryNarrative(match, stats, recap, 'en', 'fan').observation).toBeNull()
  })
})
