"""Entry point for Huntly.

Starts the Telegram bot in a background thread and runs the scraper in foreground.
"""
import threading
import runpy
import signal
import sys
from huntly.core.validation import validate_config, sanity_check
from rich.console import Console

console = Console()

def signal_handler(sig, frame):
    """Handle shutdown signals gracefully."""
    console.print("\n[bold red]Shutting down Huntly...[/bold red]")
    sys.exit(0)

def run_telegram_bot():
    runpy.run_module("huntly.integrations.telegram_bot", run_name="__main__")

def run_scraper():
    runpy.run_module("huntly.workana.scraper", run_name="__main__")

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    console.print("[bold green]Starting Huntly...[/bold green]")
    
    # Validate configuration before starting services
    validate_config()
    sanity_check()

    # Start Telegram bot in background thread
    t = threading.Thread(target=run_telegram_bot, daemon=True, name="TelegramBot")
    t.start()
    console.print("[dim]✓ Telegram bot thread started[/dim]")

    # Run scraper in main thread
    console.print("[dim]✓ Starting Workana scraper...[/dim]")
    run_scraper()
