# main.py
import threading
import runpy

def run_telegram_bot():
    # ejecuta telegram_bot.py como si fuera __main__
    runpy.run_module("telegram_bot", run_name="__main__")

def run_scraper():
    # ejecuta workana_scraper.py original
    runpy.run_module("workana_scraper", run_name="__main__")

if __name__ == "__main__":
    t = threading.Thread(target=run_telegram_bot, daemon=True)
    t.start()

    run_scraper()