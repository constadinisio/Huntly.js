# workana_scraper.py
"""
A robust web scraper for extracting job offers from Workana (or similar job listing sites).

Features:
- Uses `requests` with realistic headers and random delays.
- Parses listings with BeautifulSoup.
- Handles pagination automatically.
- Saves results to CSV and optionally JSON.
- Deduplicates entries based on the job URL.
- Prints progress to the console.

The scraper is written in a modular way so you can adapt it to other sites by
changing the `parse_jobs` function and the pagination logic.
"""

import csv
import json
import random
import time
import re
from pathlib import Path
from typing import List, Dict, Set

import requests
from bs4 import BeautifulSoup
import notifications
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Rich for beautiful TUI
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.status import Status
from rich import box
from datetime import datetime

console = Console()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DEFAULT_URL = "https://www.workana.com/jobs?language=es&publication=1d&skills=html"
USER_AGENT_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

# Delay range (seconds) between requests – adjust for respectful crawling
DELAY_MIN = 3
DELAY_MAX = 7

# Output files
CSV_OUTPUT = Path("workana_jobs.csv")
JSON_OUTPUT = Path("workana_jobs.json")

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def get_headers() -> dict:
    """Return a headers dict with a random realistic User‑Agent."""
    return {"User-Agent": random.choice(USER_AGENT_LIST)}


def polite_sleep():
    """Sleep for a random interval within the configured range."""
    time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))


def load_seen_urls(csv_path: Path) -> Set[str]:
    """Load job URLs from the existing CSV to avoid double notifications."""
    seen = set()
    if csv_path.exists():
        try:
            with csv_path.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if "url" in row:
                        seen.add(row["url"])
        except Exception as exc:
            console.print(f"[bold yellow][WARN][/bold yellow] Could not load existing CSV: {exc}")
    return seen


def parse_age_to_hours(date_str: str) -> float:
    """Convert human-readable age string (e.g., 'Hace 3 horas') to hours."""
    low_date = date_str.lower()
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
    return 999.0  # Default to very old if unknown


def fetch_page(url: str, session: requests.Session) -> str | None:
    """Download a page and return its HTML text.

    Handles HTTP errors and time‑outs gracefully – returns ``None`` on failure.
    """
    try:
        response = session.get(url, headers=get_headers(), timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as exc:
        console.print(f"[bold red][ERROR][/bold red] Failed to fetch {url}: {exc}")
        return None

# ---------------------------------------------------------------------------
# Parsing logic – adapt this for other sites
# ---------------------------------------------------------------------------

def parse_jobs(html: str) -> List[Dict[str, str]]:
    """
    Parses job offers from Workana's HTML by extracting the JSON
    data embedded in the <search> tag.
    """
    soup = BeautifulSoup(html, "html.parser")
    jobs = []

    # Workana embeds the initial job results in a <search> tag's ':results-initials' attribute
    search_tag = soup.find("search")
    if not search_tag:
        return []

    results_attr = search_tag.get(":results-initials")
    if not results_attr:
        return []

    try:
        data = json.loads(results_attr)
        results = data.get("results", [])
    except (json.JSONDecodeError, AttributeError):
        return []

    for item in results:
        # The 'title' field in JSON often contains an HTML snippet with the link
        title_html = item.get("title", "")
        title_soup = BeautifulSoup(title_html, "html.parser")
        title_tag = title_soup.find("span") or title_soup.find("a")
        title = title_tag.get("title") or title_tag.get_text() if title_tag else "N/A"
        
        # Extract link from titlesoup if present, otherwise use slug
        link_tag = title_soup.find("a")
        if link_tag and link_tag.get("href"):
            link = link_tag.get("href")
            if link.startswith("/"):
                link = "https://www.workana.com" + link
        else:
            slug = item.get("slug")
            link = f"https://www.workana.com/job/{slug}" if slug else "N/A"

        # Description and other fields
        short_desc = item.get("description", "").replace("<br/>", " ").replace("<br />", " ").strip()
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
# Pagination handling – generic but works for Workana's "page" query param
# ---------------------------------------------------------------------------

def build_page_url(base_url: str, page_number: int) -> str:
    """Return a URL for the given page number.

    Workana uses the ``page`` query parameter. If the base URL already contains
    parameters, we simply append ``&page=``; otherwise we add ``?page=``.
    """
    if "page=" in base_url:
        # Replace existing page parameter (unlikely for the default URL)
        return re.sub(r"page=\d+", f"page={page_number}", base_url)
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}page={page_number}"

# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

def scrape(
    start_url: str = DEFAULT_URL,
    csv_path: Path = CSV_OUTPUT,
    json_path: Path | None = JSON_OUTPUT,
    max_pages: int | None = None,
    notify_config: dict | None = None,
    seen_urls: Set[str] | None = None,
    max_age_hours: float | None = None, # Added parameter
) -> List[Dict[str, str]]:
    """Run the scraper and return the collected job entries.

    Parameters
    ----------
    start_url: str
        The first page to crawl. Can be changed to point to another site.
    csv_path: Path
        Where to write the CSV file.
    json_path: Path | None
        Optional JSON output file.
    max_pages: int | None
        Upper bound for pagination – useful for testing. ``None`` means crawl
        until no new jobs are found.
    seen_urls: Set[str] | None
        Optional set of already scraped URLs to avoid duplicates/notifications.
    """
    session = requests.Session()
    if seen_urls is None:
        seen_urls = set()
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
            
            # Deduplicate and Filter by Age
            new_jobs = []
            filtered_by_age = 0
            for job in page_jobs:
                is_new = job["url"] not in seen_urls
                if not is_new:
                    continue
                
                # Time filter logic
                if max_age_hours is not None:
                    job_age = parse_age_to_hours(job["date"])
                    if job_age > max_age_hours:
                        filtered_by_age += 1
                        continue
                
                new_jobs.append(job)
                seen_urls.add(job["url"])
            
            all_jobs.extend(new_jobs)
            
            if filtered_by_age > 0:
                console.print(f"[dim]Página {page}: {filtered_by_age} trabajos omitidos por ser más antiguos de {max_age_hours} horas.[/dim]")

            if new_jobs:
                # Show results in a table for each page
                table = Table(title=f"Nuevos Trabajos - Página {page}", box=box.ROUNDED, show_header=True, header_style="bold magenta")
                table.add_column("Título", style="cyan", no_wrap=False)
                table.add_column("Presupuesto", style="green")
                table.add_column("Fecha", style="dim")
                
                for job in new_jobs:
                    table.add_row(job["title"], job["budget"], job["date"])
                
                console.print(table)
                
                # Notifications
                if notify_config:
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
                console.print(f"[dim]Página {page}: No hay trabajos nuevos.[/dim]")
            
            # Watch Mode logic/Polite sleep
            status.update(f"[bold dim]Esperando intervalo de cortesía...")
            polite_sleep()
            page += 1
            if max_pages and page > max_pages:
                break
    # -------------------------------------------------------------------
    # Persist results
    # -------------------------------------------------------------------
    if all_jobs:
        # Saving Logic
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
                            old_urls = {j["url"] for j in old_data}
                            for j in all_jobs:
                                if j["url"] not in old_urls:
                                    old_data.append(j)
                            full_data = old_data
                except Exception: pass
            with json_path.open("w", encoding="utf-8") as f:
                json.dump(full_data, f, ensure_ascii=False, indent=2)
        
        console.print(Panel(f"[bold green]¡Éxito![/bold green]\nSe guardaron [bold]{len(all_jobs)}[/bold] nuevos trabajos.\nCSV: {csv_path}\nJSON: {json_path or 'N/A'}", border_style="green", title="Resultados"))
        
        if notify_config:
            notifications.notify(
                "🏁 Ciclo de Scraping Finalizado", 
                f"✅ Se encontraron un total de <b>{len(all_jobs)}</b> nuevos trabajos en esta pasada.", 
                notify_config
            )
    else:
        console.print("[bold yellow]No se encontraron nuevos trabajos en esta pasada.[/bold yellow]")
    return all_jobs

# ---------------------------------------------------------------------------
# Entry point for command‑line execution
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Workana job scraper with notifications")
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help="Base URL to start scraping (default: Workana jobs page)",
    )
    parser.add_argument(
        "--csv",
        default=str(CSV_OUTPUT),
        help="Path to output CSV file",
    )
    parser.add_argument(
        "--json",
        default=str(JSON_OUTPUT),
        help="Path to optional JSON output file (set empty string to skip)",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Maximum number of pages to crawl (useful for testing)",
    )
    # Notification related arguments
    parser.add_argument("--notify-email", action="store_true", help="Enable email notifications")
    parser.add_argument("--notify-telegram", action="store_true", help="Enable Telegram notifications")
    parser.add_argument("--smtp-server", help="SMTP server address")
    parser.add_argument("--smtp-port", type=int, help="SMTP server port")
    parser.add_argument("--smtp-user", help="SMTP username / sender email")
    parser.add_argument("--smtp-pass", help="SMTP password or app token")
    parser.add_argument("--email-to", help="Recipient email address")
    parser.add_argument("--tg-token", help="Telegram bot token")
    parser.add_argument("--tg-chat", help="Telegram chat ID")
    parser.add_argument(
        "--max-age-hours",
        type=float,
        help="Only process jobs posted within the last X hours (e.g., 3)",
    )
    parser.add_argument("--watch", action="store_true", help="Run continuously (Watch Mode)")
    parser.add_argument("--interval", type=int, default=10, help="Interval in minutes between checks (default: 10)")

    args = parser.parse_args()

    # --- Configuration Loading ---
    config = {}
    config_path = Path("config.json")
    if config_path.exists():
        try:
            with config_path.open("r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as exc:
            console.print(f"[bold yellow][WARN][/bold yellow] No se pudo cargar config.json: {exc}")

    def get_config_val(env_key, json_key, default=None):
        """Helper to get config value from ENV, then JSON, then default."""
        val = os.getenv(env_key)
        if val is not None and val != "":
            # Convert numeric strings if necessary
            if env_key in ["SMTP_PORT", "INTERVAL_MINUTES", "MAX_PAGES"]:
                try: return int(val)
                except: pass
            if env_key in ["MAX_AGE_HOURS"]:
                try: return float(val)
                except: pass
            if env_key in ["NOTIFY_EMAIL", "NOTIFY_TELEGRAM", "WATCH_MODE"]:
                return val.lower() == "true"
            return val
        return config.get(json_key, default)

    # Build notification config from ENV/JSON defaults + CLI overrides
    notify_config = {}
    
    # Email settings
    is_email_active = args.notify_email or get_config_val("NOTIFY_EMAIL", "notify_email", False)
    if is_email_active:
        notify_config.update({
            "notify_email": True,
            "smtp_server": args.smtp_server or get_config_val("SMTP_SERVER", "smtp_server"),
            "smtp_port": args.smtp_port or get_config_val("SMTP_PORT", "smtp_port"),
            "smtp_user": args.smtp_user or get_config_val("SMTP_USER", "smtp_user"),
            "smtp_pass": args.smtp_pass or get_config_val("SMTP_PASS", "smtp_pass"),
            "email_to": args.email_to or get_config_val("EMAIL_TO", "email_to"),
        })

    # Telegram settings
    is_tg_active = args.notify_telegram or get_config_val("NOTIFY_TELEGRAM", "notify_telegram", False)
    if is_tg_active:
        notify_config.update({
            "notify_telegram": True,
            "tg_token": args.tg_token or get_config_val("TG_TOKEN", "tg_token"),
            "tg_chat": str(args.tg_chat or get_config_val("TG_CHAT", "tg_chat", "")),
        })

    if not notify_config:
        notify_config = None

    # General settings
    target_url = args.url if args.url != DEFAULT_URL else get_config_val("URL", "url", DEFAULT_URL)
    csv_path = Path(args.csv if args.csv != str(CSV_OUTPUT) else get_config_val("CSV_FILE", "csv", str(CSV_OUTPUT)))
    json_path_str = args.json if args.json != str(JSON_OUTPUT) else get_config_val("JSON_FILE", "json", str(JSON_OUTPUT))
    json_path = Path(json_path_str) if json_path_str else None
    
    max_pages = args.max_pages if args.max_pages is not None else get_config_val("MAX_PAGES", "max_pages")
    interval = args.interval if args.interval != 10 else get_config_val("INTERVAL_MINUTES", "interval", 10)
    watch_mode = args.watch or get_config_val("WATCH_MODE", "watch", False)
    max_age = args.max_age_hours if args.max_age_hours is not None else get_config_val("MAX_AGE_HOURS", "max_age_hours")

    if watch_mode:
        console.print(Panel(
            "[bold bright_white]MODO WATCH ACTIVADO[/bold bright_white]\n"
            "[dim]Monitoreando la plataforma en tiempo real...[/dim]\n\n"
            "Presiona [bold red]Ctrl+C[/bold red] para detener.\n\n"
            "[italic grey70]Desarrollado por:[/italic grey70] [bold yellow]@constadinisio[/bold yellow]",
            title="[bold cyan]Workana Scraper[/bold cyan]",
            border_style="cyan",
            padding=(1, 2)
        ))
        
        seen_urls = load_seen_urls(csv_path)
        if seen_urls:
            console.print(f"[dim]Se cargaron {len(seen_urls)} URLs previas para evitar duplicados.[/dim]")

        try:
            while True:
                now = datetime.now().strftime("%H:%M:%S")
                console.rule(f"[bold blue]Ciclo iniciado a las {now}[/bold blue]")
                
                scrape(
                    start_url=target_url,
                    csv_path=csv_path,
                    json_path=json_path,
                    max_pages=max_pages,
                    notify_config=notify_config,
                    seen_urls=seen_urls,
                    max_age_hours=max_age,
                )
                
                next_run = datetime.fromtimestamp(time.time() + interval * 60).strftime("%H:%M:%S")
                console.print(f"\n[bold dim]Próximo chequeo programado para las {next_run}...[/bold dim]")
                time.sleep(interval * 60)
        except KeyboardInterrupt:
            console.print("\n[bold red]Scraper detenido por el usuario.[/bold red]")
    else:
        # Single run mode
        console.print(Panel(
            "[bold bright_white]INICIANDO ESCANEO ÚNICO[/bold bright_white]\n"
            "[dim]Extrayendo trabajos de las páginas configuradas...[/dim]\n\n"
            "[italic grey70]Desarrollado por:[/italic grey70] [bold yellow]@constadinisio[/bold yellow]",
            title="[bold green]Workana Scraper[/bold green]",
            border_style="green",
            padding=(1, 2)
        ))
        seen_urls = load_seen_urls(csv_path)
        scrape(
            start_url=target_url,
            csv_path=csv_path,
            json_path=json_path,
            max_pages=max_pages,
            notify_config=notify_config,
            seen_urls=seen_urls,
            max_age_hours=max_age,
        )
