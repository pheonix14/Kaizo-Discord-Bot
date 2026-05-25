-- Project Kaizer K5 Database Schema
-- Run this in your Supabase SQL Editor to initialize the database tables and RLS policies.

-- Enable UUID extension if not already enabled
create extension if not exists "uuid-ossp";

-- 1. Bot Configuration Table (Global credentials)
create table if not exists public.bot_config (
    id uuid default uuid_generate_v4() primary key,
    bot_token text not null,
    client_id text not null,
    client_secret text,
    public_key text,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable RLS for bot_config
alter table public.bot_config enable row level security;

-- Policy: Only service_role can access (normal client keys are blocked)
drop policy if exists "Service role bypass for bot_config" on public.bot_config;
create policy "Service role bypass for bot_config" 
on public.bot_config 
for all 
using (auth.role() = 'service_role');


-- 2. Guild Settings Table (Anti-Nuke limits & Feature configurations)
create table if not exists public.guild_settings (
    guild_id text primary key, -- Discord Guild ID (snowflake)
    guild_name text,
    
    -- Anti-Nuke configurations
    anti_ban_limit integer default 3,
    anti_ban_time_frame integer default 60, -- in seconds
    anti_kick_limit integer default 3,
    anti_kick_time_frame integer default 60,
    anti_channel_delete_limit integer default 2,
    anti_channel_delete_time_frame integer default 60,
    anti_role_delete_limit integer default 2,
    anti_role_delete_time_frame integer default 60,
    anti_bot_add boolean default true,
    quarantine_role_id text,
    
    -- Welcome & Goodbye configurations
    welcome_enabled boolean default false,
    welcome_channel text,
    welcome_message text,
    goodbye_enabled boolean default false,
    goodbye_channel text,
    goodbye_message text,
    
    -- Logging configurations
    logging_enabled boolean default false,
    log_channel text,
    log_events text[] default '{}'::text[],
    mod_log_channel text,
    
    -- Roles & Moderation configurations
    admin_roles text[] default '{}'::text[],
    mod_roles text[] default '{}'::text[],
    mute_role text,
    dj_role text,
    language text default 'en',
    embed_color text default '#0affe4',
    warn_thresholds jsonb default '{}'::jsonb,
    
    -- Leveling configurations
    leveling_enabled boolean default false,
    level_up_channel text,
    level_up_message text default 'GG {user}, you level up to **{level}**!',
    level_up_message_enabled boolean default true,
    xp_blacklist_channels text[] default '{}'::text[],
    xp_rate integer default 1,
    level_roles jsonb default '{}'::jsonb,
    level_permissions jsonb default '[]'::jsonb,
    
    -- AutoMod rules configuration
    automod_rules jsonb default '{}'::jsonb,
    
    -- Live User Counter configurations
    counter_category_id text,
    counter_total_chan_id text,
    counter_online_chan_id text,
    counter_offline_chan_id text,
    counter_invc_chan_id text,
    counter_style text default 'minimal', -- 'minimal', 'detailed', 'custom'
    counter_refresh_interval text default '7d', -- '1h', '6h', '7d'
    counter_total_fmt text default 'members: {count}',
    counter_online_fmt text default 'online: {online}',
    counter_offline_fmt text default 'offline: {offline}',
    counter_invc_fmt text default 'in vc: {invc}',
    counter_tracked_vc_id text,
    
    -- Temp VC configurations
    temp_vc_category text,
    temp_vc_lobby text,
    temp_vc_limit integer default 0,
    temp_vc_locked boolean default false,
    temp_vc_name_format text default '{user}''s VC',
    
    -- Ticket configurations
    ticket_enabled boolean default false,
    ticket_category text,
    ticket_limit integer default 1,
    ticket_log_channel text,
    ticket_panel_message text,
    ticket_support_role text,

    k4_defence_enabled boolean default false,
    admin_role_id text,
    auto_roles text[] default '{}'::text[],
    booster_role_id text,
    currency_name text default 'credits',
    currency_emoji text default '🪙',
    log_channel_id text,
    welcome_channel_id text,
    leave_channel_id text,

    is_active boolean default true,
    updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable RLS for guild_settings
alter table public.guild_settings enable row level security;

-- Policy: Only service_role can access (dashboard API handles user verification)
drop policy if exists "Service role bypass for guild_settings" on public.guild_settings;
create policy "Service role bypass for guild_settings" 
on public.guild_settings 
for all 
using (auth.role() = 'service_role');


-- 3. Guild Whitelist Table (Users immune to anti-nuke actions)
create table if not exists public.guild_whitelist (
    id uuid default uuid_generate_v4() primary key,
    guild_id text references public.guild_settings(guild_id) on delete cascade not null,
    user_id text not null, -- Whitelisted Discord User ID
    executor_tag text,
    reason text,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    unique(guild_id, user_id)
);

-- Enable RLS for guild_whitelist
alter table public.guild_whitelist enable row level security;

-- Policy: Only service_role can access
drop policy if exists "Service role bypass for guild_whitelist" on public.guild_whitelist;
create policy "Service role bypass for guild_whitelist" 
on public.guild_whitelist 
for all 
using (auth.role() = 'service_role');


-- 4. Protection Logs Table (Audit trail of security incidents)
create table if not exists public.protection_logs (
    id uuid default uuid_generate_v4() primary key,
    guild_id text not null,
    event_type text not null, -- e.g., 'MASS_BAN', 'CHANNEL_DELETE', 'BOT_ADD'
    executor_id text not null, -- Discord ID of user triggering the nuke behavior
    executor_tag text,
    action_taken text not null, -- e.g., 'BANNED_EXECUTOR', 'QUARANTINED', 'RESTORED_CHANNEL'
    details text,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable RLS for protection_logs
alter table public.protection_logs enable row level security;

-- Policy: Only service_role can access
drop policy if exists "Service role bypass for protection_logs" on public.protection_logs;
create policy "Service role bypass for protection_logs" 
on public.protection_logs 
for all 
using (auth.role() = 'service_role');

-- 5. Playlists Table
create table if not exists public.playlists (
    id uuid default uuid_generate_v4() primary key,
    guild_id text not null,
    user_id text not null,
    name text not null,
    tracks jsonb not null default '[]'::jsonb,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    unique(guild_id, name)
);

-- Enable RLS for playlists
alter table public.playlists enable row level security;

-- Policy: Only service_role can access
drop policy if exists "Service role bypass for playlists" on public.playlists;
create policy "Service role bypass for playlists" 
on public.playlists 
for all 
using (auth.role() = 'service_role');


-- 6. Live User Counter Table
create table if not exists public.guild_counters (
    guild_id text primary key,
    category_id text,
    total_channel_id text,
    online_channel_id text,
    offline_channel_id text,
    invc_channel_id text,
    style text default 'minimal', -- 'minimal', 'detailed', 'custom'
    refresh_interval text default '7d', -- '1h', '6h', '7d'
    total_format text default 'members: {count}',
    online_format text default 'online: {online}',
    offline_format text default 'offline: {offline}',
    invc_format text default 'in vc: {invc}',
    tracked_vc_id text,
    updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable RLS for guild_counters
alter table public.guild_counters enable row level security;

-- Policy: Only service_role can access
drop policy if exists "Service role bypass for guild_counters" on public.guild_counters;
create policy "Service role bypass for guild_counters" 
on public.guild_counters 
for all 
using (auth.role() = 'service_role');


-- 7. Temp VC Settings Table
create table if not exists public.temp_vc_settings (
    guild_id text primary key,
    lobby_channel_id text not null,
    category_id text not null,
    default_limit integer default 0,
    default_name_format text default '{user}''s VC',
    default_locked boolean default false,
    updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable RLS for temp_vc_settings
alter table public.temp_vc_settings enable row level security;

-- Policy: Only service_role can access
drop policy if exists "Service role bypass for temp_vc_settings" on public.temp_vc_settings;
create policy "Service role bypass for temp_vc_settings" 
on public.temp_vc_settings 
for all 
using (auth.role() = 'service_role');


-- 8. Active Temp VCs Table
create table if not exists public.active_temp_vcs (
    channel_id text primary key,
    guild_id text not null,
    owner_id text not null,
    is_locked boolean default false,
    is_hidden boolean default false,
    allowed_users jsonb not null default '[]'::jsonb,
    banned_users jsonb not null default '[]'::jsonb,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable RLS for active_temp_vcs
alter table public.active_temp_vcs enable row level security;

-- Policy: Only service_role can access
drop policy if exists "Service role bypass for active_temp_vcs" on public.active_temp_vcs;
create policy "Service role bypass for active_temp_vcs" 
on public.active_temp_vcs 
for all 
using (auth.role() = 'service_role');


-- 9. Decoration Backups Table
create table if not exists public.decor_backups (
    id uuid default uuid_generate_v4() primary key,
    guild_id text not null,
    channels_backup jsonb not null default '[]'::jsonb,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable RLS for decor_backups
alter table public.decor_backups enable row level security;

-- Policy: Only service_role can access
drop policy if exists "Service role bypass for decor_backups" on public.decor_backups;
create policy "Service role bypass for decor_backups" 
on public.decor_backups 
for all 
using (auth.role() = 'service_role');

-- MIGRATION: Add columns if they do not exist
ALTER TABLE public.guild_settings ADD COLUMN IF NOT EXISTS level_roles jsonb DEFAULT '{}'::jsonb;
ALTER TABLE public.guild_settings ADD COLUMN IF NOT EXISTS level_permissions jsonb DEFAULT '[]'::jsonb;
ALTER TABLE public.guild_settings ADD COLUMN IF NOT EXISTS ticket_log_channel text;

-- 10. Custom Commands Table
CREATE TABLE IF NOT EXISTS public.custom_commands (
    guild_id text NOT NULL,
    trigger_word text NOT NULL,
    response_text text NOT NULL,
    permission_level text DEFAULT 'Everyone',
    image_url text,
    gif_url text,
    PRIMARY KEY (guild_id, trigger_word)
);

-- Enable RLS for custom_commands
ALTER TABLE public.custom_commands ENABLE ROW LEVEL SECURITY;

-- Policy: Only service_role can access
DROP POLICY IF EXISTS "Service role bypass for custom_commands" ON public.custom_commands;
CREATE POLICY "Service role bypass for custom_commands" 
ON public.custom_commands 
FOR ALL 
USING (auth.role() = 'service_role');

-- MIGRATION: Add custom_commands columns if they do not exist
ALTER TABLE public.custom_commands ADD COLUMN IF NOT EXISTS permission_level text DEFAULT 'Everyone';
ALTER TABLE public.custom_commands ADD COLUMN IF NOT EXISTS image_url text;
ALTER TABLE public.custom_commands ADD COLUMN IF NOT EXISTS gif_url text;

-- 11. Giveaways Table
CREATE TABLE IF NOT EXISTS public.giveaways (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    guild_id text NOT NULL,
    channel_id text NOT NULL,
    message_id text NOT NULL DEFAULT 'pending',
    host_id text NOT NULL,
    prize text NOT NULL,
    winners_count integer DEFAULT 1,
    start_time timestamp with time zone DEFAULT timezone('utc'::text, now()),
    end_time timestamp with time zone NOT NULL,
    restrict_roles_enabled boolean DEFAULT false,
    allowed_roles jsonb DEFAULT '[]'::jsonb,
    roles_mode text DEFAULT 'any',
    roles_reverse boolean DEFAULT false,
    animation_style text DEFAULT 'scrolling_wheel',
    embed_config jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable RLS for giveaways
ALTER TABLE public.giveaways ENABLE ROW LEVEL SECURITY;

-- Policy: Only service_role can access
DROP POLICY IF EXISTS "Service role bypass for giveaways" ON public.giveaways;
CREATE POLICY "Service role bypass for giveaways" 
ON public.giveaways 
FOR ALL 
USING (auth.role() = 'service_role');

-- MIGRATION: Add giveaways columns if they do not exist
ALTER TABLE public.giveaways ADD COLUMN IF NOT EXISTS start_time timestamp with time zone DEFAULT timezone('utc'::text, now());
ALTER TABLE public.giveaways ADD COLUMN IF NOT EXISTS restrict_roles_enabled boolean DEFAULT false;
ALTER TABLE public.giveaways ADD COLUMN IF NOT EXISTS allowed_roles jsonb DEFAULT '[]'::jsonb;
ALTER TABLE public.giveaways ADD COLUMN IF NOT EXISTS roles_mode text DEFAULT 'any';
ALTER TABLE public.giveaways ADD COLUMN IF NOT EXISTS roles_reverse boolean DEFAULT false;
ALTER TABLE public.giveaways ADD COLUMN IF NOT EXISTS animation_style text DEFAULT 'scrolling_wheel';
ALTER TABLE public.giveaways ADD COLUMN IF NOT EXISTS embed_config jsonb DEFAULT '{}'::jsonb;

-- Note: Participants list is synchronized directly inside the embed_config JSONB field (embed_config->'participants') and ended state under (embed_config->'ended') for backward compatibility.

-- MIGRATION: Add prefix column to guild_settings if it does not exist
ALTER TABLE public.guild_settings ADD COLUMN IF NOT EXISTS prefix text DEFAULT 'k!, !';


-- 12. Command Configurations Table (Permission overrides & granular switches)
CREATE TABLE IF NOT EXISTS public.command_configs (
    guild_id text NOT NULL,
    command_name text NOT NULL,
    enabled boolean DEFAULT true,
    permission_level text DEFAULT 'Everyone',
    allowed_roles text[] DEFAULT '{}'::text[],
    allowed_channels text[] DEFAULT '{}'::text[],
    PRIMARY KEY (guild_id, command_name)
);

-- Enable RLS for command_configs
ALTER TABLE public.command_configs ENABLE ROW LEVEL SECURITY;

-- Policy for Service Role bypass
DROP POLICY IF EXISTS "Service role bypass for command_configs" ON public.command_configs;
CREATE POLICY "Service role bypass for command_configs" 
ON public.command_configs 
FOR ALL 
USING (auth.role() = 'service_role');


-- 13. Economy Users Table (Balances & persistent cooldowns)
CREATE TABLE IF NOT EXISTS public.economy_users (
    guild_id text NOT NULL,
    user_id text NOT NULL,
    wallet bigint DEFAULT 0,
    bank bigint DEFAULT 0,
    last_daily text,
    last_weekly text,
    last_monthly text,
    last_work text,
    last_crime text,
    last_rob text,
    last_fish text,
    last_hunt text,
    last_mine text,
    PRIMARY KEY (guild_id, user_id)
);

-- Enable RLS for economy_users
ALTER TABLE public.economy_users ENABLE ROW LEVEL SECURITY;

-- Policy for Service Role bypass
DROP POLICY IF EXISTS "Service role bypass for economy_users" ON public.economy_users;
CREATE POLICY "Service role bypass for economy_users" 
ON public.economy_users 
FOR ALL 
USING (auth.role() = 'service_role');


-- 14. Economy Shop Table (Purchasable shop registers)
CREATE TABLE IF NOT EXISTS public.economy_shop (
    item_id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    guild_id text NOT NULL,
    name text NOT NULL,
    price integer NOT NULL,
    type text DEFAULT 'item',
    role_id text,
    emoji text,
    description text,
    created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable RLS for economy_shop
ALTER TABLE public.economy_shop ENABLE ROW LEVEL SECURITY;

-- Policy for Service Role bypass
DROP POLICY IF EXISTS "Service role bypass for economy_shop" ON public.economy_shop;
CREATE POLICY "Service role bypass for economy_shop" 
ON public.economy_shop 
FOR ALL 
USING (auth.role() = 'service_role');


-- 15. Economy Inventory Table (User inventories mapping)
CREATE TABLE IF NOT EXISTS public.economy_inventory (
    guild_id text NOT NULL,
    user_id text NOT NULL,
    item_id uuid REFERENCES public.economy_shop(item_id) ON DELETE CASCADE NOT NULL,
    quantity integer DEFAULT 1,
    PRIMARY KEY (guild_id, user_id, item_id)
);

-- Enable RLS for economy_inventory
ALTER TABLE public.economy_inventory ENABLE ROW LEVEL SECURITY;

-- Policy for Service Role bypass
DROP POLICY IF EXISTS "Service role bypass for economy_inventory" ON public.economy_inventory;
CREATE POLICY "Service role bypass for economy_inventory" 
ON public.economy_inventory 
FOR ALL 
USING (auth.role() = 'service_role');


-- 16. Leveling Users Table
CREATE TABLE IF NOT EXISTS public.leveling_users (
    guild_id text NOT NULL,
    user_id text NOT NULL,
    xp bigint DEFAULT 0,
    level integer DEFAULT 0,
    PRIMARY KEY (guild_id, user_id)
);

ALTER TABLE public.leveling_users ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Service role bypass for leveling_users" ON public.leveling_users;
CREATE POLICY "Service role bypass for leveling_users" 
ON public.leveling_users 
FOR ALL 
USING (auth.role() = 'service_role');


-- 17. Music Playlists Table
CREATE TABLE IF NOT EXISTS public.music_playlists (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id text NOT NULL,
    name text NOT NULL,
    created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(user_id, name)
);

ALTER TABLE public.music_playlists ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Service role bypass for music_playlists" ON public.music_playlists;
CREATE POLICY "Service role bypass for music_playlists" 
ON public.music_playlists 
FOR ALL 
USING (auth.role() = 'service_role');


-- 18. Music Playlist Tracks Table
CREATE TABLE IF NOT EXISTS public.music_playlist_tracks (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    playlist_id uuid REFERENCES public.music_playlists(id) ON DELETE CASCADE NOT NULL,
    title text NOT NULL,
    url text NOT NULL,
    duration integer NOT NULL,
    position integer NOT NULL,
    created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);

ALTER TABLE public.music_playlist_tracks ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Service role bypass for music_playlist_tracks" ON public.music_playlist_tracks;
CREATE POLICY "Service role bypass for music_playlist_tracks" 
ON public.music_playlist_tracks 
FOR ALL 
USING (auth.role() = 'service_role');


-- 19. Reaction Roles Table
CREATE TABLE IF NOT EXISTS public.reaction_roles (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    guild_id text NOT NULL,
    channel_id text NOT NULL,
    message_id text NOT NULL,
    emoji text NOT NULL,
    role_id text NOT NULL,
    created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(guild_id, message_id, emoji)
);

ALTER TABLE public.reaction_roles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Service role bypass for reaction_roles" ON public.reaction_roles;
CREATE POLICY "Service role bypass for reaction_roles" 
ON public.reaction_roles 
FOR ALL 
USING (auth.role() = 'service_role');


-- 20. Temp Voice Channels Table
CREATE TABLE IF NOT EXISTS public.temp_voice_channels (
    channel_id text PRIMARY KEY,
    guild_id text NOT NULL,
    owner_id text NOT NULL,
    created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);

ALTER TABLE public.temp_voice_channels ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Service role bypass for temp_voice_channels" ON public.temp_voice_channels;
CREATE POLICY "Service role bypass for temp_voice_channels" 
ON public.temp_voice_channels 
FOR ALL 
USING (auth.role() = 'service_role');


-- 21. Awake Telemetry Table
CREATE TABLE IF NOT EXISTS public.awake_telemetry (
    node_url text PRIMARY KEY,
    label text,
    last_seen text,
    ping_count integer DEFAULT 0,
    peers jsonb DEFAULT '[]'::jsonb,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);

ALTER TABLE public.awake_telemetry ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Service role bypass for awake_telemetry" ON public.awake_telemetry;
CREATE POLICY "Service role bypass for awake_telemetry" 
ON public.awake_telemetry 
FOR ALL 
USING (auth.role() = 'service_role');




