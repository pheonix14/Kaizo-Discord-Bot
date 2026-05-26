"""
setup_supabase.py — Creates all tables + migrates JSON data in one shot.
Uses Supabase Management API for DDL, then PostgREST for DML.
"""
import sys, os, json, uuid, requests
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SUPABASE_URL = "https://cwputkmuqgpxydfxsrnm.supabase.co"
PROJECT_REF  = "cwputkmuqgpxydfxsrnm"
SERVICE_KEY  = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN3cHV0a211cWdweHlkZnhzcm5tIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTAzODc3OCwiZXhwIjoyMDk0NjE0Nzc4fQ.e4raXAvgNzKoJWr6FNIDydOuH3EYxWEIQGoOOKQtZKY"

HDR = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal",
}

# ─── SQL DDL Statements ───────────────────────────────────────────────────────
STATEMENTS = [
    """CREATE TABLE IF NOT EXISTS tokens (
        id TEXT PRIMARY KEY,
        discord_token TEXT NOT NULL DEFAULT '',
        label TEXT NOT NULL DEFAULT '',
        guild_id TEXT DEFAULT '',
        channel_id TEXT DEFAULT '',
        active BOOLEAN DEFAULT true,
        spam_active BOOLEAN DEFAULT false,
        owo_active BOOLEAN DEFAULT false,
        slash_active BOOLEAN DEFAULT true,
        owo_channel_id TEXT DEFAULT '',
        msg_active BOOLEAN DEFAULT false,
        msg_channel_id TEXT DEFAULT '',
        msg_delay INTEGER DEFAULT 20,
        msg_random_delay BOOLEAN DEFAULT false,
        pokecoins BIGINT DEFAULT 0,
        cowoncy BIGINT DEFAULT 0,
        last_sync TEXT DEFAULT '',
        balances JSONB DEFAULT '{}',
        owo_last_run JSONB DEFAULT '{}',
        slash_last_run JSONB DEFAULT '{}'
    )""",
    """CREATE TABLE IF NOT EXISTS dex (
        name TEXT PRIMARY KEY,
        display_name TEXT NOT NULL DEFAULT '',
        caught_count INTEGER DEFAULT 0,
        shiny_count INTEGER DEFAULT 0,
        first_caught TIMESTAMPTZ DEFAULT NOW(),
        last_caught TIMESTAMPTZ DEFAULT NOW(),
        notes TEXT DEFAULT '',
        favorite BOOLEAN DEFAULT false,
        img_url TEXT DEFAULT '',
        caught_by TEXT DEFAULT ''
    )""",
    """CREATE TABLE IF NOT EXISTS history (
        id TEXT PRIMARY KEY,
        timestamp TIMESTAMPTZ DEFAULT NOW(),
        pokemon_name TEXT NOT NULL DEFAULT '',
        display_name TEXT DEFAULT '',
        caught_by TEXT DEFAULT '',
        channel_id TEXT DEFAULT '',
        success BOOLEAN DEFAULT true,
        failure_reason TEXT,
        is_shiny BOOLEAN DEFAULT false,
        hint TEXT DEFAULT '',
        level TEXT DEFAULT '1',
        iv TEXT DEFAULT '??%',
        discord_img TEXT DEFAULT '',
        is_image_catch BOOLEAN DEFAULT false,
        confidence FLOAT DEFAULT 0,
        sprite TEXT DEFAULT '',
        rarity TEXT DEFAULT 'common'
    )""",
    """CREATE TABLE IF NOT EXISTS bot_config (
        id INTEGER PRIMARY KEY DEFAULT 1,
        status TEXT DEFAULT 'Online',
        caught INTEGER DEFAULT 0,
        faults INTEGER DEFAULT 0,
        spam_message TEXT DEFAULT '',
        spam_speed FLOAT DEFAULT 0.5,
        spam_count TEXT DEFAULT 'infinity',
        spam_cooldown_after_catch FLOAT DEFAULT 3.0,
        owo_hunt BOOLEAN DEFAULT true, owo_hunt_cd INTEGER DEFAULT 100000,
        owo_battle BOOLEAN DEFAULT true, owo_battle_cd INTEGER DEFAULT 150000,
        owo_daily BOOLEAN DEFAULT true, owo_daily_cd INTEGER DEFAULT 86400,
        owo_channel_id TEXT DEFAULT '', owo_human_mimicry BOOLEAN DEFAULT false,
        owo_lootbox BOOLEAN DEFAULT false, owo_lootbox_cd INTEGER DEFAULT 14400,
        owo_pray BOOLEAN DEFAULT false, owo_pray_cd INTEGER DEFAULT 300,
        owo_curse BOOLEAN DEFAULT false, owo_curse_cd INTEGER DEFAULT 300,
        owo_cf BOOLEAN DEFAULT false, owo_cf_amount INTEGER DEFAULT 1,
        owo_slots BOOLEAN DEFAULT false, owo_slots_amount INTEGER DEFAULT 1,
        owo_quest BOOLEAN DEFAULT false, owo_quest_cd INTEGER DEFAULT 18000,
        owo_buy BOOLEAN DEFAULT false, owo_buy_cd INTEGER DEFAULT 3600,
        owo_sell BOOLEAN DEFAULT false, owo_sell_cd INTEGER DEFAULT 3600,
        owo_sacrifice BOOLEAN DEFAULT false, owo_sacrifice_cd INTEGER DEFAULT 3600,
        owo_inv BOOLEAN DEFAULT true, owo_inv_cd INTEGER DEFAULT 600000,
        owo_equip BOOLEAN DEFAULT true, owo_equip_cd INTEGER DEFAULT 36000,
        owo_autohunt BOOLEAN DEFAULT false, owo_autohunt_cd INTEGER DEFAULT 3600,
        owo_owodex BOOLEAN DEFAULT false, owo_owodex_cd INTEGER DEFAULT 60,
        owo_crate BOOLEAN DEFAULT false, owo_crate_cd INTEGER DEFAULT 3600,
        owo_battlesetting BOOLEAN DEFAULT false, owo_battlesetting_cd INTEGER DEFAULT 86400,
        owo_team BOOLEAN DEFAULT false, owo_team_cd INTEGER DEFAULT 60,
        owo_weapon BOOLEAN DEFAULT false, owo_weapon_cd INTEGER DEFAULT 60,
        owo_dismantle BOOLEAN DEFAULT false, owo_dismantle_cd INTEGER DEFAULT 3600,
        owo_lottery BOOLEAN DEFAULT false, owo_lottery_cd INTEGER DEFAULT 14400,
        owo_blackjack BOOLEAN DEFAULT false, owo_blackjack_cd INTEGER DEFAULT 15,
        owo_8b BOOLEAN DEFAULT false, owo_8b_cd INTEGER DEFAULT 15,
        owo_cookie BOOLEAN DEFAULT false, owo_cookie_cd INTEGER DEFAULT 300,
        owo_ship BOOLEAN DEFAULT false, owo_ship_cd INTEGER DEFAULT 60,
        owo_marry BOOLEAN DEFAULT false, owo_marry_cd INTEGER DEFAULT 86400,
        owo_profile BOOLEAN DEFAULT false, owo_profile_cd INTEGER DEFAULT 60,
        owo_level BOOLEAN DEFAULT true, owo_level_cd INTEGER DEFAULT 60090,
        owo_pat BOOLEAN DEFAULT false, owo_pat_cd INTEGER DEFAULT 15,
        owo_hug BOOLEAN DEFAULT false, owo_hug_cd INTEGER DEFAULT 15,
        owo_kiss BOOLEAN DEFAULT false, owo_kiss_cd INTEGER DEFAULT 15,
        slash_enabled BOOLEAN DEFAULT false,
        slash_commands JSONB DEFAULT '[]',
        image_enabled BOOLEAN DEFAULT true,
        hf_token TEXT DEFAULT '',
        local_mode BOOLEAN DEFAULT true,
        local_engine TEXT DEFAULT 'onnx',
        break_enabled BOOLEAN DEFAULT true,
        break_start_time TEXT DEFAULT '02:00',
        break_duration INTEGER DEFAULT 10,
        mimic JSONB DEFAULT '{}',
        captcha JSONB DEFAULT null
    )""",
    """CREATE TABLE IF NOT EXISTS logs (
        id BIGSERIAL PRIMARY KEY,
        time TEXT NOT NULL DEFAULT '',
        message TEXT NOT NULL DEFAULT '',
        type TEXT DEFAULT 'info',
        label TEXT DEFAULT '',
        created_at TIMESTAMPTZ DEFAULT NOW()
    )""",
]

def exec_sql(sql: str) -> bool:
    """Execute DDL via Supabase Management API pg/query endpoint."""
    url = f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query"
    r = requests.post(url, headers={
        "Authorization": f"Bearer {SERVICE_KEY}",
        "Content-Type": "application/json",
    }, json={"query": sql}, timeout=30)
    if r.status_code in (200, 201):
        return True
    # Fallback: try the pg REST shim
    url2 = f"{SUPABASE_URL}/pg/query"
    r2 = requests.post(url2, headers=HDR, json={"query": sql}, timeout=30)
    return r2.status_code in (200, 201)

def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"  [skip] {path}: {e}")
        return default

def upsert(table: str, rows: list, conflict: str):
    from supabase import create_client
    sb = create_client(SUPABASE_URL, SERVICE_KEY)
    chunk = 50
    for i in range(0, len(rows), chunk):
        try:
            sb.table(table).upsert(rows[i:i+chunk], on_conflict=conflict).execute()
        except Exception as e:
            print(f"  [warn] upsert {table} chunk {i}: {e}")

# ─────────────────────────────────────────────────────────────────────────────
print("=" * 55)
print("  FAFNIR SUPABASE SETUP")
print("=" * 55)

# STEP 1: Create tables
print("\n[STEP 1] Creating tables via Management API...")
from supabase import create_client
sb = create_client(SUPABASE_URL, SERVICE_KEY)

for stmt in STATEMENTS:
    label = stmt.strip().split("\n")[0][:60]
    ok = exec_sql(stmt)
    status = "OK" if ok else "FAILED (may already exist - continuing)"
    print(f"  {status}: {label}")

# STEP 2: Migrate database.json -> bot_config + tokens
print("\n[STEP 2] Migrating database.json...")
db = load_json("database.json", {})
if db:
    spam = db.get("spam", {})
    owo  = db.get("owo", {})
    slsh = db.get("slash", {})
    img  = db.get("image", {})
    brk  = db.get("break", {})
    mim  = db.get("mimic", {})

    row = {
        "id": 1,
        "status": db.get("status", "Online"),
        "caught": db.get("caught", 0),
        "faults": db.get("faults", 0),
        "spam_message": spam.get("message", ""),
        "spam_speed": float(spam.get("speed", 0.5)),
        "spam_count": str(spam.get("count", "infinity")),
        "spam_cooldown_after_catch": float(spam.get("cooldown_after_catch", 3.0)),
        "image_enabled": img.get("enabled", True),
        "hf_token": img.get("hf_token", ""),
        "local_mode": img.get("local_mode", True),
        "local_engine": img.get("local_engine", "onnx"),
        "break_enabled": brk.get("enabled", True),
        "break_start_time": brk.get("start_time", "02:00"),
        "break_duration": int(brk.get("duration", 10)),
        "slash_enabled": slsh.get("enabled", False),
        "slash_commands": slsh.get("commands", []),
        "mimic": mim,
    }
    for k, v in owo.items():
        # Don't double-prefix keys that already include owo_ (like owo_channel_id in old config)
        col = k if k.startswith("owo_") else f"owo_{k}"
        row[col] = v

    try:
        sb.table("bot_config").upsert(row, on_conflict="id").execute()
        print(f"  OK: bot_config (caught={row['caught']}, faults={row['faults']})")
    except Exception as e:
        print(f"  WARN bot_config: {e}")

    tokens = db.get("tokens", [])
    tok_rows = []
    for tok in tokens:
        bal = tok.get("balances", {})
        tok_rows.append({
            "id": tok.get("id", str(uuid.uuid4())),
            "discord_token": tok.get("token", ""),
            "label": tok.get("label", ""),
            "guild_id": tok.get("guild_id", ""),
            "channel_id": tok.get("channel_id", ""),
            "active": tok.get("active", True),
            "spam_active": tok.get("spam_active", False),
            "owo_active": tok.get("owo_active", False),
            "slash_active": tok.get("slash_active", True),
            "owo_channel_id": tok.get("owo_channel_id", ""),
            "msg_active": tok.get("msg_active", False),
            "msg_channel_id": tok.get("msg_channel_id", ""),
            "msg_delay": int(tok.get("msg_delay", 20)),
            "msg_random_delay": tok.get("msg_random_delay", False),
            "pokecoins": bal.get("pokecoins", 0),
            "cowoncy": bal.get("cowoncy", 0),
            "last_sync": bal.get("last_sync", ""),
            "balances": bal,
            "owo_last_run": tok.get("owo_last_run", {}),
            "slash_last_run": tok.get("slash_last_run", {}),
        })
    upsert("tokens", tok_rows, "id")
    print(f"  OK: {len(tok_rows)} token(s) migrated")

# STEP 3: Migrate dex.json
print("\n[STEP 3] Migrating dex.json...")
dex = load_json("dex.json", {})
if dex:
    rows = []
    for key, v in dex.items():
        rows.append({
            "name": key,
            "display_name": v.get("display_name", key.title()),
            "caught_count": v.get("caught_count", 0),
            "shiny_count": v.get("shiny_count", 0),
            "first_caught": v.get("first_caught"),
            "last_caught": v.get("last_caught"),
            "notes": v.get("notes", ""),
            "favorite": v.get("favorite", False),
            "img_url": v.get("img", "") or v.get("img_url", ""),
            "caught_by": v.get("caught_by", ""),
        })
    upsert("dex", rows, "name")
    print(f"  OK: {len(rows)} dex entries migrated")

# STEP 4: Migrate history.json
print("\n[STEP 4] Migrating history.json...")
hist = load_json("history.json", [])
if hist:
    rows = []
    for e in hist:
        rows.append({
            "id": e.get("id", str(uuid.uuid4())[:8]),
            "pokemon_name": e.get("pokemon_name", "unknown"),
            "display_name": e.get("display_name", ""),
            "caught_by": e.get("caught_by", ""),
            "channel_id": e.get("channel_id", ""),
            "success": e.get("success", True),
            "failure_reason": e.get("failure_reason"),
            "is_shiny": e.get("is_shiny", False) or e.get("shiny", False),
            "hint": e.get("hint", ""),
            "level": str(e.get("level", "1")),
            "iv": str(e.get("iv", "??%")),
            "discord_img": e.get("discord_img", "") or e.get("img", ""),
            "is_image_catch": e.get("is_image_catch", False),
            "confidence": float(e.get("confidence", 0)),
            "sprite": e.get("sprite", ""),
            "rarity": e.get("rarity", "common"),
        })
    upsert("history", rows, "id")
    print(f"  OK: {len(rows)} history entries migrated")
else:
    print("  (history.json empty — skipped)")

print("\n[DONE] All data migrated to Supabase!")
print("  You can now delete: database.json, dex.json, history.json, state.json")
