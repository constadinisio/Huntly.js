import os
import json
from pathlib import Path
from dotenv import load_dotenv
import notifications

# Load environment variables
load_dotenv()

def test_telegram():
    # Helper to get config
    tg_token = os.getenv("TG_TOKEN")
    tg_chat = os.getenv("TG_CHAT")
    notify_tg = os.getenv("NOTIFY_TELEGRAM", "false").lower() == "true"

    # Fallback to config.json if not in ENV
    if not tg_token or not tg_chat:
        config_path = Path("config.json")
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                tg_token = tg_token or config.get("tg_token")
                tg_chat = tg_chat or config.get("tg_chat")
                notify_tg = notify_tg or config.get("notify_telegram", False)

    if not notify_tg:
        print("Telegram notifications are disabled (NOTIFY_TELEGRAM=false)")
        return

    if not tg_token or not tg_chat:
        print("Error: TG_TOKEN or TG_CHAT not found in .env or config.json")
        return

    notify_config = {
        "notify_telegram": True,
        "tg_token": tg_token,
        "tg_chat": tg_chat
    }

    print(f"Sending test notification to Telegram Chat ID: {notify_config['tg_chat']}...")
    try:
        notifications.notify(
            "Test Scraper", 
            "¡Hola! Esta es una prueba de notificación desde tu Workana Scraper. 🚀", 
            notify_config
        )
        print("Success! Check your Telegram.")
    except Exception as e:
        print(f"Failed to send notification: {e}")

if __name__ == "__main__":
    test_telegram()
