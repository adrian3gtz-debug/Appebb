# Generator refinement and replay insights — stage 2

The browser and varied-mode CLI now use **varied-v2**, seed 7 by default. This
version makes pass context explicit and adjusts the base pass-failure probability
after the [first Wyscout reference comparison](reference-validation.md). It is a
limited reference-informed change, not a calibrated professional-match simulator.

## Explicit contexts, with legacy compatibility

Passes have an optional `pass_context`: `open_play`, `kickoff`, `throw_in`,
`goal_kick`, `corner` or `free_kick`. A missing/null value means unknown, preserving
existing authored fixtures. V2 emits the first four contexts; it does not yet
generate corners or fouls/free kicks. A restart applies only to its first pass.
Goalkeeper claims after saves are recoveries followed by open-play actions.

The frontend shows kickoff, throw-in and goal-kick labels in EN/ES. Statistics
still count these as attempted passes. The independent audit checks declared
kickoffs at the centre, throw-ins at a touchline and restarts at a possession start.
The analytics engine receives events rather than generator intentions.

Wyscout normal type-8 passes are called `unmarked` in research: that release
includes kickoffs among those passes. They cannot all be certified as open play.
Type-3 pass restarts are mapped explicitly. This small definitional difference is
retained in reports rather than assigning unobserved provider labels.

V1 remains selectable and reproduces its original seed-7 signature. In `backend/`:

```text
python -m app.services.generate_match --mode varied --generator-version varied-v1 --seed 7 --audit --output ../data/reference/legacy-v1.json
python -m app.services.generate_match --mode varied --generator-version varied-v2 --seed 7 --audit --output ../data/reference/current-v2.json
```

## What was adjusted and why

The pass-failure rule changes only its base term from **0.04 to 0.075**. The
distance term (`assumed_metres/260`), modeled-pressure addition (0.10) and advanced
destination addition (0.05) remain engineering assumptions. These are not a fitted
pass-success model. Carry losses, shot availability/outcome rules and action timing
are unchanged. The same seed can produce a different game under V2 because changed
failures affect subsequent possessions and random-number consumption.

Before evaluating the 80 reserved matches, we examined six declared candidates on
the 300-match tuning cohort and synthetic seeds 0–19. The
[sensitivity report](reports/wyscout-context-experiment.json) records all candidates,
not just the selected one. These are synthetic medians per match:

| Candidate | Ordinary passes | Known-outcome accuracy (%) | Adjacent pass gap (s) | Shots |
| --- | ---: | ---: | ---: | ---: |
| V1 behavior plus annotations | 642.5 | 86.49 | 5 | 21.5 |
| Travel floor reduced from 2s to 1s | 702 | 86.24 | 4 | 25 |
| Base failure 0.075 — selected | 614 | 82.50 | 5 | 23.5 |
| Travel floor 1s + base failure 0.075 | 670.5 | 82.68 | 4 | 25.5 |
| Also decision log-mean 0.85 | 754 | 82.73 | 3 | 28 |
| Also decision log-mean 0.65 | 826.5 | 82.56 | 3 | 28 |

The faster candidates improve pass volume/gaps but worsen shot volume: 28 exceeds
the tuning reference's upper quartile of 25. We selected the limited accuracy
change, retaining the original timing pending a better representation of
interruptions and action semantics. This is a conservative engineering choice,
not an optimization guarantee or a significance claim. All six candidates passed
the existing structural audit across those twenty seeds.

## Frozen evaluation

After choosing the rule and metrics, the
[evaluation report](reports/wyscout-context-evaluation.json) compares 100 identical
seed indices before/after and reports the previously reserved 80 real matches.
No rules were adjusted after inspecting this holdout. Counts cover both teams and
the first 2,700 seconds in each half, preserving real added time outside these
comparison windows. Figures are medians of per-match measures:

| Measure | 300 tuning games | 80 evaluation games | V1 behavior, annotated | V2 |
| --- | ---: | ---: | ---: | ---: |
| Ordinary/unmarked passes | 811.5 | 816.5 | 630.5 | 613.5 |
| Known-outcome accuracy (%) | 82.63 | 83.16 | 86.41 | 82.55 |
| Adjacent pass gap (s) | 2.41 | 2.39 | 5 | 5 |
| Shots | 22 | 21 | 22 | 22 |
| Marked pass restarts | 87 | 89 | 36 | 42 |

The accuracy discrepancy shrinks. Pass volume worsens slightly and remains too low;
action gaps remain longer. Equal shot medians do not establish matching shot
distributions or locations. Pass directions also differ: the reference has more
lateral recorded passes. Missing fouls, corners and rebounds limit timing and
restart comparisons. These remain unresolved findings, not hidden acceptance gates.

An adjacent-pass gap measures time between two consecutive ordinary/unmarked pass
records by the same team in the same half, with an explicitly completed first
pass. Synthetic pressure annotations at the action timestamp are omitted before
checking adjacency. Real duels, touches and interruptions break the pair. This is
conditional on recording conventions; it includes decision and travel time and
does not measure exact ball speed or possession duration. Direction sectors use
an assumed 105×68m pitch, not measured field dimensions.

The 80-match cohort has now been used for this evaluation. Future tuning must
acknowledge that its results have been seen; repeated adaptive evaluation on it
cannot be described as fresh independent validation.

Reproduce on the downloaded files from the previous stage, from `backend/`:

```text
python -m app.reference.context_report --events ../data/reference/wyscout-2017-18/events_England.json --matches ../data/reference/wyscout-2017-18/matches_England.json --experiment --output ../data/reference/context-experiment.json
python -m app.reference.context_report --events ../data/reference/wyscout-2017-18/events_England.json --matches ../data/reference/wyscout-2017-18/matches_England.json --evaluate-held-out --output ../data/reference/context-evaluation.json
```

The experiment command rejects simultaneous held-out evaluation. Input checksums
and split version are in the reports. Stage-1 reporting explicitly uses V1 so its
committed baseline remains reproducible after advancing the demo to V2.

## Insights during replay

The API computes evidence at the requested replay second. React shares one query
for statistics and recoveries, polling at most every 500ms during playback and
querying again on pause/seek. A timestamp identifies the latest available evidence;
network latency can make it lag behind the clock. Future responses are hidden on
rewind and requests are aborted when the playback context changes.

Recovery sequences are available as events occur. The first interval-comparison
insight can appear at **20:00** (65:00 in the second half), then at subsequent
ten-minute boundaries when its rule is met. An insight is not guaranteed in the
varied match. These are event-backed rules/templates, not a language-model service
or live ingestion of an external match.

To inspect the update in the UI: select **More high recoveries**, seek to 19:58,
choose 1× and press Play. After crossing 20:00, the card reports **1→6** recoveries.
Pause, rewind to 19:59, and verify that the closed-window insight disappears.
Restart returns to 00:00 and pauses. This was exercised in Chromium with the real
local API, including EN/ES restart labels and a 390px-wide viewport.

Verification for this stage: **140 backend tests**, **9 frontend tests** and the
frontend production build passed. Tests include the historical V1 signature,
restart declarations and API insight appearance/rewind boundaries. Chromium also
verified actual playback across 20:00, pause, rewind, restart, language switching,
and no horizontal overflow at 390px. No public deployment was performed.
