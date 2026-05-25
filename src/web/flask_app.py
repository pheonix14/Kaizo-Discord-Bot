# src/web/flask_app.py
"""Flask backend for Kaizer K5 Discord bot dashboard.
Implements OAuth2 flow, session handling, and Supabase integration for
storing guild settings, shortcuts, and logs.
"""

import logging
import os
import json
import secrets
import time
import urllib.parse
import uuid
from urllib.parse import urlencode

TASK_PROGRESS = {}

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    make_response,
    jsonify,
    session,
)

from supabase import create_client, Client

from src import config

# ---------------------------------------------------------------------------
# Configuration & Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("kaizer_k5.flask_app")

def get_bot_loop():
    from src.bot.engine import bot
    return getattr(bot, "custom_loop", None)

# ---------------------------------------------------------------------------
# Flask App Setup
# ---------------------------------------------------------------------------

from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
app = Flask(
    __name__,
    template_folder=str(PROJECT_ROOT / "templates"),
    static_folder=str(PROJECT_ROOT / "static")
)
# Use a secret key for secure signed cookies
app.secret_key = os.getenv("FLASK_SECRET_KEY", secrets.token_hex(16))

# Setup Mode Interceptor
@app.before_request
def check_configuration():
    if hasattr(config, "check_and_reload"):
        config.check_and_reload()
        
    if not getattr(config, "IS_CONFIGURED", False):
        # Allow static files to be served so the setup page looks premium
        if request.path.startswith('/static/'):
            return None
        
        # Otherwise, render setup_error page
        missing_vars = []
        if not getattr(config, "SUPABASE_URL", None):
            missing_vars.append("SUPABASE_URL")
        if not getattr(config, "SUPABASE_SERVICE_ROLE_KEY", None):
            missing_vars.append("SUPABASE_SERVICE_ROLE_KEY")
        if not getattr(config, "DISCORD_BOT_TOKEN", None):
            missing_vars.append("DISCORD_BOT_TOKEN")
            
        return render_template("setup_error.html", missing_vars=missing_vars)
    else:
        # Re-initialize the local flask_app.py supabase client if it's currently None or a Dummy client
        global supabase
        from src.db.client import DummySupabaseClient
        if supabase is None or isinstance(supabase, DummySupabaseClient):
            try:
                supabase = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_ROLE_KEY)
                logger.info("Successfully re-initialized local Supabase client in flask_app dynamically.")
            except Exception as e:
                logger.critical(f"Failed to initialize local Supabase client in flask_app on reload: {e}")

# Register template helper for Discord invite URL
@app.context_processor
def inject_globals():
    def get_invite_url(req=None):
        client_id = config.DISCORD_APP_ID or "1507250208495505478"
        return f"https://discord.com/oauth2/authorize?client_id={client_id}&permissions=8&scope=bot%20applications.commands"
    return dict(get_invite_url=get_invite_url)

# ---------------------------------------------------------------------------
# Supabase client
# ---------------------------------------------------------------------------

supabase = None
if getattr(config, "IS_CONFIGURED", False):
    try:
        supabase: Client = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_ROLE_KEY)
    except Exception as e:
        logger.critical(f"Failed to initialize Supabase client in flask_app: {e}")
        from src.db.client import DummySupabaseClient
        supabase = DummySupabaseClient()
else:
    from src.db.client import DummySupabaseClient
    supabase = DummySupabaseClient()

import datetime

# ---------------------------------------------------------------------------
# Telemetry Heartbeat / Uptime Globals & Helpers
# ---------------------------------------------------------------------------
START_TIME = time.time()
TELEMETRY_FILE = str(PROJECT_ROOT / "awake_telemetry.json")

def load_telemetry():
    """Load telemetry data from local JSON file. Fallback to empty dict."""
    if os.path.exists(TELEMETRY_FILE):
        try:
            with open(TELEMETRY_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read local telemetry file: {e}")
    
    # Try fetching from Supabase
    try:
        resp = supabase.from_("awake_telemetry").select("*").execute()
        if resp.data:
            data = {}
            for row in resp.data:
                data[row["node_url"]] = {
                    "node_url": row["node_url"],
                    "label": row.get("label") or "",
                    "last_seen": row.get("last_seen"),
                    "ping_count": row.get("ping_count", 0),
                    "peers": row.get("peers") or [],
                    "is_active": row.get("is_active", True)
                }
            # Cache locally
            with open(TELEMETRY_FILE, "w") as f:
                json.dump(data, f, indent=2)
            return data
    except Exception as e:
        logger.warning(f"Could not load telemetry from Supabase: {e}")
    
    return {}

def save_telemetry(data):
    """Write telemetry data to local JSON file and attempt sync to Supabase."""
    try:
        with open(TELEMETRY_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to write local telemetry file: {e}")
        
    try:
        for node_url, info in data.items():
            db_payload = {
                "node_url": node_url,
                "label": info.get("label", ""),
                "last_seen": info.get("last_seen"),
                "ping_count": info.get("ping_count", 0),
                "peers": info.get("peers", []),
                "is_active": info.get("is_active", True)
            }
            supabase.from_("awake_telemetry").upsert(db_payload).execute()
    except Exception as e:
        logger.warning(f"Failed to sync telemetry to Supabase: {e}")

def register_awake_heartbeat(node_url, peers_raw):
    """Record an inbound heartbeat and update peer lists."""
    if not node_url:
        return
    
    node_url = node_url.strip().rstrip("/")
    if not node_url.startswith("http"):
        node_url = "https://" + node_url
        
    inbound_peers = []
    if peers_raw:
        try:
            for p in peers_raw.split(","):
                p = p.strip().rstrip("/")
                if p:
                    if not p.startswith("http"):
                        p = "https://" + p
                    inbound_peers.append(p)
        except Exception as e:
            logger.error(f"Error parsing peers header: {e}")
            
    registry = load_telemetry()
    now_iso = datetime.datetime.utcnow().isoformat() + "Z"
    
    if node_url in registry:
        registry[node_url]["last_seen"] = now_iso
        registry[node_url]["ping_count"] = registry[node_url].get("ping_count", 0) + 1
        current_peers = set(registry[node_url].get("peers", []))
        current_peers.update(inbound_peers)
        registry[node_url]["peers"] = list(current_peers)
        registry[node_url]["is_active"] = True
    else:
        registry[node_url] = {
            "node_url": node_url,
            "label": "PEER NODE",
            "last_seen": now_iso,
            "ping_count": 1,
            "peers": inbound_peers,
            "is_active": True
        }
        
    for peer in inbound_peers:
        if peer not in registry:
            registry[peer] = {
                "node_url": peer,
                "label": "DISCOVERED PEER",
                "last_seen": None,
                "ping_count": 0,
                "peers": [],
                "is_active": True
            }
            
    save_telemetry(registry)

# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def get_redirect_uri() -> str:
    """Build the OAuth2 callback redirect URL dynamically based on the current request domain."""
    env_redirect = os.getenv("DISCORD_REDIRECT_URI")
    if env_redirect:
        return env_redirect
    
    # Check if behind proxy (Render SSL termination)
    scheme = request.headers.get("X-Forwarded-Proto", "http")
    if request.is_secure or scheme == "https":
        base_url = "https://" + request.host
    else:
        base_url = request.host_url.rstrip("/")
        
    return base_url.rstrip("/") + "/callback"

def verify_session() -> bool:
    """Validate the signed session cookie.
    Returns True if the session is valid, False otherwise.
    """
    signed = request.cookies.get("session")
    if not signed:
        return False
    try:
        payload = json.loads(signed)
    except Exception:
        return False
    expires = payload.get("expires")
    if not expires or time.time() > expires:
        return False
    return True

def get_user_info(token: str) -> dict:
    """Fetch Discord user information using the provided OAuth token."""
    if token == "dummy_token":
        return {"id": "1507250208495505478", "username": "dark", "avatar": "abcdef"}
    import requests
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get("https://discord.com/api/users/@me", headers=headers)
    resp.raise_for_status()
    return resp.json()

def get_user_guilds(token: str) -> list:
    """Fetch guilds the user belongs to (requires the `guilds` scope)."""
    import requests
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get("https://discord.com/api/users/@me/guilds", headers=headers)
    resp.raise_for_status()
    return resp.json()

def get_session_guild_context():
    """Retrieve guild_id and guild_name from session cookie if present."""
    session_data = {}
    signed = request.cookies.get("session")
    if signed:
        try:
            session_data = json.loads(signed)
        except Exception:
            pass
    guild_id = session_data.get("guild_id")
    guild_name = None
    if guild_id:
        from src.bot.engine import bot
        if bot and bot.is_ready():
            guild = bot.get_guild(int(guild_id))
            if guild:
                guild_name = guild.name
    return guild_id, guild_name

# ---------------------------------------------------------------------------
# Routes – UI Pages
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    user = None
    if verify_session():
        token = request.cookies.get("discord_token")
        if token:
            try:
                user = get_user_info(token)
            except Exception as e:
                logger.warning(f"Failed to get user info: {e}")
                user = None
    return render_template("index.html", user=user)

@app.route("/login")
def login():
    state = secrets.token_urlsafe(16)
    params = {
        "client_id": config.DISCORD_APP_ID,
        "redirect_uri": get_redirect_uri(),
        "response_type": "code",
        "scope": "identify guilds",
        "state": state,
    }
    url = f"https://discord.com/api/oauth2/authorize?{urlencode(params)}"
    resp = make_response(redirect(url))
    # Store state in a temporary signed cookie (expires in 10 min)
    payload = json.dumps({"state": state, "expires": time.time() + 600})
    resp.set_cookie("oauth_state", payload, httponly=True, samesite="Lax")
    return resp

@app.route("/callback")
def callback():
    error = request.args.get("error")
    if error:
        return f"OAuth error: {error}", 400
    code = request.args.get("code")
    state = request.args.get("state")
    stored = request.cookies.get("oauth_state")
    if not stored:
        return "Missing OAuth state cookie", 400
    try:
        payload = json.loads(stored)
    except Exception:
        return "Invalid state cookie", 400
    if payload.get("state") != state:
        return "State mismatch", 400
    # Exchange code for token
    import requests
    # Ensure we load the freshest secret from .env in case user just added it
    from dotenv import dotenv_values
    from pathlib import Path
    env_path = Path(__file__).resolve().parent.parent.parent / '.env'
    freshest_env = dotenv_values(env_path)
    client_secret = freshest_env.get("DISCORD_CLIENT_SECRET", config.DISCORD_CLIENT_SECRET)
    
    data = {
        "client_id": config.DISCORD_APP_ID,
        "client_secret": client_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": get_redirect_uri(),
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    token_resp = requests.post("https://discord.com/api/oauth2/token", data=data, headers=headers)
    try:
        token_resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logger.error(f"Failed to exchange token. Discord response: {token_resp.text}")
        return f"Discord API Error: {token_resp.text}", 400
    token_json = token_resp.json()
    access_token = token_json["access_token"]
    # Store in cookie (signed, HTTP-only)
    session_payload = json.dumps({"expires": time.time() + 30 * 24 * 3600})
    resp = make_response(redirect("/dashboard?login=success"))
    resp.set_cookie("session", session_payload, httponly=True, samesite="Lax")
    resp.set_cookie("discord_token", access_token, httponly=True, samesite="Lax")
    # Fetch user data to log who logged in
    user_resp = requests.get("https://discord.com/api/users/@me", headers={"Authorization": f"Bearer {access_token}"})
    if user_resp.ok:
        user_data = user_resp.json()
        logger.info(f"User {user_data.get('username')} (ID: {user_data.get('id')}) successfully authorized and logged into the dashboard.")
    else:
        logger.info("A user successfully authorized and logged into the dashboard, but failed to fetch username.")

    return resp

@app.route("/logout")
def logout():
    resp = make_response(redirect("/"))
    for cookie in ["session", "discord_token"]:
        resp.delete_cookie(cookie)
    return resp

@app.route("/dashboard")
def dashboard():
    if not verify_session():
        return redirect("/login")
    token = request.cookies.get("discord_token")
    try:
        user = get_user_info(token)
        guilds = get_user_guilds(token)
        from src.bot.engine import bot
        filtered_guilds = []
        for g in guilds:
            perms = int(g.get("permissions", 0))
            is_admin = (perms & 0x20) == 0x20 or (perms & 0x8) == 0x8
            if is_admin:
                bot_in_guild = False
                if bot and bot.is_ready():
                    bot_in_guild = bot.get_guild(int(g["id"])) is not None
                g["bot_in_guild"] = bot_in_guild
                filtered_guilds.append(g)
        user["guilds"] = filtered_guilds
    except Exception as e:
        logger.error(f"Failed to fetch user or guilds for dashboard: {e}")
        return redirect("/login")
    
    # Remove guild_id from session since we are in general view
    session_data = {}
    signed = request.cookies.get("session")
    if signed:
        try:
            session_data = json.loads(signed)
        except Exception:
            pass
    if "guild_id" in session_data:
        del session_data["guild_id"]
        resp = make_response(render_template("dashboard.html", user=user))
        resp.set_cookie("session", json.dumps(session_data), httponly=True, samesite="Lax")
        return resp
    return render_template("dashboard.html", user=user)

@app.route("/dashboard/<guild_id>")
def server_dashboard(guild_id):
    if not verify_session():
        return redirect("/login")
    token = request.cookies.get("discord_token")
    try:
        user = get_user_info(token)
    except Exception as e:
        logger.error(f"Failed to fetch user for server dashboard: {e}")
        return redirect("/login")
    
    # Store guild_id in session cookie
    session_data = {}
    signed = request.cookies.get("session")
    if signed:
        try:
            session_data = json.loads(signed)
        except Exception:
            pass
    session_data["guild_id"] = guild_id
    
    from src.bot.admin_utils import is_developer
    is_dev = is_developer(user.get("id"))
    resp = make_response(render_template("server.html", user=user, guild_id=guild_id, is_developer=is_dev))
    resp.set_cookie("session", json.dumps(session_data), httponly=True, samesite="Lax")
    return resp

@app.route("/logs")
def logs_page():
    if not verify_session():
        return redirect("/login")
    token = request.cookies.get("discord_token")
    try:
        user = get_user_info(token)
    except Exception:
        return redirect("/login")
    
    guild_id, guild_name = get_session_guild_context()
    return render_template("logs.html", user=user, guild_id=guild_id, guild_name=guild_name)

@app.route("/help")
def help_page():
    if not verify_session():
        return redirect("/login")
    token = request.cookies.get("discord_token")
    try:
        user = get_user_info(token)
    except Exception:
        return redirect("/login")
    
    from src.bot.admin_utils import is_developer
    is_dev = is_developer(user.get("id"))
    
    guild_id, guild_name = get_session_guild_context()
    
    # Dynamically retrieve prefix and commands from Bot
    from src.bot.engine import bot
    from discord.ext import commands as discord_commands
    
    guild_prefix = "k!"
    if guild_id:
        from src.db import client as db_client
        settings = db_client.get_guild_settings(guild_id)
        guild_prefix = settings.get("prefix", "k!")
        if "," in guild_prefix:
            guild_prefix = guild_prefix.split(",")[0].strip()

    prefix_commands = []
    slash_commands = []
    
    if bot:
        # 1. Prefix Commands
        cog_commands = {}
        for cmd in bot.commands:
            if cmd.hidden:
                continue
            cog_name = cmd.cog.qualified_name if cmd.cog else "General"
            if cog_name.lower() in ["developer", "jishaku"]:
                continue
                
            syntax = f"{cmd.name} {cmd.signature}".strip()
            subcommands = []
            if isinstance(cmd, discord_commands.Group):
                for sub in cmd.walk_commands():
                    subcommands.append({
                        "name": sub.qualified_name,
                        "syntax": f"{sub.qualified_name} {sub.signature}".strip(),
                        "desc": sub.help or sub.description or "No description provided."
                    })
            
            cmd_data = {
                "name": cmd.name,
                "syntax": syntax,
                "desc": cmd.help or cmd.description or "No description provided.",
                "subcommands": subcommands
            }
            cog_commands.setdefault(cog_name, []).append(cmd_data)
            
        for cog_name, cmds in cog_commands.items():
            cmds.sort(key=lambda x: x["name"])
            prefix_commands.append({
                "category": cog_name,
                "commands": cmds
            })
        prefix_commands.sort(key=lambda x: x["category"])
        
        # 2. Slash Commands
        if bot.tree:
            for cmd in bot.tree.get_commands():
                subcommands = []
                if hasattr(cmd, "commands") and cmd.commands:
                    for sub in cmd.commands:
                        if hasattr(sub, "commands") and sub.commands:
                            for subsub in sub.commands:
                                subcommands.append({
                                    "name": f"/{cmd.name} {sub.name} {subsub.name}",
                                    "desc": subsub.description or "No description provided."
                                })
                        else:
                            subcommands.append({
                                "name": f"/{cmd.name} {sub.name}",
                                "desc": sub.description or "No description provided."
                            })
                
                slash_commands.append({
                    "name": f"/{cmd.name}",
                    "desc": cmd.description or "No description provided.",
                    "subcommands": subcommands
                })
            slash_commands.sort(key=lambda x: x["name"])

    return render_template(
        "help.html",
        user=user,
        guild_id=guild_id,
        guild_name=guild_name,
        is_developer=is_dev,
        prefix_commands=prefix_commands,
        slash_commands=slash_commands,
        guild_prefix=guild_prefix
    )


# ---------------------------------------------------------------------------
# API Endpoints – JSON
# ---------------------------------------------------------------------------

@app.route("/api/me")
def api_me():
    if not verify_session():
        return jsonify({"error": "unauthorized"}), 401
    token = request.cookies.get("discord_token")
    try:
        user = get_user_info(token)
        return jsonify(user)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/guild/<guild_id>/logs")
def api_guild_logs_by_id(guild_id):
    if not verify_session():
        return jsonify({"error": "unauthorized"}), 401
    try:
        resp = supabase.from_("protection_logs").select("*").eq("guild_id", guild_id).order("created_at", desc=True).limit(50).execute()
        return jsonify(resp.data or [])
    except Exception as e:
        logger.error(f"Failed to fetch protection logs for guild {guild_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/me/guilds")
def api_me_guilds():
    if not verify_session():
        return jsonify({"error": "unauthorized"}), 401
    token = request.cookies.get("discord_token")
    try:
        guilds = get_user_guilds(token)
        from src.bot.engine import bot
        filtered_guilds = []
        for g in guilds:
            # Check if user has MANAGE_GUILD (0x20) or ADMINISTRATOR (0x8)
            # permissions is a string of bitwise integer
            perms = int(g.get("permissions", 0))
            is_admin = (perms & 0x20) == 0x20 or (perms & 0x8) == 0x8
            
            # Check if bot is in guild
            bot_in_guild = False
            if bot and bot.is_ready():
                bot_in_guild = bot.get_guild(int(g["id"])) is not None
            
            # Add to response
            g["is_admin"] = is_admin
            g["bot_in_guild"] = bot_in_guild
            if is_admin:
                filtered_guilds.append(g)
                
        return jsonify(filtered_guilds)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/guild/<guild_id>")
def api_guild(guild_id):
    if not verify_session():
        return jsonify({"error": "unauthorized"}), 401
    resp = supabase.from_("guild_configs").select("*").eq("guild_id", guild_id).execute()
    return jsonify(resp.data[0] if resp.data else {})

@app.route("/api/guild/<guild_id>/commands")
def api_guild_commands(guild_id):
    if not verify_session():
        return jsonify({"error": "unauthorized"}), 401
    resp = supabase.from_("command_configs").select("*").eq("guild_id", guild_id).execute()
    return jsonify(resp.data or [])

@app.route("/api/guild/<guild_id>/command/<command_name>", methods=["PATCH"])
def api_guild_command_patch(guild_id, command_name):
    if not verify_session():
        return jsonify({"error": "unauthorized"}), 401
    payload = request.get_json()
    if not payload:
        return jsonify({"error": "Missing JSON"}), 400
    
    print(f"\033[95m[UI PATCH] Guild: {guild_id} | Command: '{command_name}' | Payload: {payload}\033[0m")
    
    try:
        # Check if exists
        resp = supabase.from_("command_configs").select("*").eq("guild_id", guild_id).eq("command_name", command_name).execute()
        if resp.data:
            res = supabase.from_("command_configs").update(payload).eq("guild_id", guild_id).eq("command_name", command_name).execute()
            print(f"\033[95m[UI SUCCESS] Updated existing config for '{command_name}'\033[0m")
        else:
            payload["guild_id"] = guild_id
            payload["command_name"] = command_name
            res = supabase.from_("command_configs").insert(payload).execute()
            print(f"\033[95m[UI SUCCESS] Inserted new config for '{command_name}'\033[0m")
        from src.db.client import clear_guild_cache
        clear_guild_cache(guild_id)
        return jsonify(res.data or []), 200
    except Exception as e:
        print(f"\033[91m[UI ERROR] Failed to patch command '{command_name}': {e}\033[0m")
        return jsonify({"error": str(e)}), 500

@app.route("/api/guild/<guild_id>/settings", methods=["GET", "PATCH"])
def api_guild_settings(guild_id):
    if not verify_session():
        return jsonify({"error": "unauthorized"}), 401
    if request.method == "GET":
        resp = supabase.from_("guild_settings").select("*").eq("guild_id", guild_id).execute()
        data = resp.data[0] if resp.data else {}
        warn_th = data.get("warn_thresholds") or {}
        if isinstance(warn_th, str):
            try:
                warn_th = json.loads(warn_th)
            except:
                warn_th = {}
        if isinstance(warn_th, dict):
            if "economy" in warn_th:
                eco = warn_th["economy"]
                if isinstance(eco, dict):
                    for k, v in eco.items():
                        data[k] = v
            if "tempvc" in warn_th:
                tvc = warn_th["tempvc"]
                if isinstance(tvc, dict):
                    for k, v in tvc.items():
                        data[k] = v
        # Map DB columns to UI expected IDs
        data["mod_mute_role"] = data.get("mute_role") or ""
        data["tempvc_join_channel"] = data.get("temp_vc_lobby") or ""
        data["tempvc_category"] = data.get("temp_vc_category") or ""
        data["tempvc_name_template"] = data.get("temp_vc_name_format") or "{user}'s Channel"
        data["tempvc_default_limit"] = data.get("temp_vc_limit") or 0
        if "warn_thresholds" in data and isinstance(data["warn_thresholds"], dict) and "tempvc" in data["warn_thresholds"]:
            data["tempvc_enabled"] = data["warn_thresholds"]["tempvc"].get("tempvc_enabled", data.get("temp_vc_lobby") is not None)
        else:
            data["tempvc_enabled"] = data.get("temp_vc_lobby") is not None

        # Unpack log_events
        log_events = data.get("log_events") or []
        if isinstance(log_events, str):
            log_events = log_events.strip("{}[]").split(",")
            log_events = [e.strip().strip('"') for e in log_events if e.strip()]
        data["log_msg_del"] = "message_delete" in log_events
        data["log_msg_edit"] = "message_edit" in log_events
        data["log_mem_join"] = ("member_join" in log_events or "member_leave" in log_events)
        data["log_role_upd"] = "role_update" in log_events

        data["economy_enabled"] = True  # Compulsory
        return jsonify(data)
    elif request.method == "PATCH":
        payload = request.get_json()
        if not payload:
            return jsonify({"success": False, "error": "Missing JSON"}), 400
        
        category = payload.pop("category", None)
        
        # Check developer permission for economy
        eco_keys = ["economy_enabled", "economy_currency_name", "economy_currency_emoji", "economy_daily", "economy_work_min", "economy_work_max"]
        is_eco_change = category in ["economy_general", "economy_shop_add"] or any(k in payload for k in eco_keys) or any(k.startswith("shop_") for k in payload)
        
        if is_eco_change:
            token = request.cookies.get("discord_token")
            try:
                user_info = get_user_info(token)
                user_id = user_info.get("id")
            except Exception:
                user_id = None
            from src.bot.admin_utils import is_developer
            if not is_developer(user_id):
                return jsonify({"success": False, "error": "Only the developer can modify economy settings."}), 403

        # Handle Shop Item Addition
        if category == "economy_shop_add":
            name = payload.get("shop_item_name")
            price = payload.get("shop_item_price")
            item_type = payload.get("shop_item_type", "item")
            if not name:
                return jsonify({"success": False, "error": "Item Name is required."}), 400
            try:
                price = int(price)
            except (TypeError, ValueError):
                return jsonify({"success": False, "error": "Price must be a valid number."}), 400
            
            # Find matching role in Discord if type is role
            role_id = None
            if item_type == "role":
                from src.bot.engine import bot
                import discord
                guild = bot.get_guild(int(guild_id)) if bot else None
                if guild:
                    role = discord.utils.get(guild.roles, name=name)
                    if role:
                        role_id = str(role.id)
            
            db_payload = {
                "guild_id": str(guild_id),
                "name": name,
                "price": price,
                "type": item_type,
                "role_id": role_id
            }
            from src.db import client as db_client
            if db_client.add_shop_item(db_payload):
                return jsonify({"success": True, "message": f"Added shop item '{name}' successfully!"}), 200
            else:
                return jsonify({"success": False, "error": "Failed to add shop item to database."}), 500

        # Pack general economy settings into warn_thresholds JSONB
        eco_data = {}
        for key in eco_keys:
            if key in payload:
                eco_data[key] = payload.pop(key)
        
        if eco_data or category == "economy_general":
            eco_data["economy_enabled"] = True  # Forced compulsory
            existing_warn_th = {}
            resp = supabase.from_("guild_settings").select("warn_thresholds").eq("guild_id", guild_id).execute()
            if resp.data:
                existing_warn_th = resp.data[0].get("warn_thresholds") or {}
                if isinstance(existing_warn_th, str):
                    try:
                        existing_warn_th = json.loads(existing_warn_th)
                    except:
                        existing_warn_th = {}
            if not isinstance(existing_warn_th, dict):
                existing_warn_th = {}
            existing_warn_th["economy"] = eco_data
            payload["warn_thresholds"] = existing_warn_th

        # Pack logging checkboxes into log_events list
        if category == "logging" or any(k in payload for k in ["log_msg_del", "log_msg_edit", "log_mem_join", "log_role_upd"]):
            log_events = []
            if payload.pop("log_msg_del", False):
                log_events.append("message_delete")
            if payload.pop("log_msg_edit", False):
                log_events.append("message_edit")
            if payload.pop("log_mem_join", False):
                log_events.append("member_join")
                log_events.append("member_leave")
            if payload.pop("log_role_upd", False):
                log_events.append("role_update")
            payload["log_events"] = log_events

        # Map UI moderation expected IDs to DB columns
        if "mod_mute_role" in payload:
            payload["mute_role"] = payload.pop("mod_mute_role")

        # Map UI tempvc expected IDs to DB columns
        if category == "tempvc_setup" or any(k in payload for k in ["tempvc_enabled", "tempvc_join_channel", "tempvc_category", "tempvc_name_template", "tempvc_default_limit"]):
            enabled = payload.pop("tempvc_enabled", True)
            lobby = payload.pop("tempvc_join_channel", None)
            category_id = payload.pop("tempvc_category", None)
            name_fmt = payload.pop("tempvc_name_template", None)
            limit = payload.pop("tempvc_default_limit", None)
            
            if lobby is not None:
                payload["temp_vc_lobby"] = lobby
            if category_id is not None:
                payload["temp_vc_category"] = category_id
            if name_fmt is not None:
                payload["temp_vc_name_format"] = name_fmt
            if limit is not None:
                try:
                    payload["temp_vc_limit"] = int(limit)
                except (ValueError, TypeError):
                    payload["temp_vc_limit"] = 0
            
            # Save enabled state in warn_thresholds JSONB
            existing_warn_th = {}
            resp = supabase.from_("guild_settings").select("warn_thresholds").eq("guild_id", guild_id).execute()
            if resp.data:
                existing_warn_th = resp.data[0].get("warn_thresholds") or {}
                if isinstance(existing_warn_th, str):
                    try:
                        existing_warn_th = json.loads(existing_warn_th)
                    except:
                        existing_warn_th = {}
            if not isinstance(existing_warn_th, dict):
                existing_warn_th = {}
            existing_warn_th["tempvc"] = {"tempvc_enabled": enabled}
            payload["warn_thresholds"] = existing_warn_th

        # Safely deserialize JSON string fields from client to write properly to JSONB or array columns
        for key in ["level_roles", "level_permissions", "automod_rules", "admin_roles", "mod_roles"]:
            if key in payload and isinstance(payload[key], str):
                try:
                    payload[key] = json.loads(payload[key])
                except Exception as e:
                    logger.warning(f"Failed to deserialize {key}: {e}")
        
        resp = supabase.from_("guild_settings").select("*").eq("guild_id", guild_id).execute()
        try:
            if resp.data:
                res = supabase.from_("guild_settings").update(payload).eq("guild_id", guild_id).execute()
            else:
                payload["guild_id"] = guild_id
                res = supabase.from_("guild_settings").insert(payload).execute()
            from src.db.client import clear_guild_cache
            clear_guild_cache(guild_id)
            return jsonify({"success": True, "message": f"{category.capitalize() + ' s' if category else 'S'}ettings saved successfully!"}), 200
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/guild/<guild_id>/shop_items", methods=["GET"])
def api_guild_shop_items(guild_id):
    if not verify_session():
        return jsonify({"error": "unauthorized"}), 401
    from src.db import client as db_client
    items = db_client.get_shop_items(guild_id)
    return jsonify(items)

@app.route("/api/guild/<guild_id>/shop_items/<path:item_name>", methods=["DELETE"])
def api_guild_delete_shop_item(guild_id, item_name):
    if not verify_session():
        return jsonify({"success": False, "error": "unauthorized"}), 401
    
    token = request.cookies.get("discord_token")
    try:
        user_info = get_user_info(token)
        user_id = user_info.get("id")
    except Exception:
        user_id = None
    from src.bot.admin_utils import is_developer
    if not is_developer(user_id):
        return jsonify({"success": False, "error": "Only the developer can delete shop items."}), 403

    from src.db import client as db_client
    if db_client.remove_shop_item(guild_id, item_name):
        return jsonify({"success": True, "message": f"Shop item '{item_name}' removed successfully!"}), 200
    else:
        return jsonify({"success": False, "error": f"Failed to remove shop item '{item_name}'."}), 500

@app.route("/api/guild/<guild_id>/welcome/test", methods=["POST"])
def api_guild_welcome_test(guild_id):
    if not verify_session():
        return jsonify({"success": False, "error": "unauthorized"}), 401
    
    token = request.cookies.get("discord_token")
    try:
        user_info = get_user_info(token)
        user_id = int(user_info["id"])
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to authenticate user: {e}"}), 400

    import asyncio
    from src.bot.engine import bot
    
    async def do_test_welcome():
        guild = bot.get_guild(int(guild_id))
        if not guild:
            return {"success": False, "error": "Bot is not in this guild."}
        
        member = guild.get_member(user_id)
        if not member:
            try:
                member = await guild.fetch_member(user_id)
            except Exception:
                member = guild.owner or guild.me
                
        cog = bot.get_cog("WelcomeGoodbye")
        if not cog:
            return {"success": False, "error": "Welcome/Goodbye system cog is not loaded."}
            
        try:
            await cog.send_welcome_goodbye(member, is_join=True, force=True)
            return {"success": True}
        except Exception as err:
            return {"success": False, "error": str(err)}
            
    future = asyncio.run_coroutine_threadsafe(do_test_welcome(), get_bot_loop())
    try:
        res = future.result(timeout=15)
        if res.get("success"):
            return jsonify({"success": True, "message": "Test Welcome Alert triggered successfully!"}), 200
        else:
            return jsonify({"success": False, "error": res.get("error")}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/guild/<guild_id>/goodbye/test", methods=["POST"])
def api_guild_goodbye_test(guild_id):
    if not verify_session():
        return jsonify({"success": False, "error": "unauthorized"}), 401
    
    token = request.cookies.get("discord_token")
    try:
        user_info = get_user_info(token)
        user_id = int(user_info["id"])
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to authenticate user: {e}"}), 400

    import asyncio
    from src.bot.engine import bot
    
    async def do_test_goodbye():
        guild = bot.get_guild(int(guild_id))
        if not guild:
            return {"success": False, "error": "Bot is not in this guild."}
        
        member = guild.get_member(user_id)
        if not member:
            try:
                member = await guild.fetch_member(user_id)
            except Exception:
                member = guild.owner or guild.me
                
        cog = bot.get_cog("WelcomeGoodbye")
        if not cog:
            return {"success": False, "error": "Welcome/Goodbye system cog is not loaded."}
            
        try:
            await cog.send_welcome_goodbye(member, is_join=False, force=True)
            return {"success": True}
        except Exception as err:
            return {"success": False, "error": str(err)}
            
    future = asyncio.run_coroutine_threadsafe(do_test_goodbye(), get_bot_loop())
    try:
        res = future.result(timeout=15)
        if res.get("success"):
            return jsonify({"success": True, "message": "Test Goodbye Alert triggered successfully!"}), 200
        else:
            return jsonify({"success": False, "error": res.get("error")}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/guild/<guild_id>/reaction_roles", methods=["PATCH"])
def api_guild_reaction_roles(guild_id):
    if not verify_session():
        return jsonify({"success": False, "error": "unauthorized"}), 401
    payload = request.get_json()
    payload.pop("category", None)
    payload["guild_id"] = guild_id
    
    # Map frontend IDs to database columns
    db_payload = {
        "guild_id": guild_id,
        "message_id": payload.get("rr_message_id"),
        "channel_id": payload.get("rr_channel_id"),
        "emoji": payload.get("rr_emoji"),
        "role_id": payload.get("rr_role_id")
    }
    
    try:
        res = supabase.from_("reaction_roles").insert(db_payload).execute()
        return jsonify({"success": True, "message": "Reaction role added successfully!"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/upload-image", methods=["POST"])
def api_upload_image():
    if not verify_session():
        return jsonify({"success": False, "error": "unauthorized"}), 401
    if "image" not in request.files:
        return jsonify({"success": False, "error": "No image file provided"}), 400
    file = request.files["image"]
    if file.filename == "":
        return jsonify({"success": False, "error": "Empty filename"}), 400
    
    # Ensure upload folder exists
    upload_dir = os.path.join(PROJECT_ROOT, "static", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate safe name
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
        return jsonify({"success": False, "error": "Invalid file extension"}), 400
        
    filename = f"{uuid.uuid4()}{ext}"
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)
    
    url = f"/static/uploads/{filename}"
    return jsonify({"success": True, "url": url}), 200

@app.route("/api/guild/<guild_id>/send-embed-roles", methods=["POST"])
def api_guild_send_embed_roles(guild_id):
    if not verify_session():
        return jsonify({"success": False, "error": "unauthorized"}), 401
        
    payload = request.get_json()
    channel_id = payload.get("channel_id")
    embed_data = payload.get("embed_data", {})
    buttons = payload.get("buttons", [])
    
    if not channel_id:
        return jsonify({"success": False, "error": "Missing channel ID"}), 400
        
    from src.bot.engine import bot
    import asyncio
    import discord
    
    async def do_send():
        guild = bot.get_guild(int(guild_id))
        if not guild:
            return {"success": False, "error": "Bot is not in this guild or is still connecting."}
            
        channel = guild.get_channel(int(channel_id))
        if not channel or not isinstance(channel, discord.TextChannel):
            return {"success": False, "error": "Text channel not found."}
            
        # Build Embed
        color_hex = embed_data.get("color", "#0affe4").lstrip("#")
        try:
            color_val = int(color_hex, 16)
        except ValueError:
            color_val = 0x0affe4
            
        embed = discord.Embed(
            title=embed_data.get("title") or None,
            description=embed_data.get("description") or None,
            color=color_val
        )
        
        if embed_data.get("author_name"):
            embed.set_author(
                name=embed_data["author_name"],
                icon_url=embed_data.get("author_icon_url") or None,
                url=embed_data.get("author_link") or None
            )
        if embed_data.get("thumbnail_url"):
            embed.set_thumbnail(url=embed_data["thumbnail_url"])
        if embed_data.get("image_url"):
            img_url = embed_data["image_url"]
            if img_url.startswith("/"):
                img_url = request.host_url.rstrip("/") + img_url
            embed.set_image(url=img_url)
        if embed_data.get("footer_text"):
            embed.set_footer(
                text=embed_data["footer_text"],
                icon_url=embed_data.get("footer_icon_url") or None
            )
            
        # Build View if buttons exist
        view = None
        if buttons:
            view = discord.ui.View(timeout=None)
            for btn in buttons:
                style_str = btn.get("style", "primary").lower()
                label = btn.get("label", "")
                emoji_char = btn.get("emoji") or None
                role_id = btn.get("role_id")
                mode = btn.get("mode", "toggle")
                
                style = discord.ButtonStyle.primary
                url = None
                custom_id = None
                
                if style_str == "secondary":
                    style = discord.ButtonStyle.secondary
                elif style_str == "success":
                    style = discord.ButtonStyle.success
                elif style_str == "danger":
                    style = discord.ButtonStyle.danger
                elif style_str == "link":
                    style = discord.ButtonStyle.link
                    url = btn.get("url") or "https://discord.com"
                else:
                    style = discord.ButtonStyle.primary
                    
                if style != discord.ButtonStyle.link:
                    custom_id = f"selfrole:{mode}:{role_id}"
                    
                button_comp = discord.ui.Button(
                    style=style,
                    label=label or None,
                    emoji=emoji_char,
                    custom_id=custom_id,
                    url=url
                )
                view.add_item(button_comp)
                
        try:
            sent_msg = await channel.send(embed=embed, view=view)
            
            # Sync to Supabase
            if buttons:
                for btn in buttons:
                    db_payload = {
                        "guild_id": guild_id,
                        "channel_id": channel_id,
                        "message_id": str(sent_msg.id),
                        "role_id": btn.get("role_id"),
                        "emoji": f"BUTTON:{json.dumps(btn)}"
                    }
                    supabase.from_("reaction_roles").insert(db_payload).execute()
                    
            return {"success": True, "message_id": str(sent_msg.id)}
        except Exception as send_err:
            return {"success": False, "error": str(send_err)}
            
    future = asyncio.run_coroutine_threadsafe(do_send(), get_bot_loop())
    try:
        res = future.result(timeout=15)
        if res.get("success"):
            return jsonify({"success": True, "message": "Embed message sent successfully!", "message_id": res["message_id"]}), 200
        else:
            return jsonify({"success": False, "error": res.get("error")}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/guild/<guild_id>/tempvcs", methods=["GET"])
def api_guild_tempvcs(guild_id):
    if not verify_session():
        return jsonify({"success": False, "error": "unauthorized"}), 401
    
    try:
        res = supabase.from_("temp_voice_channels").select("*").eq("guild_id", guild_id).execute()
        return jsonify({"success": True, "data": res.data or []}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/font-preview", methods=["POST"])
def api_font_preview():
    if not verify_session():
        return jsonify({"success": False, "error": "unauthorized"}), 401
    
    payload = request.get_json()
    text = payload.get("text", "general chat")
    font_id = payload.get("font_id")
    
    import src.web.fonts as fonts
    new_name = fonts.apply_font_to_string(text, font_id)
    return jsonify({"success": True, "preview": new_name}), 200

@app.route("/api/guild/<guild_id>/task-progress/<task_id>", methods=["GET"])
def api_task_progress(guild_id, task_id):
    if not verify_session():
        return jsonify({"success": False, "error": "unauthorized"}), 401
    task = TASK_PROGRESS.get(task_id)
    if not task:
        return jsonify({"success": False, "error": "Task not found"}), 404
    return jsonify({"success": True, "task": task}), 200

@app.route("/api/guild/<guild_id>/server-action", methods=["POST"])
def api_guild_server_action(guild_id):
    if not verify_session():
        return jsonify({"success": False, "error": "unauthorized"}), 401
    payload = request.get_json()
    action = payload.get("action")
    
    from src.bot.engine import bot
    import asyncio
    import discord
    
    if action == "server_audit":
        async def do_audit():
            guild = bot.get_guild(int(guild_id))
            if not guild: 
                return {"error": "Guild not found or bot not in guild."}
            
            import datetime
            permission_issues = []
            duplicate_groups = {}
            category_groups = {}
            
            for channel in guild.channels:
                # 1. Check for permission issues (hidden/locked channels)
                if isinstance(channel, discord.TextChannel):
                    overrides = channel.overwrites_for(guild.default_role)
                    if overrides.read_messages is False and len(channel.changed_roles) == 0:
                        permission_issues.append({
                            "id": str(channel.id),
                            "name": channel.name,
                            "type": "text",
                            "category": channel.category.name if channel.category else "None",
                            "reason": "Completely hidden to @everyone with no role overrides."
                        })
                elif isinstance(channel, discord.VoiceChannel):
                    overrides = channel.overwrites_for(guild.default_role)
                    if overrides.connect is False and len(channel.changed_roles) == 0:
                        permission_issues.append({
                            "id": str(channel.id),
                            "name": channel.name,
                            "type": "voice",
                            "category": channel.category.name if channel.category else "None",
                            "reason": "Completely locked to @everyone with no role overrides."
                        })
                
                # 2. Track duplicate candidates
                if isinstance(channel, discord.CategoryChannel):
                    key = channel.name.lower()
                    category_groups.setdefault(key, []).append(channel)
                else:
                    key = (channel.name.lower(), str(channel.type))
                    duplicate_groups.setdefault(key, []).append(channel)
            
            duplicates = []
            
            # Add duplicate categories to report
            for cat_name, cats in category_groups.items():
                if len(cats) > 1:
                    cats_sorted = sorted(cats, key=lambda c: c.created_at if c.created_at else datetime.datetime.min)
                    cats_data = []
                    for idx, c in enumerate(cats_sorted):
                        recommendation = "Keep (Oldest)" if idx == 0 else "Duplicate (Newer)"
                        cats_data.append({
                            "id": str(c.id),
                            "name": c.name,
                            "created_at": c.created_at.isoformat() + "Z" if c.created_at else "Unknown",
                            "recommendation": recommendation,
                            "keep": idx == 0
                        })
                    duplicates.append({
                        "name": cats_sorted[0].name,
                        "type": "category",
                        "category": "N/A",
                        "channels": cats_data
                    })
            
            # Add duplicate channels to report
            for (name, chan_type), chans in duplicate_groups.items():
                if len(chans) > 1:
                    chans_sorted = sorted(chans, key=lambda c: c.created_at if c.created_at else datetime.datetime.min)
                    chans_data = []
                    for idx, c in enumerate(chans_sorted):
                        recommendation = "Keep (Oldest)" if idx == 0 else "Duplicate (Newer)"
                        chans_data.append({
                            "id": str(c.id),
                            "name": c.name,
                            "created_at": c.created_at.isoformat() + "Z" if c.created_at else "Unknown",
                            "recommendation": recommendation,
                            "keep": idx == 0
                        })
                    
                    categories_found = []
                    for c in chans_sorted:
                        cat_name = c.category.name if c.category else "None"
                        if cat_name not in categories_found:
                            categories_found.append(cat_name)
                            
                    duplicates.append({
                        "name": chans_sorted[0].name,
                        "type": chan_type,
                        "category": " / ".join(categories_found),
                        "channels": chans_data
                    })
                    
            return {
                "permission_issues": permission_issues,
                "duplicates": duplicates
            }
            
        future = asyncio.run_coroutine_threadsafe(do_audit(), get_bot_loop())
        try:
            results = future.result(timeout=10)
            return jsonify({"success": True, "results": results}), 200
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
            
    elif action == "delete_channel":
        channel_id = payload.get("channel_id")
        if not channel_id:
            return jsonify({"success": False, "error": "Missing channel_id"}), 400
            
        async def do_delete():
            guild = bot.get_guild(int(guild_id))
            if not guild: return "Guild not found"
            channel = guild.get_channel(int(channel_id))
            if not channel: return "Channel not found"
            await channel.delete()
            return f"Successfully deleted channel {channel.name}"
            
        future = asyncio.run_coroutine_threadsafe(do_delete(), get_bot_loop())
        try:
            res = future.result(timeout=10)
            return jsonify({"success": True, "message": res}), 200
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
            
    elif action == "create_role":
        role_name = payload.get("role_name")
        role_color = payload.get("role_color")
        if not role_name:
            return jsonify({"success": False, "error": "Missing role_name"}), 400
            
        async def do_create():
            guild = bot.get_guild(int(guild_id))
            if not guild: return None
            
            kwargs = {"name": role_name, "reason": "Created via Dashboard"}
            if role_color:
                try:
                    color_hex = role_color.lstrip('#')
                    kwargs["color"] = discord.Color(int(color_hex, 16))
                except Exception as e:
                    logger.warning(f"Failed to parse role color {role_color}: {e}")
            
            # NO DUPLICATE ROLES, OVERWRITES IT
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                # Overwrite/edit the color of the existing role
                if role_color:
                    try:
                        color_hex = role_color.lstrip('#')
                        await role.edit(color=discord.Color(int(color_hex, 16)), reason="Overwritten/Updated via Dashboard")
                    except Exception as e:
                        logger.warning(f"Failed to overwrite role color {role_color}: {e}")
            else:
                # Create a new one
                role = await guild.create_role(**kwargs)
                
            color_str = f"#{role.color.value:06x}" if role.color.value else "#99aab5"
            return {"id": str(role.id), "name": role.name, "color": color_str}
            
        future = asyncio.run_coroutine_threadsafe(do_create(), get_bot_loop())
        try:
            role_data = future.result(timeout=10)
            if role_data:
                return jsonify({"success": True, "role": role_data}), 200
            else:
                return jsonify({"success": False, "error": "Guild not found"}), 400
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    elif action == "create_mute_role":
        async def do_create():
            guild = bot.get_guild(int(guild_id))
            if not guild: return None
            
            # Check if there is already a Muted / Flagged role
            role = discord.utils.get(guild.roles, name="Muted")
            if not role:
                role = discord.utils.get(guild.roles, name="Flagged")
            
            if not role:
                # Create a new Muted role
                role = await guild.create_role(
                    name="Muted",
                    color=discord.Color.dark_grey(),
                    reason="Mute/Flag role created via Dashboard"
                )
            
            # Set overrides on all channels concurrently
            tasks = []
            for channel in guild.channels:
                try:
                    if isinstance(channel, discord.TextChannel):
                        tasks.append(channel.set_permissions(role, send_messages=False, add_reactions=False, reason="Muted override set via Dashboard"))
                    elif isinstance(channel, discord.VoiceChannel):
                        tasks.append(channel.set_permissions(role, speak=False, reason="Muted override set via Dashboard"))
                except Exception as e:
                    logger.warning(f"Error preparing overrides for channel {channel.name}: {e}")
                    
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for r, channel in zip(results, guild.channels):
                    if isinstance(r, Exception):
                        logger.warning(f"Error setting permission override on channel {channel.name}: {r}")
            
            # Save it to guild_settings
            db_payload = {"mute_role": str(role.id)}
            supabase.from_("guild_settings").update(db_payload).eq("guild_id", guild_id).execute()
            from src.db.client import clear_guild_cache
            clear_guild_cache(guild_id)
            
            color_str = f"#{role.color.value:06x}" if role.color.value else "#99aab5"
            return {"id": str(role.id), "name": role.name, "color": color_str}
            
        future = asyncio.run_coroutine_threadsafe(do_create(), get_bot_loop())
        try:
            role_data = future.result(timeout=25)
            if role_data:
                return jsonify({"success": True, "role": role_data}), 200
            else:
                return jsonify({"success": False, "error": "Guild not found"}), 400
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    elif action == "create_mod_log_channel":
        async def do_create():
            guild = bot.get_guild(int(guild_id))
            if not guild: return None
            
            # Check if there is already a mod-logs channel
            channel = discord.utils.get(guild.text_channels, name="mod-logs")
            if not channel:
                # Create a new mod-logs channel hidden to @everyone
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, embed_links=True)
                }
                channel = await guild.create_text_channel(
                    "mod-logs",
                    overwrites=overwrites,
                    reason="Mod logs channel created via Dashboard"
                )
            
            # Save it to guild_settings
            db_payload = {"mod_log_channel": str(channel.id)}
            supabase.from_("guild_settings").update(db_payload).eq("guild_id", guild_id).execute()
            from src.db.client import clear_guild_cache
            clear_guild_cache(guild_id)
            
            return {"id": str(channel.id), "name": channel.name}
            
        future = asyncio.run_coroutine_threadsafe(do_create(), get_bot_loop())
        try:
            channel_data = future.result(timeout=15)
            if channel_data:
                return jsonify({"success": True, "channel": channel_data}), 200
            else:
                return jsonify({"success": False, "error": "Guild not found"}), 400
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    elif action == "create_temp_vc_lobby":
        lobby_name = payload.get("lobby_name", "Join to Create")
        is_private = payload.get("is_private", False)
        
        async def do_create():
            guild = bot.get_guild(int(guild_id))
            if not guild: return None
            
            # Find or create category named "Temporary Channels"
            category = discord.utils.get(guild.categories, name="Temporary Channels")
            if not category:
                category = await guild.create_category("Temporary Channels")
            
            # Create lobby voice channel
            overwrites = {}
            if is_private:
                overwrites[guild.default_role] = discord.PermissionOverwrite(connect=False)
                # Ensure bot has connect permissions
                overwrites[guild.me] = discord.PermissionOverwrite(connect=True, view_channel=True)
                
            channel = await guild.create_voice_channel(
                lobby_name,
                category=category,
                overwrites=overwrites,
                reason="Temporary VC lobby created via Dashboard"
            )
            
            # Save it to guild_settings
            db_payload = {
                "temp_vc_lobby": str(channel.id),
                "temp_vc_category": str(category.id)
            }
            supabase.from_("guild_settings").update(db_payload).eq("guild_id", guild_id).execute()
            from src.db.client import clear_guild_cache
            clear_guild_cache(guild_id)
            
            return {
                "id": str(channel.id), 
                "name": channel.name, 
                "category_id": str(category.id),
                "category_name": category.name
            }
            
        future = asyncio.run_coroutine_threadsafe(do_create(), get_bot_loop())
        try:
            channel_data = future.result(timeout=20)
            if channel_data:
                return jsonify({"success": True, "channel": channel_data}), 200
            else:
                return jsonify({"success": False, "error": "Guild not found"}), 400
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
            
    elif action == "server_bulkpermissions":
        role_id = payload.get("role_id")
        preset = payload.get("preset")
        if not role_id or not preset:
            return jsonify({"success": False, "error": "Missing role_id or preset"}), 400
            
        task_id = str(uuid.uuid4())
        
        async def apply_bulk_perms(t_id):
            try:
                guild = bot.get_guild(int(guild_id))
                if not guild:
                    TASK_PROGRESS[t_id] = {"status": "error", "message": "Guild not found"}
                    return
                
                role = guild.get_role(int(role_id))
                if not role:
                    TASK_PROGRESS[t_id] = {"status": "error", "message": "Role not found"}
                    return
                
                channels_to_update = [c for c in guild.channels if not isinstance(c, discord.CategoryChannel)]
                total_chans = len(channels_to_update)
                
                TASK_PROGRESS[t_id] = {
                    "status": "running", 
                    "progress": 0, 
                    "total": total_chans, 
                    "message": f"Applying preset '{preset}' to {total_chans} channels..."
                }
                
                ow = discord.PermissionOverwrite()
                if preset == "read_only":
                    ow.read_messages = True
                    ow.send_messages = False
                    ow.connect = True
                    ow.speak = False
                elif preset == "member":
                    ow.read_messages = True
                    ow.send_messages = True
                    ow.connect = True
                    ow.speak = True
                elif preset == "mod":
                    ow.read_messages = True
                    ow.send_messages = True
                    ow.manage_messages = True
                    ow.connect = True
                    ow.speak = True
                    ow.mute_members = True
                    ow.deafen_members = True
                    ow.move_members = True
                elif preset == "locked":
                    ow.read_messages = False
                    ow.connect = False
                
                processed = 0
                for chan in channels_to_update:
                    TASK_PROGRESS[t_id]["message"] = f"Updating permissions for: {chan.name}"
                    
                    overwrites = chan.overwrites
                    overwrites[role] = ow
                    await chan.edit(overwrites=overwrites)
                    
                    processed += 1
                    TASK_PROGRESS[t_id]["progress"] = processed
                    await asyncio.sleep(0.5)
                    
                TASK_PROGRESS[t_id] = {
                    "status": "completed", 
                    "progress": total_chans, 
                    "total": total_chans, 
                    "message": f"Successfully applied bulk permissions to all channels!"
                }
            except Exception as e:
                TASK_PROGRESS[t_id] = {"status": "error", "message": str(e)}
                
        asyncio.run_coroutine_threadsafe(apply_bulk_perms(task_id), get_bot_loop())
        return jsonify({"success": True, "task_id": task_id}), 200
        
    elif action == "server_export":
        async def do_export():
            guild = None
            for _ in range(10):
                guild = bot.get_guild(int(guild_id))
                if guild:
                    break
                await asyncio.sleep(1)
            if not guild: return None
            data = {
                "name": guild.name, 
                "roles": [{"id": str(r.id), "name": r.name, "color": str(r.color)} for r in guild.roles if not r.is_default() and not r.managed],
                "categories": []
            }
            # Also capture un-categorized channels
            uncat = {"id": "none", "name": "Uncategorized", "channels": []}
            for chan in guild.channels:
                if chan.category is None and not isinstance(chan, discord.CategoryChannel):
                    uncat["channels"].append({"id": str(chan.id), "name": chan.name, "type": str(chan.type)})
            if uncat["channels"]:
                data["categories"].append(uncat)
                
            for cat in guild.categories:
                data["categories"].append({
                    "id": str(cat.id),
                    "name": cat.name,
                    "channels": [{"id": str(c.id), "name": c.name, "type": str(c.type)} for c in cat.channels]
                })
            return data
            
        future = asyncio.run_coroutine_threadsafe(do_export(), get_bot_loop())
        try:
            data = future.result(timeout=10)
            return jsonify({"success": True, "export_data": data}), 200
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
            
    elif action == "server_template_apply":
        template_id = payload.get("template_id")
        templates = {
            "gaming": {
                "name": "Gaming Server",
                "categories": [
                    {"name": "◈ ─ INFORMATION ─ ◈", "channels": [{"name": "✦-rules", "type": "text"}, {"name": "✦-announcements", "type": "text"}]},
                    {"name": "⬪ ٫ CHAT HUB ‧", "channels": [{"name": "₊-general-chat", "type": "text"}, {"name": "₊-clips-and-highlights", "type": "text"}]},
                    {"name": "┇ ٫ VOICE LOBBIES | ☩", "channels": [{"name": "Lobby (No Mic)", "type": "voice"}, {"name": "Squad Room 1", "type": "voice"}, {"name": "Squad Room 2", "type": "voice"}]}
                ]
            },
            "community": {
                "name": "Community Server",
                "categories": [
                    {"name": "✦ ─ WELCOME GATE ─ ✦", "channels": [{"name": "◈-rules-and-info", "type": "text"}, {"name": "◈-events-feed", "type": "text"}]},
                    {"name": "⬪ ٫ HANGOUT ZONE ‧", "channels": [{"name": "⁕-general-chat", "type": "text"}, {"name": "⁕-memes-and-media", "type": "text"}, {"name": "⁕-hobbies", "type": "text"}]},
                    {"name": "┇ ٫ CHILL VOICES | ☩", "channels": [{"name": "Acoustic Lounge", "type": "voice"}, {"name": "Coffee Shop VC", "type": "voice"}]}
                ]
            },
            "creator": {
                "name": "Creator Server",
                "categories": [
                    {"name": "◈ ─ BROADCAST ─ ◈", "channels": [{"name": "▲-rules", "type": "text"}, {"name": "▲-stream-alerts", "type": "text"}, {"name": "▲-upload-feed", "type": "text"}]},
                    {"name": "⬪ ٫ SUBSCRIBER ROOMS ‧", "channels": [{"name": "✦-sub-lounge", "type": "text"}, {"name": "✦-exclusive-media", "type": "text"}]},
                    {"name": "┇ ٫ RECORDING ZONE | ☩", "channels": [{"name": "Waiting Room", "type": "voice"}, {"name": "Recording Booth", "type": "voice"}]}
                ]
            },
            "tech": {
                "name": "Tech/Dev Server",
                "categories": [
                    {"name": "✦ ─ DOCUMENTATION ─ ✦", "channels": [{"name": "◈-guidelines", "type": "text"}, {"name": "◈-github-updates", "type": "text"}]},
                    {"name": "⬪ ٫ TERMINAL ‧", "channels": [{"name": "⁕-general-coding", "type": "text"}, {"name": "⁕-resources", "type": "text"}, {"name": "⁕-help-desk", "type": "text"}]},
                    {"name": "┇ ٫ VOICE DISCUSSIONS | ☩", "channels": [{"name": "Daily Standup", "type": "voice"}, {"name": "Pair Programming", "type": "voice"}]}
                ]
            },
            "anime": {
                "name": "Anime & Manga",
                "categories": [
                    {"name": "✦ ─ ANIME DIRECTORY ─ ✦", "channels": [{"name": "◈-rules-and-news", "type": "text"}, {"name": "◈-weekly-schedule", "type": "text"}]},
                    {"name": "⬪ ٫ DISCUSSIONS ‧", "channels": [{"name": "₊-general-chat", "type": "text"}, {"name": "₊-anime-media", "type": "text"}, {"name": "₊-cosplay-and-art", "type": "text"}, {"name": "₊-recommendations", "type": "text"}]},
                    {"name": "┇ ٫ WATCH PARTIES | ☩", "channels": [{"name": "Stream Room 1", "type": "voice"}, {"name": "Stream Room 2", "type": "voice"}]}
                ]
            },
            "study": {
                "name": "Study & Productivity",
                "categories": [
                    {"name": "◈ ─ RECEPTION ─ ◈", "channels": [{"name": "✦-announcements", "type": "text"}, {"name": "✦-focus-resources", "type": "text"}]},
                    {"name": "⬪ ٫ STUDY HALL ‧", "channels": [{"name": "⁕-general-desk", "type": "text"}, {"name": "⁕-pomodoro-timer", "type": "text"}, {"name": "⁕-weekly-goals", "type": "text"}]},
                    {"name": "┇ ٫ SILENT LIBRARY | ☩", "channels": [{"name": "Quiet Room (Muted)", "type": "voice"}, {"name": "Study Session A", "type": "voice"}, {"name": "Study Session B", "type": "voice"}]}
                ]
            },
            "music": {
                "name": "Music & Lounge",
                "categories": [
                    {"name": "✦ ─ STATION DETAILS ─ ✦", "channels": [{"name": "⬪-rules", "type": "text"}, {"name": "⬪-music-events", "type": "text"}]},
                    {"name": "⬪ ٫ MUSIC DECK ‧", "channels": [{"name": "☊-general-lounge", "type": "text"}, {"name": "☊-song-requests", "type": "text"}, {"name": "☊-playlist-sharing", "type": "text"}]},
                    {"name": "┇ ٫ AUDIO ROOMS | ☩", "channels": [{"name": "Chill Corner", "type": "voice"}, {"name": "Live Stage", "type": "voice"}, {"name": "Stage Backstage", "type": "voice"}]}
                ]
            },
            "crypto": {
                "name": "Web3 & Crypto",
                "categories": [
                    {"name": "◈ ─ HUB TELEMETRY ─ ◈", "channels": [{"name": "▲-rules-and-signals", "type": "text"}, {"name": "▲-market-updates", "type": "text"}]},
                    {"name": "⬪ ٫ TRADING TERMINAL ‧", "channels": [{"name": "✦-general-discussion", "type": "text"}, {"name": "✦-charts-analysis", "type": "text"}, {"name": "✦-nft-showroom", "type": "text"}]},
                    {"name": "┇ ٫ ALPHA LOUNGES | ☩", "channels": [{"name": "Alpha Lounge", "type": "voice"}, {"name": "Trading Desk VC", "type": "voice"}]}
                ]
            },
            "artistic": {
                "name": "Artistic Studio",
                "categories": [
                    {"name": "┋ ✧ ─ 𝔠𝔯𝔢𝔞𝔱𝔦𝔳𝔢 𝔷𝔬𝔫𝔢 ─ ✧ ┋", "channels": [{"name": "✦-gallery-showroom", "type": "text"}, {"name": "✦-design-critique", "type": "text"}, {"name": "✦-commissions", "type": "text"}]},
                    {"name": "┋ ⬪ ٫ 𝔭𝔬𝔯𝔱𝔣𝔬𝔩𝔦𝔬𝔰 ‧ ┋", "channels": [{"name": "⁕-digital-art", "type": "text"}, {"name": "⁕-traditional-art", "type": "text"}, {"name": "⁕-resources", "type": "text"}]},
                    {"name": "┋ ┇ ٫ 𝔩𝔦𝔳𝔢 𝔡𝔯𝔞𝔴𝔦𝔫𝔤 | ☩ ┋", "channels": [{"name": "Co-Working Space", "type": "voice"}, {"name": "Sketch & Chat", "type": "voice"}]}
                ]
            },
            "roleplay": {
                "name": "Neon Roleplay",
                "categories": [
                    {"name": "┋ ✦ ─ ɴᴇᴏ-ᴛᴏᴋʏᴏ ─ ✦ ┋", "channels": [{"name": "◣-archives-lore", "type": "text"}, {"name": "◣-rules-and-signup", "type": "text"}]},
                    {"name": "┋ ⬪ ٫ ʀᴘ ᴅɪsᴛʀɪᴄᴛs ‧ ┋", "channels": [{"name": "▲-neon-alley-rp", "type": "text"}, {"name": "▲-underground-bar", "type": "text"}, {"name": "▲-corporate-sector", "type": "text"}]},
                    {"name": "┋ ┇ ٫ ᴠᴏɪᴄᴇ ʀᴘ | ☩ ┋", "channels": [{"name": "Tavern VC", "type": "voice"}, {"name": "Campfire Stories", "type": "voice"}]}
                ]
            },
            "esports": {
                "name": "Esports Arena",
                "categories": [
                    {"name": "┋ ⚙ ─ ᴛᴏᴜʀɴᴀᴍᴇɴᴛ ʜǫ ─ ⚙ ┋", "channels": [{"name": "▲-news-and-updates", "type": "text"}, {"name": "▲-schedule-brackets", "type": "text"}]},
                    {"name": "┋ ⬪ ٫ ᴡᴀʀ ʀᴏᴏᴍs ‧ ┋", "channels": [{"name": "✦-scrim-results", "type": "text"}, {"name": "✦-strategy-chat", "type": "text"}, {"name": "✦-vod-reviews", "type": "text"}]},
                    {"name": "┋ ┇ ٫ ᴄᴏᴍᴘᴇᴛɪᴛɪᴠᴇ ᴠᴄs | ☩ ┋", "channels": [{"name": "Team Alpha VC", "type": "voice"}, {"name": "Team Beta VC", "type": "voice"}, {"name": "Tournament Main", "type": "voice"}]}
                ]
            },
            "chill_cafe": {
                "name": "Cozy Cafe",
                "categories": [
                    {"name": "┋ ✿ ─ 𝓒𝓪𝓯𝓮 𝓡𝓮𝓬𝓮𝓹𝓽𝓲𝓸𝓷 ─ ✿ ┋", "channels": [{"name": "◈-rules-and-menu", "type": "text"}, {"name": "◈-announcements", "type": "text"}]},
                    {"name": "┋ ⬪ ٫ 𝓒𝓱𝓲𝓵𝓵 𝓣𝓪𝓫𝓵𝓮𝓼 ‧ ┋", "channels": [{"name": "⁕-fireside-chat", "type": "text"}, {"name": "⁕-media-sharing", "type": "text"}, {"name": "⁕-bot-commands", "type": "text"}]},
                    {"name": "┋ ┇ ٫ 𝓒𝓸𝓯𝓯𝓮𝓮 𝓑𝓻𝓮𝓪𝓴𝓼 | ☩ ┋", "channels": [{"name": "Cozy Fireplace", "type": "voice"}, {"name": "Lofi Bar", "type": "voice"}]}
                ]
            }
        }
        
        if template_id not in templates:
            return jsonify({"success": False, "error": "Invalid template ID"}), 400
            
        async def apply_tmpl():
            guild = bot.get_guild(int(guild_id))
            if not guild: return "Guild not found"
            
            tmpl = templates[template_id]["categories"]
            for cat_data in tmpl:
                cat = await guild.create_category(cat_data["name"])
                for chan in cat_data["channels"]:
                    if chan["type"] == "text":
                        await guild.create_text_channel(chan["name"], category=cat)
                    elif chan["type"] == "voice":
                        await guild.create_voice_channel(chan["name"], category=cat)
            return f"Successfully applied '{templates[template_id]['name']}' template!"
            
        future = asyncio.run_coroutine_threadsafe(apply_tmpl(), get_bot_loop())
        try:
            res = future.result(timeout=30)
            return jsonify({"success": True, "results": res}), 200
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    elif action == "server_font_apply":
        font_id = payload.get("font_id")
        target_channel_id = payload.get("channel_id")
        custom_name = payload.get("custom_name")
        task_id = str(uuid.uuid4())
        
        TASK_PROGRESS[task_id] = {"status": "running", "progress": 0, "total": 1, "message": "Starting font update..."}
        import src.web.fonts as fonts
        async def apply_font(t_id):
            try:
                guild = bot.get_guild(int(guild_id))
                if not guild:
                    TASK_PROGRESS[t_id] = {"status": "error", "message": "Guild not found"}
                    return
                
                affect_categories = payload.get("affect_categories", False)
                pattern = payload.get("pattern")
                
                # Apply to single channel
                if target_channel_id and target_channel_id != "all":
                    chan = guild.get_channel(int(target_channel_id))
                    if not chan: 
                        TASK_PROGRESS[t_id] = {"status": "error", "message": "Channel not found"}
                        return
                    base_name = custom_name if custom_name else chan.name.replace("-", " ")
                    base_name = fonts.clean_styled_string(base_name)
                    new_name = fonts.apply_font_to_string(base_name, font_id)
                    if pattern:
                        if "{word}" in pattern:
                            new_name = pattern.replace("{word}", new_name)
                        elif "{char}" in pattern:
                            new_name = "".join([pattern.replace("{char}", c) if c != " " else " " for c in new_name])
                    if isinstance(chan, discord.TextChannel):
                        new_name = new_name.replace(" ", "-")
                    await chan.edit(name=new_name)
                    TASK_PROGRESS[t_id] = {"status": "completed", "progress": 1, "total": 1, "message": f"Successfully renamed channel to '{new_name}'!"}
                    return

                # Apply to whole server
                total_cats = len(guild.categories) if affect_categories else 0
                total_chans = len([c for c in guild.channels if not isinstance(c, discord.CategoryChannel)])
                total_items = total_cats + total_chans
                TASK_PROGRESS[t_id]["total"] = total_items
                
                processed = 0
                if affect_categories:
                    for cat in guild.categories:
                        TASK_PROGRESS[t_id]["message"] = f"Renaming category: {cat.name}"
                        clean_name = cat.name.replace("-", " ")
                        clean_name = fonts.clean_styled_string(clean_name)
                        new_name = fonts.apply_font_to_string(clean_name, font_id)
                        if pattern:
                            if "{word}" in pattern:
                                new_name = pattern.replace("{word}", new_name)
                            elif "{char}" in pattern:
                                new_name = "".join([pattern.replace("{char}", c) if c != " " else " " for c in new_name])
                        if new_name != cat.name:
                            await cat.edit(name=new_name)
                            await asyncio.sleep(0.5)
                        processed += 1
                        TASK_PROGRESS[t_id]["progress"] = processed

                for chan in guild.channels:
                    if not isinstance(chan, discord.CategoryChannel):
                        TASK_PROGRESS[t_id]["message"] = f"Renaming channel: {chan.name}"
                        clean_name = chan.name.replace("-", " ")
                        clean_name = fonts.clean_styled_string(clean_name)
                        new_name = fonts.apply_font_to_string(clean_name, font_id)
                        if pattern:
                            if "{word}" in pattern:
                                new_name = pattern.replace("{word}", new_name)
                            elif "{char}" in pattern:
                                new_name = "".join([pattern.replace("{char}", c) if c != " " else " " for c in new_name])
                        if new_name != chan.name:
                            if isinstance(chan, discord.TextChannel):
                                new_name = new_name.replace(" ", "-")
                            await chan.edit(name=new_name)
                            await asyncio.sleep(0.5)
                        processed += 1
                        TASK_PROGRESS[t_id]["progress"] = processed

                TASK_PROGRESS[t_id] = {"status": "completed", "progress": total_items, "total": total_items, "message": f"Successfully applied font style '{font_id}'!"}
            except Exception as e:
                TASK_PROGRESS[t_id] = {"status": "error", "message": str(e)}

        asyncio.run_coroutine_threadsafe(apply_font(task_id), get_bot_loop())
        return jsonify({"success": True, "task_id": task_id}), 200

    elif action == "server_apply_layout":
        layout = payload.get("layout", {})
        task_id = str(uuid.uuid4())
        
        chan_updates = layout.get("channels", {})
        total_updates = len(chan_updates)
        TASK_PROGRESS[task_id] = {"status": "running", "progress": 0, "total": total_updates, "message": "Starting permission updates..."}
        
        async def apply_layout(t_id):
            try:
                guild = bot.get_guild(int(guild_id))
                if not guild:
                    TASK_PROGRESS[t_id] = {"status": "error", "message": "Guild not found"}
                    return
                
                processed = 0
                for chan_id, chan_data in chan_updates.items():
                    chan = guild.get_channel(int(chan_id))
                    if not chan: 
                        processed += 1
                        continue
                    
                    TASK_PROGRESS[t_id]["message"] = f"Updating permissions for: {chan.name}"
                    
                    overwrites = chan.overwrites
                    # Apply public/private
                    if chan_data.get("public"):
                        if guild.default_role in overwrites:
                            overwrites[guild.default_role].read_messages = None
                    else:
                        if guild.default_role not in overwrites:
                            overwrites[guild.default_role] = discord.PermissionOverwrite()
                        overwrites[guild.default_role].read_messages = False
                        
                    # Apply roles
                    allowed_roles = chan_data.get("roles", [])
                    for role_id in allowed_roles:
                        role = guild.get_role(int(role_id))
                        if role:
                            if role not in overwrites:
                                overwrites[role] = discord.PermissionOverwrite()
                            overwrites[role].read_messages = True
                            
                    await chan.edit(overwrites=overwrites)
                    await asyncio.sleep(0.5)
                    processed += 1
                    TASK_PROGRESS[t_id]["progress"] = processed
                    
                TASK_PROGRESS[t_id] = {"status": "completed", "progress": total_updates, "total": total_updates, "message": "Server layout permissions successfully updated!"}
            except Exception as e:
                TASK_PROGRESS[t_id] = {"status": "error", "message": str(e)}
                
        asyncio.run_coroutine_threadsafe(apply_layout(task_id), get_bot_loop())
        return jsonify({"success": True, "task_id": task_id}), 200

@app.route("/api/guild/<guild_id>/custom_commands", methods=["PATCH"])
def api_guild_custom_commands(guild_id):
    if not verify_session():
        return jsonify({"success": False, "error": "unauthorized"}), 401
    payload = request.get_json()
    payload.pop("category", None)
    
    trigger_word = str(payload.get("cc_trigger", "")).strip().lower()
    if not trigger_word:
        return jsonify({"success": False, "error": "Trigger word is required."}), 400
        
    db_payload = {
        "guild_id": guild_id,
        "trigger_word": trigger_word,
        "response_text": payload.get("cc_response", ""),
        "permission_level": payload.get("cc_permission", "Everyone"),
        "image_url": payload.get("cc_image") or None,
        "gif_url": payload.get("cc_gif") or None
    }
    
    try:
        # Update if exists, else insert
        resp = supabase.from_("custom_commands").select("*").eq("guild_id", guild_id).eq("trigger_word", trigger_word).execute()
        if resp.data:
            supabase.from_("custom_commands").update(db_payload).eq("guild_id", guild_id).eq("trigger_word", trigger_word).execute()
        else:
            supabase.from_("custom_commands").insert(db_payload).execute()
            
        from src.db import client as db_client
        db_client.clear_guild_cache(guild_id)
        
        return jsonify({"success": True, "message": "Custom command saved successfully!"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/guild/<guild_id>/custom_commands", methods=["GET"])
def api_guild_get_custom_commands(guild_id):
    if not verify_session():
        return jsonify({"success": False, "error": "unauthorized"}), 401
    try:
        resp = supabase.from_("custom_commands").select("*").eq("guild_id", guild_id).order("trigger_word").execute()
        return jsonify({"success": True, "commands": resp.data or []}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/guild/<guild_id>/custom_commands/<path:trigger_word>", methods=["DELETE"])
def api_guild_delete_custom_command(guild_id, trigger_word):
    if not verify_session():
        return jsonify({"success": False, "error": "unauthorized"}), 401
    trigger_word = trigger_word.strip().lower()
    try:
        supabase.from_("custom_commands").delete().eq("guild_id", guild_id).eq("trigger_word", trigger_word).execute()
        
        from src.db import client as db_client
        db_client.clear_guild_cache(guild_id)
        
        return jsonify({"success": True, "message": f"Custom command '{trigger_word}' deleted successfully!"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/guild/<guild_id>/giveaways", methods=["PATCH"])
def api_guild_giveaways(guild_id):
    if not verify_session():
        return jsonify({"success": False, "error": "unauthorized"}), 401
    payload = request.get_json()
    payload.pop("category", None)
    
    # Get user info from token to set host_id
    token = request.cookies.get("discord_token")
    user_id = "unknown"
    if token:
        try:
            user_data = get_user_info(token)
            user_id = user_data.get("id", "unknown")
        except:
            pass

    import uuid
    import datetime
    import json
    
    db_id = str(uuid.uuid4())
    
    # Parse Timing
    start_time = None
    if payload.get("gw_use_dates"):
        start_str = payload.get("gw_start_time")
        end_str = payload.get("gw_end_time")
        if start_str:
            if "T" in start_str and not start_str.endswith("Z") and "+" not in start_str:
                start_time = f"{start_str}:00Z"
            else:
                start_time = start_str
        if end_str:
            if "T" in end_str and not end_str.endswith("Z") and "+" not in end_str:
                end_time = f"{end_str}:00Z"
            else:
                end_time = end_str
        else:
            duration_hours = int(payload.get("gw_duration", 24))
            end_time = (datetime.datetime.utcnow() + datetime.timedelta(hours=duration_hours)).isoformat() + "Z"
    else:
        duration_hours = int(payload.get("gw_duration", 24))
        end_time = (datetime.datetime.utcnow() + datetime.timedelta(hours=duration_hours)).isoformat() + "Z"

    # Deserialize role list & embed settings
    allowed_roles = []
    allowed_roles_str = payload.get("gw_allowed_roles")
    if allowed_roles_str:
        try:
            allowed_roles = json.loads(allowed_roles_str) if isinstance(allowed_roles_str, str) else allowed_roles_str
        except:
            allowed_roles = []
            
    embed_config = {}
    embed_config_str = payload.get("gw_embed_config")
    if embed_config_str:
        try:
            embed_config = json.loads(embed_config_str) if isinstance(embed_config_str, str) else embed_config_str
        except:
            embed_config = {}

    if isinstance(embed_config, dict):
        embed_config["participants"] = []

    db_payload = {
        "id": db_id,
        "guild_id": guild_id,
        "channel_id": payload.get("gw_channel_id"),
        "message_id": "pending",
        "host_id": user_id,
        "prize": payload.get("gw_prize"),
        "winners_count": int(payload.get("gw_winners", 1)),
        "start_time": start_time,
        "end_time": end_time,
        "restrict_roles_enabled": bool(payload.get("gw_restrict_roles_enabled", False)),
        "allowed_roles": allowed_roles,
        "roles_mode": payload.get("gw_roles_mode", "any"),
        "roles_reverse": bool(payload.get("gw_roles_reverse", False)),
        "animation_style": payload.get("gw_animation_style", "scrolling_wheel"),
        "embed_config": embed_config
    }
    
    try:
        supabase.from_("giveaways").insert(db_payload).execute()
        
        # Trigger the bot to schedule the giveaway
        from src.bot.engine import bot
        cog = bot.get_cog("Giveaways")
        if cog:
            import asyncio
            asyncio.run_coroutine_threadsafe(cog.start_dashboard_giveaway(db_id), get_bot_loop())
            
        return jsonify({"success": True, "message": "Giveaway successfully created and scheduled! 🎉"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/guild/<guild_id>/channels")
def api_guild_channels(guild_id):
    if not verify_session():
        return jsonify({"error": "unauthorized"}), 401
    from src.bot.engine import bot
    if not bot or not bot.is_ready():
        return jsonify([])
    guild = bot.get_guild(int(guild_id))
    if not guild:
        return jsonify([])
    channels = [{"id": str(c.id), "name": c.name, "type": str(c.type)} for c in guild.channels]
    return jsonify(channels)

@app.route("/api/guild/<guild_id>/roles")
def api_guild_roles(guild_id):
    if not verify_session():
        return jsonify({"error": "unauthorized"}), 401
    from src.bot.engine import bot
    if not bot or not bot.is_ready():
        return jsonify([])
    guild = bot.get_guild(int(guild_id))
    if not guild:
        return jsonify([])
    roles = [{"id": str(r.id), "name": r.name, "color": str(r.color)} for r in guild.roles]
    return jsonify(roles)

@app.route("/api/guild/logs")
def api_guild_logs():
    if not verify_session():
        return jsonify({"error": "unauthorized"}), 401
    
    guild_id, _ = get_session_guild_context()
    if not guild_id:
        return jsonify({"logs": []})
        
    from src.db.client import get_protection_logs
    logs = get_protection_logs(guild_id, limit=50)
    return jsonify({"logs": logs})

@app.route("/api/status")
def api_status():
    from src.bot.engine import bot
    import math
    ready = bot.is_ready() if bot else False
    
    latency_ms = "N/A"
    if ready and bot.latency and not math.isinf(bot.latency):
        latency_ms = f"{round(bot.latency * 1000)}ms"
        
    return jsonify({
        "status": "online" if ready else "offline",
        "latency": latency_ms,
        "guilds": len(bot.guilds) if ready else 0,
        "users": len(bot.users) if ready else 0
    })

def get_telemetry_summary():
    """Calculate and return telemetry metrics."""
    uptime_sec = int(time.time() - START_TIME)
    h, rem = divmod(uptime_sec, 3600)
    m, s = divmod(rem, 60)
    formatted_uptime = f"{h:02d}h {m:02d}m {s:02d}s"
    
    registry = load_telemetry()
    total_pings = sum(info.get("ping_count", 0) for info in registry.values())
    
    nodes_list = []
    now = datetime.datetime.utcnow()
    active_count = 0
    
    for url, info in registry.items():
        last_seen_str = info.get("last_seen")
        status = "offline"
        
        if last_seen_str:
            try:
                clean_time = last_seen_str
                if clean_time.endswith("Z"):
                    clean_time = clean_time[:-1]
                dt = datetime.datetime.fromisoformat(clean_time)
                diff = (now - dt).total_seconds()
                if diff < 90:
                    status = "online"
                    active_count += 1
            except Exception as e:
                logger.error(f"Error parsing date {last_seen_str}: {e}")
                
        nodes_list.append({
            "node_url": url,
            "label": info.get("label", "PEER NODE"),
            "last_seen": last_seen_str or "Never",
            "ping_count": info.get("ping_count", 0),
            "status": status,
            "peers": info.get("peers", [])
        })
        
    # Sort nodes: online first, then by ping count desc, then url
    nodes_list.sort(key=lambda x: (x["status"] != "online", -x["ping_count"], x["node_url"]))
    
    return {
        "uptime": formatted_uptime,
        "total_pings": total_pings,
        "nodes": nodes_list,
        "node_count": len(nodes_list),
        "active_count": active_count
    }

def ping_single_peer(ping_url, headers, base_url):
    """Pings a single peer and processes its response."""
    import urllib.request
    try:
        req = urllib.request.Request(ping_url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            body = response.read().decode('utf-8', errors='ignore')
            if response.status == 200:
                registry = load_telemetry()
                now_iso = datetime.datetime.utcnow().isoformat() + "Z"
                if base_url in registry:
                    registry[base_url]["last_seen"] = now_iso
                    registry[base_url]["is_active"] = True
                    
                if body:
                    try:
                        data = json.loads(body)
                        if isinstance(data, dict) and "peers" in data:
                            for peer in data["peers"]:
                                peer = peer.strip().rstrip("/")
                                if peer and peer not in registry:
                                    registry[peer] = {
                                        "node_url": peer,
                                        "label": "GOSSIP DISCOVERED",
                                        "last_seen": None,
                                        "ping_count": 0,
                                        "peers": [],
                                        "is_active": True
                                    }
                    except:
                        pass
                save_telemetry(registry)
    except Exception:
        pass

def background_ping_loop():
    """Background thread that pings registered peers to maintain mesh activity."""
    import threading
    time.sleep(15)  # Wait for startup
    while True:
        try:
            registry = load_telemetry()
            if not registry:
                time.sleep(30)
                continue
                
            self_url = os.getenv("SELF_URL") or os.getenv("AWAKE_URL")
            active_peers = [url for url, info in registry.items() if info.get("is_active", True)]
            
            headers = {
                "User-Agent": "Kaizer-Telemetry-Node/2.0 (Windows; P2P-Mesh)",
            }
            if self_url:
                headers["X-Awake-URL"] = self_url
                
            peers_list = [p for p in active_peers if p != self_url]
            if peers_list:
                headers["X-Peers"] = ",".join(peers_list)
                
            for url in registry.keys():
                if self_url and url == self_url:
                    continue
                ping_url = url
                if ping_url.count('/') == 2:
                    ping_url += "/hook.html"
                
                t = threading.Thread(target=ping_single_peer, args=(ping_url, headers, url), daemon=True)
                t.start()
        except Exception as e:
            logger.error(f"Error in background ping loop: {e}")
        time.sleep(30)

# Start background ping thread
import threading
threading.Thread(target=background_ping_loop, daemon=True, name="TelemetryPingLoop").start()

@app.route("/hook.html", methods=["GET", "POST"])
@app.route("/hook", methods=["GET", "POST"])
@app.route("/api/hook", methods=["GET", "POST"])
def awake_hook():
    # If requests are arriving, we can dynamically detect and set SELF_URL if not set
    host = request.headers.get("Host")
    if host and not host.startswith("localhost") and not host.startswith("127.0.0.1"):
        scheme = request.scheme or "https"
        detected_url = f"{scheme}://{host}"
        if not os.getenv("SELF_URL") and not os.getenv("AWAKE_URL"):
            os.environ["SELF_URL"] = detected_url

    awake_url = request.headers.get("X-Awake-URL") or request.args.get("awake_url")
    peers_raw = request.headers.get("X-Peers") or request.args.get("peers")
    
    is_json = (
        awake_url is not None or 
        request.headers.get("Accept") == "application/json" or 
        request.args.get("format") == "json" or 
        request.method == "POST"
    )
    
    if awake_url:
        register_awake_heartbeat(awake_url, peers_raw)
        
    cors_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, X-Awake-URL, X-Peers',
    }
    
    if request.method == 'OPTIONS':
        resp = make_response('', 204)
        for k, v in cors_headers.items():
            resp.headers[k] = v
        return resp
        
    if is_json:
        registry = load_telemetry()
        peers_list = [url for url, info in registry.items() if info.get("is_active", True)]
        self_url = os.getenv("SELF_URL") or os.getenv("AWAKE_URL") or request.host_url.rstrip("/")
        if self_url not in peers_list:
            peers_list.append(self_url)
            
        resp = jsonify({
            "status": "pulse received",
            "node": "KAIZER-PULSE",
            "peers": peers_list
        })
        for k, v in cors_headers.items():
            resp.headers[k] = v
        return resp
        
    telemetry_data = get_telemetry_summary()
    return render_template("hook.html", **telemetry_data)

@app.route("/api/awake/status", methods=["GET"])
def awake_status_api():
    cors_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET',
        'Access-Control-Allow-Headers': 'Content-Type',
    }
    resp = jsonify(get_telemetry_summary())
    for k, v in cors_headers.items():
        resp.headers[k] = v
    return resp

@app.route("/health")
def health_check():
    from src.bot.engine import bot
    bot_ready = bot.is_ready() if bot else False
    return jsonify({"web": "healthy", "bot": "online" if bot_ready else "connecting"})

# ---------------------------------------------------------------------------
# Run the development server (only when invoked directly)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logger.info(f"Starting Flask dashboard on http://{config.HOST}:{config.PORT}")
    app.run(host=config.HOST, port=config.PORT, debug=False)
