"""Entry point for Huntly.

Starts the Telegram bot in a background thread and runs the scraper in foreground.
"""
import threading
import runpy


def run_telegram_bot():
    runpy.run_module("huntly.integrations.telegram_bot", run_name="__main__")


def run_scraper():
    runpy.run_module("huntly.workana.scraper", run_name="__main__")


if __name__ == "__main__":
    t = threading.Thread(target=run_telegram_bot, daemon=True)
    t.start()

    run_scraper()
# main.py
import threading
import runpy

def run_telegram_bot():
    # ejecuta el bot reorganizado en paquete
    runpy.run_module("huntly.integrations.telegram_bot", run_name="__main__")

def run_scraper():
    # ejecuta el scraper reorganizado en paquete
    runpy.run_module("huntly.workana.scraper", run_name="__main__")

if __name__ == "__main__":
    t = threading.Thread(target=run_telegram_bot, daemon=True)
    t.start()

    run_scraper()