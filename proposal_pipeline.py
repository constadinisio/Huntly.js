# proposal_pipeline.py
import os
import html
import hashlib
import asyncio
import threading
from dotenv import load_dotenv
from bs4 import BeautifulSoup

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.request import HTTPXRequest

from storage import upsert_job

load_dotenv()

TG_BOT_TOKEN = (os.getenv("TG_BOT_TOKEN") or os.getenv("TG_TOKEN") or "").strip()
TG_CHAT_ID = (os.getenv("TG_CHAT_ID") or os.getenv("TG_CHAT") or "").strip()

def telegram_enabled() -> bool:
    return os.getenv("NOTIFY_TELEGRAM", "false").strip().lower() == "true"

if not TG_BOT_TOKEN or not TG_CHAT_ID:
    raise RuntimeError("❌ Falta TG_BOT_TOKEN/TG_TOKEN o TG_CHAT_ID/TG_CHAT en el .env")

# ✅ Aumentamos pool + timeouts (evita Pool timeout)
_request = HTTPXRequest(
    connection_pool_size=10,
    pool_timeout=20.0,
    connect_timeout=15.0,
    read_timeout=30.0,
    write_timeout=30.0,
)
bot = Bot(token=TG_BOT_TOKEN, request=_request)

# =========================================================
# Event loop dedicado + cola de envíos (1 por vez)
# =========================================================
_loop = asyncio.new_event_loop()
_queue: "asyncio.Queue[tuple[dict, str]]" = asyncio.Queue()

def _loop_runner():
    asyncio.set_event_loop(_loop)
    _loop.run_forever()

_thread = threading.Thread(target=_loop_runner, daemon=True)
_thread.start()

# Worker: manda 1 mensaje por vez y reintenta
async def _sender_worker():
    while True:
        job, job_id = await _queue.get()
        try:
            await _send_interest(job, job_id)
        except Exception as e:
            print(f"[proposal_pipeline] ⚠️ Worker error: {e!r}")
        finally:
            _queue.task_done()

# arrancar worker dentro del loop dedicado
def _start_worker():
    _loop.create_task(_sender_worker())

_loop.call_soon_threadsafe(_start_worker)

# =========================================================

def make_job_id(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]

def keyboard_interest(job_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("⭐ Me interesa", callback_data=f"INT|{job_id}"),
        InlineKeyboardButton("❌ Ignorar", callback_data=f"NO|{job_id}")
    ]])

def strip_html(text: str) -> str:
    if not text:
        return ""
    try:
        return BeautifulSoup(text, "html.parser").get_text(" ", strip=True)
    except Exception:
        return text.replace("<br/>", " ").replace("<br />", " ").replace("\n", " ").strip()

def build_message_no_proposal(job: dict) -> str:
    title = strip_html(job.get("title", ""))
    budget = strip_html(job.get("budget", "") or "")
    date = strip_html(job.get("date", "") or "")
    url = (job.get("url", "") or "").strip()

    desc_plain = strip_html(job.get("short_description", "") or "")
    if len(desc_plain) > 1200:
        desc_plain = desc_plain[:1200].rstrip() + "..."

    return (
        "🆕 <b>¡Nuevo Trabajo Encontrado! 🚀</b>\n\n"
        f"💼 <b>Título:</b> {html.escape(title)}\n"
        f"💰 <b>Presupuesto:</b> {html.escape(budget)}\n"
        f"📅 <b>Fecha:</b> {html.escape(date)}\n"
        f"🔗 <b>Link:</b> <a href=\"{html.escape(url)}\">{html.escape(url)}</a>\n\n"
        "📝 <b>Descripción:</b>\n"
        f"{html.escape(desc_plain)}"
    )

async def _send_interest(job: dict, job_id: str):
    # Reintentos suaves
    for attempt in range(1, 4):
        try:
            await bot.send_message(
                chat_id=TG_CHAT_ID,
                text=build_message_no_proposal(job),
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard_interest(job_id),
                disable_web_page_preview=True,
            )
            return
        except Exception as e:
            if attempt == 3:
                print(f"[proposal_pipeline] ⚠️ Error enviando Telegram (final): {e!r}")
                return
            # backoff: 1s, 2s
            await asyncio.sleep(attempt)

def handle_new_job(job: dict):
    url = (job.get("url") or "").strip()
    if not url or not url.startswith("http"):
        return

    # opcional: normalizar URL sin params
    url = url.split("?")[0]

    job_id = make_job_id(url)

    upsert_job(
        job_id=job_id,
        url=url,
        title=strip_html(job.get("title", "")),
        description=strip_html(job.get("short_description", "")),
        budget=strip_html(job.get("budget", "")),
        date=strip_html(job.get("date", "")),
        proposal="",
        status="pending_interest"
    )

    # Respeta NOTIFY_TELEGRAM
    if not telegram_enabled():
        return

    # ✅ Encolamos en vez de disparar 50 coroutines simultáneas
    def _enqueue():
        try:
            _queue.put_nowait((job, job_id))
        except Exception as e:
            print(f"[proposal_pipeline] ⚠️ No pude encolar mensaje: {e!r}")

    _loop.call_soon_threadsafe(_enqueue)
