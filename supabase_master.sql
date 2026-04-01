-- Kaizo MASTER SUPABASE SCHEMA
-- Copy and paste this entirely into the Supabase SQL Editor and run it.

-- 1. Create or replace `guild_settings` table
CREATE TABLE IF NOT EXISTS guild_settings (
    guild_id VARCHAR PRIMARY KEY,
    guild_name VARCHAR,
    
    -- Anti-Nuke Settings
    anti_ban_limit INT DEFAULT 3,
    anti_ban_time_frame INT DEFAULT 60,
    anti_kick_limit INT DEFAULT 3,
    anti_kick_time_frame INT DEFAULT 60,
    anti_channel_delete_limit INT DEFAULT 2,
    anti_channel_delete_time_frame INT DEFAULT 60,
    anti_role_delete_limit INT DEFAULT 2,
    anti_role_delete_time_frame INT DEFAULT 60,
    anti_bot_add BOOLEAN DEFAULT true,
    is_active BOOLEAN DEFAULT true,
    
    -- General Settings
    prefix VARCHAR DEFAULT 'k!',
    language VARCHAR DEFAULT 'en',
    embed_color VARCHAR DEFAULT '#0affe4',
    dj_role VARCHAR,
    admin_roles JSONB DEFAULT '[]'::jsonb,
    mod_roles JSONB DEFAULT '[]'::jsonb,

    -- Welcome & Goodbye
    welcome_enabled BOOLEAN DEFAULT false,
    welcome_channel VARCHAR,
    welcome_message TEXT DEFAULT 'Welcome {user} to {server}!',
    goodbye_enabled BOOLEAN DEFAULT false,
    goodbye_channel VARCHAR,
    goodbye_message TEXT DEFAULT '{user} left the server.',

    -- Leveling
    leveling_enabled BOOLEAN DEFAULT false,
    xp_rate FLOAT DEFAULT 1.0,
    level_up_message_enabled BOOLEAN DEFAULT true,
    level_up_channel VARCHAR,
    level_up_message TEXT DEFAULT 'GG {user}, you leveled up to level {level}!',
    xp_blacklist_channels JSONB DEFAULT '[]'::jsonb,

    -- Logging
    logging_enabled BOOLEAN DEFAULT false,
    log_channel VARCHAR,
    log_events JSONB DEFAULT '{"message_delete": true, "message_edit": true, "member_join": true}'::jsonb,

    -- Moderation Settings
    k4_defence_enabled BOOLEAN DEFAULT false,
    automod_rules JSONB DEFAULT '{}'::jsonb,
    warn_thresholds JSONB DEFAULT '{"3": "mute", "5": "kick", "10": "ban"}'::jsonb,
    mute_role VARCHAR,
    mod_log_channel VARCHAR,

    -- Tickets
    ticket_enabled BOOLEAN DEFAULT false,
    ticket_category VARCHAR,
    ticket_support_role VARCHAR,
    ticket_log_channel VARCHAR,
    ticket_limit INT DEFAULT 1,
    ticket_panel_message TEXT DEFAULT 'Click the button below to open a support ticket.',

    -- Live Stats Counters
    counter_style VARCHAR DEFAULT 'dot',
    counter_refresh_interval INT DEFAULT 10,
    counter_category_id VARCHAR,
    counter_tracked_vc_id VARCHAR,
    counter_total_chan_id VARCHAR,
    counter_total_fmt VARCHAR DEFAULT 'Total: {count}',
    counter_online_chan_id VARCHAR,
    counter_online_fmt VARCHAR DEFAULT 'Online: {count}',
    counter_offline_chan_id VARCHAR,
    counter_offline_fmt VARCHAR DEFAULT 'Offline: {count}',
    counter_invc_chan_id VARCHAR,
    counter_invc_fmt VARCHAR DEFAULT 'In VC: {count}',

    -- Temp VC
    temp_vc_lobby VARCHAR,
    temp_vc_category VARCHAR,
    temp_vc_name_format VARCHAR DEFAULT '{user}''s Lounge',
    temp_vc_limit INT DEFAULT 0,
    temp_vc_locked BOOLEAN DEFAULT false
);

-- 2. Create `guild_whitelist` table
CREATE TABLE IF NOT EXISTS guild_whitelist (
    guild_id VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL,
    reason TEXT DEFAULT 'No reason provided',
    executor_tag VARCHAR DEFAULT 'System',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    PRIMARY KEY (guild_id, user_id)
);

-- 3. Create `protection_logs` table
CREATE TABLE IF NOT EXISTS protection_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    guild_id VARCHAR NOT NULL,
    event_type VARCHAR NOT NULL,
    executor_id VARCHAR NOT NULL,
    executor_tag VARCHAR DEFAULT 'Unknown',
    action_taken VARCHAR NOT NULL,
    details TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- 4. Create `command_configs` table
CREATE TABLE IF NOT EXISTS command_configs (
    guild_id VARCHAR NOT NULL,
    command_name VARCHAR NOT NULL,
    enabled BOOLEAN DEFAULT true,
    permission_level VARCHAR DEFAULT 'Everyone',
    cooldown INT DEFAULT 0,
    allowed_channels JSONB DEFAULT '[]'::jsonb,
    allowed_roles JSONB DEFAULT '[]'::jsonb,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    PRIMARY KEY (guild_id, command_name)
);

-- 5. Create `reaction_roles` table
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

-- 6. Create `custom_commands` table
CREATE TABLE IF NOT EXISTS custom_commands (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    guild_id VARCHAR NOT NULL,
    trigger_word VARCHAR NOT NULL,
    response_text TEXT NOT NULL,
    permission_level VARCHAR DEFAULT 'Everyone',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    UNIQUE(guild_id, trigger_word)
);

-- 7. Create `giveaways` table
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

-- 8. Alter existing tables if they already exist to ensure columns are present
-- (This ensures you don't lose data if you re-run this)
DO $$
BEGIN
    BEGIN
        ALTER TABLE guild_settings ADD COLUMN counter_style VARCHAR DEFAULT 'dot';
        ALTER TABLE guild_settings ADD COLUMN counter_refresh_interval INT DEFAULT 10;
        ALTER TABLE guild_settings ADD COLUMN counter_category_id VARCHAR;
        ALTER TABLE guild_settings ADD COLUMN counter_tracked_vc_id VARCHAR;
        ALTER TABLE guild_settings ADD COLUMN counter_total_chan_id VARCHAR;
        ALTER TABLE guild_settings ADD COLUMN counter_total_fmt VARCHAR DEFAULT 'Total: {count}';
        ALTER TABLE guild_settings ADD COLUMN counter_online_chan_id VARCHAR;
        ALTER TABLE guild_settings ADD COLUMN counter_online_fmt VARCHAR DEFAULT 'Online: {count}';
        ALTER TABLE guild_settings ADD COLUMN counter_offline_chan_id VARCHAR;
        ALTER TABLE guild_settings ADD COLUMN counter_offline_fmt VARCHAR DEFAULT 'Offline: {count}';
        ALTER TABLE guild_settings ADD COLUMN counter_invc_chan_id VARCHAR;
        ALTER TABLE guild_settings ADD COLUMN counter_invc_fmt VARCHAR DEFAULT 'In VC: {count}';
        ALTER TABLE guild_settings ADD COLUMN temp_vc_lobby VARCHAR;
        ALTER TABLE guild_settings ADD COLUMN temp_vc_category VARCHAR;
        ALTER TABLE guild_settings ADD COLUMN temp_vc_name_format VARCHAR DEFAULT '{user}''s Lounge';
        ALTER TABLE guild_settings ADD COLUMN temp_vc_limit INT DEFAULT 0;
        ALTER TABLE guild_settings ADD COLUMN temp_vc_locked BOOLEAN DEFAULT false;
    EXCEPTION
        WHEN duplicate_column THEN null;
    END;
END $$;

-- 9. Create `economy_users` table
CREATE TABLE IF NOT EXISTS economy_users (
    user_id VARCHAR NOT NULL,
    guild_id VARCHAR NOT NULL,
    wallet BIGINT DEFAULT 0,
    bank BIGINT DEFAULT 0,
    last_daily TIMESTAMP WITH TIME ZONE,
    last_weekly TIMESTAMP WITH TIME ZONE,
    last_monthly TIMESTAMP WITH TIME ZONE,
    last_work TIMESTAMP WITH TIME ZONE,
    last_rob TIMESTAMP WITH TIME ZONE,
    last_crime TIMESTAMP WITH TIME ZONE,
    last_fish TIMESTAMP WITH TIME ZONE,
    last_hunt TIMESTAMP WITH TIME ZONE,
    last_mine TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (user_id, guild_id)
);

-- 10. Create `economy_shop` table
CREATE TABLE IF NOT EXISTS economy_shop (
    item_id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    guild_id VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    description TEXT,
    price BIGINT NOT NULL,
    type VARCHAR DEFAULT 'collectable',
    role_id VARCHAR,
    emoji VARCHAR,
    stock INT DEFAULT -1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- 11. Create `economy_inventory` table
CREATE TABLE IF NOT EXISTS economy_inventory (
    user_id VARCHAR NOT NULL,
    guild_id VARCHAR NOT NULL,
    item_id UUID NOT NULL REFERENCES economy_shop(item_id) ON DELETE CASCADE,
    quantity INT DEFAULT 1,
    PRIMARY KEY (user_id, guild_id, item_id)
);

-- 12. Create `music_playlists` table
CREATE TABLE IF NOT EXISTS music_playlists (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    share_code VARCHAR UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    UNIQUE(user_id, name)
);

-- 13. Create `music_playlist_tracks` table
CREATE TABLE IF NOT EXISTS music_playlist_tracks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    playlist_id UUID NOT NULL REFERENCES music_playlists(id) ON DELETE CASCADE,
    title VARCHAR NOT NULL,
    url VARCHAR NOT NULL,
    duration INT,
    position INT NOT NULL
);

-- 14. Create `temp_voice_channels` table
CREATE TABLE IF NOT EXISTS temp_voice_channels (
    channel_id VARCHAR PRIMARY KEY,
    guild_id VARCHAR NOT NULL,
    owner_id VARCHAR NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- 15. Create `leveling_users` table
CREATE TABLE IF NOT EXISTS leveling_users (
    guild_id VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL,
    xp INT DEFAULT 0,
    level INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    PRIMARY KEY (guild_id, user_id)
);
