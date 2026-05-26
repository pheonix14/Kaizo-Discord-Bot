import os
import re
import time
import random
import queue
import threading
import requests
import json
from datetime import datetime, timezone
from logger import _sb, SUPABASE_URL, SUPABASE_KEY, log_event

# ── Dynamic DB Bootstrap ──────────────────────────────────────────────────────
def bootstrap_db():
    sql_file = "supabase_schema_additions.sql"
    if not os.path.exists(sql_file):
        print(f"[Scanner Boot] SQL file {sql_file} not found. Skipping bootstrap.")
        return

    try:
        with open(sql_file, "r", encoding="utf-8") as f:
            stmt = f.read()
        
        print("[Scanner Boot] Bootstrapping scanner tables in Supabase...", flush=True)
        r = requests.post(
            f"{SUPABASE_URL}/rest/v1/rpc/exec_sql",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            },
            json={"sql": stmt},
            timeout=15
        )
        if r.status_code in (200, 201, 204):
            print("[Scanner Boot] Bootstrap successful! Scanner tables ready.", flush=True)
        else:
            print(f"[Scanner Boot] Bootstrap response code: {r.status_code}. Response: {r.text}", flush=True)
    except Exception as e:
        print(f"[Scanner Boot] Failed to bootstrap database: {e}", flush=True)

bootstrap_db()

# ── Global Scanner State ──────────────────────────────────────────────────────
ACTIVE_SCANS = {}  # (token_id, guild_id) -> { "guild_name": str, "members_scanned": int, "total_members": int, "status": str, "log": list, "started_at": str }
_scans_lock = threading.Lock()

# Profile request queue to fetch bio/profile rate-limited in background
profile_queue = queue.Queue()
_profile_workers = []

# ── Configuration Manager ─────────────────────────────────────────────────────
def get_scan_config() -> dict:
    try:
        res = _sb.table("scan_config").select("*").eq("id", 1).single().execute()
        if res.data:
            return res.data
    except Exception as e:
        pass
    
    # Defaults
    default_config = {
        "id": 1,
        "auto_scan": False,
        "selected_tokens": [],
        "priority_guilds": [],
        "last_auto_scan": None
    }
    try:
        _sb.table("scan_config").upsert(default_config).execute()
    except Exception as e:
        print(f"[Scanner Config] Upsert error: {e}")
    return default_config

def save_scan_config(cfg: dict):
    try:
        cfg["id"] = 1
        _sb.table("scan_config").upsert(cfg, on_conflict="id").execute()
    except Exception as e:
        print(f"[Scanner Config] Save error: {e}")

def fetch_user_bio_now(user_id: str) -> str:
    import engine
    nodes = list(engine._nodes.values())
    active_nodes = [n for n in nodes if not n._captcha_detected and getattr(n, "bot", None)]
    if not active_nodes:
        raise Exception("No active scanner tokens available.")
    
    node = random.choice(active_nodes)
    url = f"https://discord.com/api/v9/users/{user_id}/profile"
    headers = {"Authorization": node.token}
    resp = requests.get(url, headers=headers, timeout=10)
    
    if resp.status_code == 200:
        pdata = resp.json()
        bio = pdata.get("user_profile", {}).get("bio", "") or pdata.get("user", {}).get("bio", "") or ""
        
        try:
            user_res = _sb.table("scanned_users").select("username,avatar,bio,past_bios").eq("id", user_id).execute()
            if user_res.data:
                existing = user_res.data[0]
                past_bios = existing.get("past_bios") or []
                old_bio = existing.get("bio", "")
                
                if old_bio and old_bio != bio:
                    if old_bio not in past_bios:
                        past_bios.append(old_bio)
                
                _sb.table("scanned_users").update({
                    "bio": bio,
                    "past_bios": past_bios,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }).eq("id", user_id).execute()
        except Exception as dberr:
            print(f"[Scanner Bio Now] Database update error: {dberr}", flush=True)
            
        return bio
    elif resp.status_code == 429:
        raise Exception("Rate limited by Discord. Try again in a few seconds.")
    else:
        raise Exception(f"Discord API returned status code {resp.status_code}")

# ── Background Profile Bio Fetcher ────────────────────────────────────────────
def start_profile_fetcher():
    global _profile_workers
    if _profile_workers:
        return
    
    def worker():
        print("[Scanner Bio Worker] Started.", flush=True)
        while True:
            try:
                user_id = profile_queue.get()
                if not user_id:
                    time.sleep(2)
                    continue
                
                # Check if we already have the bio to avoid unnecessary requests
                try:
                    res = _sb.table("scanned_users").select("bio").eq("id", user_id).single().execute()
                    if res.data and res.data.get("bio"):
                        profile_queue.task_done()
                        continue
                except:
                    pass
                
                # Find an active node to make the request
                import engine
                nodes = list(engine._nodes.values())
                active_nodes = [n for n in nodes if not n._captcha_detected and getattr(n, "bot", None)]
                
                if not active_nodes:
                    # Put it back and sleep
                    profile_queue.put(user_id)
                    time.sleep(15)
                    profile_queue.task_done()
                    continue
                
                # Rotate tokens to avoid getting flagged
                node = random.choice(active_nodes)
                
                # Fetch full user profile
                url = f"https://discord.com/api/v9/users/{user_id}/profile"
                headers = {"Authorization": node.token}
                resp = requests.get(url, headers=headers, timeout=10)
                
                if resp.status_code == 200:
                    pdata = resp.json()
                    bio = pdata.get("user_profile", {}).get("bio", "") or pdata.get("user", {}).get("bio", "")
                    
                    if bio:
                        # Fetch current record for history tracking
                        user_res = _sb.table("scanned_users").select("username,avatar,bio,past_bios").eq("id", user_id).execute()
                        if user_res.data:
                            existing = user_res.data[0]
                            past_bios = existing.get("past_bios") or []
                            old_bio = existing.get("bio", "")
                            
                            if old_bio and old_bio != bio:
                                if old_bio not in past_bios:
                                    past_bios.append(old_bio)
                            
                            _sb.table("scanned_users").update({
                                "bio": bio,
                                "past_bios": past_bios,
                                "updated_at": datetime.now(timezone.utc).isoformat()
                            }).eq("id", user_id).execute()
                            
                            print(f"[Scanner Bio Worker] Bio synced for user {user_id}", flush=True)
                elif resp.status_code == 429:
                    retry_after = resp.json().get("retry_after", 30)
                    print(f"[Scanner Bio Worker] 429 Ratelimited. Waiting {retry_after}s...", flush=True)
                    time.sleep(retry_after)
                    profile_queue.put(user_id)
                else:
                    # Non-critical, ignore or log
                    pass
                
                profile_queue.task_done()
                # Safe delay between profile calls
                time.sleep(random.uniform(15.0, 30.0))
            except Exception as e:
                print(f"[Scanner Bio Worker] Loop error: {e}", flush=True)
                time.sleep(10)
                try: profile_queue.task_done()
                except: pass

    t = threading.Thread(target=worker, daemon=True, name="BioScraper")
    t.start()
    _profile_workers.append(t)

# ── Dynamic Webhook / Event Callback for discum ──────────────────────────────
def register_scanner_hooks(node):
    """Registers scanner gateway callbacks on a BotNode's gateway client."""
    if getattr(node, "_scanner_hooks_registered", False):
        return
    node._scanner_hooks_registered = True
    bot = node.bot

    # ── fetchMembers uses op14 (LAZY_REQUEST) which fires GUILD_MEMBER_LIST_UPDATE.
    # GUILD_MEMBERS_CHUNK (op8) is for queryGuildMembers / searchGuildMembers only.
    # Hook guild_member_list and read members accumulated in discum's session cache.
    @bot.gateway.command
    def on_guild_member_list(resp):
        if not resp.event.guild_member_list:
            return
        try:
            d = resp.raw.get('d', {})
            guild_id = d.get("guild_id")
            if not guild_id:
                return
            task_key = (node.id, guild_id)
            with _scans_lock:
                task = ACTIVE_SCANS.get(task_key)
            if not task:
                return
            # discum stores fetched members in session after processing each op14
            try:
                session_members = dict(bot.gateway.session.guild(guild_id).members)
            except (KeyError, AttributeError):
                session_members = {}

            count    = len(session_members)
            total    = task.get("total_members", 100)
            finished = bot.gateway.finishedMemberFetching(guild_id)

            with _scans_lock:
                t = ACTIVE_SCANS.get(task_key)
                if t:
                    t["members_scanned"] = count
                    t["status"] = "processing" if not finished else "done"

            if session_members:
                threading.Thread(
                    target=flush_session_members_to_db,
                    args=(node.id, guild_id, session_members, finished, total),
                    daemon=True
                ).start()
        except Exception as ex:
            print(f"[Scanner Hook] guild_member_list hook error: {ex}", flush=True)

    # GUILD_MEMBERS_CHUNK listener (op8 fallback — used by queryGuildMembers)
    @bot.gateway.command
    def on_guild_members_chunk(resp):
        if not resp.event.guild_members_chunk:
            return
        try:
            d = resp.raw.get('d', {})
            guild_id   = d.get("guild_id")
            members    = d.get("members", [])
            presences  = d.get("presences", [])
            chunk_index = d.get("chunk_index", 0)
            chunk_count = d.get("chunk_count", 1)
            task_key = (node.id, guild_id)
            with _scans_lock:
                task = ACTIVE_SCANS.get(task_key)
            if not task:
                return
            threading.Thread(
                target=process_member_chunk,
                args=(node.id, guild_id, members, presences, chunk_index, chunk_count),
                daemon=True
            ).start()
        except Exception as ex:
            print(f"[Scanner Hook] Chunk hook error: {ex}", flush=True)

    # GUILD_CREATE — auto-scan new servers if auto_scan enabled
    @bot.gateway.command
    def on_guild_create(resp):
        if not resp.event.guild:
            return
        try:
            cfg = get_scan_config()
            if not cfg.get("auto_scan", False):
                return
            selected_tokens = cfg.get("selected_tokens", [])
            if selected_tokens and node.id not in selected_tokens:
                return
            d = resp.raw.get('d', {})
            guild_id   = d.get("id")
            guild_name = d.get("name", "Unknown Server")
            print(f"[Scanner Hook] Joined {guild_name} ({guild_id}). Auto-scanning in 30s...", flush=True)
            def delayed_scan():
                time.sleep(random.uniform(25, 45))
                trigger_guild_scan(node.id, guild_id, guild_name)
            threading.Thread(target=delayed_scan, daemon=True).start()
        except Exception as ex:
            print(f"[Scanner Hook] Guild create hook error: {ex}", flush=True)

# ── Flush discum session members to Supabase ──────────────────────────────────
# discum's fetchMembers (op14) stores members in session.guild(guild_id).members as:
# { user_id: { username, avatar, discriminator, nick, roles, joined_at, ... } }
def flush_session_members_to_db(token_id, guild_id, session_members: dict, finished: bool, total_members: int):
    task_key = (token_id, guild_id)
    with _scans_lock:
        task = ACTIVE_SCANS.get(task_key)
        if not task:
            return

    import engine
    node  = engine.get_node(token_id)
    label = node.label if node else "Unknown"

    user_ids = list(session_members.keys())
    if not user_ids:
        return

    try:
        existing_users   = {}
        existing_members = {}
        batch_size       = 400

        for i in range(0, len(user_ids), batch_size):
            res = _sb.table("scanned_users").select("id,username,bio,past_usernames,past_bios").in_("id", user_ids[i:i+batch_size]).execute()
            if res.data:
                for u in res.data:
                    existing_users[u["id"]] = u

        composite_ids = [f"{guild_id}:{uid}" for uid in user_ids]
        for i in range(0, len(composite_ids), batch_size):
            res = _sb.table("scanned_members").select("id,nickname,past_nicknames").in_("id", composite_ids[i:i+batch_size]).execute()
            if res.data:
                for m in res.data:
                    existing_members[m["id"]] = m

        users_to_upsert   = []
        members_to_upsert = []

        for uid, mdata in session_members.items():
            if not uid:
                continue
            username    = mdata.get("username", "Unknown")
            avatar_hash = mdata.get("avatar")
            avatar_url  = f"https://cdn.discordapp.com/avatars/{uid}/{avatar_hash}.png" if avatar_hash else "https://cdn.discordapp.com/embed/avatars/0.png"
            is_bot      = mdata.get("bot", False)
            nickname    = mdata.get("nick")
            joined_at   = mdata.get("joined_at")
            roles       = mdata.get("roles") or []
            presence    = mdata.get("presence", {}) or {}
            status      = presence.get("status", "offline")
            custom_status = ""
            for act in (presence.get("activities") or []):
                if act.get("type") == 4:
                    custom_status = act.get("state", "")
                    break

            user_past_names = []
            user_past_bios  = []
            current_bio     = ""
            if uid in existing_users:
                ex = existing_users[uid]
                user_past_names = ex.get("past_usernames") or []
                user_past_bios  = ex.get("past_bios") or []
                current_bio     = ex.get("bio") or ""
                old_name = ex.get("username")
                if old_name and old_name != username and old_name not in user_past_names:
                    user_past_names.append(old_name)

            users_to_upsert.append({
                "id": uid, "username": username, "avatar": avatar_url,
                "bio": current_bio, "custom_status": custom_status,
                "status": status, "bot": is_bot,
                "past_usernames": user_past_names, "past_bios": user_past_bios,
                "updated_at": datetime.now(timezone.utc).isoformat()
            })

            if not current_bio and not is_bot and status != "offline":
                profile_queue.put(uid)

            composite_id      = f"{guild_id}:{uid}"
            member_past_nicks = []
            if composite_id in existing_members:
                ex_mem = existing_members[composite_id]
                member_past_nicks = ex_mem.get("past_nicknames") or []
                old_nick = ex_mem.get("nickname")
                if old_nick and nickname and old_nick != nickname and old_nick not in member_past_nicks:
                    member_past_nicks.append(old_nick)

            members_to_upsert.append({
                "id": composite_id, "user_id": uid, "guild_id": guild_id,
                "nickname": nickname, "joined_at": joined_at, "roles": roles,
                "past_nicknames": member_past_nicks,
                "last_seen": datetime.now(timezone.utc).isoformat()
            })

        if users_to_upsert:
            _sb.table("scanned_users").upsert(users_to_upsert, on_conflict="id").execute()
        if members_to_upsert:
            _sb.table("scanned_members").upsert(members_to_upsert, on_conflict="id").execute()
        print(f"[Scanner DB] [{label}] Wrote {len(users_to_upsert)} members for guild {guild_id}", flush=True)

    except Exception as dberr:
        log_event(f"[Scanner DB Write Error] [{label}] {dberr}", "error")

    if finished:
        with _scans_lock:
            task = ACTIVE_SCANS.get(task_key)
            if task:
                task["status"] = "done"
                task["members_scanned"] = total_members
                log_scanner_event(task, f"Scan complete. {len(user_ids)} members written to DB.", "success")
        try:
            _sb.table("scanned_guilds").update({"last_scanned": datetime.now(timezone.utc).isoformat()}).eq("id", guild_id).execute()
        except: pass
    else:
        with _scans_lock:
            task = ACTIVE_SCANS.get(task_key)
            if task:
                progress = min(99, int((len(user_ids) / max(1, total_members)) * 100))
                log_scanner_event(task, f"Fetching... {len(user_ids)}/{total_members} ({progress}%)")

# ── Member Chunk Processing (op8 / queryGuildMembers fallback) ─────────────────
def process_member_chunk(token_id, guild_id, members, presences, chunk_index, chunk_count):
    task_key = (token_id, guild_id)
    with _scans_lock:
        task = ACTIVE_SCANS.get(task_key)
        if not task:
            return
        task["status"] = "processing"
    
    import engine
    node = engine.get_node(token_id)
    label = node.label if node else "Unknown"
    log_event(f"[SCANNER] [{label}] Processing member chunk {chunk_index+1}/{chunk_count} for guild {guild_id}. Parsed {len(members)} members.", "info")
    
    # Match presences by user_id for faster lookup
    presence_map = {}
    for p in presences:
        uid = p.get("user", {}).get("id")
        if uid:
            presence_map[uid] = p

    user_ids = [m.get("user", {}).get("id") for m in members if m.get("user", {}).get("id")]
    if not user_ids:
        return
    
    # ── Database updates ──
    try:
        # 1. Bulk check existing users in Supabase to calculate historical diffs
        existing_users = {}
        batch_size = 400
        for i in range(0, len(user_ids), batch_size):
            slice_ids = user_ids[i:i+batch_size]
            res = _sb.table("scanned_users").select("id,username,bio,past_usernames,past_bios").in_("id", slice_ids).execute()
            if res.data:
                for u in res.data:
                    existing_users[u["id"]] = u

        # 2. Bulk check existing members in Supabase for nickname history
        existing_members = {}
        member_composite_ids = [f"{guild_id}:{uid}" for uid in user_ids]
        for i in range(0, len(member_composite_ids), batch_size):
            slice_mids = member_composite_ids[i:i+batch_size]
            res = _sb.table("scanned_members").select("id,nickname,past_nicknames").in_("id", slice_mids).execute()
            if res.data:
                for m in res.data:
                    existing_members[m["id"]] = m

        users_to_upsert = []
        members_to_upsert = []

        for m in members:
            u = m.get("user", {})
            uid = u.get("id")
            if not uid:
                continue

            username = u.get("username", "Unknown")
            avatar_hash = u.get("avatar")
            avatar_url = f"https://cdn.discordapp.com/avatars/{uid}/{avatar_hash}.png" if avatar_hash else "https://cdn.discordapp.com/embed/avatars/0.png"
            is_bot = u.get("bot", False)
            
            # Presence mapping
            pres = presence_map.get(uid, {})
            status = pres.get("status", "offline")
            
            # Custom status extract
            custom_status = ""
            activities = pres.get("activities", []) or []
            for act in activities:
                if act.get("type") == 4:  # Custom Status Type
                    custom_status = act.get("state", "")
                    break

            # ── Process User Record ──
            user_past_names = []
            user_past_bios = []
            current_bio = ""
            
            if uid in existing_users:
                ex = existing_users[uid]
                user_past_names = ex.get("past_usernames") or []
                user_past_bios = ex.get("past_bios") or []
                current_bio = ex.get("bio") or ""
                
                # Check for username changes
                old_name = ex.get("username")
                if old_name and old_name != username:
                    if old_name not in user_past_names:
                        user_past_names.append(old_name)
            
            users_to_upsert.append({
                "id": uid,
                "username": username,
                "avatar": avatar_url,
                "bio": current_bio,  # Retain existing bio (fetched via background worker)
                "custom_status": custom_status,
                "status": status,
                "bot": is_bot,
                "past_usernames": user_past_names,
                "past_bios": user_past_bios,
                "updated_at": datetime.now(timezone.utc).isoformat()
            })

            # Queue user for full REST bio fetching if they have none yet and are active/online
            if not current_bio and not is_bot and status != 'offline':
                profile_queue.put(uid)

            # ── Process Member Record ──
            composite_id = f"{guild_id}:{uid}"
            nickname = m.get("nick")
            joined_at = m.get("joined_at")
            roles = m.get("roles", []) or []
            member_past_nicks = []

            if composite_id in existing_members:
                ex_mem = existing_members[composite_id]
                member_past_nicks = ex_mem.get("past_nicknames") or []
                old_nick = ex_mem.get("nickname")
                
                if old_nick and nickname and old_nick != nickname:
                    if old_nick not in member_past_nicks:
                        member_past_nicks.append(old_nick)

            members_to_upsert.append({
                "id": composite_id,
                "user_id": uid,
                "guild_id": guild_id,
                "nickname": nickname,
                "joined_at": joined_at,
                "roles": roles,
                "past_nicknames": member_past_nicks,
                "last_seen": datetime.now(timezone.utc).isoformat()
            })

        # Bulk upsert to Supabase
        import time
        db_start = time.time()
        if users_to_upsert:
            _sb.table("scanned_users").upsert(users_to_upsert, on_conflict="id").execute()
        if members_to_upsert:
            _sb.table("scanned_members").upsert(members_to_upsert, on_conflict="id").execute()
        db_duration = time.time() - db_start
        log_event(f"[Scanner DB Write] [{label}] Wrote {len(users_to_upsert)} users and {len(members_to_upsert)} memberships to Supabase in {db_duration:.3f}s.", "success")

    except Exception as dberr:
        log_event(f"[Scanner DB Write Error] [{label}] Failed to write chunk to Supabase: {dberr}", "error")

    # Update progress in memory
    with _scans_lock:
        task = ACTIVE_SCANS.get(task_key)
        if task:
            task["members_scanned"] += len(members)
            
            # Discord chunks sometimes arrive slightly out of order or count varies,
            # we check index and finished status of Discum combo
            import engine
            n = engine.get_node(token_id)
            finished = False
            if n:
                finished = n.bot.gateway.finishedMemberFetching(guild_id)
            
            if chunk_index == chunk_count - 1 or finished:
                task["status"] = "done"
                task["members_scanned"] = task["total_members"]
                log_scanner_event(task, f"Scan completed successfully. Scraped {task['members_scanned']} members.", "success")
                
                # Update last scan date for the guild
                try:
                    _sb.table("scanned_guilds").update({
                        "last_scanned": datetime.now(timezone.utc).isoformat()
                    }).eq("id", guild_id).execute()
                except: pass
            else:
                progress = min(99, int((task["members_scanned"] / max(1, task["total_members"])) * 100))
                log_scanner_event(task, f"Received chunk {chunk_index+1}/{chunk_count} ({progress}%). Scanned {task['members_scanned']} members.")

def log_scanner_event(task, msg, typ="info"):
    ts = datetime.now().strftime("%H:%M:%S")
    task["log"].insert(0, f"[{ts}] {msg}")
    if len(task["log"]) > 100:
        task["log"].pop()
    log_event(f"[SCANNER] {msg}", typ)

# ── Trigger Guild Scanning ────────────────────────────────────────────────────
def trigger_guild_scan(token_id, guild_id, guild_name=None) -> bool:
    import engine
    node = engine.get_node(token_id)
    if not node:
        log_event(f"Scan Trigger: Node for token {token_id[:8]}... not active.", "error")
        return False

    # Bind current thread to this node's session for thread-local settings lookup
    import _thread
    from discum.gateway.session import _thread_to_session, _thread_to_session_lock
    ident = _thread.get_ident()
    with _thread_to_session_lock:
        _thread_to_session[ident] = node.bot.gateway.session

    # Get guild info if not provided
    if not guild_name:
        guilds = node.get_guilds_and_channels()
        guild_info = next((g for g in guilds if g["id"] == guild_id), None)
        guild_name = guild_info["name"] if guild_info else "Unknown Server"

    # Make sure scanner hooks are registered
    register_scanner_hooks(node)

    # 1. Fetch guild member count and metadata to update scanned_guilds
    total_members = 100
    icon_url = ""
    try:
        g_obj = node.bot.gateway.session.guild(guild_id)
        if g_obj:
            # Guard: settings_ready may not have 'guilds' yet — use getattr safely
            try:
                mc = g_obj.memberCount
                total_members = mc if mc else 100
            except (KeyError, AttributeError):
                total_members = 100
            icon_hash = getattr(g_obj, 'icon', None)
            if icon_hash:
                icon_url = f"https://cdn.discordapp.com/icons/{guild_id}/{icon_hash}.png"
            else:
                icon_url = "https://cdn.discordapp.com/embed/avatars/0.png"
    except Exception:
        pass

    # 2. Try to fetch/generate invite link for the server
    invite_link = "No Invite Link"
    try:
        # Check vanity URL
        g_obj = node.bot.gateway.session.guild(guild_id)
        if g_obj and getattr(g_obj, "vanityUrlCode", None):
            invite_link = f"https://discord.gg/{g_obj.vanityUrlCode}"
        else:
            # Query invites via REST
            inv_resp = node.bot.getGuildInvites(guild_id)
            if inv_resp.status_code == 200:
                invites = inv_resp.json()
                if invites:
                    invite_link = f"https://discord.gg/{invites[0].get('code')}"
    except:
        pass

    # Update scanned_guilds table
    try:
        _sb.table("scanned_guilds").upsert({
            "id": guild_id,
            "name": guild_name,
            "icon": icon_url,
            "invite_link": invite_link,
            "last_scanned": datetime.now(timezone.utc).isoformat()
        }, on_conflict="id").execute()
    except Exception as ex:
        print(f"[Scanner DB] Error updating guild metadata: {ex}", flush=True)

    # 3. Choose a suitable text channel in the guild to view member list
    channels = []
    try:
        ch_resp = node.bot.s.get(f"https://discord.com/api/v9/guilds/{guild_id}/channels")
        if ch_resp.status_code == 200:
            channels = [c for c in ch_resp.json() if c.get("type") == 0]
    except:
        pass

    if not channels:
        # Fallback to general/default scan using whatever channel we can get
        print(f"[Scanner] Warning: Could not resolve channels for {guild_name}. Fetching members may fail.", flush=True)
        channel_id = "0"
    else:
        channel_id = channels[0]["id"]

    # 4. Initialize task state in ACTIVE_SCANS
    task_key = (token_id, guild_id)
    with _scans_lock:
        ACTIVE_SCANS[task_key] = {
            "guild_name": guild_name,
            "members_scanned": 0,
            "total_members": total_members,
            "status": "scanning",
            "log": [],
            "started_at": datetime.now().strftime("%H:%M:%S")
        }
        task = ACTIVE_SCANS[task_key]

    log_scanner_event(task, f"Initializing scan for server: {guild_name} ({total_members} members)...")

    # Start profile bio workers
    start_profile_fetcher()

    # 5. Fire Discum fetchMembers
    # Guard: wait for gateway session to have settings_ready populated.
    # The KeyError: 'guilds' crash happens when fetchMembers fires before
    # the READY event has fully processed the guild list into settings_ready.
    def _is_session_ready():
        try:
            sr = node.bot.gateway.session.settings_ready
            return isinstance(sr, dict) and 'guilds' in sr
        except:
            return False

    # Wait up to 15 seconds for the session to be ready
    wait_start = time.time()
    while not _is_session_ready() and (time.time() - wait_start) < 15:
        time.sleep(0.5)

    if not _is_session_ready():
        with _scans_lock:
            if task_key in ACTIVE_SCANS:
                ACTIVE_SCANS[task_key]["status"] = "failed"
        log_scanner_event(task, "Gateway session not ready (settings_ready missing 'guilds'). Aborting scan.", "error")
        return False

    try:
        node.bot.gateway.fetchMembers(
            guild_id=guild_id,
            channel_id=channel_id,
            keep="all",
            reset=True,
            wait=random.uniform(1.2, 2.5)
        )
        return True
    except Exception as ex:
        with _scans_lock:
            if task_key in ACTIVE_SCANS:
                ACTIVE_SCANS[task_key]["status"] = "failed"
        log_scanner_event(task, f"Failed to initiate fetchMembers: {ex}", "error")
        return False

# ── Auto Scan Daemon Loop ─────────────────────────────────────────────────────
def auto_scan_loop():
    print("[Scanner Auto-Daemon] Started.", flush=True)
    # Sleep 30s at startup to allow nodes to connect
    time.sleep(30)
    
    while True:
        try:
            cfg = get_scan_config()
            if not cfg.get("auto_scan", False):
                time.sleep(60)
                continue

            selected_tokens = cfg.get("selected_tokens", [])
            priority_guilds = cfg.get("priority_guilds", [])
            
            if not selected_tokens:
                time.sleep(60)
                continue

            import engine
            nodes = [engine.get_node(tid) for tid in selected_tokens if engine.get_node(tid)]
            active_nodes = [n for n in nodes if not n._captcha_detected and getattr(n, "bot", None)]

            if not active_nodes:
                time.sleep(60)
                continue

            # Assemble list of all accessible guilds across active tokens
            all_accessible_guilds = []
            for n in active_nodes:
                guilds = n.get_guilds_and_channels()
                for g in guilds:
                    # check if already in the list
                    if not any(x["id"] == g["id"] for x in all_accessible_guilds):
                        all_accessible_guilds.append({
                            "id": g["id"],
                            "name": g["name"],
                            "token_id": n.id
                        })

            if not all_accessible_guilds:
                time.sleep(60)
                continue

            # Prioritize guilds
            # Sort: Priority first, then oldest/never scanned
            # Fetch last scanned times from DB
            guild_scans = {}
            try:
                res = _sb.table("scanned_guilds").select("id,last_scanned").execute()
                if res.data:
                    for g in res.data:
                        guild_scans[g["id"]] = g["last_scanned"]
            except:
                pass

            def sort_key(g):
                is_prio = g["id"] in priority_guilds
                last_time_str = guild_scans.get(g["id"])
                if not last_time_str:
                    last_time = 0
                else:
                    try:
                        last_time = datetime.fromisoformat(last_time_str.replace("Z", "+00:00")).timestamp()
                    except:
                        last_time = 0
                # Higher priority first, then oldest last_scanned first
                return (not is_prio, last_time)

            all_accessible_guilds.sort(key=sort_key)
            target = all_accessible_guilds[0]

            # Check if recently scanned (< 4 hours) to avoid hammering
            last_scanned_str = guild_scans.get(target["id"])
            if last_scanned_str:
                try:
                    last_time = datetime.fromisoformat(last_scanned_str.replace("Z", "+00:00"))
                    age = (datetime.now(timezone.utc) - last_time).total_seconds() / 3600
                    if age < 4.0:
                        # Everything scanned recently, sleep and check later
                        time.sleep(300)
                        continue
                except:
                    pass

            print(f"[Scanner Auto-Daemon] Selecting {target['name']} ({target['id']}) for background scan...", flush=True)
            trigger_guild_scan(target["token_id"], target["id"], target["name"])

            # Update auto-scan config
            cfg["last_auto_scan"] = datetime.now(timezone.utc).isoformat()
            save_scan_config(cfg)

            # Sleep between scans (random 20 to 45 minutes) to ensure natural behavior
            sleep_sec = random.randint(1200, 2700)
            print(f"[Scanner Auto-Daemon] Sleeping {sleep_sec}s before next auto-scan.", flush=True)
            time.sleep(sleep_sec)

        except Exception as e:
            print(f"[Scanner Auto-Daemon] Error: {e}", flush=True)
            time.sleep(180)

# Start background auto-scanner daemon
threading.Thread(target=auto_scan_loop, daemon=True, name="ScannerDaemon").start()
