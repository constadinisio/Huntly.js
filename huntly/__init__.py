"""Huntly package root.

Centralized package init: load `.env` from the `config/` folder so modules
can rely on environment variables when imported. Keep this file lightweight
to avoid heavy side-effects on import.
"""
from pathlib import Path
from dotenv import load_dotenv

# Load .env from repository config/ if present
dotenv_path = Path(__file__).resolve().parents[1] / "config" / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path=dotenv_path)

__all__ = [
    "core",
    "integrations",
    "workana",
    "pipeline",
    "ai",
]
