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


-- 2. Guild Settings Table (Anti-Nuke limits)
create table if not exists public.guild_settings (
    guild_id text primary key, -- Discord Guild ID (snowflake)
    guild_name text,
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
