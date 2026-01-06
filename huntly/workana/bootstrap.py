import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright

# Allow override via env; default to repo_root/config/workana_state.json
repo_root = Path(__file__).resolve().parents[2]
# Support both names used in examples
WORKANA_STATE = os.getenv("WORKANA_STATE") or os.getenv("WORKANA_STATE_FILE") or str(repo_root / "config" / "workana_state.json")
LOGIN_URL = "https://www.workana.com/login"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=200)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(LOGIN_URL, wait_until="domcontentloaded")

        print("Logueate manualmente en Workana y presioná ENTER aquí.")
        input()

        # Ensure parent dir exists
        Path(WORKANA_STATE).parent.mkdir(parents=True, exist_ok=True)
        await context.storage_state(path=str(WORKANA_STATE))
        await browser.close()
        print("Sesión guardada en", WORKANA_STATE)

if __name__ == "__main__":
    asyncio.run(main())
