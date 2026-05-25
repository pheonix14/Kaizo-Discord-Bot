import logging
import discord
import time
import random
import string
import os
import requests
from fastapi import FastAPI, Request, Response, Form, HTTPException, Depends, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Dict, Optional
from pathlib import Path
from src import config
from src.db import client as db_client

logger = logging.getLogger("kaizer_k5.web")

app = FastAPI(title="Project Kaizer K5 Dashboard")

# Set up templates and static directories
BASE_DIR = Path(__file__).parent.parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Register global template helper for Discord invite URL
def get_invite_url(request: Request) -> str:
    client_id = config.DISCORD_APP_ID or "1507250208495505478"
    # Use a configurable redirect URI; fallback to request base URL + /callback
    redirect_uri = os.getenv("DISCORD_REDIRECT_URI")
    if not redirect_uri:
        base_url = str(request.base_url).rstrip('/')
        redirect_uri = f"{base_url}/callback"
    # Encode redirect URI
    from urllib.parse import quote_plus
    encoded_redirect = quote_plus(redirect_uri)
    # Use appropriate OAuth2 scopes for login (identify and email). Exclude bot permissions.
    scope = "identify%20email"
    return f"https://discord.com/api/oauth2/authorize?client_id={client_id}&redirect_uri={encoded_redirect}&response_type=code&scope={scope}"

templates.env.globals["get_invite_url"] = get_invite_url

# Shared in-memory login codes
# Structure: code -> {"guild_id": str, "user_id": str, "expires_at": float}
active_login_codes: Dict[str, dict] = {}

# Active dashboard sessions
# Structure: session_token -> {"guild_id": str, "user_id": str, "expires_at": float}
active_sessions: Dict[str, dict] = {}

def generate_pin_code() -> str:
    """Generate a random 6-character alphanumeric PIN code."""
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choice(chars) for _ in range(6))

def register_login_code(guild_id: str, user_id: str) -> str:
    """Generate and register a passcode for a guild admin."""
    # Remove any existing codes for this user/guild
    to_delete = [code for code, data in active_login_codes.items() if data["guild_id"] == guild_id and data["user_id"] == user_id]
    for code in to_delete:
        active_login_codes.pop(code, None)
        
    code = generate_pin_code()
    active_login_codes[code] = {
        "guild_id": str(guild_id),
        "user_id": str(user_id),
        "expires_at": time.time() + 300  # 5 minutes expiration
    }
    return code

def verify_session(session_token: Optional[str] = Cookie(None)) -> dict:
    """Dependency to verify if a user session is active and valid."""
    if not session_token or session_token not in active_sessions:
        raise HTTPException(status_code=303, detail="Not authorized")
        
    session = active_sessions[session_token]
    if time.time() > session["expires_at"]:
        active_sessions.pop(session_token, None)
        raise HTTPException(status_code=303, detail="Session expired")
        
    # Extend session expiration time on interaction
    session["expires_at"] = time.time() + 3600  # 1 hour extension
    return session

@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request, error: Optional[str] = None):
    # Check if bot is connected
    from src.bot.engine import bot
    bot_online = bot.is_ready() if bot else False
    
    token = request.cookies.get("session_token")
    guild_id = None
    if token and token in active_sessions:
        guild_id = active_sessions[token]["guild_id"]
        
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "bot_online": bot_online,
            "error": error,
            "guild_id": guild_id
        }
    )

@app.get("/login", response_class=HTMLResponse)
async def get_login(request: Request, error: Optional[str] = None):
    # Check if bot is connected
    from src.bot.engine import bot
    bot_online = bot.is_ready() if bot else False
    
    token = request.cookies.get("session_token")
    guild_id = None
    if token and token in active_sessions:
        guild_id = active_sessions[token]["guild_id"]
        
    return templates.TemplateResponse(
        request=request,
        name="auth.html",
        context={
            "bot_online": bot_online,
            "error": error,
            "guild_id": guild_id
        }
    )

@app.post("/login")
async def do_login(request: Request, pin: str = Form(...)):
    pin = pin.strip().upper()
    now = time.time()
    
    # Check if code exists and is valid
    if pin not in active_login_codes:
        return templates.TemplateResponse(
            request=request,
            name="auth.html",
            context={
                "bot_online": True,
                "error": "Invalid login code. Make sure you entered it correctly."
            }
        )
        
    code_data = active_login_codes[pin]
    if now > code_data["expires_at"]:
        active_login_codes.pop(pin, None)
        return templates.TemplateResponse(
            request=request,
            name="auth.html",
            context={
                "bot_online": True,
                "error": "Login code has expired. Generate a new one in Discord."
            }
        )
        
    # Valid code, create session
    session_token = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(32))
    active_sessions[session_token] = {
        "guild_id": code_data["guild_id"],
        "user_id": code_data["user_id"],
        "expires_at": now + 3600  # 1 hour session
    }
    
    # Clean up the code
    active_login_codes.pop(pin, None)
    
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(key="session_token", value=session_token, httponly=True)
    return response

@app.get("/logout")
async def do_logout(response: Response, session_token: Optional[str] = Cookie(None)):
    if session_token in active_sessions:
        active_sessions.pop(session_token, None)
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="session_token")
    return response

@app.get("/callback")
async def oauth_callback(request: Request, code: Optional[str] = None):
    """Handle Discord OAuth2 callback, exchange code for token, retrieve user info, and create a session."""
    if not code:
        # Fallback: if no code, maybe legacy flow with guild_id param
        guild_id = request.query_params.get("guild_id")
        if not guild_id:
            return RedirectResponse(url="/login?error=Missing+code+or+guild_id", status_code=303)
        # Treat as admin login using guild_id only (legacy)
        session_token = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(32))
        active_sessions[session_token] = {
            "guild_id": str(guild_id),
            "user_id": "admin",
            "expires_at": time.time() + 3600
        }
        response = RedirectResponse(url="/dashboard", status_code=303)
        response.set_cookie(key="session_token", value=session_token, httponly=True)
        return response
    # Exchange code for access token
    client_id = config.DISCORD_APP_ID
    client_secret = os.getenv("DISCORD_CLIENT_SECRET")
    redirect_uri = os.getenv("DISCORD_REDIRECT_URI") or str(request.base_url).rstrip('/') + "/callback"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    import requests
    token_resp = requests.post("https://discord.com/api/oauth2/token", data=data, headers=headers)
    if token_resp.status_code != 200:
        logger.error(f"OAuth token exchange failed: {token_resp.text}")
        return RedirectResponse(url="/login?error=OAuth+failed", status_code=303)
    token_json = token_resp.json()
    access_token = token_json.get("access_token")
    # Retrieve user info
    user_resp = requests.get("https://discord.com/api/users/@me", headers={"Authorization": f"Bearer {access_token}"})
    if user_resp.status_code != 200:
        logger.error(f"Failed to fetch user info: {user_resp.text}")
        return RedirectResponse(url="/login?error=User+info+failed", status_code=303)
    user_json = user_resp.json()
    user_id = str(user_json.get("id"))
    # Determine guild membership via bot (optional). Here we just set guild_id to 0 if not known.
    guild_id = "0"
    # Create session token
    session_token = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(32))
    active_sessions[session_token] = {
        "guild_id": guild_id,
        "user_id": user_id,
        "expires_at": time.time() + 3600
    }
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(key="session_token", value=session_token, httponly=True)
    return response

@app.get("/dashboard", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    token = request.cookies.get("session_token")
    try:
        session = verify_session(token)
    except HTTPException:
        return RedirectResponse(url="/login?error=Please login to access the dashboard", status_code=303)
        
    guild_id = session["guild_id"]
    
    # Get bot guild details
    from src.bot.engine import bot
    guild = bot.get_guild(int(guild_id)) if bot else None
    guild_name = guild.name if guild else "Protected Server"
    guild_icon = str(guild.icon.url) if guild and guild.icon else None
    
    # Fetch settings from Supabase
    settings = db_client.get_guild_settings(guild_id, guild_name)
    whitelist_ids = db_client.get_guild_whitelist(guild_id)
    
    # Match whitelist IDs to Discord Members if online
    whitelist_users = []
    for uid in whitelist_ids:
        member = guild.get_member(int(uid)) if guild else None
        whitelist_users.append({
            "id": uid,
            "name": member.name if member else f"User ID: {uid}",
            "avatar": str(member.display_avatar.url) if member else None
        })

    # Fetch counters settings
    counters_settings = db_client.get_counter_settings(guild_id)
    if not counters_settings:
        counters_settings = {
            "style": "minimal",
            "refresh_interval": "7d",
            "total_format": "members: {count}",
            "online_format": "online: {online}",
            "offline_format": "offline: {offline}",
            "invc_format": "in vc: {invc}",
            "category_id": "",
            "total_channel_id": "",
            "online_channel_id": "",
            "offline_channel_id": "",
            "invc_channel_id": "",
            "tracked_vc_id": ""
        }

    # Fetch temp VC settings
    temp_vc_settings = db_client.get_temp_vc_settings(guild_id)
    if not temp_vc_settings:
        temp_vc_settings = {
            "lobby_channel_id": "",
            "category_id": "",
            "default_limit": 0,
            "default_name_format": "{user}'s VC",
            "default_locked": False
        }

    from src.bot.decoration import DECOR_THEMES
    
    # Build list of categories, voice channels, and text channels
    categories = []
    voice_channels = []
    text_channels = []
    if guild:
        for ch in guild.categories:
            categories.append({"id": str(ch.id), "name": ch.name})
        for ch in guild.voice_channels:
            voice_channels.append({"id": str(ch.id), "name": ch.name})
        for ch in guild.text_channels:
            text_channels.append({"id": str(ch.id), "name": ch.name})

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "guild_name": guild_name,
            "guild_id": guild_id,
            "guild_icon": guild_icon,
            "settings": settings,
            "whitelist": whitelist_users,
            "counters_settings": counters_settings,
            "temp_vc_settings": temp_vc_settings,
            "categories": categories,
            "voice_channels": voice_channels,
            "text_channels": text_channels,
            "decor_themes": DECOR_THEMES
        }
    )

@app.get("/logs", response_class=HTMLResponse)
async def read_logs_page(request: Request):
    token = request.cookies.get("session_token")
    try:
        session = verify_session(token)
    except HTTPException:
        return RedirectResponse(url="/login?error=Please login to access logs", status_code=303)
        
    guild_id = session["guild_id"]
    from src.bot.engine import bot
    guild = bot.get_guild(int(guild_id)) if bot else None
    guild_name = guild.name if guild else "Protected Server"
    
    return templates.TemplateResponse(
        request=request,
        name="logs.html",
        context={
            "guild_name": guild_name,
            "guild_id": guild_id
        }
    )

@app.get("/help", response_class=HTMLResponse)
async def read_help(request: Request):
    # Check if there is an active session
    token = request.cookies.get("session_token")
    guild_id = None
    if token and token in active_sessions:
        guild_id = active_sessions[token]["guild_id"]
        
    return templates.TemplateResponse(
        request=request,
        name="help.html",
        context={
            "guild_id": guild_id
        }
    )

# --- JSON API ROUTES ---

@app.get("/api/guild/settings")
async def get_settings(session: dict = Depends(verify_session)):
    guild_id = session["guild_id"]
    settings = db_client.get_guild_settings(guild_id)
    return JSONResponse(content=settings)

@app.post("/api/guild/settings")
async def update_settings(request: Request, session: dict = Depends(verify_session)):
    guild_id = session["guild_id"]
    body = await request.json()
    
    # Sanitize and compile settings payload
    updates = {
        "anti_ban_limit": int(body.get("anti_ban_limit", 3)),
        "anti_ban_time_frame": int(body.get("anti_ban_time_frame", 60)),
        "anti_kick_limit": int(body.get("anti_kick_limit", 3)),
        "anti_kick_time_frame": int(body.get("anti_kick_time_frame", 60)),
        "anti_channel_delete_limit": int(body.get("anti_channel_delete_limit", 2)),
        "anti_channel_delete_time_frame": int(body.get("anti_channel_delete_time_frame", 60)),
        "anti_role_delete_limit": int(body.get("anti_role_delete_limit", 2)),
        "anti_role_delete_time_frame": int(body.get("anti_role_delete_time_frame", 60)),
        "anti_bot_add": bool(body.get("anti_bot_add", True)),
        "is_active": bool(body.get("is_active", True))
    }
    
    result = db_client.update_guild_settings(guild_id, updates)
    return JSONResponse(content={"success": True, "data": result})

@app.get("/api/guild/whitelist")
async def get_whitelist(session: dict = Depends(verify_session)):
    guild_id = session["guild_id"]
    from src.bot.engine import bot
    guild = bot.get_guild(int(guild_id)) if bot else None
    
    whitelist_ids = db_client.get_guild_whitelist(guild_id)
    whitelist_details = []
    
    for uid in whitelist_ids:
        member = guild.get_member(int(uid)) if guild else None
        whitelist_details.append({
            "id": uid,
            "name": member.name if member else f"ID: {uid}",
            "avatar": str(member.display_avatar.url) if member else "/static/images/default_avatar.png"
        })
        
    return JSONResponse(content={"whitelist": whitelist_details})

@app.post("/api/guild/whitelist")
async def add_whitelist(request: Request, session: dict = Depends(verify_session)):
    guild_id = session["guild_id"]
    body = await request.json()
    user_id = str(body.get("user_id", "")).strip()
    
    if not user_id:
        return JSONResponse(status_code=400, content={"success": False, "error": "Invalid User ID"})
        
    # Check if member exists in Discord guild
    from src.bot.engine import bot
    guild = bot.get_guild(int(guild_id)) if bot else None
    member = None
    if guild:
        try:
            member = guild.get_member(int(user_id)) or await guild.fetch_member(int(user_id))
        except Exception:
            pass
            
    name_tag = str(member) if member else "Manual Add"
    
    success = db_client.add_to_whitelist(
        guild_id=guild_id, 
        user_id=user_id, 
        reason="Added via Web Dashboard", 
        executor_tag="Web Admin"
    )
    if success:
        return JSONResponse(content={"success": True, "user": {"id": user_id, "name": name_tag}})
    return JSONResponse(status_code=500, content={"success": False, "error": "Database error"})

@app.delete("/api/guild/whitelist/{user_id}")
async def remove_whitelist(user_id: str, session: dict = Depends(verify_session)):
    guild_id = session["guild_id"]
    success = db_client.remove_from_whitelist(guild_id, user_id)
    if success:
        return JSONResponse(content={"success": True})
    return JSONResponse(status_code=500, content={"success": False, "error": "Database error"})

@app.get("/api/guild/logs")
async def get_logs(session: dict = Depends(verify_session)):
    guild_id = session["guild_id"]
    logs = db_client.get_protection_logs(guild_id, limit=50)
    return JSONResponse(content={"logs": logs})

@app.post("/api/guild/counters")
async def update_counters_config(request: Request, session: dict = Depends(verify_session)):
    guild_id = session["guild_id"]
    body = await request.json()
    
    settings = {
        "style": body.get("style", "minimal"),
        "refresh_interval": body.get("refresh_interval", "7d"),
        "total_format": body.get("total_format", "members: {count}"),
        "online_format": body.get("online_format", "online: {online}"),
        "offline_format": body.get("offline_format", "offline: {offline}"),
        "invc_format": body.get("invc_format", "in vc: {invc}"),
        "category_id": body.get("category_id") or None,
        "total_channel_id": body.get("total_channel_id") or None,
        "online_channel_id": body.get("online_channel_id") or None,
        "offline_channel_id": body.get("offline_channel_id") or None,
        "invc_channel_id": body.get("invc_channel_id") or None,
        "tracked_vc_id": body.get("tracked_vc_id") or None
    }
    
    success = db_client.save_counter_settings(guild_id, settings)
    if success:
        from src.bot.engine import bot
        guild = bot.get_guild(int(guild_id))
        if guild:
            cog = bot.get_cog("Counters")
            if cog:
                await cog.update_guild_counters(guild)
        return JSONResponse(content={"success": True})
    return JSONResponse(status_code=500, content={"success": False, "error": "Database error"})

@app.post("/api/guild/counters/auto-generate")
async def auto_generate_counters(request: Request, session: dict = Depends(verify_session)):
    guild_id = session["guild_id"]
    body = await request.json()
    style = body.get("style", "minimal")
    
    from src.bot.engine import bot
    guild = bot.get_guild(int(guild_id))
    if not guild:
        return JSONResponse(status_code=400, content={"success": False, "error": "Bot not connected to this guild"})
        
    cog = bot.get_cog("Counters")
    if not cog:
        return JSONResponse(status_code=500, content={"success": False, "error": "Counters cog not loaded"})
        
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(connect=False, view_channel=True)
    }
    
    try:
        category = await guild.create_category(name="📊 KAIZER STATS")
        
        total_chan = await guild.create_voice_channel(name="members: counting...", category=category, overwrites=overwrites)
        online_chan = await guild.create_voice_channel(name="online: counting...", category=category, overwrites=overwrites)
        offline_chan = await guild.create_voice_channel(name="offline: counting...", category=category, overwrites=overwrites)
        invc_chan = await guild.create_voice_channel(name="in vc: counting...", category=category, overwrites=overwrites)
        
        settings = {
            "category_id": str(category.id),
            "total_channel_id": str(total_chan.id),
            "online_channel_id": str(online_chan.id),
            "offline_channel_id": str(offline_chan.id),
            "invc_channel_id": str(invc_chan.id),
            "style": style,
            "refresh_interval": body.get("refresh_interval", "7d"),
            "total_format": body.get("total_format", "members: {count}"),
            "online_format": body.get("online_format", "online: {online}"),
            "offline_format": body.get("offline_format", "offline: {offline}"),
            "invc_format": body.get("invc_format", "in vc: {invc}"),
            "tracked_vc_id": body.get("tracked_vc_id") or None
        }
        
        db_client.save_counter_settings(guild_id, settings)
        await cog.update_guild_counters(guild)
        
        return JSONResponse(content={
            "success": True,
            "category_id": str(category.id),
            "total_channel_id": str(total_chan.id),
            "online_channel_id": str(online_chan.id),
            "offline_channel_id": str(offline_chan.id),
            "invc_channel_id": str(invc_chan.id)
        })
    except Exception as e:
        logger.error(f"Failed to auto-generate counters: {e}")
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

@app.post("/api/guild/temp-vc")
async def update_temp_vc_config(request: Request, session: dict = Depends(verify_session)):
    guild_id = session["guild_id"]
    body = await request.json()
    
    settings = {
        "lobby_channel_id": body.get("lobby_channel_id") or None,
        "category_id": body.get("category_id") or None,
        "default_limit": int(body.get("default_limit", 0)),
        "default_name_format": body.get("default_name_format", "{user}'s VC"),
        "default_locked": bool(body.get("default_locked", False))
    }
    
    success = db_client.save_temp_vc_settings(guild_id, settings)
    if success:
        return JSONResponse(content={"success": True})
    return JSONResponse(status_code=500, content={"success": False, "error": "Database error"})

@app.post("/api/guild/decor/apply")
async def apply_decor_theme(request: Request, session: dict = Depends(verify_session)):
    guild_id = session["guild_id"]
    body = await request.json()
    theme_key = body.get("theme_key", "").lower().replace("-", "_")
    
    from src.bot.decoration import DECOR_THEMES
    if theme_key not in DECOR_THEMES:
        return JSONResponse(status_code=400, content={"success": False, "error": "Theme not found"})
        
    from src.bot.engine import bot
    guild = bot.get_guild(int(guild_id))
    if not guild:
        return JSONResponse(status_code=400, content={"success": False, "error": "Bot not connected to this guild"})
        
    try:
        backup = []
        for ch in guild.channels:
            backup.append({
                "id": str(ch.id),
                "name": ch.name,
                "type": "category" if isinstance(ch, discord.CategoryChannel) else ("text" if isinstance(ch, discord.TextChannel) else "voice")
            })
        db_client.save_decor_backup(guild_id, backup)
        
        theme = DECOR_THEMES[theme_key]
        success_count = 0
        error_count = 0
        
        for ch in guild.channels:
            original_clean_name = ch.name.split(" ", 1)[-1] if " " in ch.name else ch.name
            original_clean_name = original_clean_name.replace("✦", "").replace("୨", "").replace("୧", "").replace("✿", "").replace("⚡", "").strip()
            
            new_name = original_clean_name
            if isinstance(ch, discord.CategoryChannel):
                new_name = theme["cat_fmt"].format(name=original_clean_name.upper())
            elif isinstance(ch, discord.TextChannel):
                formatted_ch_name = original_clean_name.lower().replace(" ", "-")
                new_name = theme["text_fmt"].format(name=formatted_ch_name)
            elif isinstance(ch, discord.VoiceChannel):
                new_name = theme["voice_fmt"].format(name=original_clean_name)
                
            if ch.name != new_name:
                try:
                    await ch.edit(name=new_name)
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    logger.warning(f"Error renaming channel {ch.name}: {e}")
                    
        return JSONResponse(content={"success": True, "success_count": success_count, "error_count": error_count})
    except Exception as e:
        logger.error(f"Failed to apply decoration theme: {e}")
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

@app.post("/api/guild/decor/undo")
async def undo_decor_theme(session: dict = Depends(verify_session)):
    guild_id = session["guild_id"]
    
    from src.bot.engine import bot
    guild = bot.get_guild(int(guild_id))
    if not guild:
        return JSONResponse(status_code=400, content={"success": False, "error": "Bot not connected to this guild"})
        
    try:
        backup_channels = db_client.pop_decor_backup(guild_id)
        if not backup_channels:
            return JSONResponse(status_code=400, content={"success": False, "error": "No backup found for this server."})
            
        success_count = 0
        for info in backup_channels:
            cid = int(info["id"])
            cname = info["name"]
            channel = guild.get_channel(cid)
            if channel:
                try:
                    if channel.name != cname:
                        await channel.edit(name=cname)
                        success_count += 1
                except Exception:
                    pass
                    
        return JSONResponse(content={"success": True, "restored_count": success_count})
    except Exception as e:
        logger.error(f"Failed to undo theme: {e}")
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

@app.post("/api/guild/build/server")
async def build_server_template(request: Request, session: dict = Depends(verify_session)):
    guild_id = session["guild_id"]
    body = await request.json()
    template = body.get("template", "").lower()
    wipe = bool(body.get("wipe", False))
    
    from src.bot.engine import bot
    guild = bot.get_guild(int(guild_id))
    if not guild:
        return JSONResponse(status_code=400, content={"success": False, "error": "Bot not connected to this guild"})
        
    if wipe:
        for ch in guild.channels:
            try:
                await ch.delete()
            except Exception:
                pass
                
    layouts = {
        "gaming": [
            ("INFORMATION", [
                ("welcome", "text", "Welcome to the server! Read the rules and enjoy."),
                ("rules", "text", "Official server rules and regulations."),
                ("announcements", "text", "Stay updated with the latest server news.")
            ]),
            ("TEXT CHANNELS", [
                ("general", "text", "General chat and discussion."),
                ("gaming-chat", "text", "Talk about your favorite games!"),
                ("clips", "text", "Share your gaming clips and highlights."),
                ("bot-commands", "text", "Interact with bot systems here.")
            ]),
            ("VOICE CHANNELS", [
                ("Lounge", "voice", None),
                ("Squad 1", "voice", None),
                ("Squad 2", "voice", None),
                ("Gaming VC", "voice", None)
            ])
        ],
        "community": [
            ("WELCOME", [
                ("rules", "text", "Server guidelines."),
                ("announcements", "text", "Community news."),
                ("introduce-yourself", "text", "Tell the community about yourself!")
            ]),
            ("CHATS", [
                ("general", "text", "Main chat corridor."),
                ("memes", "text", "Share your funny images and jokes."),
                ("bot-commands", "text", "Bot play area.")
            ]),
            ("MEDIA & FUN", [
                ("art-and-media", "text", "Share drawings, videos and photos."),
                ("hobbies", "text", "Discuss sports, travel, cooking etc."),
                ("music-sharing", "text", "Share what you are listening to!")
            ]),
            ("VC AREA", [
                ("General Lounge", "voice", None),
                ("Gaming VC", "voice", None),
                ("Music Room", "voice", None)
            ])
        ],
        "study": [
            ("INFO", [
                ("announcements", "text", "Important updates."),
                ("resources", "text", "School, notes and study guide materials."),
                ("questions", "text", "Ask the group for help.")
            ]),
            ("STUDY ROOMS", [
                ("general-study", "text", "Discuss study plans."),
                ("math-science", "text", "Math and science discussion."),
                ("humanities", "text", "History, language, literature chat."),
                ("coding", "text", "Programming and tech talk.")
            ]),
            ("VOICE DECK", [
                ("Silent Study 1", "voice", None),
                ("Group Study 2", "voice", None),
                ("Lofi Radio", "voice", None)
            ])
        ],
        "business": [
            ("WELCOME", [
                ("announcements", "text", "Company and team bulletins."),
                ("company-updates", "text", "Corporate logs."),
                ("onboarding", "text", "Helpful hints for new hires.")
            ]),
            ("OFFICE DECK", [
                ("general-discussion", "text", "Water cooler talks."),
                ("marketing", "text", "Marketing team channel."),
                ("sales", "text", "Sales tracking and sync."),
                ("development", "text", "Engineering tasks.")
            ]),
            ("MEETING ROOMS", [
                ("Boardroom", "voice", None),
                ("Standup 1", "voice", None),
                ("Huddle 2", "voice", None)
            ])
        ]
    }
    
    if template not in layouts:
        return JSONResponse(status_code=400, content={"success": False, "error": "Invalid template name"})
        
    layout = layouts[template]
    created_count = 0
    
    try:
        for cat_name, channels in layout:
            category = await guild.create_category(name=cat_name)
            for ch_name, ch_type, topic in channels:
                if ch_type == "text":
                    await guild.create_text_channel(name=ch_name, category=category, topic=topic)
                elif ch_type == "voice":
                    await guild.create_voice_channel(name=ch_name, category=category)
                created_count += 1
                
        return JSONResponse(content={"success": True, "created_count": created_count})
    except Exception as e:
        logger.error(f"Failed to generate layout: {e}")
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})


@app.get("/api/status")
async def get_status():
    from src.bot.engine import bot
    ready = bot.is_ready() if bot else False
    return JSONResponse(content={
        "status": "online" if ready else "offline",
        "latency": f"{round(bot.latency * 1000)}ms" if ready else "N/A",
        "guilds": len(bot.guilds) if ready else 0,
        "users": len(bot.users) if ready else 0
    })

# --- HEALTH CHECK FOR RENDER ---
@app.get("/health")
async def health_check():
    from src.bot.engine import bot
    bot_ready = bot.is_ready() if bot else False
    return JSONResponse(content={"web": "healthy", "bot": "online" if bot_ready else "connecting"})
