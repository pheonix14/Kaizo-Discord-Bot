import os
import sys
import json
import asyncio
import subprocess
from quart import Quart, request, jsonify, render_template

app = Quart(__name__)
app.secret_key = "KAIZER_X_SECRET_DASHBOARD_KEY"

# Ensure directories exist
DB_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOTS_CONFIG_FILE = os.path.join(DB_DIR, "database", "bots_config.json")
LOGS_DIR = os.path.join(DB_DIR, "logs")

# In-memory dictionary tracking running subprocesses {bot_id: subprocess.Popen}
running_bots = {}

def load_bots_config():
    if not os.path.exists(BOTS_CONFIG_FILE):
        with open(BOTS_CONFIG_FILE, 'w') as f:
            json.dump({}, f)
    with open(BOTS_CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_bots_config(data):
    with open(BOTS_CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=4)

async def watchdog_task():
    """
    Background task that constantly monitors running bots.
    If a bot subprocess dies unexpectedly, it restarts it.
    """
    while True:
        for bot_id, proc in list(running_bots.items()):
            if proc.poll() is not None:
                print(f"[ WATCHDOG ] Bot {bot_id} crashed with exit code {proc.returncode}. Restarting...")
                await start_bot_process(bot_id)
        await asyncio.sleep(5)

async def start_bot_process(bot_id):
    config = load_bots_config().get(bot_id)
    if not config:
        return False
        
    token = config.get("token")
    if not token:
        return False

    # Start the bot as a detached subprocess
    bot_path = os.path.join(DB_DIR, "bot.py")
    proc = subprocess.Popen(
        [sys.executable, bot_path, "--token", token, "--id", bot_id],
        cwd=DB_DIR,
        stdout=subprocess.DEVNULL, # Handled by bot.py's internal logging to file
        stderr=subprocess.DEVNULL
    )
    running_bots[bot_id] = proc
    print(f"[ DASHBOARD ] Started Bot Instance: {bot_id} (PID: {proc.pid})")
    return True

@app.before_serving
async def startup():
    print("[ DASHBOARD ] Starting Watchdog Manager...")
    app.add_background_task(watchdog_task)
    
    # Auto-start all configured bots
    configs = load_bots_config()
    for bot_id in configs:
        await start_bot_process(bot_id)

@app.route('/')
async def index():
    return await render_template('index.html')

@app.route('/api/bots', methods=['GET'])
async def get_bots():
    configs = load_bots_config()
    status = {}
    for bid, cfg in configs.items():
        status[bid] = {
            "running": bid in running_bots and running_bots[bid].poll() is None,
            "token": f"{cfg.get('token')[:10]}...{cfg.get('token')[-5:]}" if cfg.get('token') else ""
        }
    return jsonify(status)

@app.route('/api/bots/add', methods=['POST'])
async def add_bot():
    data = await request.json
    bot_id = data.get("id")
    token = data.get("token")
    
    if not bot_id or not token:
        return jsonify({"error": "Missing id or token"}), 400
        
    configs = load_bots_config()
    configs[bot_id] = {"token": token}
    save_bots_config(configs)
    
    await start_bot_process(bot_id)
    return jsonify({"success": True, "message": f"Bot {bot_id} added and started."})

@app.route('/api/bots/stop', methods=['POST'])
async def stop_bot():
    data = await request.json
    bot_id = data.get("id")
    
    if bot_id in running_bots:
        proc = running_bots.pop(bot_id)
        proc.terminate()
        return jsonify({"success": True, "message": f"Bot {bot_id} stopped."})
    return jsonify({"error": "Bot not running"}), 400

@app.route('/api/logs/<bot_id>')
async def get_logs(bot_id):
    """
    Returns the last 100 lines of the bot's log file.
    """
    log_path = os.path.join(LOGS_DIR, f"{bot_id}.log")
    if not os.path.exists(log_path):
        return jsonify({"logs": "No logs found yet."})
        
    with open(log_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        return jsonify({"logs": "".join(lines[-100:])})

if __name__ == "__main__":
    app.run(port=5000, host="0.0.0.0")
