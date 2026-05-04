import os
import sys
import json
import asyncio
import aiohttp
from quart import Quart, request, jsonify, render_template, session, redirect, url_for
from config import Config

# Add parent directory to path to import bot logic
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import bot as bot_logic

app = Quart(__name__)
app.secret_key = os.getenv("DASHBOARD_SECRET_KEY", "KAIZER_X_SECRET_DASHBOARD_KEY")

# Ensure directories exist
DB_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOTS_CONFIG_FILE = os.path.join(DB_DIR, "database", "bots_config.json")
LOGS_DIR = os.path.join(DB_DIR, "logs")

if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR, exist_ok=True)

# In-memory dictionary tracking running bot instances {bot_id: bot_object}
running_bots = {}

# --- Manual Discord OAuth Implementation (Fallback for Missing quart-discord) ---
DISCORD_API_BASE_URL = "https://discord.com/api"
DISCORD_TOKEN_URL = f"{DISCORD_API_BASE_URL}/oauth2/token"
DISCORD_USER_URL = f"{DISCORD_API_BASE_URL}/users/@me"

async def exchange_code(code):
    data = {
        'client_id': Config.CLIENT_ID,
        'client_secret': Config.CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': Config.REDIRECT_URI,
        'scope': 'identify'
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    async with aiohttp.ClientSession() as session:
        async with session.post(DISCORD_TOKEN_URL, data=data, headers=headers) as resp:
            return await resp.json()

async def get_user_info(access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    async with aiohttp.ClientSession() as session:
        async with session.get(DISCORD_USER_URL, headers=headers) as resp:
            return await resp.json()

# --- Bot Management Logic (In-Process Fallback) ---

def load_bots_config():
    if not os.path.exists(BOTS_CONFIG_FILE):
        if not os.path.exists(os.path.dirname(BOTS_CONFIG_FILE)):
            os.makedirs(os.path.dirname(BOTS_CONFIG_FILE), exist_ok=True)
        with open(BOTS_CONFIG_FILE, 'w') as f:
            json.dump({}, f)
    with open(BOTS_CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_bots_config(data):
    with open(BOTS_CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=4)

async def start_bot_instance(bot_id):
    """
    Starts a bot instance as an internal asyncio task.
    """
    config = load_bots_config().get(bot_id)
    if not config or not config.get("token"):
        return False
        
    if bot_id in running_bots:
        # Stop existing instance if running
        await stop_bot_instance(bot_id)

    print(f"[ DASHBOARD ] Launching Bot Instance: {bot_id} (In-Process)")
    
    # Create the bot object using our refactored bot_logic
    bot_obj = bot_logic.create_bot(config["token"], bot_id)
    
    # Start it as a background task
    task = asyncio.create_task(bot_obj.start(config["token"]))
    running_bots[bot_id] = {"bot": bot_obj, "task": task}
    return True

async def stop_bot_instance(bot_id):
    if bot_id in running_bots:
        data = running_bots.pop(bot_id)
        bot_obj = data["bot"]
        task = data["task"]
        
        print(f"[ DASHBOARD ] Stopping Bot Instance: {bot_id}")
        await bot_obj.close()
        task.cancel()
        return True
    return False

@app.before_serving
async def startup():
    print("[ DASHBOARD ] Initializing Multi-Instance Controller...")
    # Auto-start all configured bots
    configs = load_bots_config()
    for bot_id in configs:
        await start_bot_instance(bot_id)

@app.route('/')
async def index():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    return await render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
async def login():
    error = None
    if request.method == 'POST':
        form = await request.form
        # Hardcoded fallback credentials as requested for quick access
        if form.get('username') == 'kali' and form.get('password') == 'kali':
            session['admin_logged_in'] = True
            return redirect(url_for('index'))
        else:
            error = "Invalid Credentials. Access denied."
    return await render_template('login.html', error=error)

@app.route('/callback')
async def callback():
    code = request.args.get('code')
    if not code:
        return "Error: No code provided", 400
    
    token_data = await exchange_code(code)
    if 'access_token' not in token_data:
        return f"Error: Failed to exchange code. {token_data}", 400
    
    user_info = await get_user_info(token_data['access_token'])
    session['admin_logged_in'] = True # For now, allow any successful Discord login to see the dash
    session['user_id'] = user_info.get('id')
    session['username'] = user_info.get('username')
    
    return redirect(url_for('index'))

@app.route('/logout')
async def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/bots', methods=['GET'])
async def get_bots():
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    configs = load_bots_config()
    status = {}
    for bid, cfg in configs.items():
        is_running = bid in running_bots and not running_bots[bid]["bot"].is_closed()
        status[bid] = {
            "running": is_running,
            "token": f"{cfg.get('token')[:10]}...{cfg.get('token')[-5:]}" if cfg.get('token') else ""
        }
    return jsonify(status)

@app.route('/api/bots/add', methods=['POST'])
async def add_bot():
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = await request.json
    bot_id = data.get("id")
    token = data.get("token")
    
    if not bot_id or not token:
        return jsonify({"error": "Missing id or token"}), 400
        
    configs = load_bots_config()
    configs[bot_id] = {"token": token}
    save_bots_config(configs)
    
    await start_bot_instance(bot_id)
    return jsonify({"success": True, "message": f"Bot {bot_id} added and started."})

@app.route('/api/bots/stop', methods=['POST'])
async def stop_bot():
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    data = await request.json
    bot_id = data.get("id")
    
    if await stop_bot_instance(bot_id):
        return jsonify({"success": True, "message": f"Bot {bot_id} stopped."})
    return jsonify({"error": "Bot not running"}), 400

@app.route('/api/logs/<bot_id>')
async def get_logs(bot_id):
    if not session.get('admin_logged_in'): return jsonify({"error": "Unauthorized"}), 401
    log_path = os.path.join(LOGS_DIR, f"{bot_id}.log")
    if not os.path.exists(log_path):
        return jsonify({"logs": "No logs found yet."})
        
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            return jsonify({"logs": "".join(lines[-100:])})
    except Exception as e:
        return jsonify({"logs": f"Error reading logs: {e}"})

if __name__ == "__main__":
    app.run(port=Config.PORT, host="0.0.0.0")
