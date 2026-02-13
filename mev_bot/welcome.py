import requests, os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT = os.getenv("TELEGRAM_CHAT_ID")

def hello():
    if not TOKEN or not CHAT:
        print("Missing credentials!")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    msg = "🚀 **LINKIVO MEV BOT v2: ARMED AND READY** 🚀\n\nStrategies Active:\n1. Async Arbitrage\n2. Auto-Liquidation Radar\n\nI will alert you here on every successful strike or critical victim spotted. 🏹💀⚓️"
    requests.post(url, data={"chat_id": CHAT, "text": msg, "parse_mode": "Markdown"})
    print("Welcome message sent to Telegram!")

if __name__ == "__main__":
    hello()
