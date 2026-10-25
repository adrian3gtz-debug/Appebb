"""Vercel entry point. Keep the local backend package and data paths intact."""

from pathlib import Path
import sys

# Local development starts inside backend/. Vercel starts at the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

from app.main import app as backend_app  # noqa: E402

app = backend_app
