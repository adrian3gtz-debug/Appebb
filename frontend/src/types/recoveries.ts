export type DemoScenario = 'original' | 'stable' | 'higher_recoveries' | 'recoveries_without_shots'
export interface RecoverySequence {
  recovery_event_id: string
  team_id: string
  period: number
  start_second: number
  possession_id: string
  event_ids: string[]
  status: 'shot' | 'lost' | 'out_of_play' | 'period_end' | 'in_progress'
  end_second: number | null
  shot_event_id: string | null
  seconds_to_shot: number | null
}
export interface RecoveryWindow {
  start_second: number
  end_second: number
  total_recoveries: number
  high_recoveries: number
  shot_sequences: number
  pending_sequences: number
}
export interface RecoveryComparison {
  team_id: string
  period: number
  previous: RecoveryWindow
  current: RecoveryWindow
}
export interface RecoveryInsight extends RecoveryComparison {
  id: string
  type: 'high_recovery_increase'
  detected_second: number
  recovery_event_ids: string[]
}
export interface RecoveryAnalysis {
  match_id: string
  as_of_second: number
  rules: {
    version: string
    window_seconds: number
    high_recovery_x: number
    minimum_current: number
    minimum_increase: number
    minimum_ratio: number
  }
  sequences: RecoverySequence[]
  comparisons: RecoveryComparison[]
  insights: RecoveryInsight[]
}
