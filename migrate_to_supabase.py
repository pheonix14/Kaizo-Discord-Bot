"""
migrate_to_supabase.py
One-time script: reads local JSON files and pushes all data to Supabase.
Run ONCE after creating the SQL tables:
    python migrate_to_supabase.py
"""
import json, os, sys, uuid
from datetime import datetime
from supabase import create_client

SUPABASE_URL = "https://cwputkmuqgpxydfxsrnm.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN3cHV0a211cWdweHlkZnhzcm5tIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTAzODc3OCwiZXhwIjoyMDk0NjE0Nzc4fQ.e4raXAvgNzKoJWr6FNIDydOuH3EYxWEIQGoOOKQtZKY"

sb = create_client(SUPABASE_URL, SUPABASE_KEY)

def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"  [skip] {path}: {e}")
        return default

def migrate_database():
    print("\n[1] Migrating database.json -> bot_config + tokens...")
    db = load_json("database.json", {})
    if not db:
        return

    # ── bot_config row ───────────────────────────────────────────
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
        "spam_speed": spam.get("speed", 0.5),
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
    # Add all owo_ columns
    for k, v in owo.items():
        row[f"owo_{k}"] = v

    sb.table("bot_config").upsert(row, on_conflict="id").execute()
    print(f"  ✓ bot_config row upserted")

    # ── tokens ───────────────────────────────────────────────────
    tokens = db.get("tokens", [])
    for tok in tokens:
        bal = tok.get("balances", {})
        sb.table("tokens").upsert({
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
        }, on_conflict="id").execute()
    print(f"  ✓ {len(tokens)} token(s) migrated")

def migrate_dex():
    print("\n[2] Migrating dex.json -> dex table...")
    dex = load_json("dex.json", {})
    if not dex:
        return
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
    # Batch upsert in chunks of 100
    chunk = 100
    for i in range(0, len(rows), chunk):
        sb.table("dex").upsert(rows[i:i+chunk], on_conflict="name").execute()
    print(f"  ✓ {len(rows)} dex entries migrated")

def migrate_history():
    print("\n[3] Migrating history.json -> history table...")
    hist = load_json("history.json", [])
    if not hist:
        print("  [skip] history.json is empty")
        return
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
    chunk = 100
    for i in range(0, len(rows), chunk):
        sb.table("history").upsert(rows[i:i+chunk], on_conflict="id").execute()
    print(f"  ✓ {len(rows)} history entries migrated")

if __name__ == "__main__":
    print("=" * 55)
    print("  FAFNIR -> SUPABASE MIGRATION")
    print("=" * 55)
    migrate_database()
    migrate_dex()
    migrate_history()
    print("\n✅ Migration complete! You can delete the .json files now.")
