-- KAIZER K5 Supabase Schema Update
-- Run this in your Supabase SQL Editor

-- 1. Alter existing `guild_settings` to add new dashboard columns (safely, won't ruin old stuff)
ALTER TABLE guild_settings 
ADD COLUMN IF NOT EXISTS language VARCHAR DEFAULT 'en',
ADD COLUMN IF NOT EXISTS embed_color VARCHAR DEFAULT '#0affe4',
ADD COLUMN IF NOT EXISTS dj_role VARCHAR,
ADD COLUMN IF NOT EXISTS admin_roles JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS mod_roles JSONB DEFAULT '[]'::jsonb,

-- Welcome & Goodbye
ADD COLUMN IF NOT EXISTS welcome_enabled BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS welcome_channel VARCHAR,
ADD COLUMN IF NOT EXISTS welcome_message TEXT DEFAULT 'Welcome {user} to {server}!',
ADD COLUMN IF NOT EXISTS goodbye_enabled BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS goodbye_channel VARCHAR,
ADD COLUMN IF NOT EXISTS goodbye_message TEXT DEFAULT '{user} left the server.',

-- Leveling
ADD COLUMN IF NOT EXISTS leveling_enabled BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS xp_rate FLOAT DEFAULT 1.0,
ADD COLUMN IF NOT EXISTS level_up_message_enabled BOOLEAN DEFAULT true,
ADD COLUMN IF NOT EXISTS level_up_channel VARCHAR,
ADD COLUMN IF NOT EXISTS level_up_message TEXT DEFAULT 'GG {user}, you leveled up to level {level}!',
ADD COLUMN IF NOT EXISTS xp_blacklist_channels JSONB DEFAULT '[]'::jsonb,

-- Logging
ADD COLUMN IF NOT EXISTS logging_enabled BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS log_channel VARCHAR,
ADD COLUMN IF NOT EXISTS log_events JSONB DEFAULT '{"message_delete": true, "message_edit": true, "member_join": true}'::jsonb,

-- Moderation Settings
ADD COLUMN IF NOT EXISTS automod_rules JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS warn_thresholds JSONB DEFAULT '{"3": "mute", "5": "kick", "10": "ban"}'::jsonb,
ADD COLUMN IF NOT EXISTS mute_role VARCHAR,
ADD COLUMN IF NOT EXISTS mod_log_channel VARCHAR,

-- Tickets
ADD COLUMN IF NOT EXISTS ticket_enabled BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS ticket_category VARCHAR,
ADD COLUMN IF NOT EXISTS ticket_support_role VARCHAR,
ADD COLUMN IF NOT EXISTS ticket_log_channel VARCHAR,
ADD COLUMN IF NOT EXISTS ticket_limit INT DEFAULT 1,
ADD COLUMN IF NOT EXISTS ticket_panel_message TEXT DEFAULT 'Click the button below to open a support ticket.';

-- 2. Create `command_configs` table
CREATE TABLE IF NOT EXISTS command_configs (
    guild_id VARCHAR NOT NULL,
    command_name VARCHAR NOT NULL,
    enabled BOOLEAN DEFAULT true,
    permission_level VARCHAR DEFAULT 'Everyone', -- 'Everyone', 'Mod', 'Admin', 'Owner'
    cooldown INT DEFAULT 0,
    allowed_channels JSONB DEFAULT '[]'::jsonb,
    allowed_roles JSONB DEFAULT '[]'::jsonb,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    PRIMARY KEY (guild_id, command_name)
);

-- 3. Create `reaction_roles` table
CREATE TABLE IF NOT EXISTS reaction_roles (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    guild_id VARCHAR NOT NULL,
    message_id VARCHAR NOT NULL,
    channel_id VARCHAR NOT NULL,
    emoji VARCHAR NOT NULL,
    role_id VARCHAR NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    UNIQUE(guild_id, message_id, emoji)
);

-- 4. Create `custom_commands` table
CREATE TABLE IF NOT EXISTS custom_commands (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    guild_id VARCHAR NOT NULL,
    trigger_word VARCHAR NOT NULL,
    response_text TEXT NOT NULL,
    permission_level VARCHAR DEFAULT 'Everyone',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    UNIQUE(guild_id, trigger_word)
);

-- 5. Create `giveaways` table
CREATE TABLE IF NOT EXISTS giveaways (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    guild_id VARCHAR NOT NULL,
    channel_id VARCHAR NOT NULL,
    message_id VARCHAR NOT NULL,
    host_id VARCHAR NOT NULL,
    prize VARCHAR NOT NULL,
    winners_count INT DEFAULT 1,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    is_ended BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);
