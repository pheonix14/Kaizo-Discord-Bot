-- ═══════════════════════════════════════════════════════════════════
-- FAFNIR SUPABASE SCHEMA
-- Run this entire block in your Supabase SQL Editor
-- ═══════════════════════════════════════════════════════════════════

-- 1. TOKENS
CREATE TABLE IF NOT EXISTS tokens (
    id                TEXT PRIMARY KEY,
    discord_token     TEXT NOT NULL,
    label             TEXT NOT NULL DEFAULT '',
    guild_id          TEXT DEFAULT '',
    channel_id        TEXT DEFAULT '',
    active            BOOLEAN DEFAULT true,
    spam_active       BOOLEAN DEFAULT false,
    owo_active        BOOLEAN DEFAULT false,
    slash_active      BOOLEAN DEFAULT true,
    owo_channel_id    TEXT DEFAULT '',
    msg_active        BOOLEAN DEFAULT false,
    msg_channel_id    TEXT DEFAULT '',
    msg_delay         INTEGER DEFAULT 20,
    msg_random_delay  BOOLEAN DEFAULT false,
    pokecoins         BIGINT DEFAULT 0,
    cowoncy           BIGINT DEFAULT 0,
    last_sync         TEXT DEFAULT '',
    balances          JSONB DEFAULT '{}',
    owo_last_run      JSONB DEFAULT '{}',
    slash_last_run    JSONB DEFAULT '{}'
);

-- 2. DEX
CREATE TABLE IF NOT EXISTS dex (
    name          TEXT PRIMARY KEY,
    display_name  TEXT NOT NULL DEFAULT '',
    caught_count  INTEGER DEFAULT 0,
    shiny_count   INTEGER DEFAULT 0,
    first_caught  TIMESTAMPTZ DEFAULT NOW(),
    last_caught   TIMESTAMPTZ DEFAULT NOW(),
    notes         TEXT DEFAULT '',
    favorite      BOOLEAN DEFAULT false,
    img_url       TEXT DEFAULT '',
    caught_by     TEXT DEFAULT ''
);

-- 3. HISTORY
CREATE TABLE IF NOT EXISTS history (
    id             TEXT PRIMARY KEY,
    timestamp      TIMESTAMPTZ DEFAULT NOW(),
    pokemon_name   TEXT NOT NULL DEFAULT '',
    display_name   TEXT DEFAULT '',
    caught_by      TEXT DEFAULT '',
    channel_id     TEXT DEFAULT '',
    success        BOOLEAN DEFAULT true,
    failure_reason TEXT,
    is_shiny       BOOLEAN DEFAULT false,
    hint           TEXT DEFAULT '',
    level          TEXT DEFAULT '1',
    iv             TEXT DEFAULT '??%',
    discord_img    TEXT DEFAULT '',
    is_image_catch BOOLEAN DEFAULT false,
    confidence     FLOAT DEFAULT 0,
    sprite         TEXT DEFAULT '',
    rarity         TEXT DEFAULT 'common'
);

-- 4. BOT CONFIG (single row, id=1)
CREATE TABLE IF NOT EXISTS bot_config (
    id                      INTEGER PRIMARY KEY DEFAULT 1,
    status                  TEXT DEFAULT 'Online',
    caught                  INTEGER DEFAULT 0,
    faults                  INTEGER DEFAULT 0,
    -- spam
    spam_message            TEXT DEFAULT '',
    spam_speed              FLOAT DEFAULT 0.5,
    spam_count              TEXT DEFAULT 'infinity',
    spam_cooldown_after_catch FLOAT DEFAULT 3.0,
    -- owo flags (stored flat for SQL simplicity)
    owo_hunt                BOOLEAN DEFAULT true,
    owo_hunt_cd             INTEGER DEFAULT 100000,
    owo_battle              BOOLEAN DEFAULT true,
    owo_battle_cd           INTEGER DEFAULT 150000,
    owo_daily               BOOLEAN DEFAULT true,
    owo_daily_cd            INTEGER DEFAULT 86400,
    owo_channel_id          TEXT DEFAULT '',
    owo_human_mimicry       BOOLEAN DEFAULT false,
    owo_lootbox             BOOLEAN DEFAULT false,
    owo_lootbox_cd          INTEGER DEFAULT 14400,
    owo_pray                BOOLEAN DEFAULT false,
    owo_pray_cd             INTEGER DEFAULT 300,
    owo_curse               BOOLEAN DEFAULT false,
    owo_curse_cd            INTEGER DEFAULT 300,
    owo_cf                  BOOLEAN DEFAULT false,
    owo_cf_amount           INTEGER DEFAULT 1,
    owo_slots               BOOLEAN DEFAULT false,
    owo_slots_amount        INTEGER DEFAULT 1,
    owo_quest               BOOLEAN DEFAULT false,
    owo_quest_cd            INTEGER DEFAULT 18000,
    owo_buy                 BOOLEAN DEFAULT false,
    owo_buy_cd              INTEGER DEFAULT 3600,
    owo_sell                BOOLEAN DEFAULT false,
    owo_sell_cd             INTEGER DEFAULT 3600,
    owo_sacrifice           BOOLEAN DEFAULT false,
    owo_sacrifice_cd        INTEGER DEFAULT 3600,
    owo_inv                 BOOLEAN DEFAULT true,
    owo_inv_cd              INTEGER DEFAULT 600000,
    owo_equip               BOOLEAN DEFAULT true,
    owo_equip_cd            INTEGER DEFAULT 36000,
    owo_autohunt            BOOLEAN DEFAULT false,
    owo_autohunt_cd         INTEGER DEFAULT 3600,
    owo_owodex              BOOLEAN DEFAULT false,
    owo_owodex_cd           INTEGER DEFAULT 60,
    owo_crate               BOOLEAN DEFAULT false,
    owo_crate_cd            INTEGER DEFAULT 3600,
    owo_battlesetting       BOOLEAN DEFAULT false,
    owo_battlesetting_cd    INTEGER DEFAULT 86400,
    owo_team                BOOLEAN DEFAULT false,
    owo_team_cd             INTEGER DEFAULT 60,
    owo_weapon              BOOLEAN DEFAULT false,
    owo_weapon_cd           INTEGER DEFAULT 60,
    owo_dismantle           BOOLEAN DEFAULT false,
    owo_dismantle_cd        INTEGER DEFAULT 3600,
    owo_lottery             BOOLEAN DEFAULT false,
    owo_lottery_cd          INTEGER DEFAULT 14400,
    owo_blackjack           BOOLEAN DEFAULT false,
    owo_blackjack_cd        INTEGER DEFAULT 15,
    "owo_8b"                BOOLEAN DEFAULT false,
    "owo_8b_cd"             INTEGER DEFAULT 15,
    owo_cookie              BOOLEAN DEFAULT false,
    owo_cookie_cd           INTEGER DEFAULT 300,
    owo_ship                BOOLEAN DEFAULT false,
    owo_ship_cd             INTEGER DEFAULT 60,
    owo_marry               BOOLEAN DEFAULT false,
    owo_marry_cd            INTEGER DEFAULT 86400,
    owo_profile             BOOLEAN DEFAULT false,
    owo_profile_cd          INTEGER DEFAULT 60,
    owo_level               BOOLEAN DEFAULT true,
    owo_level_cd            INTEGER DEFAULT 60090,
    owo_pat                 BOOLEAN DEFAULT false,
    owo_pat_cd              INTEGER DEFAULT 15,
    owo_hug                 BOOLEAN DEFAULT false,
    owo_hug_cd              INTEGER DEFAULT 15,
    owo_kiss                BOOLEAN DEFAULT false,
    owo_kiss_cd             INTEGER DEFAULT 15,
    -- slash
    slash_enabled           BOOLEAN DEFAULT false,
    slash_commands          JSONB DEFAULT '[]',
    -- image/AI
    image_enabled           BOOLEAN DEFAULT true,
    hf_token                TEXT DEFAULT '',
    local_mode              BOOLEAN DEFAULT true,
    local_engine            TEXT DEFAULT 'onnx',
    -- break
    break_enabled           BOOLEAN DEFAULT true,
    break_start_time        TEXT DEFAULT '02:00',
    break_duration          INTEGER DEFAULT 10,
    -- mimic (entire nested config as JSONB)
    mimic                   JSONB DEFAULT '{}',
    -- captcha state
    captcha                 JSONB DEFAULT NULL
);

-- 5. LOGS (rolling event log)
CREATE TABLE IF NOT EXISTS logs (
    id        BIGSERIAL PRIMARY KEY,
    time      TEXT NOT NULL,
    message   TEXT NOT NULL,
    type      TEXT DEFAULT 'info',
    label     TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Keep only last 2000 log rows automatically
CREATE OR REPLACE FUNCTION trim_logs() RETURNS TRIGGER AS $$
BEGIN
    DELETE FROM logs WHERE id IN (
        SELECT id FROM logs ORDER BY id DESC OFFSET 2000
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_trim_logs ON logs;
CREATE TRIGGER trg_trim_logs AFTER INSERT ON logs
FOR EACH ROW EXECUTE FUNCTION trim_logs();

-- ═══════════════════════════════════════════════════════════════
-- STORAGE BUCKETS (create via Supabase Dashboard → Storage)
-- Bucket 1: pokemon_profiles   (public)
-- Bucket 2: pokemon_images     (public)
-- ═══════════════════════════════════════════════════════════════
