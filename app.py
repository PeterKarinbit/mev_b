from flask import Flask
import threading
import os
import subprocess
import time

app = Flask(__name__)

@app.route('/')
def home():
    return "🚀 **Linkivo MEV Bot** is actively hunting on Base!<br>Remote control is enabled via Telegram. 🏹💀⚓️"

def run_bots():
    # Wait a few seconds for the environment to settle
    time.sleep(5)
    print("Starting MEV Engine components...")
    # These start the bots in the background on Render's server
    subprocess.Popen(["python3", "mev_bot/executor.py"])
    subprocess.Popen(["python3", "mev_bot/radar.py"])
    subprocess.Popen(["python3", "mev_bot/listener.py"])

# Start bots IMMEDIATELY upon deployment
threading.Thread(target=run_bots, daemon=True).start()

if __name__ == "__main__":
    # Render provides a PORT environment variable
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
