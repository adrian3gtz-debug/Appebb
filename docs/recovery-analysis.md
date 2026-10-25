# Recovery-to-attack analysis, version 1

This feature answers two observable questions: where a team won possession, and whether the resulting possession reached a recorded shot. It describes synthetic events, not inferred formations or coaching instructions. No AI or external service is used; the UI renders bilingual templates from structured Python evidence.

## Definitions

Coordinates remain fixed to the pitch as described in [event-schema.md](event-schema.md). Convert event x into distance along the team's attacking direction:

- Home, period 1; away, period 2: `attacking_x = x`.
- Home, period 2; away, period 1: `attacking_x = 100 - x`.

A **high recovery** is a `recovery` event with `attacking_x >= 200/3`. The boundary is included; these are normalized units, not metres. The analyzer uses the match's team IDs, not literal strings such as `home`.

A **sequence** begins at that recovery and follows the same possession ID. It ends at the first recorded shot, incomplete pass, change of possession, loss of controlled ball state (including contested time), out-of-play interval, or half end, whichever occurs first. Opposing pressure events sharing the possession ID do not themselves end it. A blocked shot counts as a shot; a rebound is not a second successful recovery-to-shot sequence. There is no arbitrary maximum number of seconds. `seconds_to_shot` is the difference between the recorded shot and recovery timestamps, not a measured physical speed.

At replay time `t`, only events with `second <= t` may appear in evidence. If the sequence has not ended by then, its status is `in_progress`. The API returns event IDs, termination status, shot ID and elapsed time so the drawing and text can be traced to original records. The map displays recovery locations, recorded pass/carry endpoints and shot locations. It does not reconstruct unobserved player movement or ball trajectories.

## Closed-window comparisons

Compare adjacent, non-overlapping ten-minute windows within each half. First-half windows start at 00:00; second-half windows start at 45:00. Comparisons become available at 20:00, 30:00, 40:00, 65:00, 75:00 and 85:00. The final five minutes of each half are available as individual sequences but not included in a complete ten-minute comparison. Nothing compares across halftime.

Windows use `[start, end)`. Every recovery belongs to exactly one window. Counts are frozen using observations before that window ends: a recovery at 09:59 followed by a shot at 10:00 is one high recovery and one **pending** sequence in 00:00–10:00, with zero shots observed in that window. The individual sequence will show the shot once replay reaches 10:00, while the historical comparison stays unchanged. This avoids using future outcomes and exposes incomplete observations.

For each team/window return:

- all recorded recoveries;
- recoveries in the attacking last third;
- number of those high-recovery sequences reaching a first shot before close;
- number still in progress at close.

Other closed sequences did not reach a shot under this definition. Raw counts use equal match-clock duration, which includes stoppages; they are not rates per possession or per minute out of possession. Higher recovery counts can reflect more opportunities to recover, not necessarily more effective pressing.

## Highlighting rule

For previous count `p` and current count `c`, highlight an increase only if:

- `c >= 4`;
- `c - p >= 3`;
- when `p > 0`, `c >= 2 * p`.

With `p = 0`, omit the ratio test; do not report an infinite percentage increase. These are explicit editorial defaults in `RecoveryRules`, not statistically validated thresholds or a significance test. The response includes the rule version and settings. No highlight means no increase met this rule, not that nothing tactically important happened.

An insight contains a stable ID within its match, team, detection second, both count snapshots and the current window's recovery event IDs. Increased recoveries can be highlighted with **zero** resulting shots: the text always reports the observed shot count independently. A shot does not establish chance quality, and pressure preceding an interception does not prove causation.

## Counterfactual test scenarios

`generate_recovery_scenario(scenario, seed=7)` builds three full-length authored fixtures:

| Generator selection | High recoveries, 00:00–10:00 → 10:00–20:00 | Shots from later-window high recoveries |
| --- | --- | --- |
| `stable` | 1 → 1 | 0 |
| `higher_recoveries` | 1 → 6 | 3 |
| `recoveries_without_shots` | 1 → 6 | 0 |

These are outputs of authored synthetic scenarios, never real-match claims. Each minute has linked possessions, an interception, passes/carries and a shot or turnover, with explicit dead-ball time and valid restarts. The construction switches direction at halftime; the increase repeats within the second half. Seeds vary coordinates; they do not change the expected behavior. Teams have eleven players each. The match payload contains opaque deterministic match IDs, shared fictional rosters, and no scenario label or expected statistics. Tests also anonymize the match identity to verify that it cannot drive the result. The selection parameter remains at the repository/API boundary; `analyze_recoveries` accepts only `Match`, time and numerical rules.

These fixtures test detection and counterexamples, not population realism. Regular one-minute blocks, fixed roles/actions and authored outcomes do not reproduce professional match distributions. The original circulation/counterattack fixture remains available unchanged. More diverse scenarios and calibration require further work.

## API and browser

- `GET /api/matches/demo?scenario=higher_recoveries`: full validated synthetic match.
- `GET /api/matches/demo/recoveries?scenario=higher_recoveries&second=1200`: evidence through 20:00.
- Other selections: `stable`, `recoveries_without_shots`, `original`. The API defaults to `original` for compatibility; the UI starts with `higher_recoveries` to demonstrate analysis.
- Invalid selections/times return 422; unreadable/invalid original fixture returns 503.

The browser requests evidence at most every 500 ms during normal polling, skips unchanged seconds and cancels replaced requests. It displays the actual evidence timestamp. Pausing refreshes the evidence immediately; going backwards hides any future snapshot before the replacement arrives. Changing scenarios resets playback, even though these counterfactual fixtures share a match ID. EN/ES changes preserve the current playback/selection. The timeline slider pauses at the selected second.

## Verification

Run `pytest` in `backend/`, and `npm test` / `npm run build` in `frontend/`.

Tests exercise the three contrasts across seeds, both teams' halftime directions with arbitrary IDs, inclusive last-third boundary, incomplete passes, possession changes, dead-ball intervals, first-shot counting, live visibility, frozen window boundaries, minimum counts, reproducibility, movement/receiver continuity and API validation.

Manual browser check: select **More high recoveries**, move the timeline to **20:00**, inspect the **1 → 6 / 3 shots** comparison, and select **12:15** to inspect its recovery, pass, carry and shot. Repeat with **Stable recoveries** (no highlight) and **More recoveries, no shots** (1 → 6 / 0 shots). Test restart, halftime, EN/ES, and a mobile viewport.
