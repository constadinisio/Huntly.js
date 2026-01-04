# telegram_bot.py
import os
import asyncio
import html as html_lib
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode

from storage import get_job, set_status, set_proposal
from proposal_generator import generar_propuesta
from workana_sender import send_proposal_to_workana

# =========================
# Cargar variables .env
# =========================
load_dotenv()

def keyboard_send(job_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Enviar propuesta", callback_data=f"OK|{job_id}"),
        InlineKeyboardButton("❌ Ignorar", callback_data=f"NO|{job_id}")
    ]])

def keyboard_interest(job_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("⭐ Me interesa", callback_data=f"INT|{job_id}"),
        InlineKeyboardButton("❌ Ignorar", callback_data=f"NO|{job_id}")
    ]])

def build_message_with_proposal(job: dict) -> str:
    title = html_lib.escape(job.get("title", ""))
    budget = html_lib.escape(job.get("budget", "") or "")
    date = html_lib.escape(job.get("date", "") or "")
    url = job.get("url", "") or ""
    desc = html_lib.escape(job.get("description", "") or "")
    proposal = html_lib.escape(job.get("proposal", "") or "")

    # Evitar superar límites de Telegram
    proposal = proposal[:3000]

    return (
        "🆕 <b>¡Nuevo Trabajo Encontrado! 🚀</b>\n\n"
        f"💼 <b>Título:</b> {title}\n"
        f"💰 <b>Presupuesto:</b> {budget}\n"
        f"📅 <b>Fecha:</b> {date}\n"
        f"🔗 <b>Link:</b> <a href=\"{html_lib.escape(url)}\">{html_lib.escape(url)}</a>\n\n"
        "📝 <b>Descripción:</b>\n"
        f"{desc}\n\n"
        "✍️ <b>Propuesta:</b>\n"
        f"<pre><code>{proposal}</code></pre>"
    )

# =========================
# Callback de botones
# =========================
async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, job_id = query.data.split("|", 1)

    job = get_job(job_id)
    if not job:
        await query.message.reply_text("❌ No encontré el trabajo en la DB.")
        return

    if action == "NO":
        set_status(job_id, "ignored")
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text("🗑️ Proyecto ignorado.")
        return

    if action == "INT":
        job = get_job(job_id) or job

        if (job.get("proposal") or "").strip():
            await query.edit_message_text(
                text=build_message_with_proposal(job),
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard_send(job_id),
                disable_web_page_preview=True
            )
            return

        set_status(job_id, "generating")
        await query.message.reply_text("🧠 Generando propuesta...")

        payload = {
            "title": job.get("title", ""),
            "description": job.get("description", ""),
            "budget": job.get("budget", ""),
            "date": job.get("date", ""),
            "url": job.get("url", "")
        }

        maybe = generar_propuesta(payload)
        proposal = await maybe if asyncio.iscoroutine(maybe) else maybe
        proposal = (proposal or "").strip()

        set_proposal(job_id, proposal, status="pending_send")
        job = get_job(job_id) or job
        job["proposal"] = proposal

        await query.edit_message_text(
            text=build_message_with_proposal(job),
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard_send(job_id),
            disable_web_page_preview=True
        )
        return

    if action == "OK":
        job = get_job(job_id) or job
        proposal = (job.get("proposal") or "").strip()

        if not proposal:
            await query.message.reply_text("⚠️ No hay propuesta generada. Tocá primero ⭐ Me interesa.")
            await query.edit_message_reply_markup(reply_markup=keyboard_interest(job_id))
            return

        await query.message.reply_text("🚀 Abriendo Workana (modo visible) y enviando la propuesta...")

        ok = await send_proposal_to_workana(job["url"], proposal)

        if ok:
            set_status(job_id, "sent")
            await query.edit_message_reply_markup(reply_markup=None)
            await query.message.reply_text("✅ Propuesta enviada correctamente en Workana.")
        else:
            set_status(job_id, "error")
            await query.message.reply_text("❌ Error al enviar la propuesta.")
        return

# =========================
# MAIN (thread-safe en Py 3.14)
# =========================
def main():
    # ✅ En threads NO hay loop: lo creamos y seteamos
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    token = (os.getenv("TG_BOT_TOKEN") or os.getenv("TG_TOKEN") or "").strip()
    if not token:
        raise RuntimeError("❌ Falta TG_BOT_TOKEN (o TG_TOKEN) en el archivo .env")

    app = Application.builder().token(token).build()
    app.add_handler(CallbackQueryHandler(on_callback))

    print("🤖 Bot de Telegram iniciado. Esperando acciones...")

    # ✅ En thread: no registrar señales (stop_signals=None)
    app.run_polling(close_loop=False, stop_signals=None)

if __name__ == "__main__":
    main()
