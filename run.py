"""Deployment entry point for hosts that run from the repository root.

The application code and dependencies live in backend/. This shim lets commands
such as `gunicorn run:app` work without requiring a host-specific root directory
setting.
"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app import create_app  # noqa: E402

app = create_app()
