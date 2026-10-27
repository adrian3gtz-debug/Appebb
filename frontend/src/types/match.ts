export interface Coordinate { x: number; y: number }
export interface Player {
  id: string
  name: string
  role: 'goalkeeper' | 'defender' | 'midfielder' | 'forward'
}
export interface Team { id: string; name: string; players: Player[] }
interface BaseEvent {
  id: string
  match_id: string
  period: 1 | 2
  second: number
  team_id: string
  player_id: string
  possession_id: string
  possession_team_id: string
  location: Coordinate
}
export type MatchEvent = BaseEvent & (
  | { type: 'pass'; end_location: Coordinate; outcome: 'complete' | 'incomplete'; receiver_id: string | null;
      pass_context?: 'open_play' | 'kickoff' | 'throw_in' | 'goal_kick' | 'corner' | 'free_kick' | null }
  | { type: 'carry'; end_location: Coordinate }
  | { type: 'recovery'; method: 'interception' | 'tackle' | 'loose_ball' | 'goalkeeper_claim' }
  | { type: 'pressure'; target_player_id: string }
  | { type: 'shot'; outcome: 'goal' | 'saved' | 'off_target' | 'blocked' }
)
export interface Match {
  id: string
  home_team: Team
  away_team: Team
  events: MatchEvent[]
  ball_states: {
    start_second: number
    end_second: number
    state: 'controlled' | 'contested' | 'out_of_play'
    team_id: string | null
  }[]
}
export interface DemoMatchResponse {
  source: 'synthetic'
  duration_seconds: number
  match: Match
}
