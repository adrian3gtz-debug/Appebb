import type { RecoveryAnalysis } from './recoveries'
import type { MatchRecap } from './recap'

export interface TeamStatistics {
  team_id: string
  passes_attempted: number
  passes_completed: number
  pass_accuracy_percent: number | null
  shots: number
  goals: number
  shots_saved: number
  shots_off_target: number
  shots_blocked: number
}

export interface MatchStatistics {
  match_id: string
  as_of_second: number
  methodology_version: 'statistics-v1'
  home: TeamStatistics
  away: TeamStatistics
  possession: {
    home_seconds: number
    away_seconds: number
    contested_seconds: number
    out_of_play_seconds: number
    home_share_percent: number | null
    away_share_percent: number | null
  } | null
}

export interface MatchAnalysis {
  source: 'synthetic'
  match_id: string
  as_of_second: number
  statistics: MatchStatistics
  recoveries: RecoveryAnalysis
  recap?: MatchRecap
}
