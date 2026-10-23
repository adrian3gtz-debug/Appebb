# Synthetic match event schema

The models in `backend/app/models/` define the common format for synthetic match data. They validate input before generation, analysis, or API presentation. They are not database tables. Later adapters may translate real provider data into this format.

## Match and field conventions

- A match has one home team and one away team. Each team has 11 players, including exactly one goalkeeper.
- Player IDs are unique across the match. An event actor belongs to the stated team.
- Field coordinates use a fixed, normalized rectangle: `x` and `y` are both 0–100. These are not metres. The orientation does not change at halftime.
- In period 1, the home team attacks toward `x = 100`; in period 2 it attacks toward `x = 0`. The away team attacks in the opposite direction.
- `second` is elapsed match time from kickoff. Period 1 covers 0–2699; period 2 covers 2700–5400. This first version models regulation time only, without stoppage time or extra time.
- Events are stored in chronological order. Equal seconds are permitted and retain list order.

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

The schema checks field bounds, allowed values, rosters, event ordering, and possession ownership. It does not yet prove that every ball movement is physically continuous or that an event sequence is tactically realistic. The synthetic generator and its tests will be responsible for those properties in the next stage.
