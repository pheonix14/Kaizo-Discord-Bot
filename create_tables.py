"""
create_tables.py
Creates all Supabase tables via the REST SQL endpoint using the service role key.
Run this FIRST, before migrate_to_supabase.py
"""
import requests, sys

SUPABASE_URL  = "https://cwputkmuqgpxydfxsrnm.supabase.co"
SERVICE_KEY   = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN3cHV0a211cWdweHlkZnhzcm5tIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTAzODc3OCwiZXhwIjoyMDk0NjE0Nzc4fQ.e4raXAvgNzKoJWr6FNIDydOuH3EYxWEIQGoOOKQtZKY"

SQL = """
CREATE TABLE IF NOT EXISTS tokens (
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
);

CREATE TABLE IF NOT EXISTS dex (
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
);

CREATE TABLE IF NOT EXISTS history (
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
);

CREATE TABLE IF NOT EXISTS bot_config (
    id INTEGER PRIMARY KEY DEFAULT 1,
    status TEXT DEFAULT 'Online',
    caught INTEGER DEFAULT 0,
    faults INTEGER DEFAULT 0,
    spam_message TEXT DEFAULT '',
    spam_speed FLOAT DEFAULT 0.5,
    spam_count TEXT DEFAULT 'infinity',
    spam_cooldown_after_catch FLOAT DEFAULT 3.0,
    owo_hunt BOOLEAN DEFAULT true,
    owo_hunt_cd INTEGER DEFAULT 100000,
    owo_battle BOOLEAN DEFAULT true,
    owo_battle_cd INTEGER DEFAULT 150000,
    owo_daily BOOLEAN DEFAULT true,
    owo_daily_cd INTEGER DEFAULT 86400,
    owo_channel_id TEXT DEFAULT '',
    owo_human_mimicry BOOLEAN DEFAULT false,
    owo_lootbox BOOLEAN DEFAULT false,
    owo_lootbox_cd INTEGER DEFAULT 14400,
    owo_pray BOOLEAN DEFAULT false,
    owo_pray_cd INTEGER DEFAULT 300,
    owo_curse BOOLEAN DEFAULT false,
    owo_curse_cd INTEGER DEFAULT 300,
    owo_cf BOOLEAN DEFAULT false,
    owo_cf_amount INTEGER DEFAULT 1,
    owo_slots BOOLEAN DEFAULT false,
    owo_slots_amount INTEGER DEFAULT 1,
    owo_quest BOOLEAN DEFAULT false,
    owo_quest_cd INTEGER DEFAULT 18000,
    owo_buy BOOLEAN DEFAULT false,
    owo_buy_cd INTEGER DEFAULT 3600,
    owo_sell BOOLEAN DEFAULT false,
    owo_sell_cd INTEGER DEFAULT 3600,
    owo_sacrifice BOOLEAN DEFAULT false,
    owo_sacrifice_cd INTEGER DEFAULT 3600,
    owo_inv BOOLEAN DEFAULT true,
    owo_inv_cd INTEGER DEFAULT 600000,
    owo_equip BOOLEAN DEFAULT true,
    owo_equip_cd INTEGER DEFAULT 36000,
    owo_autohunt BOOLEAN DEFAULT false,
    owo_autohunt_cd INTEGER DEFAULT 3600,
    owo_owodex BOOLEAN DEFAULT false,
    owo_owodex_cd INTEGER DEFAULT 60,
    owo_crate BOOLEAN DEFAULT false,
    owo_crate_cd INTEGER DEFAULT 3600,
    owo_battlesetting BOOLEAN DEFAULT false,
    owo_battlesetting_cd INTEGER DEFAULT 86400,
    owo_team BOOLEAN DEFAULT false,
    owo_team_cd INTEGER DEFAULT 60,
    owo_weapon BOOLEAN DEFAULT false,
    owo_weapon_cd INTEGER DEFAULT 60,
    owo_dismantle BOOLEAN DEFAULT false,
    owo_dismantle_cd INTEGER DEFAULT 3600,
    owo_lottery BOOLEAN DEFAULT false,
    owo_lottery_cd INTEGER DEFAULT 14400,
    owo_blackjack BOOLEAN DEFAULT false,
    owo_blackjack_cd INTEGER DEFAULT 15,
    owo_8b BOOLEAN DEFAULT false,
    owo_8b_cd INTEGER DEFAULT 15,
    owo_cookie BOOLEAN DEFAULT false,
    owo_cookie_cd INTEGER DEFAULT 300,
    owo_ship BOOLEAN DEFAULT false,
    owo_ship_cd INTEGER DEFAULT 60,
    owo_marry BOOLEAN DEFAULT false,
    owo_marry_cd INTEGER DEFAULT 86400,
    owo_profile BOOLEAN DEFAULT false,
    owo_profile_cd INTEGER DEFAULT 60,
    owo_level BOOLEAN DEFAULT true,
    owo_level_cd INTEGER DEFAULT 60090,
    owo_pat BOOLEAN DEFAULT false,
    owo_pat_cd INTEGER DEFAULT 15,
    owo_hug BOOLEAN DEFAULT false,
    owo_hug_cd INTEGER DEFAULT 15,
    owo_kiss BOOLEAN DEFAULT false,
    owo_kiss_cd INTEGER DEFAULT 15,
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
    captcha JSONB DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS logs (
    id BIGSERIAL PRIMARY KEY,
    time TEXT NOT NULL DEFAULT '',
    message TEXT NOT NULL DEFAULT '',
    type TEXT DEFAULT 'info',
    label TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
"""

def run_sql(sql: str):
    url = f"{SUPABASE_URL}/rest/v1/rpc/exec_sql"
    # Use the pg REST endpoint
    url2 = f"{SUPABASE_URL}/pg/query"
    headers = {
        "apikey": SERVICE_KEY,
        "Authorization": f"Bearer {SERVICE_KEY}",
        "Content-Type": "application/json",
    }
    # Try direct SQL via the management API
    mgmt_url = f"https://api.supabase.com/v1/projects/cwputkmuqgpxydfxsrnm/database/query"
    r = requests.post(mgmt_url, headers={
        "Authorization": f"Bearer {SERVICE_KEY}",
        "Content-Type": "application/json",
    }, json={"query": sql})
    return r

if __name__ == "__main__":
    print("Creating Supabase tables...")
    # Split into individual statements
    statements = [s.strip() for s in SQL.split(";") if s.strip()]
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    
    from supabase import create_client
    sb = create_client(SUPABASE_URL, SERVICE_KEY)
    
    for stmt in statements:
        if not stmt:
            continue
        try:
            # Use rpc exec if available, otherwise skip
            r = requests.post(
                f"{SUPABASE_URL}/rest/v1/rpc/exec_sql",
                headers={
                    "apikey": SERVICE_KEY,
                    "Authorization": f"Bearer {SERVICE_KEY}",
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal",
                },
                json={"sql": stmt}
            )
            if r.status_code in (200, 201, 204):
                first_line = stmt.split("\n")[0][:60]
                print(f"  OK: {first_line}")
            else:
                print(f"  SKIP ({r.status_code}): {stmt[:60]}")
        except Exception as e:
            print(f"  ERR: {e}")
    
    print("\nDone. Now run: python migrate_to_supabase.py")
