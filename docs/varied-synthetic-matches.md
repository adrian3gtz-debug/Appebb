# Varied synthetic matches — version 1

This generator replaces fixed-length blocks for the exploratory demo. It produces a seeded sequence of linked possessions with variable duration and outcomes. It is **not calibrated to professional match distributions**. The older authored fixtures remain regression tests, with their existing expected results.

## State and action model

The process starts each half at the centre, with home then away kickoff. Each possession chooses a pattern using its starting field zone, whether it began with a recovery and a sampled team tendency:

- **Circulation:** backward, near-lateral and forward options, particularly during deeper buildup.
- **Progression:** more frequent forward movements, with losses possible before a shot.
- **Wide play:** movement toward a flank, then possible central combinations/cutbacks in advanced zones.
- **Transition:** available after selected recoveries, with more direct movements and shorter decision times.

Pattern names are generator internals. They are not emitted as tactical labels, and the analyzer receives only the common `Match`. A pattern does not guarantee a shot or goal. The generator does not prescribe a winner, a final possession percentage or a minimum number of insights.

At each step, the current ball zone and possession context determine available actions. Pressure can accompany an opposing action; pass failure depends on distance, advanced destination and simulated pressure. Pass endpoints become the next receiver's action location. Carries keep the same ball holder. An incomplete pass or tackle can produce a recovery at the endpoint, optionally after contested time. A pass going out produces explicit dead-ball time followed by an opposing throw-in represented as a pass.

Shots are available in advanced locations, with four possible outcomes. Goals lead to an opposing centre kickoff; off-target shots to an opposing goalkeeper restart; saves to a goalkeeper claim; blocked shots to a contested interval and opposing loose-ball recovery. The last case deliberately omits same-team rebounds and corners in this version.

Transitions have sampled durations, rather than advancing in equal blocks. Actions that would cross halftime are not emitted. Ball-state intervals cover the full 5,400-second clock without gaps or overlap. Each half ends independently, including when an action would finish near its boundary. No added time is modeled.

## Explicit assumptions, not fitted football rates

The implementation is `backend/app/services/varied_generator.py`, version `varied-v1`. These defaults are engineering assumptions for coherent synthetic examples:

| Choice | Current rule |
| --- | --- |
| Pitch | Fixed coordinates 0–100; hypothetical dimensions 105 × 68 m for travel plausibility. Teams reverse attack direction at halftime. |
| Team tendencies | Directness weight sampled in 0.35–0.65; pressure-action tendency in 0.12–0.30. They do not describe real teams. |
| Forward choice | Base probability 0.40 for circulation, 0.78 for transition, 0.66 otherwise; space near the goal lines changes these choices. Some passes explicitly select near-lateral movement. |
| Travel time | Distance / sampled speed, rounded up, plus variable decision time. Carry speeds sampled in 3.5–6.5 m/s; pass speeds in 12–23 m/s. These are simulation inputs, not measured physical quantities. |
| Pass failure | `0.04 + assumed_distance_m / 260 + 0.10 if pressured + 0.05 if destination is beyond attacking x=65`. This is a heuristic, not a pass-completion model trained on data. |
| Shooting | Possible from attacking x≥68 and within 32 normalized y units of the centre. Choice probabilities rise with x. This omits very long shots and many contextual factors. |
| Shot outcomes | Goal weight depends on x and lateral position, bounded to 0.025–0.14; other outcomes are sampled from explicit weights. These weights are **not xG**, are not returned as chance-quality estimates, and have no scientific validation. |
| Interruption time | Sampled throw-in, goalkeeper-restart, goal-celebration and contested intervals. No fouls, offside, substitutions or injury stoppages. |

The schema treats an action's result as available at its recorded timestamp, while control includes the modeled flight to the next action/recovery. It does not emit separate ball-release and arrival messages or continuous trajectories. Only the ball holder's action chain is checked; unobserved players' positions and off-ball movement are not reconstructed.

## Independent audit

`audit_match(match)` consumes events and control intervals, without generator patterns, seed or intended outcomes. It returns:

- Structural issues: endpoint/receiver discontinuity, actions exceeding assumed speed bounds, a new possession lacking recovery/restart, and invalid restart after a goal, off-target shot or save.
- Count/min/median/max for controlled spells and passes per recorded possession.
- Event counts, recovery zones, incomplete-pass endpoint zones, shot zones and a coarse shot-location grid.
- Forward/backward/lateral pass sectors: ±45 degrees around the attacking axis on the assumed pitch. This diagnostic definition is not a progressive-pass metric.
- Observed full-match statistics, with the usual possession denominator and explicit excluded time.

An empty `structural_issues` list means that these specific checks passed. It is not a realism certificate. A schema-invalid match fails Pydantic validation before the audit. `calibrated_to_real_data` is explicitly false.

For seeds 0–19 in this version, the inspected outputs were:

| Per-match quantity | Minimum | Median | Maximum |
| --- | ---: | ---: | ---: |
| Attempted passes, both teams | 640 | 680 | 732 |
| Shots, both teams | 14 | 21.5 | 31 |
| Goals, both teams | 0 | 1 | 4 |
| Home possession share (%) | 38.53 | 51.71 | 57.98 |

These are **synthetic outputs**, not acceptance ranges or empirical football benchmarks. All twenty matches passed the implemented structural checks. The tests also find home wins, away wins and draws across seeds, while retaining reproducibility for a fixed seed and version. For seed 7, controlled spells range from 3 to 198 seconds, and passes per recorded possession from 1 to 24. A short terminal spell may reflect the halftime boundary.

A remaining limitation is effective playing time: with limited interruption types, the generator may keep the ball controlled for too much of the regulation clock. Seed 7 has 4,789 controlled seconds, 78 contested seconds and 533 out-of-play seconds. These values must not be used to claim professional timing realism. Broadening represented stoppages and comparing their distributions to an appropriate dataset are required before calibration claims.

## Running it

In `backend/`, with the virtual environment active:

```powershell
python -m app.services.generate_match --mode varied --seed 7 --audit --output ../data/synthetic/varied-7.json
```

The output JSON contains only the common match model. The command prints generator provenance and a separate diagnostic report. It refuses to overwrite existing files. Change `--seed` to generate a different match; keep both seed and generator version to reproduce it. Omitting `--mode varied` preserves the old authored CLI behavior.

The browser now starts with **Varied match / Partido variado**, using seed 7. The repository caches this fixed demo per process to avoid regeneration on every analysis poll. Select the authored examples to inspect guaranteed contrasts such as 1→6 recoveries. The API's default remains `original` for backward compatibility; use `scenario=varied` explicitly for the new match.

## Research and next calibration step

[Karun Singh's xT explanation](https://karun.in/blog/expected-threat.html) describes modeling movement and shooting choices conditional on location. It informed the state-dependent approach; this generator does not learn xT or fit those transition probabilities.

The [official StatsBomb Open Data repository](https://github.com/hudl/open-data) provides selected competitions, event files and documentation, with separate 360 coverage for selected matches. Its README requires attribution and a logo for published derived analysis; the full [license](https://github.com/hudl/open-data/blob/master/LICENSE.pdf) must be reviewed before dataset use. No real match records, derived reference distributions or trained parameters were imported in this implementation.

The next calibration task is to choose a representative, permitted reference sample, reconcile coordinate/action/possession definitions, compare distributions and review mismatches. Event feeds alone do not establish exact controlled or contested seconds; timing comparisons need a compatible definition/source. Keep a hold-out set of real matches for evaluation and retain the authored synthetic fixtures as regression tests. This step is still pending.
