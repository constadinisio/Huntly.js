"""Workana integration modules.

Avoid importing submodules with side-effects at package import time.
Import `bootstrap` only when executed as a script to prevent double-run
warnings when using `python -m huntly.workana.bootstrap`.
"""
from . import scraper, sender

__all__ = ["scraper", "sender"]
