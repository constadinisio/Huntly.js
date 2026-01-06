from playwright.async_api import async_playwright
import os
from pathlib import Path

# Default path: repo_root/config/workana_state.json (override with WORKANA_STATE env)
repo_root = Path(__file__).resolve().parents[2]
# Support both names used in examples
WORKANA_STATE = os.getenv("WORKANA_STATE") or os.getenv("WORKANA_STATE_FILE") or str(repo_root / "config" / "workana_state.json")

def to_message_url(u: str) -> str:
    if "/messages/bid/" in u:
        if "tab=" not in u:
            sep = "&" if "?" in u else "?"
            return f"{u}{sep}tab=message&ref=project_view"
        return u
    if "/job/" in u:
        slug = u.split("/job/")[1].split("?")[0].strip("/")
        return f"https://www.workana.com/messages/bid/{slug}/?tab=message&ref=project_view"
    return u

async def send_proposal_to_workana(job_or_message_url: str, proposal: str):
    url = to_message_url(job_or_message_url)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=200)
        context = await browser.new_context(storage_state=str(WORKANA_STATE))
        page = await context.new_page()
        await page.goto(url, wait_until="domcontentloaded")
        textarea = page.locator("form textarea").first
        await textarea.wait_for(timeout=15000)
        await textarea.fill(proposal)
        btn = page.locator('form input[type="submit"][value="Enviar"]').first
        await btn.wait_for(timeout=15000)
        await btn.click()
        await page.wait_for_timeout(1500)
        await browser.close()
        return True
