"""Configuration validation helpers.

Provide simple checks for required environment variables and print
user-friendly instructions if something is missing.
"""
from __future__ import annotations

import os
import sys
from typing import List


def _is_true(val: str | None) -> bool:
    if not val:
        return False
    return val.strip().lower() in ("1", "true", "yes", "y")


def validate_config() -> None:
    """Validate essential environment variables.

    Exits the process with a non-zero code after printing helpful messages
    if required variables are missing.
    """
    missing: List[str] = []
    hints: List[str] = []

    # Core: scraping URL is required
    workana_url = os.getenv("WORKANA_URL") or os.getenv("URL")
    if not workana_url:
        missing.append("WORKANA_URL (or URL)")
        hints.append("Añade la URL de búsqueda de Workana en config/.env: WORKANA_URL=https://www.workana.com/jobs?skills=python")

    # Telegram notification vars (required only if enabled)
    notify_telegram = _is_true(os.getenv("NOTIFY_TELEGRAM"))
    if notify_telegram:
        if not os.getenv("TG_TOKEN"):
            missing.append("TG_TOKEN")
            hints.append("Crea un bot y coloca TG_TOKEN en config/.env (ver README).")
        if not os.getenv("TG_CHAT"):
            missing.append("TG_CHAT")
            hints.append("Coloca el ID de chat en TG_CHAT en config/.env.")

    # OpenAI key (optional, warn if OPENAI_ENABLED is true)
    openai_enabled = _is_true(os.getenv("OPENAI_ENABLED")) or bool(os.getenv("OPENAI_API_KEY"))
    if openai_enabled and not os.getenv("OPENAI_API_KEY"):
        missing.append("OPENAI_API_KEY")
        hints.append("Si quieres generar propuestas automáticamente, añade OPENAI_API_KEY en config/.env.")

    # Playwright storage state hint: only a warning
    if not os.getenv("WORKANA_STATE_FILE"):
        hints.append("Si usarás envío automático, configura WORKANA_STATE_FILE (por defecto config/workana_state.json) y ejecuta python -m huntly.workana.bootstrap")

    if missing:
        print("ERROR: faltan variables de entorno requeridas:\n")
        for v in missing:
            print(f" - {v}")
        print("\nSugerencias:")
        for h in hints:
            print(f" - {h}")
        print("\nEdita config/.env o exporta las variables y vuelve a ejecutar.")
        sys.exit(2)


def sanity_check() -> None:
    """Non-fatal checks that only print warnings."""
    # warn if neither telegram nor email notifications enabled
    notify_telegram = _is_true(os.getenv("NOTIFY_TELEGRAM"))
    notify_email = _is_true(os.getenv("NOTIFY_EMAIL"))
    if not (notify_telegram or notify_email):
        print("[WARN] Ningún canal de notificación habilitado. Activa NOTIFY_TELEGRAM o NOTIFY_EMAIL en config/.env si quieres recibir alertas.")
