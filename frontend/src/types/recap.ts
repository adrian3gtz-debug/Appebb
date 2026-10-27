export interface MatchRecap {
  methodology_version: 'recap-v1'
  generation: 'rules'
  match_id: string
  as_of_second: number
  phase: 'in_progress' | 'full_time'
  goals: {
    event_id: string
    team_id: string
    player_id: string
    second: number
    home_score: number
    away_score: number
  }[]
  control_shots_contrast: {
    team_id: string
    opponent_team_id: string
    controlled_seconds: number
    opponent_controlled_seconds: number
    shots: number
    opponent_shots: number
  } | null
}
