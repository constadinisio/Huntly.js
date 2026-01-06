"""Notifications utilities for Huntly core."""
import logging
import smtplib
from email.mime.text import MIMEText
from typing import Dict
import requests


def send_email(subject: str, body: str, cfg: Dict[str, str]) -> None:
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = cfg.get("smtp_user", "")
        msg["To"] = cfg.get("email_to", "")
        with smtplib.SMTP(cfg.get("smtp_server", ""), int(cfg.get("smtp_port", 0)), timeout=10) as server:
            if cfg.get("smtp_user"):
                server.starttls()
                server.login(cfg.get("smtp_user"), cfg.get("smtp_pass", ""))
            server.send_message(msg)
    except Exception as exc:
        logging.error(f"[NOTIFY] Email send failed: {exc}")


def send_telegram(message: str, cfg: Dict[str, str]) -> None:
    try:
        url = f"https://api.telegram.org/bot{cfg.get('tg_token')}/sendMessage"
        payload = {
            "chat_id": cfg.get("tg_chat"),
            "text": message,
            "parse_mode": "HTML"
        }
        resp = requests.post(url, data=payload, timeout=10)
        resp.raise_for_status()
    except Exception as exc:
        logging.error(f"[NOTIFY] Telegram send failed: {exc}")


def notify(subject: str, body: str, cfg: Dict[str, any]) -> None:
    if not cfg:
        return
    
    if cfg.get("notify_email"):
        send_email(subject, body, cfg)
    
    if cfg.get("notify_telegram"):
        full_msg = f"<b>{subject}</b>\n\n{body}"
        send_telegram(full_msg, cfg)
