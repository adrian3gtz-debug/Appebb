# Football analytics research and implementation decisions

Reviewed for the statistics-v1 stage. These are primary project/vendor references, not proof that our synthetic generator matches professional football. None of the learned models below is implemented or trained in this stage.

## Relevant approaches

| Reference | Technique | Data requirements and project decision |
| --- | --- | --- |
| [KU Leuven socceraction: Expected Threat](https://socceraction.readthedocs.io/en/latest/documentation/valuing_actions/xT.html) | Learn zone values from ball movement, shot and scoring probabilities; value successful possession-preserving movements by their change in zone value. | A credible training sample and consistent action coordinates/direction are required. The location-only assumption misses defenders, passing options and other context. This is the most approachable learned extension for our event-based architecture, after calibration and data/license review. |
| [KU Leuven socceraction: VAEP](https://socceraction.readthedocs.io/en/latest/documentation/valuing_actions/vaep.html) | Estimate scoring and conceding probabilities from recent actions, with game-state context; value the change associated with an action. | Needs historical training/evaluation matches and a richer action representation. Our authored scenarios would mainly teach a model their script. Retain sequence and time context now; defer model training. |
| [Friends of Tracking: LaurieOnTracking](https://github.com/Friends-of-Tracking-Data-FoTD/LaurieOnTracking) | Pitch-control models evaluate passing options using tracking; EPV can combine possession value with spatial control. | Requires synchronized player/ball tracking and motion estimates. Event endpoints cannot reconstruct unobserved defenders. Our SVG remains a record of observed actions, not a pitch-control map. |
| [StatsBomb: Upgrading Expected Goals](https://blogarchive.statsbomb.com/articles/soccer/upgrading-expected-goals/) | Estimate shot conversion with contextual data; richer models incorporate goalkeeper/defender positions and distinguish chance quality from execution. | A simpler location-based xG model is possible in principle, but it still needs representative training and calibration. Our shot locations and authored outcomes do not establish validated goal probabilities. Keep observed shot outcomes separate now. |

## Decisions applied now

The references support retaining action context and distinguishing observed outcomes from estimated values. Our implementation choices are:

1. Compute descriptive statistics in Python with explicit denominators and observation cutoffs; render them alongside recovery sequences rather than inventing a combined momentum score.
2. Expose both pass completion counts and attempts, and shot outcomes alongside possession. High possession or completion alone must not become a claim of territorial or attacking superiority.
3. Share one observation timestamp and API request between statistics and recovery analysis. Rewinding must remove future evidence.
4. Document definitions and data limitations so a later provider adapter can reconcile different event conventions.

## Recommended next stages (proposals, not implemented)

**Observable progression first.** Define attacking-relative pass direction and completed entries from outside to inside the last third. Distinguish attempts, completions and carries, account for halftime, and state restart treatment. Publish the progressive-pass definition before using it. Avoid claiming that an entry creates a chance. This is our proposed next step, not a universal provider definition.

**Improve synthetic realism.** The separate generator with varied patterns, state transitions and diagnostics is now implemented as [varied-v1](varied-synthetic-matches.md), while authored fixtures remain regression tests. Empirical calibration is still pending: compare possession lengths, passes per possession, shot locations, turnover zones and restart frequencies against an appropriately licensed reference sample. Changing the seed alone does not establish professional realism.

**Evaluate xT before more complex action models.** Review dataset/model licenses, record provenance, normalize coordinates and split training/validation/test by entire matches (and time where possible). Fit on training matches only, evaluate probability calibration and predictive error on held-out matches against a simple baseline, and inspect spatial coverage. A pretrained grid also needs compatible definitions and external validation. Applying it to synthetic events must remain labelled as a simulation. A more complex model is not automatically a more accurate one.

**Guard against unsupported pressure claims.** Recovery counts need exposure context: time out of possession and opponent activity can change the number of recovery opportunities. Consider those denominators before interpreting increases. Do not label our current recovery metric as PPDA: the schema does not yet provide the complete defensive-action coverage that such a definition would require.

**Separate detection from storytelling.** Expand evidence-backed detections and test false highlights on stable and noisy scenarios before introducing generated explanations. Threshold rules remain editorial rules until evaluated; they are not statistical significance tests. Templates or language models must communicate that distinction.

These priorities reflect our current data limitations. The main constraint is representative, well-defined input data, not access to a more complicated algorithm.
