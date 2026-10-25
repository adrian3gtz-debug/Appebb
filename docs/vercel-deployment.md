# Deploying the frontend and API to Vercel

Use two Vercel projects connected to the same GitHub repository and branch. The frontend needs a public API origin: Vite's development proxy does not run on the deployed static site.

| Setting | Frontend project (`futbolify`) | API project (suggested name: `futbolify-api`) |
| --- | --- | --- |
| Repository | `adrian3gtz-debug/Appebb` | Same repository |
| Production branch | `phase1-foundation` | `phase1-foundation` |
| Root Directory | `frontend` | Repository root: leave empty or `./` |
| Framework / Application Preset | Vite | FastAPI |
| Build / Install / Output settings | Defaults; no overrides | Defaults; no overrides |
| Environment variable | `VITE_API_BASE_URL` = API origin | `BACKEND_CORS_ORIGINS` = allowed frontend origins |

Use the Hobby plan and the provided `vercel.app` domains. This setup does not enable a paid plan, database, AI provider or Azure service. It remains subject to Vercel's current Hobby quotas and permitted-use terms. The project is an unsigned public demo: no secrets belong in frontend variables, and CORS is not authentication.

## What the deployment files do

- Root `main.py` exposes the existing `app.main.app` through a location Vercel recognizes. It adds `backend/` to Python's import path, equivalent to running from that folder locally. It does not start a separate Uvicorn server inside a function.
- Root `requirements.txt` lists the Python dependencies directly for Vercel. `backend/requirements.txt` includes that list for local pip installs, so there is one dependency list. The root file must remain flat: the Vercel deployment rejected an included requirements file.
- `.python-version` selects Python 3.12.
- Root `vercel.json` excludes `frontend/**` from the Python function. It does not force a framework across the repository; the API project's FastAPI preset and recognized root `main.py` select the backend. The backend code and `data/synthetic/` remain inside the project root and the function bundle; no generated JSON needs to be duplicated or downloaded at runtime.
- `frontend/vercel.json` selects Vite for the frontend project, whose Root Directory must be `frontend`. Each project must read the configuration associated with its own root.
- `frontend/src/services/api.ts` shares the API origin between health, match and analysis requests. It removes whitespace and trailing slashes. The variable is read by Vite at **build time**.

The existing frontend project must keep `frontend` as its Root Directory. The repository-root FastAPI configuration is for the separate API project, whose Root Directory is `./`. Running `uvicorn app.main:app --reload` inside `backend/` still works locally.

## 1. Create the API project after the change is pushed

1. In Vercel, choose **Add New → Project** and import the existing `Appebb` repository again under a different Vercel project name, such as `futbolify-api`. Keep the current Hobby workspace.
2. Set **Root Directory** to the repository root (`./`) and **Application Preset** to **FastAPI**. Leave Build, Install and Output overrides disabled. The API project does not output `dist`.
3. Add `BACKEND_CORS_ORIGINS` for **Production** with the frontend's stable Production origin, copied from its **Domains** page. For the current frontend, the previously shown domain was `https://futbolify-psi.vercel.app`; confirm it is still the assigned domain before using it. Include `https://` and omit a trailing slash or path.
4. If importing uses `main`, Vercel may create an initial failed deployment because that branch has no API code. Open the created project's **Settings → Environments → Production → Branch Tracking**, enter `phase1-foundation` and save. This changes only the Vercel project, not GitHub's default branch.
5. Open **Deployments → ⋯** (the menu above the list) → **Create Deployment**, select the Git reference `phase1-foundation` and the **Production** environment. Confirm the source is the commit containing these deployment files. Redeploying the old `main` deployment would use the old source again.
6. Wait for **Ready**. Copy the API's stable Production domain from **Domains**. Do not assume the suggested project name is available or hardcode a domain before Vercel assigns it.

## 2. Verify the API before connecting the frontend

Open these URLs with the API's actual Production domain:

- `https://YOUR-API.vercel.app/api/health` → `{"status":"ok"}`.
- `https://YOUR-API.vercel.app/api/matches/demo` → synthetic match JSON. This checks that the checked-in fixture was packaged.
- `https://YOUR-API.vercel.app/api/matches/demo/recoveries?scenario=higher_recoveries&second=1200` → a synthetic high-recovery insight with current-window counts of six recoveries and three sequences reaching shots.
- `https://YOUR-API.vercel.app/docs` → FastAPI's interactive endpoint documentation.

These should work without a Vercel login in a private browser window. If the API redirects to a Vercel authentication page, inspect that API project's **Deployment Protection** settings and use its public Production deployment. A CORS variable cannot bypass deployment authentication. Opening just `/` on the API can return 404; the health route is `/api/health`.

## 3. Connect the existing frontend project

In the **frontend** Vercel project, add this variable for **Production**:

```dotenv
VITE_API_BASE_URL=https://YOUR-API.vercel.app
```

Choose the **Config** variable type, not **Secret**. The `VITE_` prefix makes this API origin public in the browser, which is necessary for frontend requests; it must never contain credentials. Use only the API origin, without `/api`, `/docs` or a frontend domain. No key or token is needed. Open **Deployments** and rebuild/redeploy a `phase1-foundation` deployment after saving. Vite embeds the value during the build, so changing the variable alone cannot update an already built frontend.

Changing `BACKEND_CORS_ORIGINS` likewise requires a new API deployment to apply the value in the function environment.

For several allowed frontend origins, use a comma-separated list in the **API** project's variable, for example:

```dotenv
BACKEND_CORS_ORIGINS=https://YOUR-FRONTEND.vercel.app,https://YOUR-EXACT-PREVIEW.vercel.app
```

Add only the exact preview origins you intend to use. The generated deployment URL differs from the stable Production domain, even for the same frontend. Do not use `*`, `localhost`, or a blanket allowance for all `vercel.app` projects as the deployed CORS configuration.

## 4. Check the complete experience

On the frontend Production URL, the indicator should show **API connected / API conectada**. Play the match and move the timeline to 20:00 to inspect the first recovery comparison. Switch to **Circulation vs counterattack** to verify that the original JSON-backed match loads as well. Open the same stable frontend link on the phone.

A function can need extra startup time on its first request. Replay itself runs in the browser, so pausing and playback speed do not require a permanently running server or WebSocket. The analysis panel polls at most twice per second during normal polling. Repeated visitors consume shared Hobby request and compute allowances; consult the Vercel Usage dashboard.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| `frontend` directory not found / only initial commit | Deployment Source must be `phase1-foundation`, not the old `main` commit. |
| API build tries Vite / asks for `dist` | API project must use FastAPI and root `./`, with no old frontend command overrides. |
| Frontend build reports `No FastAPI entrypoint found` | Frontend project must use root `frontend` and Vite. Deploy the commit containing `frontend/vercel.json` and the root configuration without a forced FastAPI framework. Redeploying an older commit repeats its old configuration. |
| API import error or cannot find dependencies | Confirm root `main.py`, `requirements.txt`, `.python-version`, and `backend/app/` are in the deployed commit. Read Build Logs / Function Logs. |
| Original match returns 503 | Verify root includes `data/synthetic/circulation-vs-counterattack.json`; do not set the API Root Directory to `backend`. |
| API health works, frontend fetch fails | Check the frontend build-time API URL, exact frontend origin in API CORS, deployment protection, and whether both deployments were recreated after variable changes. |
| No new deployment after settings changes | Create a deployment from `phase1-foundation`; settings changes alone do not move the existing website to a different Git commit. |

## Local verification of the deployment entry

From the repository root, with backend dependencies installed, run:

```powershell
.\backend\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

The isolated bundle test in `backend/tests/test_vercel_entrypoint.py` copies only the root entry, backend app and synthetic data into a temporary directory, then checks health, fixture loading, recovery analysis and CORS. In `backend/`, run `python -m pytest tests/test_vercel_entrypoint.py -q`. This verifies local imports and behavior; the first real Vercel deployment still needs its own build and public URL checks.

References: [Vercel's FastAPI example](https://github.com/vercel/vercel/tree/main/examples/fastapi) and [Python runtime builder](https://github.com/vercel/vercel/tree/main/packages/python).
