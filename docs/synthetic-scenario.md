# First synthetic fixture: circulation versus counterattack

This is an **authored test scenario with seeded variations**, not a statistically calibrated football simulator. All teams and players are fictional. A seed varies action timing, pass receivers, and coordinates; it does not vary the intended winner or shot outcomes. There is no random or independently assigned scoreboard: the CLI counts recorded shot outcomes to calculate it.

## Construction

The generator builds 36 blocks of 150 seconds, split across two halves. Each block contains a longer home possession, a shorter away possession, and explicit dead-ball time. Harbor FC circulates through deeper positions with backward and lateral passes. Occasional attacks end in off-target shots. Other possessions end in incomplete passes intercepted by Ridge United, who progress more directly and sometimes shoot. Both teams switch direction at halftime, and the away team takes the second-half kickoff.

- Completed passes end where the next receiver acts; carries continue with the same player.
- Interceptions start at the preceding incomplete pass's endpoint.
- A shot wide or a pass over the touchline is followed by dead-ball time before a goal kick or throw-in. A goal is followed by the opposing team's kickoff from the centre.
- The first pass after a stoppage represents the restart; dedicated restart event types are not yet implemented.
- Pressure events record an opposing player applying pressure before selected losses. Their presence does not establish that pressure caused the loss.
- Control intervals cover the running match clock, including dead-ball time, excluding the halftime break and added time. Team control includes the flight of a pass until recovery or the ball leaving play. This fixture has no sustained contested intervals.
- Scenario instructions stay in the generator and this document. The match JSON contains events, teams, and control intervals, with no scenario label or expected winner for an analyzer to read.

The JSON at `data/synthetic/circulation-vs-counterattack.json` uses seed 7. To write another instance from `backend/`:

```powershell
python -m app.services.generate_match --seed 19 --output ../data/synthetic/example-19.json
```

The output path must be new; the command refuses to overwrite an existing file. It prints event counts, shots, goals, and possession calculated from that generated match. These are synthetic outputs, not observations about real teams.

## Validation and limits

Tests check reproducibility, model validation, full timeline coverage, receiver and ball continuity, halftime direction, kickoff placement, and the contrast between possession, shots, and goals across several seeds. Endpoint/time checks use a hypothetical 105 x 68 metre pitch to reject implausibly fast recorded passes or carries. They are plausibility bounds, not measured ball or player velocities.

The fixed block structure, limited outcomes (off-target shots and two authored away goals), long home possessions, and selected pressure examples intentionally make this scenario easy to inspect. It must not be used to estimate real shot conversion, pressure success, or population-level match distributions. It does not model full player trajectories, fouls, saves, offside, substitutions, or tactical formation. The engine cannot infer causal instructions or defensive shape from these events. Broader realism requires more possession templates and calibration against an appropriate real dataset in a later approved step.
