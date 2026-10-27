# Match summaries and audience modes

The replay now offers **Casual fan / Analyst** modes in EN/ES. It also produces a
time-bounded match summary, which becomes a final recap only at 90:00. This stage
uses deterministic metrics and text templates. Foundry/model integration remains
a separate pending delivery task.

## Same facts, different experiences

Casual fan mode leads with the current score, shot counts and a plain-language
observation when the data supports one. Full statistics remain expandable.
Recorded actions of a selected recovery possession are collapsed initially.

Analyst mode adds completed/attempted passes, accuracy and controlled-time possession
to the summary and opens the complete statistics as a section. Its control/shot
observation reports the underlying seconds and counts. Missing percentages remain
unavailable rather than becoming zero.
Selected recovery actions are expanded in Analyst mode, with the same event IDs.

The viewing preference is saved locally. Switching modes does not reload the match,
reset or pause the clock, alter speed, change language or create another polling
loop. Changing scenarios retains the selected audience while resetting replay as
before. EN/ES and audience preferences survive a page reload; replay still starts
paused at 00:00.

## Summary contract and evidence

`GET /api/matches/demo/analysis?scenario=varied&second=1200` now includes `recap`
alongside statistics and recoveries. All three have the same match and cutoff.
Statistics are calculated once and reused to build the summary.

`MatchRecap` (`recap-v1`, generation `rules`) contains:

- Match ID, observation second and `in_progress`/`full_time` phase.
- Observed goal events with original event/player/team IDs, timestamp and the
  cumulative home/away score immediately after that goal.
- An optional descriptive contrast when one team has strictly more controlled
  seconds but strictly fewer shots. The payload supplies both teams' seconds and
  shot counts. Missing control intervals or equal quantities produce no contrast.

There is no automatic inference of dominance, chance quality, coaching decisions
or tactical causes. The contrast does not explain why a team won. A team can have
more possession, fewer shots and lose; the original authored fixture exercises
that case. A summary at 89:59 cannot declare a final winner.

The **Goals and supporting events** disclosure links each goal to its replay
timestamp, pausing at that event for inspection. An away win is narrated with the
winner's score first, while the scoreboard and event list retain home/away order.

The frontend derives wording solely from the current API statistics and recap;
it does not scan the downloaded match's future goals to generate the summary.
The existing snapshot guard hides responses from a future cutoff after rewinding.
If an older API has not deployed the new `recap` field yet, the UI displays summary
unavailability and keeps statistics/recoveries usable.

## Try it locally

1. Run API and frontend using the README commands.
2. Choose **Circulation vs counterattack** and move the timeline to 90:00.
3. Check the final 0–2 scoreboard, the away-win headline and the control/shot contrast.
4. Switch between Casual fan and Analyst; the clock must stay at 90:00.
5. Open goal evidence and select the first goal. The summary becomes in-progress
   and the later goal disappears from its evidence.
6. Switch EN/ES during playback and change the audience while playing; speed and
   playback continue. Reload to confirm saved preferences and the paused reset.

The backend suite checks timestamp boundaries, future-event mutation, rewinds,
missing control data, score consistency, all five scenarios and the shared cutoff.
Frontend narrative tests check live/final wording, away-score order, draws and
matching facts across both audiences. Chromium exercises actual goal navigation,
mode/language changes, preference persistence, request reuse, mobile width and
compatibility with an API response that lacks a recap.
