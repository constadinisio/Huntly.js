"""Workana scraper (moved into huntly.workana)."""
import csv
import json
import random
import time
import re
import os
from pathlib import Path
from typing import List, Dict, Set
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from ..core import notifications
from ..pipeline.proposal_pipeline import handle_new_job

# Rich UI
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.status import Status
from rich import box

console = Console()

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
DEFAULT_URL = "https://www.workana.com/jobs?language=es&publication=1d&skills=html"

USER_AGENT_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

DELAY_MIN = 3
DELAY_MAX = 7

# Default output files (can be overridden by env)
# Place outputs inside repo_root/data by default
repo_root = Path(__file__).resolve().parents[2]
DATA_DIR = repo_root / "data"
CSV_OUTPUT_DEFAULT = DATA_DIR / "workana_jobs.csv"
JSON_OUTPUT_DEFAULT = DATA_DIR / "workana_jobs.json"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_headers() -> dict:
    return {"User-Agent": random.choice(USER_AGENT_LIST)}

def polite_sleep():
    time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

def load_seen_urls(csv_path: Path) -> Set[str]:
    seen = set()
    if csv_path.exists():
        try:
            with csv_path.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    url = (row.get("url") or "").strip()
                    if url:
                        seen.add(url)
        except Exception as exc:
            console.print(f"[bold yellow][WARN][/bold yellow] Could not load existing CSV: {exc}")
    return seen

def parse_age_to_hours(date_str: str) -> float:
    low_date = (date_str or "").lower()
    try:
        if "minuto" in low_date:
            match = re.search(r"(\d+)", low_date)
            return int(match.group(1)) / 60 if match else 0
        elif "hora" in low_date:
            match = re.search(r"(\d+)", low_date)
            return float(match.group(1)) if match else 1.0
        elif "ayer" in low_date:
            return 24.0
        elif "día" in low_date or "dia" in low_date:
            match = re.search(r"(\d+)", low_date)
            return float(match.group(1)) * 24 if match else 24.0
    except Exception:
        pass
    return 999.0

def fetch_page(url: str, session: requests.Session) -> str | None:
    try:
        response = session.get(url, headers=get_headers(), timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as exc:
        console.print(f"[bold red][ERROR][/bold red] Failed to fetch {url}: {exc}")
        return None

# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def parse_jobs(html: str) -> List[Dict[str, str]]:
    """
    Workana embeds results in a <search> tag attribute ':results-initials' (JSON).
    """
    soup = BeautifulSoup(html, "html.parser")
    jobs: List[Dict[str, str]] = []

    search_tag = soup.find("search")
    if not search_tag:
        return []

    results_attr = search_tag.get(":results-initials")
    if not results_attr:
        return []

    try:
        data = json.loads(results_attr)
        results = data.get("results", [])
    except Exception:
        return []

    for item in results:
        title_html = item.get("title", "")
        title_soup = BeautifulSoup(title_html, "html.parser")
        title_tag = title_soup.find("span") or title_soup.find("a")
        title = title_tag.get("title") or title_tag.get_text(strip=True) if title_tag else "N/A"

        link_tag = title_soup.find("a")
        if link_tag and link_tag.get("href"):
            link = link_tag.get("href")
            if link.startswith("/"):
                link = "https://www.workana.com" + link
        else:
            slug = item.get("slug")
            link = f"https://www.workana.com/job/{slug}" if slug else None

        if not link or not str(link).startswith("http"):
            continue

        short_desc = (item.get("description", "") or "").replace("<br/>", " ").replace("<br />", " ").strip()
        budget = item.get("budget", "N/A")
        date = item.get("postedDate", "N/A")

        jobs.append({
            "title": title,
            "short_description": short_desc,
            "budget": budget,
            "date": date,
            "url": link,
            "platform": "Workana",
        })

    return jobs

# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------

def build_page_url(base_url: str, page_number: int) -> str:
    if "page=" in base_url:
        return re.sub(r"page=\d+", f"page={page_number}", base_url)
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}page={page_number}"

# ---------------------------------------------------------------------------
# Main scrape
# ---------------------------------------------------------------------------

def scrape(
    start_url: str,
    csv_path: Path,
    json_path: Path | None,
    max_pages: int | None,
    notify_config: dict | None,
    seen_urls: Set[str],
    max_age_hours: float | None,
) -> List[Dict[str, str]]:
    session = requests.Session()
    all_jobs: List[Dict[str, str]] = []

    page = 1
    with Status("[bold blue]Iniciando scraping...", console=console) as status:
        while True:
            url = build_page_url(start_url, page)
            status.update(f"[bold blue]Procesando página {page}...")

            html = fetch_page(url, session)
            if html is None:
                break

            page_jobs = parse_jobs(html)
            if not page_jobs:
                console.print(f"[yellow][INFO][/yellow] No se encontraron más trabajos en la página {page}.")
                break

            new_jobs: List[Dict[str, str]] = []
            filtered_by_age = 0

            for job in page_jobs:
                job_url = (job.get("url") or "").strip()
                if not job_url or job_url in seen_urls:
                    continue

                if max_age_hours is not None:
                    job_age = parse_age_to_hours(job.get("date", ""))
                    if job_age > max_age_hours:
                        filtered_by_age += 1
                        continue

                new_jobs.append(job)
                seen_urls.add(job_url)

            all_jobs.extend(new_jobs)

            if filtered_by_age > 0 and max_age_hours is not None:
                console.print(f"[dim]Página {page}: {filtered_by_age} trabajos omitidos por ser más antiguos de {max_age_hours} horas.[/dim]")

            if new_jobs:
                table = Table(
                    title=f"Nuevos Trabajos - Página {page}",
                    box=box.ROUNDED,
                    show_header=True,
                    header_style="bold magenta"
                )
                table.add_column("Título", style="cyan", no_wrap=False)
                table.add_column("Presupuesto", style="green")
                table.add_column("Fecha", style="dim")

                for job in new_jobs:
                    handle_new_job(job)
                    table.add_row(job["title"], job["budget"], job["date"])

                console.print(table)

                if notify_config and notify_config.get("notify_email"):
                    for job in new_jobs:
                        msg = (
                            f"💼 <b>Título:</b> {job['title']}\n"
                            f"💰 <b>Presupuesto:</b> {job['budget']}\n"
                            f"📅 <b>Fecha:</b> {job['date']}\n"
                            f"🔗 <b>Link:</b> {job['url']}\n\n"
                            f"📝 <b>Descripción:</b> {job['short_description'][:200]}..."
                        )
                        notifications.notify("🆕 ¡Nuevo Trabajo Encontrado! 🚀", msg, notify_config)
            else:
                console.print(f"[dim]Página {page}: sin nuevos trabajos[/dim]")

            status.update("[bold dim]Esperando intervalo de cortesía...")
            polite_sleep()

            page += 1
            if max_pages and page > max_pages:
                break

    if all_jobs:
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        file_exists = csv_path.exists()

        with csv_path.open("a" if file_exists else "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["title", "short_description", "budget", "date", "url", "platform"])
            if not file_exists:
                writer.writeheader()
            writer.writerows(all_jobs)

        if json_path:
            json_path.parent.mkdir(parents=True, exist_ok=True)
            full_data = list(all_jobs)

            if json_path.exists():
                try:
                    with json_path.open("r", encoding="utf-8") as f:
                        old_data = json.load(f)
                        if isinstance(old_data, list):
                            old_urls = {j.get("url") for j in old_data}
                            for j in all_jobs:
                                if j.get("url") not in old_urls:
                                    old_data.append(j)
                            full_data = old_data
                except Exception:
                    pass

            with json_path.open("w", encoding="utf-8") as f:
                json.dump(full_data, f, ensure_ascii=False, indent=2)

        console.print(Panel(
            f"[bold green]¡Éxito![/bold green]\n"
            f"Se guardaron [bold]{len(all_jobs)}[/bold] nuevos trabajos.\n"
            f"CSV: {csv_path}\n"
            f"JSON: {json_path or 'N/A'}",
            border_style="green",
            title="Resultados"
        ))

        if notify_config and notify_config.get("notify_email"):
            notifications.notify(
                "🏁 Ciclo de Scraping Finalizado",
                f"✅ Se encontraron un total de <b>{len(all_jobs)}</b> nuevos trabajos en esta pasada.",
                notify_config
            )

    return all_jobs

if __name__ == "__main__":
    target_url = (os.getenv("URL") or DEFAULT_URL).strip()

    # Respect env vars but resolve simple filenames into the data directory
    csv_env = os.getenv("CSV_FILE")
    json_env = os.getenv("JSON_FILE")

    def resolve_output(p: str, default: Path) -> Path:
        if not p:
            return default
        pth = Path(p)
        # If user provided only a filename (no parent), place it under DATA_DIR
        if not pth.parent or str(pth.parent) in (".", ""):
            return DATA_DIR / pth.name
        return pth

    csv_path = resolve_output(csv_env, CSV_OUTPUT_DEFAULT)
    json_path = resolve_output(json_env, JSON_OUTPUT_DEFAULT) if (json_env or JSON_OUTPUT_DEFAULT) else None

    max_pages_str = (os.getenv("MAX_PAGES") or "").strip()
    max_pages = int(max_pages_str) if max_pages_str.isdigit() else None

    interval_str = (os.getenv("INTERVAL_MINUTES") or "10").strip()
    interval = int(interval_str) if interval_str.isdigit() else 10

    watch_mode = (os.getenv("WATCH_MODE") or "false").strip().lower() == "true"

    max_age_str = (os.getenv("MAX_AGE_HOURS") or "").strip()
    max_age = float(max_age_str) if max_age_str else None

    notify_email = (os.getenv("NOTIFY_EMAIL") or "false").strip().lower() == "true"
    notify_config = {"notify_email": True} if notify_email else None

    console.print(Panel(
        "[bold bright_white]Workana Scraper[/bold bright_white]\n"
        "[dim]Monitoreando la plataforma en tiempo real...[/dim]\n\n"
        "Presiona [bold red]Ctrl+C[/bold red] para detener.\n\n"
        "[italic grey70]Desarrollado por:[/italic grey70] [bold yellow]@constadinisio[/bold yellow]",
        title="[bold cyan]Workana Scraper[/bold cyan]",
        border_style="cyan",
        padding=(1, 2)
    ))

    seen = load_seen_urls(csv_path)
    if seen:
        console.print(f"[dim]Se cargaron {len(seen)} URLs previas para evitar duplicados.[/dim]")

    def run_once():
        now = datetime.now().strftime("%H:%M:%S")
        console.rule(f"[bold blue]Ciclo iniciado a las {now}[/bold blue]")
        scrape(
            start_url=target_url,
            csv_path=csv_path,
            json_path=json_path,
            max_pages=max_pages,
            notify_config=notify_config,
            seen_urls=seen,
            max_age_hours=max_age,
        )

    if not watch_mode:
        run_once()
    else:
        try:
            while True:
                run_once()
                next_run = datetime.fromtimestamp(time.time() + interval * 60).strftime("%H:%M:%S")
                console.print(f"\n[bold dim]Próximo chequeo programado para las {next_run}...[/bold dim]")
                time.sleep(interval * 60)
        except KeyboardInterrupt:
            console.print("\n[bold red]Scraper detenido por el usuario.[/bold red]")
