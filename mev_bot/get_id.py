import requests, time

TOKEN = "8544989599:AAEUj7HxoOz_48eyrCNDA9fNHcnYZz4Abwo"

def get_id():
    print("Waiting for you to message @bitbug21_bot...")
    while True:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
            res = requests.get(url).json()
            if res["result"]:
                chat_id = res["result"][-1]["message"]["chat"]["id"]
                print(f"\n✅ FOUND YOUR CHAT ID: {chat_id}")
                print("Update your .env with this number!")
                return chat_id
        except Exception as e:
            pass
        time.sleep(2)

if __name__ == "__main__":
    get_id()
