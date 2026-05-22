# 🛡️ Project Kaizer K5 - Discord Security Guard

Project Kaizer K5 is a high-fidelity Discord server protection bot and administrative dashboard. It tracks and mitigates nuke attempts (mass bans, mass kicks, mass channel/role deletions, rogue bot invites) in real-time, backed by a secure Supabase database with Row Level Security (RLS) and a responsive glassmorphic web interface.

---

## Features

- **Mass Ban Protection**: Bans any administrator who exceeds a customizable ban limit within a specified timeframe, and automatically unbans the victims.
- **Mass Kick Protection**: Bans rogue administrators who perform too many kicks.
- **Mass Channel/Role Deletion Protection**: Restores channels/roles deleted by unauthorized administrators and removes their permissions.
- **Anti-Bot Invitation**: Instantly bans unauthorized bots invited to the server and the administrator who invited them.
- **Interactive Dashboard**: A gorgeous, glassmorphic dark-mode web console to configure thresholds and manage white-listed moderators.
- **Zero-Friction Login**: Admins type `k!dashboard` on Discord to get a secure 5-minute login PIN to access the web panel without configuring complex OAuth credentials.
- **Supabase Backed**: Fully persistent and secured by Row Level Security (RLS).

---

## Quick Setup Guide

### 1. Discord Bot Setup
1. Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Open your application and navigate to the **Bot** tab:
   - Enable **Privileged Gateway Intents** (Presence Intent, Server Members Intent, and Message Content Intent).
3. Generate an invite link in **OAuth2 -> URL Generator**:
   - Select Scopes: `bot`, `applications.commands` (optional, for future slash commands).
   - Select Bot Permissions: `Administrator` (required to recreate channels/roles, adjust roles, and ban rogue admins).
4. **Hierarchy warning**: The bot's role in your Discord server's role list **MUST** be placed above all other administrators' roles. The bot cannot manage or ban members with roles higher than its own.

### 2. Supabase Setup
1. Create a new project in [Supabase](https://supabase.com).
2. Go to the **SQL Editor** on the left menu.
3. Paste the contents of the [schema.sql](file:///c:/Users/acer/Desktop/kaizer%20k5/database/schema.sql) file and run it. This will create the required tables and configure Row Level Security (RLS) so that normal public client keys cannot read or modify settings.

### 3. Local Environment Variables
The project contains a pre-filled `.env` file at the root folder containing the required database credentials:
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_ANON_KEY`: Your Supabase anonymous key
- `SUPABASE_SERVICE_ROLE_KEY`: Your Supabase service role key (required to bypass RLS for bot system actions)
- `DISCORD_BOT_TOKEN`: Your Discord bot token
- `DISCORD_APP_ID`: Your Discord application ID
- `DISCORD_PUBLIC_KEY`: Your Discord public key

### 4. Running the Application Locally

First, install the Python package dependencies:
```bash
pip install -r requirements.txt
```

Launch the combined web dashboard and Discord bot runner:
```bash
python main.py
```
The console will boot both the Discord Gateway client and the Uvicorn web server on `http://127.0.0.1:8000`.

---

## Discord Commands

All commands require **Administrator** permissions on the target server.
- `k!dashboard` - Generates a 6-digit login PIN and DMs it to the admin to log in to the web panel.
- `k!status` - Displays active protection limits and triggers.
- `k!whitelist @User` - Adds a user to the security whitelist (immunity from anti-nuke triggers).
- `k!unwhitelist @User` - Removes a user from the whitelist.
- `k!logs` - Returns the last 5 security events caught by the bot.

---

## Deployment to Render

This project contains a [render.yaml](file:///c:/Users/acer/Desktop/kaizer%20k5/render.yaml) file, allowing you to deploy it in minutes:
1. Push this workspace to your GitHub repository.
2. Link your GitHub account to [Render](https://render.com).
3. Click **New +** -> **Blueprint Route** and select this repository.
4. Render will read your `render.yaml` and configure the Web Service automatically. Input your credentials under the Environment Variables section and deploy.
