# Match statistics v1

The panel describes recorded synthetic actions and ball-control time. It does not assign dominance, chance quality, pressure effectiveness or an overall performance score.

## Observation boundary

`calculate_statistics(match, second)` includes events with `event.second <= second`. The schema records each action and its outcome at a single timestamp; this timestamp is treated as the availability time of that outcome. The current feed does not model separate pass-release and pass-arrival messages.

Control intervals use `[start, end)`. Only their intersection with `[0, second)` contributes time. An event at kickoff can be counted with zero elapsed controlled time. Historical results are independent of later events and control time. A complete `ball_states` timeline is required for possession; an event-only match returns `possession: null` while retaining observable counts.

## Definitions

| Output | Calculation | Interpretation limit |
| --- | --- | --- |
| Passes attempted | Number of pass events | Includes restarts represented as passes in the current generator. |
| Passes completed | Pass events with outcome `complete` | Backward and lateral completions count equally. |
| Pass accuracy | 100 × completed / attempted | Null with no attempts. Does not measure difficulty or progression. |
| Possession | 100 × team controlled seconds / both teams' controlled seconds | Null when the denominator is zero. No inference from pass counts. |
| Contested / out-of-play time | Sum of clipped intervals of each state | Assigned to neither team and excluded from possession percentages. |
| Shots | Number of shot events | No estimate of chance quality. |
| Shot breakdown | Mutually exclusive goal, saved, off-target and blocked counts | Sum equals total shots. This version does not derive a provider-specific shots-on-target definition. |

Possession follows the generator's control convention, including pass flight until recovery or the ball going out. The percentages are exact for this synthetic timeline, not claims about real possession from sparse events. Rates are calculated before display rounding; the UI uses one decimal place and locale-aware formatting. `0` and unavailable (`—`) are distinct.

## API and UI

`GET /api/matches/demo/analysis?scenario=original&second=1200` returns `source`, `match_id`, `as_of_second`, `statistics` (methodology `statistics-v1`) and `recoveries`, all from one match and cutoff. The existing `/recoveries` endpoint remains available.

The browser shares one polling loop between both panels, with a 500 ms interval, at most one in-flight request, and no repeated request for an unchanged second after success. A slow response is allowed to finish; the displayed timestamp identifies its actual observation time. Pausing/seeking cancels replaced work. A snapshot from another scenario or from the future is hidden. Failures show a retry control while retaining any valid, explicitly timestamped previous snapshot.

## Verification

- Hand-counted fixtures verify partial control intervals, exact event boundaries, no attempts, missing possession data, halftime, all shot outcomes and the final clock.
- Future-event and future-control changes must not change an earlier result. Computing a full match before rewinding must also leave earlier results unchanged.
- The circulation/counterattack fixture must keep its higher-possession team below the opponent in shots and goals. No tactical narrative is inferred from this contrast alone.
- API tests check all four scenarios, a shared observation cutoff and invalid queries.
- Browser checks cover EN/ES, resets, seeking, error/retry, slow responses, and mobile width.

Run `python -m pytest` in `backend/`, then `npm test` and `npm run build` in `frontend/`. In the browser select **Circulation vs counterattack**, seek to 90:00, inspect the statistics and shot breakdown, then rewind to 00:00 and verify that future counts disappear.

The next research-informed steps and their data requirements are documented in [the research notes](football-analytics-research.md).
