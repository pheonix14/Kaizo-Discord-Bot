-- ═══════════════════════════════════════════════════════════════════
-- ADDITIONAL TABLES FOR DISCORD MEMBER & SERVER PROFILE SCANNER
-- Run this entire block in your Supabase SQL Editor.
-- All statements are NON-DESTRUCTIVE (IF NOT EXISTS / OR REPLACE).
-- ═══════════════════════════════════════════════════════════════════

-- ── 1. TABLES ─────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS scanned_guilds (
    id           TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    icon         TEXT,
    invite_link  TEXT,
    last_scanned TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS scanned_users (
    id             TEXT PRIMARY KEY,
    username       TEXT NOT NULL,
    avatar         TEXT,
    bio            TEXT,
    custom_status  TEXT,
    status         TEXT DEFAULT 'offline',
    bot            BOOLEAN DEFAULT false,
    past_usernames JSONB DEFAULT '[]',
    past_bios      JSONB DEFAULT '[]',
    updated_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS scanned_members (
    id             TEXT PRIMARY KEY,  -- format: guild_id:user_id
    user_id        TEXT NOT NULL,
    guild_id       TEXT NOT NULL,
    nickname       TEXT,
    joined_at      TEXT,              -- stored as text/ISO string
    roles          JSONB DEFAULT '[]',
    past_nicknames JSONB DEFAULT '[]',
    last_seen      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS scan_config (
    id              INTEGER PRIMARY KEY DEFAULT 1,
    auto_scan       BOOLEAN DEFAULT false,
    selected_tokens JSONB DEFAULT '[]',
    priority_guilds JSONB DEFAULT '[]',
    last_auto_scan  TIMESTAMPTZ
);

-- ── 2. PERFORMANCE INDEXES (non-destructive) ──────────────────────

CREATE INDEX IF NOT EXISTS idx_scanned_users_updated_at
    ON scanned_users (updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_scanned_users_username
    ON scanned_users (username);

CREATE INDEX IF NOT EXISTS idx_scanned_members_user_id
    ON scanned_members (user_id);

CREATE INDEX IF NOT EXISTS idx_scanned_members_guild_id
    ON scanned_members (guild_id);

CREATE INDEX IF NOT EXISTS idx_scanned_members_last_seen
    ON scanned_members (last_seen DESC);

-- ── 3. RLS — enable but allow service_role full access ────────────
-- Your app uses the service_role key which bypasses RLS automatically.
-- These policies ensure anon/authenticated users can't read the data.

ALTER TABLE scanned_guilds  ENABLE ROW LEVEL SECURITY;
ALTER TABLE scanned_users   ENABLE ROW LEVEL SECURITY;
ALTER TABLE scanned_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE scan_config     ENABLE ROW LEVEL SECURITY;

-- Create policies only if they don't already exist.
-- Uses exception handling — NEVER drops existing policies.
DO $$
BEGIN
    -- scanned_guilds
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename  = 'scanned_guilds'
          AND policyname = 'service_role_all_scanned_guilds'
    ) THEN
        EXECUTE 'CREATE POLICY "service_role_all_scanned_guilds"
            ON scanned_guilds FOR ALL TO service_role
            USING (true) WITH CHECK (true)';
    END IF;

    -- scanned_users
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename  = 'scanned_users'
          AND policyname = 'service_role_all_scanned_users'
    ) THEN
        EXECUTE 'CREATE POLICY "service_role_all_scanned_users"
            ON scanned_users FOR ALL TO service_role
            USING (true) WITH CHECK (true)';
    END IF;

    -- scanned_members
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename  = 'scanned_members'
          AND policyname = 'service_role_all_scanned_members'
    ) THEN
        EXECUTE 'CREATE POLICY "service_role_all_scanned_members"
            ON scanned_members FOR ALL TO service_role
            USING (true) WITH CHECK (true)';
    END IF;

    -- scan_config
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename  = 'scan_config'
          AND policyname = 'service_role_all_scan_config'
    ) THEN
        EXECUTE 'CREATE POLICY "service_role_all_scan_config"
            ON scan_config FOR ALL TO service_role
            USING (true) WITH CHECK (true)';
    END IF;
END
$$;

-- ── 4. REFRESH POSTGREST SCHEMA CACHE ────────────────────────────
-- Must run after creating new tables so PostgREST can see them.
NOTIFY pgrst, 'reload schema';

