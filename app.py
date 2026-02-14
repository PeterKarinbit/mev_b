from flask import Flask
import subprocess
import threading
import os
import time

app = Flask(__name__)

def run_script(script_name):
    """Run a Python script in the background."""
    print(f"🚀 Starting {script_name}...")
    subprocess.Popen(["python3", script_name])

# Start MEV Bots in separate threads to not block Flask
def start_bots():
    time.sleep(5)  # Wait for Flask to stabilize
    run_script("mev_bot/radar.py")
    run_script("mev_bot/gorilla_bot.py")

# Launch the bots when the app starts
threading.Thread(target=start_bots, daemon=True).start()

@app.route('/')
def home():
    return """
    <h1>🦍 Linkivo MEV System Active</h1>
    <ul>
        <li><b>Gorilla Bot:</b> HUNTING [Silent Mode]</li>
        <li><b>Whale Radar:</b> SCANNING</li>
        <li><b>Flash Engine:</b> ARMED ($2,000)</li>
    </ul>
    """

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
