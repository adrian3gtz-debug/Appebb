# Wyscout EPL 2017/18 reference validation — stage 1

Selected reference: men's Premier League 2017/18, **380 matches, 20 clubs,
38 matches per club and 643,150 events**. This is a historical reference, not
validation against today's Premier League. This document records the V1 baseline;
[stage 2](generator-refinement.md) adds contexts and a limited V2 adjustment, with
the now-completed frozen evaluation on the 80 reserved matches.

## Source and reproducibility

Data collected by **Wyscout**, published by **Luca Pappalardo and Emanuele Massucco**
in the [Soccer match event dataset](https://doi.org/10.6084/m9.figshare.c.4415000).
The [events](https://figshare.com/articles/dataset/Events/7770599) and
[matches](https://figshare.com/articles/dataset/Matches/7770422) entries identify
**CC BY 4.0**. Credit the authors and Wyscout, link the
[license](https://creativecommons.org/licenses/by/4.0/), and identify transformations.
Cite Pappalardo et al. (2019),
[A public data set of spatio-temporal match events in soccer competitions](https://doi.org/10.1038/s41597-019-0247-7).

The downloader uses the raw ZIP mirror linked by
[Kloppy](https://kloppy.pysport.org/user-guide/loading-data/wyscout/), pinned to
`koenvo/wyscout-soccer-match-event-dataset@ebc4c54c1093c420a81ce442c69e4186fab33bb4`.
It validates SHA-256 of both archives and the extracted England files. Both
archives together are about 78 MB; other competitions are not extracted. Raw
records stay outside Git. The report contains derived aggregates, split IDs,
source version and input checksums.

From `backend/`, with the project's Python environment active, on PowerShell or Bash:

```text
python -m app.reference.download --directory ../data/reference/wyscout-2017-18
python -m app.reference.report --events ../data/reference/wyscout-2017-18/events_England.json --matches ../data/reference/wyscout-2017-18/matches_England.json --synthetic-count 100 --output ../data/reference/comparison.json
```

Both commands reject existing output destinations. Reporting is offline. It
validates competition, season, team membership, bounds, timestamps, duplicate IDs
and event coverage for every match. Unsupported periods cause an explicit error.
Raw extra fields remain in the original files, identified by hash and event ID;
the comparison view exposes the fields used or preserved by its adapter.

## Contract decisions based on actual data

The existing synthetic `Match` describes a complete simulated world. Importing
Wyscout directly would require inventing facts or weakening replay invariants.
`backend/app/reference/` introduces common observations for both sources first:

| Concern | Decision and reason |
| --- | --- |
| Clock | Keep period and fractional seconds within that period. First-half added time must not collide with second-half events. |
| Coordinates | Research observations face the attacking goal. Wyscout already uses that orientation; synthetic fixed-field coordinates rotate both axes when the team attacks the other way. These are not fixed-field replay positions. Preserve endpoints when supplied. |
| Actor | `playerId=0` means unknown. There are 48,031 such events; no player is assigned. |
| Receiver | This release has no explicit receiver field. Leave it unknown; the next actor need not be a clean reception. |
| Accuracy | Tags 1801/1802 identify recorded success/failure. Goal kicks in this release have neither. Report unknown outcomes; accuracy uses explicitly tagged outcomes only. |
| Restarts | Wyscout type 3 subtypes 30,31,32,34,36 count as pass restarts; 33 and 35 are free-kick shots/penalties. Synthetic passes do not identify restart context. Compare inclusive counts and expose this mismatch. |
| Shots | Include normal shots, direct free-kick shots and penalties. Save records are not additional shots. No xG or goal inference. |
| Recoveries | Preserve raw type/subtype/tags. A won duel does not alone establish a clean recovery; do not map it automatically. |
| Possession | Exact controlled/contested/dead-ball seconds, carries and possession IDs are not reconstructed. These comparison measures remain unavailable. |
| Rosters | Keep original starters, bench and substitutions in source metadata. Do not squeeze participants into an exactly-eleven-player roster. |

The subsequent real-data replay migration should introduce a versioned contract
with period clocks, declared coordinate orientation, optional receiver/actor,
explicit event/restart context and lineup/substitution records. It should identify
recorded, derived and simulated facts. Existing synthetic fixtures stay strict.
The API and frontend do not yet replay real matches.

## Comparison protocol

Split matches by SHA-256 of `wyscout-epl-2017-18-v1:{match_id}`: the first 300 IDs
sorted by digest are for diagnosis/adjustment, the other 80 for later evaluation.
Input order and results do not select the split. Schema, taxonomy and quality were
examined across the full release; held-out outcome distributions are not computed
by this report. This is a holdout within one season, not independent later-season
validation.

Synthetic cohort: `varied-v1`, seeds 0–99, selected before reviewing distributions.
Counts include both teams and zero-count matches. Quartiles use Python's inclusive
interpolation. A 6×4 shot grid uses attacking coordinates, clamping boundary points
into the last cell. Normalize raw grid counts by shot totals before comparing
cohorts of different sizes.

Real full-clock totals are preserved. A second view observes `[0,2700)` in each
half, matching the generator's two 45-minute windows. This window comparison does
not measure exact effective playing time. Across the full release, 38,971 events
occur at or after 45 minutes within their half. Timestamps are not compressed or
relabeled.

## First results

Reproducible output: [baseline JSON](reports/wyscout-epl-2017-18-baseline.json).
Medians per match across 300 reference and 100 synthetic games:

| Measure | Reference, full clock | Reference, two 45-minute windows | Synthetic |
| --- | ---: | ---: | ---: |
| Passes including pass restarts | 952.5 | 900.5 | 668.5 |
| Shots including shot restarts | 24 | 22 | 22 |
| Passes with unknown outcome | 16 | 15 | 0 |
| Accuracy among known pass outcomes (%) | 82.38 | 82.61 | 86.30 |

The generator produces fewer pass-like actions in comparable windows and a higher
median accuracy among known outcomes. Matching shot medians does not establish
matching distributions or locations. Unknown real outcomes and restart coverage
also constrain interpretation.

These findings justify investigating action timing, pass/restart definitions and
completion rules. They do not justify multiplying counts or forcing a score.
First add explicit restart context and inspect timing definitions; then adjust a
versioned generator against the 300-match set. Evaluate the 80 reserved matches
after parameters and metrics are frozen. No realism score or calibration claim.

## Verification

At the end of stage 1 the backend suite passed (132 tests, including 23 new reference tests).
Tests cover added-time clocks, unknown actors/outcomes, restart taxonomy, boundary
coordinates, invalid records, deterministic splitting, held-out exclusion and
parity with existing synthetic statistics. Both downloaded archives and extracted
files were verified against their checksums, and the full 380-match import ran
successfully. The frontend was not changed or retested in this stage.
