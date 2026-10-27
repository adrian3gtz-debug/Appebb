import type { Language } from '../../i18n'
import type { Match } from '../../types/match'
import type { MatchRecap } from '../../types/recap'
import type { MatchStatistics } from '../../types/statistics'
import { teamLabel } from '../replay/displayNames'
import type { Audience } from './audience'
import { summaryCopy } from './copy'

export function summaryNarrative(match: Match, stats: MatchStatistics, recap: MatchRecap, language: Language, audience: Audience) {
  const copy = summaryCopy[language]
  const home = teamLabel(match.home_team.name)
  const away = teamLabel(match.away_team.name)
  const h = stats.home.goals
  const a = stats.away.goals
  const final = recap.phase === 'full_time'
  const headline = h === a ? (final ? copy.drawn : copy.level)(`${h}–${a}`)
    : (final ? copy.won : copy.leads)(h > a ? home : away, h > a ? `${h}–${a}` : `${a}–${h}`)
  const contrast = recap.control_shots_contrast
  let observation: string | null = null
  if (contrast) {
    const team = contrast.team_id === match.home_team.id ? home : away
    const other = contrast.opponent_team_id === match.home_team.id ? home : away
    observation = audience === 'fan' ? copy.fanContrast(team, other)
      : copy.analystContrast(team, contrast.controlled_seconds, contrast.shots, other,
        contrast.opponent_controlled_seconds, contrast.opponent_shots)
  }
  return { headline, shots: copy.shots(home, away, stats.home.shots, stats.away.shots), observation }
}
