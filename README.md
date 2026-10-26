# Football Intelligence Lab

From match events to explainable football intelligence.

For project status, collaboration preferences, research decisions and the proposed next stage, start with [the project context and handoff (Spanish)](docs/project-context.md).

This is the foundation for Match Story Engine. It contains a React frontend, FastAPI endpoints, validated match models, possession-time calculation, and browser playback of reproducible synthetic fixtures, and a first recovery-to-attack analysis with inspectable evidence. AI provider integration is planned for a later stage.

## Requirements

- Node.js 20.19+ or 22.12+
- Python 3.10+

## Run locally (PowerShell)

Open two terminals in this repository.

Backend:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The connection indicator should show **API connected** or **API conectada**, depending on your language selection. Use **EN** and **ES** to switch languages; the choice is saved in your browser. The API health endpoint is http://127.0.0.1:8000/api/health and API docs are at http://127.0.0.1:8000/docs.

If PowerShell blocks activation, run `.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload` from `backend/`. On Bash, activate with `source .venv/bin/activate`.

## Configuration

Defaults work without an `.env` file. Copy `.env.example` to `frontend/.env` to set `VITE_API_BASE_URL` for a direct API origin. When unset, Vite proxies `/api` to port 8000. Set `BACKEND_CORS_ORIGINS` in the backend process environment if you need other browser origins. Never commit secrets.

## Checks

Run `npm test` and `npm run build` in `frontend/`. In `backend/`, install `requirements-dev.txt` and run `pytest`.

## Generate a synthetic match

The exploratory demo now uses a **Varied match** with state-dependent possessions, variable durations and sampled outcomes. Its parameters are explicit assumptions, not fitted professional football rates. The older authored scenarios remain available as regression examples. Read [the varied-generator methodology and diagnostic results](docs/varied-synthetic-matches.md).

To generate and audit a varied match from `backend/`:

```powershell
python -m app.services.generate_match --mode varied --seed 7 --audit --output ../data/synthetic/varied-7.json
```

The same seed and generator version reproduce the same sequence; different seeds can change actions, timing and results. Diagnostics check structural continuity and summarize distributions without assigning a realism score.

To reproduce the original authored circulation/counterattack fixture, run from `backend/` with the virtual environment active:

```powershell
python -m app.services.generate_match --seed 19 --output ../data/synthetic/example-19.json
```

This writes a new JSON file and prints statistics derived from its events and control intervals. The command refuses to overwrite existing files. Seed 7 is already included at `data/synthetic/circulation-vs-counterattack.json`. This authored scenario demonstrates higher possession with fewer shots and a defeat. It is not calibrated to professional match distributions. See [the scenario documentation](docs/synthetic-scenario.md) for the methodology and limitations.

## Structure

- `frontend/`: React, TypeScript, Vite, Tailwind CSS
- `backend/`: FastAPI and Pydantic

All generated match data is synthetic and must be identified as such.

## Replay the demo

`GET /api/matches/demo` loads and validates the included fixture with Pydantic. Its response includes `source: "synthetic"`, `duration_seconds: 5400`, and the full match. Missing or invalid fixture files return HTTP 503.

The browser downloads the full match once and starts paused at 00:00. Use Play/Pause, Restart, and the 1×/10×/30×/60× speed selector. The default 30× plays the 90-minute match in three minutes, excluding pauses. The compact controls stay visible while scrolling. The scoreboard and latest eight events are derived only from events at or before the playback clock. Restart clears the visible progress and pauses, preserving speed. Playback stops at 90:00. The second half begins at 45:00 without a halftime break; this fixture has no added time. Changing EN/ES preserves playback.

This is local playback of a recorded synthetic sequence, not server-side live ingestion or a new match generated on every play. The fixture is delivered in full, so future events can be inspected in the network response even though the UI hides them. Timing uses elapsed browser time; after a background-tab delay the next update may catch up.

Code: `backend/app/api/matches.py` exposes the endpoint, `backend/app/services/match_repository.py` reads the fixture, and `frontend/src/features/replay/` contains the playback clock, controls and event list.

## Inspect recovery-to-attack evidence

Select **More high recoveries** for an authored recovery example. Under **From recovery to attack**, choose **View comparison at 20:00** (seeking pauses playback). This example's first comparison shows high recoveries increasing from **1 to 6**, with **3** of the later-window sequences reaching a shot before the interval closed. These are synthetic scenario outputs. Select **12:15** on the pitch/list to inspect its recorded actions. Open **Evidence and interpretation limits** for interval counts, definitions and limitations. Before the second half's first comparison, the shortcut correctly targets **65:00**. The default **Varied match** does not guarantee any highlight.

Switch to **Stable recoveries** for a no-highlight counterexample, or **More recoveries, no shots** for an increase without resulting shots. **Circulation vs counterattack** preserves the original fixture. Changing the test match resets playback. All controls, evidence explanations and labels support EN/ES.

The API computes evidence through the requested second at `/api/matches/demo/recoveries?scenario=higher_recoveries&second=1200`. The UI refreshes analysis separately from the playback clock and displays its evidence timestamp. No AI calls or paid services are involved. Read [the recovery methodology](docs/recovery-analysis.md) for formulas, editable thresholds, sequence termination, incomplete observations, window boundaries and synthetic-data limits.

## Inspect match statistics

Open **Match statistics / Estadísticas del partido** below the main analysis to see possession, attempted/completed passes, accuracy, shots and goals through the displayed analysis time. Expand the shot breakdown and calculation notes to inspect outcomes and controlled/contested/out-of-play time. Missing percentages display `—` rather than zero. **Latest events / Últimos eventos** is a separate expandable section. A single notice identifies all teams and players as fictional; compact display names preserve the original records.

Statistics and recovery evidence share `/api/matches/demo/analysis?scenario=original&second=1200`, avoiding a second polling loop. Pausing or seeking updates the cutoff; future counts are hidden when rewinding. Try **Circulation vs counterattack** at 90:00 to inspect higher possession alongside fewer shots and a defeat. These remain authored synthetic outcomes.

Read [the statistics methodology](docs/match-statistics.md) and [the research notes on xT, VAEP, pitch control and xG](docs/football-analytics-research.md). These advanced models are research directions, not implemented features.

## Deploy to Vercel

Use two projects from this repository: **Vite** with Root Directory `frontend`, and **FastAPI** with Root Directory `./`. Both track `phase1-foundation`. The root deployment entry keeps `backend/app/` and `data/synthetic/` available in the Python function.

Set `BACKEND_CORS_ORIGINS` on the API project to the exact frontend Production origin. Set `VITE_API_BASE_URL` on the frontend project to the API Production origin, without `/api`. Redeploy each project after changing its environment variables. See [the deployment guide](docs/vercel-deployment.md) for the dashboard steps, branch selection, validation URLs and troubleshooting.
