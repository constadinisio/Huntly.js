import asyncio
from playwright.async_api import async_playwright

WORKANA_STATE = "workana_state.json"
LOGIN_URL = "https://www.workana.com/login"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=200)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(LOGIN_URL, wait_until="domcontentloaded")

        print("Logueate manualmente en Workana y presioná ENTER aquí.")
        input()

        await context.storage_state(path=WORKANA_STATE)
        await browser.close()
        print("Sesión guardada en", WORKANA_STATE)

asyncio.run(main())
