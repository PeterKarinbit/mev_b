from flask import Flask
import threading
import os
import subprocess

app = Flask(__name__)

@app.route('/')
def home():
    return "🚀 Linkivo MEV Bot is Hunting! (24/7 Enabled)"

def run_bots():
    # This fires up all our logic in the background on the Render server
    print("Starting MEV Engine...")
    subprocess.Popen(["python3", "mev_bot/executor.py"])
    subprocess.Popen(["python3", "mev_bot/radar.py"])
    subprocess.Popen(["python3", "mev_bot/listener.py"])

if __name__ == "__main__":
    # Start bots in a separate thread so the web server can work
    threading.Thread(target=run_bots, daemon=True).start()
    
    # Render provides a PORT environment variable
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
