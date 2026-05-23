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

supabase: Client = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_ROLE_KEY)

# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def get_redirect_uri() -> str:
    """Build the OAuth2 callback redirect URL dynamically based on the current request domain."""
    env_redirect = os.getenv("DISCORD_REDIRECT_URI")
    if env_redirect:
        return env_redirect
    return request.host_url.rstrip("/") + "/callback"

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
    
    resp = make_response(render_template("server.html", user=user, guild_id=guild_id))
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
    return render_template(
        "help.html",
        user=user,
        guild_id=guild_id,
        guild_name=guild_name,
        is_developer=is_dev
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
        return jsonify(resp.data[0] if resp.data else {})
    elif request.method == "PATCH":
        payload = request.get_json()
        if not payload:
            return jsonify({"success": False, "error": "Missing JSON"}), 400
        
        # Remove category if it exists since it's just for frontend tracking
        category = payload.pop("category", None)
        
        resp = supabase.from_("guild_settings").select("*").eq("guild_id", guild_id).execute()
        try:
            if resp.data:
                res = supabase.from_("guild_settings").update(payload).eq("guild_id", guild_id).execute()
            else:
                payload["guild_id"] = guild_id
                res = supabase.from_("guild_settings").insert(payload).execute()
            return jsonify({"success": True, "message": f"{category.capitalize() + ' s' if category else 'S'}ettings saved successfully!"}), 200
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
            if not guild: return "Guild not found or bot not in guild."
            issues = 0
            for channel in guild.channels:
                if isinstance(channel, discord.TextChannel):
                    overrides = channel.overwrites_for(guild.default_role)
                    if overrides.read_messages is False and len(channel.changed_roles) == 0:
                        issues += 1
            if issues == 0:
                return "Server permissions look healthy."
            return f"Found {issues} channels completely hidden to everyone with no role overrides."
            
        future = asyncio.run_coroutine_threadsafe(do_audit(), bot.loop)
        try:
            results = future.result(timeout=10)
            return jsonify({"success": True, "results": results}), 200
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
            
    elif action == "server_export":
        async def do_export():
            guild = bot.get_guild(int(guild_id))
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
            
        future = asyncio.run_coroutine_threadsafe(do_export(), bot.loop)
        try:
            data = future.result(timeout=10)
            return jsonify({"success": True, "export_data": data}), 200
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
            
    elif action == "server_template_apply":
        template_id = payload.get("template_id")
        templates = {
            "gaming": [
                {"name": "Information", "channels": [{"name": "rules", "type": "text"}, {"name": "announcements", "type": "text"}]},
                {"name": "Main Hub", "channels": [{"name": "general", "type": "text"}, {"name": "looking-for-group", "type": "text"}]},
                {"name": "Voice Lobbies", "channels": [{"name": "Lobby", "type": "voice"}, {"name": "Gaming 1", "type": "voice"}, {"name": "Gaming 2", "type": "voice"}]}
            ],
            "community": [
                {"name": "Welcome", "channels": [{"name": "rules", "type": "text"}, {"name": "introductions", "type": "text"}]},
                {"name": "General", "channels": [{"name": "chat", "type": "text"}, {"name": "media", "type": "text"}, {"name": "memes", "type": "text"}]},
                {"name": "Voice", "channels": [{"name": "General VC", "type": "voice"}, {"name": "Music VC", "type": "voice"}]}
            ],
            "creator": [
                {"name": "Announcements", "channels": [{"name": "new-videos", "type": "text"}, {"name": "stream-alerts", "type": "text"}]},
                {"name": "Community", "channels": [{"name": "chat", "type": "text"}, {"name": "fan-art", "type": "text"}]},
                {"name": "Voice", "channels": [{"name": "Hangout", "type": "voice"}, {"name": "Stage", "type": "voice"}]}
            ],
            "tech": [
                {"name": "Info", "channels": [{"name": "readme", "type": "text"}, {"name": "guidelines", "type": "text"}]},
                {"name": "Development", "channels": [{"name": "general", "type": "text"}, {"name": "github-feed", "type": "text"}, {"name": "support", "type": "text"}]},
                {"name": "Meetings", "channels": [{"name": "Standup", "type": "voice"}, {"name": "Discussion", "type": "voice"}]}
            ]
        }
        
        if template_id not in templates:
            return jsonify({"success": False, "error": "Invalid template ID"}), 400
            
        async def apply_tmpl():
            guild = bot.get_guild(int(guild_id))
            if not guild: return "Guild not found"
            
            tmpl = templates[template_id]
            for cat_data in tmpl:
                cat = await guild.create_category(cat_data["name"])
                for chan in cat_data["channels"]:
                    if chan["type"] == "text":
                        await guild.create_text_channel(chan["name"], category=cat)
                    elif chan["type"] == "voice":
                        await guild.create_voice_channel(chan["name"], category=cat)
            return f"Successfully applied '{template_id}' template!"
            
        future = asyncio.run_coroutine_threadsafe(apply_tmpl(), bot.loop)
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
                
                # Apply to single channel
                if target_channel_id and target_channel_id != "all":
                    chan = guild.get_channel(int(target_channel_id))
                    if not chan: 
                        TASK_PROGRESS[t_id] = {"status": "error", "message": "Channel not found"}
                        return
                    base_name = custom_name if custom_name else chan.name.replace("-", " ")
                    new_name = fonts.apply_font_to_string(base_name, font_id)
                    if isinstance(chan, discord.TextChannel):
                        new_name = new_name.replace(" ", "-")
                    await chan.edit(name=new_name)
                    TASK_PROGRESS[t_id] = {"status": "completed", "progress": 1, "total": 1, "message": f"Successfully renamed channel to '{new_name}'!"}
                    return

                # Apply to whole server
                total_cats = len(guild.categories)
                total_chans = len([c for c in guild.channels if not isinstance(c, discord.CategoryChannel)])
                total_items = total_cats + total_chans
                TASK_PROGRESS[t_id]["total"] = total_items
                
                processed = 0
                for cat in guild.categories:
                    TASK_PROGRESS[t_id]["message"] = f"Renaming category: {cat.name}"
                    clean_name = cat.name.replace("-", " ")
                    new_name = fonts.apply_font_to_string(clean_name, font_id)
                    if new_name != cat.name:
                        await cat.edit(name=new_name)
                        await asyncio.sleep(0.5)
                    processed += 1
                    TASK_PROGRESS[t_id]["progress"] = processed

                for chan in guild.channels:
                    if not isinstance(chan, discord.CategoryChannel):
                        TASK_PROGRESS[t_id]["message"] = f"Renaming channel: {chan.name}"
                        clean_name = chan.name
                        new_name = fonts.apply_font_to_string(clean_name, font_id)
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

        asyncio.run_coroutine_threadsafe(apply_font(task_id), bot.loop)
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
                
        asyncio.run_coroutine_threadsafe(apply_layout(task_id), bot.loop)
        return jsonify({"success": True, "task_id": task_id}), 200

@app.route("/api/guild/<guild_id>/custom_commands", methods=["PATCH"])
def api_guild_custom_commands(guild_id):
    if not verify_session():
        return jsonify({"success": False, "error": "unauthorized"}), 401
    payload = request.get_json()
    payload.pop("category", None)
    
    db_payload = {
        "guild_id": guild_id,
        "trigger_word": payload.get("cc_trigger"),
        "response_text": payload.get("cc_response"),
        "permission_level": payload.get("cc_permission", "Everyone")
    }
    
    try:
        # Update if exists, else insert
        resp = supabase.from_("custom_commands").select("*").eq("guild_id", guild_id).eq("trigger_word", db_payload["trigger_word"]).execute()
        if resp.data:
            supabase.from_("custom_commands").update(db_payload).eq("guild_id", guild_id).eq("trigger_word", db_payload["trigger_word"]).execute()
        else:
            supabase.from_("custom_commands").insert(db_payload).execute()
        return jsonify({"success": True, "message": "Custom command saved successfully!"}), 200
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

    import datetime
    duration_hours = int(payload.get("gw_duration", 24))
    end_time = (datetime.datetime.utcnow() + datetime.timedelta(hours=duration_hours)).isoformat()

    db_payload = {
        "guild_id": guild_id,
        "channel_id": payload.get("gw_channel_id"),
        "message_id": "pending", # Would be updated by the bot when it sends the message
        "host_id": user_id,
        "prize": payload.get("gw_prize"),
        "winners_count": payload.get("gw_winners", 1),
        "end_time": end_time
    }
    
    try:
        supabase.from_("giveaways").insert(db_payload).execute()
        # In a real scenario, you would trigger the bot via websocket/redis to send the actual Discord message
        return jsonify({"success": True, "message": "Giveaway created! (Note: Bot needs to post the message)"}), 200
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
