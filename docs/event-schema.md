# Synthetic match event schema

The models in `backend/app/models/` define the common format for synthetic match data. They validate input before generation, analysis, or API presentation. They are not database tables. Later adapters may translate real provider data into this format.

## Match and field conventions

- A match has one home team and one away team. Each team has 11 players, including exactly one goalkeeper.
- Player IDs are unique across the match. An event actor belongs to the stated team.
- Field coordinates use a fixed, normalized rectangle: `x` and `y` are both 0–100. These are not metres. The orientation does not change at halftime.
- In period 1, the home team attacks toward `x = 100`; in period 2 it attacks toward `x = 0`. The away team attacks in the opposite direction.
- `second` is elapsed match time from kickoff. Period 1 covers 0–2699; period 2 covers 2700–5399. The clock boundary at 5400 ends regulation time and cannot contain an action. This first version models regulation time only, without stoppage time or extra time.
- Events are stored in chronological order. Equal seconds are permitted and retain list order.

## Ball-control timeline and possession time

`ball_states` is a separate, optional list of intervals. Each interval has `start_second`, `end_second`, `state`, and (only for `controlled`) `team_id`. States are `controlled`, `contested`, and `out_of_play`. Intervals are half-open: `[start_second, end_second)`, so a change at second 100 belongs to the interval starting at 100.

If a timeline is present, it must cover seconds 0–5400 in order, without gaps or overlaps. A recorded event must occur during a `controlled` interval for its `possession_team_id`. An event-only match remains valid, but its possession time cannot be calculated.

`calculate_possession` adds each team's controlled seconds. Home and away percentages use **home controlled seconds + away controlled seconds** as the denominator. Contested and out-of-play seconds are reported separately and assigned to neither team. If neither team controls the ball, both percentages are unavailable rather than invented. These values are exact only within a complete synthetic timeline; sparse event logs alone cannot establish real possession duration.

## Event fields

Every event contains `id`, `match_id`, `type`, `period`, `second`, `team_id`, `player_id`, `possession_id`, `possession_team_id`, and `location`.

`possession_team_id` names the team with the ball *at that event*. It is the acting team for passes, carries, recoveries, and shots. A pressure event is performed by the opposing team while the ball remains with `possession_team_id`. A recovery starts a new possession ID for the team that gained the ball. Events sharing a possession ID must be consecutive and have the same owner.

| Type | Additional fields | Meaning |
| --- | --- | --- |
| `pass` | `end_location`, `outcome`, `receiver_id` | `outcome` is `complete` or `incomplete`. Completed passes require a receiver on the passing team. |
| `carry` | `end_location` | Movement by a player with the ball. |
| `recovery` | `method` | Gaining possession by `interception`, `tackle`, `loose_ball`, or `goalkeeper_claim`. |
| `pressure` | `target_player_id` | A recorded pressure action against a player on the team in possession. It does not, alone, establish a team-wide pressing pattern. |
| `shot` | `outcome` | `goal`, `saved`, `off_target`, or `blocked`. No expected-goals value is assigned. |

An illustrative sequence has an away possession with home pressure, followed by a home recovery with a new possession ID, a completed pass, a carry, and a saved shot. The corresponding validation example is in `backend/tests/test_match_models.py`. It is an example of structure, not a real match or a generated scenario.

The schema checks field bounds, allowed values, rosters, event ordering, and possession ownership. It does not yet prove that every ball movement is physically continuous or that an event sequence is tactically realistic. The synthetic generators and their tests check continuity and selected plausibility bounds; see [the original scenario](synthetic-scenario.md) and [recovery analysis](recovery-analysis.md) for their scope and limitations.
