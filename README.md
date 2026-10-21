# Football Intelligence Lab

From match events to explainable football intelligence.

This is the foundation for Match Story Engine. It currently contains a React frontend, a FastAPI backend, and a live connection check. Match simulation, analytics, and AI are planned for later stages.

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

Open http://localhost:5173. The connection badge should show **Backend connected**. The API health endpoint is http://127.0.0.1:8000/api/health and API docs are at http://127.0.0.1:8000/docs.

If PowerShell blocks activation, run `.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload` from `backend/`. On Bash, activate with `source .venv/bin/activate`.

## Configuration

Defaults work without an `.env` file. Copy `.env.example` to `frontend/.env` to set `VITE_API_BASE_URL` for a direct API origin. When unset, Vite proxies `/api` to port 8000. Set `BACKEND_CORS_ORIGINS` in the backend process environment if you need other browser origins. Never commit secrets.

## Checks

Run `npm run build` in `frontend/`. In `backend/`, install `requirements-dev.txt` and run `pytest`.

## Structure

- `frontend/`: React, TypeScript, Vite, Tailwind CSS
- `backend/`: FastAPI and Pydantic

All future match data must be identified as synthetic.
