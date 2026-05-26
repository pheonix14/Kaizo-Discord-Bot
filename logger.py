"""
logger.py — Supabase-native storage layer for Fafnir.
Replaces all local JSON files with direct PostgreSQL operations via supabase-py.
Tables: tokens, dex, history, bot_config, bot_state, logs
"""
import sys, threading, time, uuid
from datetime import datetime

# ── UTF-8 output fix ──────────────────────────────────────────────────────────
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── Supabase client ───────────────────────────────────────────────────────────
from supabase import create_client, Client

SUPABASE_URL = "https://cwputkmuqgpxydfxsrnm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN3cHV0a211cWdweHlkZnhzcm5tIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTAzODc3OCwiZXhwIjoyMDk0NjE0Nzc4fQ.e4raXAvgNzKoJWr6FNIDydOuH3EYxWEIQGoOOKQtZKY"

_sb: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── In-memory caches for lightning-speed reads ────────────────────────────────
_lock         = threading.Lock()
_config_cache = None   # bot_config row (dict)
_tokens_cache = None   # list of token dicts
_dex_cache    = None   # dict keyed by pokemon name
_hist_cache   = None   # list of history entries (last 500)
_logs_cache   = []     # in-process rotating log list (not persisted to Supabase)

# ── Console colours ───────────────────────────────────────────────────────────
V="\\033[95m"; C="\\033[96m"; G="\\033[92m"; Y="\\033[93m"; R="\\033[91m"; X="\\033[0m"; B="\\033[1m"
TYPE_COLOR = {"info":C,"success":G,"warning":Y,"error":R,"catch":V+B,"spawn":V,"history":""}

# ─────────────────────────────────────────────────────────────────────────────
# INTERNAL HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _sb_upsert(table: str, data: dict, conflict_col: str = "id") -> bool:
    """Fire-and-forget upsert. Returns True on success."""
    try:
        _sb.table(table).upsert(data, on_conflict=conflict_col).execute()
        return True
    except Exception as e:
        print(f"[SB] upsert {table} error: {e}", file=sys.stderr)
        return False

def _sb_update(table: str, match: dict, data: dict) -> bool:
    try:
        q = _sb.table(table).update(data)
        for k, v in match.items():
            q = q.eq(k, v)
        q.execute()
        return True
    except Exception as e:
        print(f"[SB] update {table} error: {e}", file=sys.stderr)
        return False

# ─────────────────────────────────────────────────────────────────────────────
# BOT CONFIG  (single-row table, id=1)
# ─────────────────────────────────────────────────────────────────────────────
_DEFAULT_CONFIG = {
    "id": 1,
    "status": "Online",
    "caught": 0,
    "faults": 0,
    # spam
    "spam_message": "",
    "spam_speed": 0.5,
    "spam_count": "infinity",
    "spam_cooldown_after_catch": 3.0,
    # owo
    "owo_hunt": True, "owo_hunt_cd": 100000,
    "owo_battle": True, "owo_battle_cd": 150000,
    "owo_daily": True, "owo_daily_cd": 86400,
    "owo_channel_id": "",
    "owo_human_mimicry": False,
    "owo_lootbox": False, "owo_lootbox_cd": 14400,
    "owo_pray": False, "owo_pray_cd": 300,
    "owo_curse": False, "owo_curse_cd": 300,
    "owo_cf": False, "owo_cf_amount": 1,
    "owo_slots": False, "owo_slots_amount": 1,
    "owo_quest": False, "owo_quest_cd": 18000,
    "owo_buy": False, "owo_buy_cd": 3600,
    "owo_sell": False, "owo_sell_cd": 3600,
    "owo_sacrifice": False, "owo_sacrifice_cd": 3600,
    "owo_inv": True, "owo_inv_cd": 600000,
    "owo_equip": True, "owo_equip_cd": 36000,
    "owo_autohunt": False, "owo_autohunt_cd": 3600,
    "owo_owodex": False, "owo_owodex_cd": 60,
    "owo_crate": False, "owo_crate_cd": 3600,
    "owo_battlesetting": False, "owo_battlesetting_cd": 86400,
    "owo_team": False, "owo_team_cd": 60,
    "owo_weapon": False, "owo_weapon_cd": 60,
    "owo_dismantle": False, "owo_dismantle_cd": 3600,
    "owo_lottery": False, "owo_lottery_cd": 14400,
    "owo_blackjack": False, "owo_blackjack_cd": 15,
    "owo_8b": False, "owo_8b_cd": 15,
    "owo_cookie": False, "owo_cookie_cd": 300,
    "owo_ship": False, "owo_ship_cd": 60,
    "owo_marry": False, "owo_marry_cd": 86400,
    "owo_profile": False, "owo_profile_cd": 60,
    "owo_level": True, "owo_level_cd": 60090,
    "owo_pat": False, "owo_pat_cd": 15,
    "owo_hug": False, "owo_hug_cd": 15,
    "owo_kiss": False, "owo_kiss_cd": 15,
    # slash
    "slash_enabled": False,
    "slash_commands": [],
    # image/AI
    "image_enabled": True,
    "hf_token": "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",
    "local_mode": True,
    "local_engine": "onnx",
    # break
    "break_enabled": True,
    "break_start_time": "02:00",
    "break_duration": 10,
    # mimic — stored as jsonb column
    "mimic": {
        "catch_randomizer": {
            "enabled": True, "catch_rate": 77, "hint_rate": 100,
            "skip_chance": 23, "min_catch_delay": 0.5, "max_catch_delay": 2,
            "min_hint_delay": 25, "max_hint_delay": 35, "min_confidence": 0.85
        },
        "owo_randomizer": {
            "enabled": False, "min_cmd_gap": 1, "max_cmd_gap": 4,
            "min_burst_gap": 8, "max_burst_gap": 18,
            "burst_limit_min": 1, "burst_limit_max": 4, "shuffle_commands": True
        },
        "auto_sleep": {
            "enabled": False, "active_start_hour": 8, "active_end_hour": 22
        },
        "adaptive_captcha": {
            "enabled": False, "spam_slowdown_multiplier": 1.5,
            "owo_cooldown_increase_minutes": 10, "hint_slowdown_seconds": 15
        },
        "advanced_mode": False
    },
    # captcha
    "captcha": None,
}

def _load_config() -> dict:
    global _config_cache
    try:
        res = _sb.table("bot_config").select("*").eq("id", 1).single().execute()
        if res.data:
            _config_cache = res.data
            return _config_cache
    except Exception as e:
        print(f"[SB] bot_config load error: {e}", file=sys.stderr)
    # Insert defaults if missing
    _config_cache = dict(_DEFAULT_CONFIG)
    _sb_upsert("bot_config", _config_cache, "id")
    return _config_cache

def _save_config(patch: dict):
    global _config_cache
    with _lock:
        if _config_cache is None:
            _load_config()
        _config_cache.update(patch)
        patch["id"] = 1
        _sb_upsert("bot_config", patch, "id")

def get_db() -> dict:
    """Returns a dict shaped like the old database.json for backwards compat."""
    global _config_cache
    if _config_cache is None:
        _load_config()
    cfg = _config_cache

    # Rebuild legacy shape
    return {
        "status": cfg.get("status", "Online"),
        "caught": cfg.get("caught", 0),
        "faults": cfg.get("faults", 0),
        "logs": list(_logs_cache),
        "tokens": get_tokens(),
        "spam": get_spam_config(),
        "owo": get_owo_config(),
        "slash": get_slash_config(),
        "image": get_image_config(),
        "break": get_break_config(),
        "mimic": get_mimic_config(),
        "captcha": cfg.get("captcha"),
    }

# ─────────────────────────────────────────────────────────────────────────────
# STATUS / CAUGHT / FAULTS
# ─────────────────────────────────────────────────────────────────────────────
def set_status(s: str):
    _save_config({"status": s})

def increment_caught(label=""):
    global _config_cache
    with _lock:
        if _config_cache is None: _load_config()
        new_val = _config_cache.get("caught", 0) + 1
        _config_cache["caught"] = new_val
    _sb_upsert("bot_config", {"id": 1, "caught": new_val}, "id")

def increment_fault(label=""):
    global _config_cache
    with _lock:
        if _config_cache is None: _load_config()
        new_val = _config_cache.get("faults", 0) + 1
        _config_cache["faults"] = new_val
    _sb_upsert("bot_config", {"id": 1, "faults": new_val}, "id")

# ─────────────────────────────────────────────────────────────────────────────
# LOGS  (in-memory ring buffer, pushed to Supabase `logs` table async)
# ─────────────────────────────────────────────────────────────────────────────
def log_event(msg: str, typ: str = "info", label: str = ""):
    col = TYPE_COLOR.get(typ, V)
    ts = datetime.now().strftime("%H:%M:%S")
    pre = f"[{label}] " if label else ""
    print(f"{V}[{ts}]{X} {col}{pre}{msg}{X}")
    entry = {"time": ts, "message": f"{pre}{msg}", "type": typ}
    with _lock:
        _logs_cache.insert(0, entry)
        if len(_logs_cache) > 100:
            _logs_cache.pop()
    # Async push to Supabase logs table
    def _push():
        try:
            _sb.table("logs").insert({
                "time": ts,
                "message": f"{pre}{msg}",
                "type": typ,
                "label": label,
            }).execute()
        except: pass
    threading.Thread(target=_push, daemon=True).start()

def log_catch(name, shiny, label, img=""):
    increment_caught(label)

# ─────────────────────────────────────────────────────────────────────────────
# TOKENS
# ─────────────────────────────────────────────────────────────────────────────
def _db_to_token(row: dict) -> dict:
    if not row: return {}
    t = dict(row)
    if "discord_token" in t:
        t["token"] = t.pop("discord_token")
    # Ensure balances dict is always synchronized with column values
    t["balances"] = {
        "pokecoins": t.get("pokecoins") if t.get("pokecoins") is not None else 0,
        "cowoncy": t.get("cowoncy") if t.get("cowoncy") is not None else 0,
        "last_sync": t.get("last_sync") if t.get("last_sync") else "Never"
    }
    return t

def _token_to_db(tok: dict) -> dict:
    if not tok: return {}
    t = dict(tok)
    if "token" in t:
        t["discord_token"] = t.pop("token")
    # Keep flat columns synchronized with nested balances dict
    bal = t.get("balances", {})
    if isinstance(bal, dict):
        t["pokecoins"] = bal.get("pokecoins", t.get("pokecoins", 0))
        t["cowoncy"] = bal.get("cowoncy", t.get("cowoncy", 0))
        t["last_sync"] = bal.get("last_sync", t.get("last_sync", "Never"))
    else:
        t["pokecoins"] = t.get("pokecoins", 0)
        t["cowoncy"] = t.get("cowoncy", 0)
        t["last_sync"] = t.get("last_sync", "Never")
    return t

def get_tokens() -> list:
    global _tokens_cache
    if _tokens_cache is not None:
        return _tokens_cache
    try:
        res = _sb.table("tokens").select("*").execute()
        raw_data = res.data or []
        _tokens_cache = [_db_to_token(r) for r in raw_data]
    except Exception as e:
        print(f"[SB] get_tokens error: {e}", file=sys.stderr)
        _tokens_cache = []
    return _tokens_cache

def save_tokens(tokens: list):
    global _tokens_cache
    with _lock:
        _tokens_cache = tokens
    def _push():
        for tok in tokens:
            db_row = _token_to_db(tok)
            _sb_upsert("tokens", db_row, "id")
    threading.Thread(target=_push, daemon=True).start()

def save_single_token(tok: dict):
    """Upsert one token immediately (used by engine _sync_state)."""
    global _tokens_cache
    with _lock:
        if _tokens_cache is not None:
            for i, t in enumerate(_tokens_cache):
                if t.get("id") == tok.get("id"):
                    _tokens_cache[i] = tok
                    break
    db_row = _token_to_db(tok)
    _sb_upsert("tokens", db_row, "id")

def delete_token(tid: str):
    global _tokens_cache
    with _lock:
        if _tokens_cache is not None:
            _tokens_cache = [t for t in _tokens_cache if t.get("id") != tid]
    try:
        _sb.table("tokens").delete().eq("id", tid).execute()
    except Exception as e:
        print(f"[SB] delete_token error: {e}", file=sys.stderr)

def invalidate_tokens_cache():
    global _tokens_cache
    _tokens_cache = None

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG SECTIONS — each maps to columns in bot_config
# ─────────────────────────────────────────────────────────────────────────────
def get_spam_config() -> dict:
    if _config_cache is None: _load_config()
    c = _config_cache
    return {
        "message": c.get("spam_message", ""),
        "speed": c.get("spam_speed", 0.5),
        "count": c.get("spam_count", "infinity"),
        "cooldown_after_catch": c.get("spam_cooldown_after_catch", 3.0),
    }

def save_spam_config(s: dict):
    _save_config({
        "spam_message": s.get("message", ""),
        "spam_speed": s.get("speed", 0.5),
        "spam_count": str(s.get("count", "infinity")),
        "spam_cooldown_after_catch": float(s.get("cooldown_after_catch", 3.0)),
    })

def get_owo_config() -> dict:
    if _config_cache is None: _load_config()
    c = _config_cache
    OWO_KEYS = [
        "hunt","hunt_cd","battle","battle_cd","daily","daily_cd","channel_id",
        "human_mimicry","lootbox","lootbox_cd","pray","pray_cd","curse","curse_cd",
        "cf","cf_amount","slots","slots_amount","quest","quest_cd","buy","buy_cd",
        "sell","sell_cd","sacrifice","sacrifice_cd","inv","inv_cd","equip","equip_cd",
        "autohunt","autohunt_cd","owodex","owodex_cd","crate","crate_cd",
        "battlesetting","battlesetting_cd","team","team_cd","weapon","weapon_cd",
        "dismantle","dismantle_cd","lottery","lottery_cd","blackjack","blackjack_cd",
        "8b","8b_cd","cookie","cookie_cd","ship","ship_cd","marry","marry_cd",
        "profile","profile_cd","level","level_cd","pat","pat_cd","hug","hug_cd","kiss","kiss_cd",
    ]
    return {k: c.get(f"owo_{k}", False) for k in OWO_KEYS}

def save_owo_config(cfg: dict):
    patch = {f"owo_{k}": v for k, v in cfg.items()}
    _save_config(patch)

def get_slash_config() -> dict:
    if _config_cache is None: _load_config()
    return {
        "enabled": _config_cache.get("slash_enabled", False),
        "commands": _config_cache.get("slash_commands", []),
    }

def save_slash_config(c: dict):
    _save_config({"slash_enabled": c.get("enabled", False), "slash_commands": c.get("commands", [])})

def get_image_config() -> dict:
    if _config_cache is None: _load_config()
    c = _config_cache
    m = c.get("mimic", {}) or {}
    return {
        "enabled": c.get("image_enabled", True),
        "hf_token": c.get("hf_token", ""),
        "local_mode": c.get("local_mode", True),
        "local_engine": c.get("local_engine", "onnx"),
        "advanced_mode": m.get("advanced_mode", False),
    }

def save_image_config(c: dict):
    if _config_cache is None: _load_config()
    current_mimic = _config_cache.get("mimic", {}) or {}
    current_mimic["advanced_mode"] = c.get("advanced_mode", False)
    _save_config({
        "image_enabled": c.get("enabled", True),
        "hf_token": c.get("hf_token", ""),
        "local_mode": c.get("local_mode", True),
        "local_engine": c.get("local_engine", "onnx"),
        "mimic": current_mimic
    })

def get_break_config() -> dict:
    if _config_cache is None: _load_config()
    c = _config_cache
    return {
        "enabled": c.get("break_enabled", True),
        "start_time": c.get("break_start_time", "02:00"),
        "duration": c.get("break_duration", 10),
    }

def save_break_config(c: dict):
    _save_config({
        "break_enabled": c.get("enabled", True),
        "break_start_time": c.get("start_time", "02:00"),
        "break_duration": int(c.get("duration", 10)),
    })

def get_mimic_config() -> dict:
    if _config_cache is None: _load_config()
    return _config_cache.get("mimic") or _DEFAULT_CONFIG["mimic"]

def save_mimic_config(c: dict):
    _save_config({"mimic": c})

# ─────────────────────────────────────────────────────────────────────────────
# CAPTCHA
# ─────────────────────────────────────────────────────────────────────────────
def get_captcha_data() -> dict:
    """Returns the full captcha data dict: {'active': {...}, 'history': [...]}"""
    if _config_cache is None:
        _load_config()
    val = _config_cache.get("captcha")
    if not isinstance(val, dict) or "active" not in val or "history" not in val:
        return {"active": {}, "history": []}
    return val

def set_captcha(url: str, label: str, node_id: str = ""):
    data = get_captcha_data()
    
    # 1. Update active list
    cap = {
        "url": url,
        "label": label,
        "time": datetime.now().strftime("%H:%M:%S"),
        "datetime": datetime.now().isoformat(),
        "id": node_id
    }
    data["active"][label] = cap
    
    # 2. Update history
    hist_entry = {
        "url": url,
        "label": label,
        "time": cap["time"],
        "datetime": cap["datetime"],
        "resolved": False
    }
    for e in data["history"]:
        if e.get("label") == label and not e.get("resolved"):
            e["resolved"] = True
            
    data["history"].insert(0, hist_entry)
    if len(data["history"]) > 200:
        data["history"].pop()
        
    _save_config({"captcha": data})

def get_captcha():
    """Legacy helper: returns the last active captcha if any."""
    data = get_captcha_data()
    if data["active"]:
        # Return any active captcha
        return list(data["active"].values())[0]
    return None

def get_captcha_history() -> list:
    return get_captcha_data().get("history", [])

def resolve_captcha_in_history(label: str):
    data = get_captcha_data()
    data["active"].pop(label, None)
    for e in data["history"]:
        if e.get("label") == label:
            e["resolved"] = True
    _save_config({"captcha": data})

def clear_captcha():
    data = get_captcha_data()
    data["active"] = {}
    for e in data["history"]:
        e["resolved"] = True
    _save_config({"captcha": data})

def clear_captcha_history():
    data = get_captcha_data()
    data["history"] = []
    _save_config({"captcha": data})


# ─────────────────────────────────────────────────────────────────────────────
# HISTORY
# ─────────────────────────────────────────────────────────────────────────────
def _load_history():
    global _hist_cache
    try:
        res = _sb.table("history").select("*").order("timestamp", desc=True).limit(500).execute()
        _hist_cache = res.data or []
    except Exception as e:
        print(f"[SB] history load error: {e}", file=sys.stderr)
        _hist_cache = []

def get_history() -> list:
    global _hist_cache
    if _hist_cache is None:
        _load_history()
    return _hist_cache

def log_history(entry: dict):
    global _hist_cache
    # Build DB row
    row = {
        "id": entry.get("id", str(uuid.uuid4())[:8]),
        "pokemon_name": entry.get("pokemon_name", "unknown"),
        "display_name": entry.get("display_name", ""),
        "caught_by": entry.get("caught_by", ""),
        "channel_id": entry.get("channel_id", ""),
        "success": entry.get("success", True),
        "failure_reason": entry.get("failure_reason"),
        "is_shiny": entry.get("is_shiny", False),
        "hint": entry.get("hint", ""),
        "level": str(entry.get("level", "1")),
        "iv": str(entry.get("iv", "??%")),
        "discord_img": entry.get("discord_img", ""),
        "is_image_catch": entry.get("is_image_catch", False),
        "confidence": float(entry.get("confidence", 0)),
        "sprite": entry.get("sprite", ""),
        "rarity": entry.get("rarity", "common"),
    }
    # Update in-memory cache
    with _lock:
        if _hist_cache is None:
            _hist_cache = []
        if not any(x.get("id") == row["id"] for x in _hist_cache):
            _hist_cache.insert(0, {**entry, **row})
            if len(_hist_cache) > 500:
                _hist_cache.pop()
    log_event(f"History Entry Added: {row['pokemon_name'].title()}", "history")
    def _push():
        _sb_upsert("history", row, "id")
    threading.Thread(target=_push, daemon=True).start()

def log_history_batch(entries: list):
    existing_ids = {x.get("id") for x in (get_history() or [])}
    for e in entries:
        if e.get("id") not in existing_ids:
            log_history(e)

def _write_hist(data: list):
    """Used by keep_alive /api/history/clear — clears history table."""
    global _hist_cache
    with _lock:
        _hist_cache = []
    def _clear():
        try:
            _sb.table("history").delete().neq("id", "___never___").execute()
        except Exception as e:
            print(f"[SB] clear history error: {e}", file=sys.stderr)
    threading.Thread(target=_clear, daemon=True).start()

# ─────────────────────────────────────────────────────────────────────────────
# POKÉDEX
# ─────────────────────────────────────────────────────────────────────────────
def _load_dex():
    global _dex_cache
    try:
        res = _sb.table("dex").select("*").execute()
        rows = res.data or []
        _dex_cache = {r["name"]: r for r in rows}
    except Exception as e:
        print(f"[SB] dex load error: {e}", file=sys.stderr)
        _dex_cache = {}

def get_dex(query: str = "") -> dict:
    global _dex_cache
    if _dex_cache is None:
        _load_dex()
    if not query:
        return _dex_cache
    q = query.lower()
    return {k: v for k, v in _dex_cache.items()
            if q in k or q in v.get("display_name", "").lower() or q in v.get("notes", "").lower()}

def save_dex(d: dict):
    global _dex_cache
    with _lock:
        _dex_cache = d
    def _push():
        for row in d.values():
            _sb_upsert("dex", row, "name")
    threading.Thread(target=_push, daemon=True).start()

def upsert_dex_entry(name: str, shiny: bool = False, img: str = "", caught_by: str = ""):
    global _dex_cache
    key = name.lower().strip()
    now = datetime.now().isoformat()
    with _lock:
        if _dex_cache is None:
            _dex_cache = {}
        e = _dex_cache.get(key, {
            "name": key,
            "display_name": name.title(),
            "caught_count": 0,
            "shiny_count": 0,
            "first_caught": now,
            "last_caught": now,
            "notes": "",
            "favorite": False,
            "img_url": img,
            "caught_by": caught_by,
        })
        e["caught_count"] = e.get("caught_count", 0) + 1
        if shiny:
            e["shiny_count"] = e.get("shiny_count", 0) + 1
        e["last_caught"] = now
        if not e.get("img_url") and img:
            e["img_url"] = img
        _dex_cache[key] = e
    row = dict(e)
    threading.Thread(target=lambda: _sb_upsert("dex", row, "name"), daemon=True).start()

def backfill_dex_from_history():
    h = get_history()
    for entry in h:
        name = entry.get("pokemon_name", "")
        if not name or not entry.get("success", False):
            continue
        upsert_dex_entry(
            name,
            shiny=entry.get("is_shiny", False) or entry.get("shiny", False),
            img=entry.get("discord_img", "") or entry.get("img", ""),
            caught_by=entry.get("caught_by", ""),
        )
    print(f"[DEX] Backfill complete. {len(_dex_cache or {})} entries.", flush=True)

# ─────────────────────────────────────────────────────────────────────────────
# INIT
# ─────────────────────────────────────────────────────────────────────────────
def init_db():
    """Load all caches from Supabase at startup."""
    global _config_cache, _tokens_cache, _hist_cache, _dex_cache
    print("[SB] Connecting to Supabase...", flush=True)
    _load_config()
    get_tokens()
    _load_history()
    _load_dex()
    print(f"[SB] Ready — config loaded, {len(_tokens_cache or [])} token(s), "
          f"{len(_hist_cache or [])} history rows, {len(_dex_cache or {})} dex entries.", flush=True)

# ── keep_alive.py calls _read() directly in /api/reset — provide shim ────────
def _read() -> dict:
    return get_db()

def _write(d: dict):
    """Legacy shim — maps flat dict writes back to bot_config."""
    patch = {}
    if "status" in d: patch["status"] = d["status"]
    if "caught" in d: patch["caught"] = d["caught"]
    if "faults" in d: patch["faults"] = d["faults"]
    if patch:
        _save_config(patch)

# Background 6-second Supabase re-sync (keeps caches fresh across restarts)
def _bg_sync():
    while True:
        time.sleep(6)
        try:
            res = _sb.table("bot_config").select("caught,faults,status").eq("id", 1).single().execute()
            if res.data:
                with _lock:
                    if _config_cache:
                        _config_cache["caught"] = res.data.get("caught", _config_cache.get("caught", 0))
                        _config_cache["faults"] = res.data.get("faults", _config_cache.get("faults", 0))
                        _config_cache["status"] = res.data.get("status", _config_cache.get("status", "Online"))
        except: pass

threading.Thread(target=_bg_sync, daemon=True, name="SBSync").start()

# ─────────────────────────────────────────────────────────────────────────────
# TEST TABLE  — stores channel scan / broadcast results per token
# Expects Supabase table `test` with columns:
#   id (text PK), token_id (text), token_label (text),
#   guild_id (text), guild_name (text),
#   channel_id (text), channel_name (text),
#   writable (bool), text_allowed (bool), link_allowed (bool),
#   last_scan (timestamptz), scan_reason (text)
# ─────────────────────────────────────────────────────────────────────────────
_test_cache: list = []

def get_test_results() -> list:
    global _test_cache
    try:
        res = _sb.table("test").select("*").order("last_scan", desc=True).execute()
        _test_cache = res.data or []
    except Exception as e:
        print(f"[SB] test load error: {e}", file=sys.stderr)
    return _test_cache

def save_test_result(row: dict):
    """Upsert a single channel scan result. row must contain `id`."""
    global _test_cache
    try:
        _sb.table("test").upsert(row, on_conflict="id").execute()
        with _lock:
            _test_cache = [r for r in _test_cache if r.get("id") != row["id"]]
            _test_cache.insert(0, row)
    except Exception as e:
        print(f"[SB] test upsert error: {e}", file=sys.stderr)

def clear_test_results_for_token(token_id: str):
    global _test_cache
    try:
        _sb.table("test").delete().eq("token_id", token_id).execute()
        with _lock:
            _test_cache = [r for r in _test_cache if r.get("token_id") != token_id]
    except Exception as e:
        print(f"[SB] test clear error: {e}", file=sys.stderr)

def clear_all_test_results():
    global _test_cache
    try:
        _sb.table("test").delete().neq("id", "___never___").execute()
        _test_cache = []
    except Exception as e:
        print(f"[SB] test clear-all error: {e}", file=sys.stderr)
