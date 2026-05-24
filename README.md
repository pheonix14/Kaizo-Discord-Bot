# 🛡️ Project Kaizer K5 - Discord Security Guard & Multipurpose System

Project Kaizer K5 is a high-fidelity Discord server protection bot and administrative dashboard. It tracks and mitigates nuke attempts (mass bans, mass kicks, mass channel/role deletions, rogue bot invites) in real-time, backed by a secure Supabase database with Row Level Security (RLS) and a responsive, glassmorphic dark-mode web console.

Additionally, Kaizer K5 contains fully integrated suites for **Economy, Music, Leveling, Custom Commands, Server Decoration, Live Stats, and Temporary Voice Channels**.

---

## 🚀 Key Modules & Features

### 1. Advanced Anti-Nuke & Automod (K4 Defence)
- **Mass Actions Mitigation**: Automatically intercepts mass bans, kicks, channel deletions, or role deletions by rogue administrators, stripping their permissions and restoring channels/roles in real-time.
- **Anti-Bot Invitation**: Instantly bans unauthorized bots invited to the server and the administrator who invited them.
- **Auditable Protection Logs**: Every incident is immediately logged to Supabase and queryable via both the bot (`.automod_logs`) and the dashboard.
- **Immunities / Whitelist**: Security managers can whitelist trusted staff members to bypass nuke thresholds.

### 2. Dual-Mode Commands (Utility & Fun)
- To keep the slash command catalog organized and prevent exceeding Discord's **100 global slash command limit**, all Utility and Fun commands are structured as subcommands under the `/util` and `/fun` slash groups.
- To maximize user convenience, these commands are dynamically cloned and registered as **direct prefix-only text commands** (e.g. `.ping`, `.calc`, `.8ball`, `.ascii`, etc.), meaning users can use them directly without prefixing them with `util` or `fun`.
- **Utility Commands**: Latency check (`.ping`), safe evaluator (`.calc`), hex preview (`.color`), Google Translate (`.translate`), weather reports (`.weather`), QR code generator (`.qr`), paste bin (`.paste`), and reminders.
- **Fun Commands**: Magic 8-ball (`.8ball`), ASCII text converter (`.ascii`), Would You Rather (`.wyr`), regional indicator regional indicators (`.emojify`), trivia quizzes, ship compatibilities, and mini-games (TicTacToe, Wordle, Hangman).

### 3. Smart Paginated Help System
- The `.help` command lists all active categories.
- Typing `.help <category>` (e.g., `.help Moderation`, `.help reaction roles`) lists every command inside that category sorted alphabetically from **A to Z**.
- For categories with more than 8 commands, interactive Discord button pagination (◀ Previous and Next ▶) is enabled.
- Category matching is case-insensitive and strips punctuation/spacing (e.g., matching `reaction_roles`, `Reaction Roles`, and `reactionroles` seamlessly).

### 4. Temporary Voice Channels (Lobby Creator)
- Converted Join-to-Create lobby and category configurations.
- **Dynamic Role Management**: Dynamically creates a `{creator} vc` role (assigned to the owner) and a `{creator}'s vc` role (assigned to users who join) upon channel creation to manage permissions.
- **Auto-Cleanup**: Instantly deletes empty temporary VCs and their associated custom roles once users leave.

### 5. Interactive Dashboard
- A gorgeous, glassmorphic dark-mode web console to configure welcome cards, moderation actions, automod rules, logging channels, stats channels, and tickets.
- **Developer-Only Restrctions**: Economy rewards, starting balances, and shop items can only be managed by administrators configured as developers.
- **Zero-Friction Login**: Admins type `.dashboard` in Discord to receive a secure 6-digit login PIN via DM, enabling dashboard access without configuring OAuth.

---

## 📁 Supabase Database Schema

The database is built on **Supabase** with **Row-Level Security (RLS)** enabled on all tables, letting only the service role key access the data directly to enforce security. The schema contains the following tables:

1. `bot_config`: Global client credentials.
2. `guild_settings`: Primary settings table including limits, welcomes, stats, levels, and tickets.
3. `guild_whitelist`: Whitelisted users immune to nuke detections.
4. `protection_logs`: Audit trail of caught security incidents.
5. `command_configs`: Per-command permission level overrides and switches.
6. `leveling_users`: XP and level records for server members.
7. `music_playlists` / `music_playlist_tracks`: Saved playlist queues.
8. `economy_users` / `economy_shop` / `economy_inventory`: Economy balances, buyable shop items, and inventories.
9. `temp_vc_settings` / `active_temp_vcs` / `temp_voice_channels`: Temporary VC lobbies, active VCs, and channel owners.
10. `decor_backups`: Backups of channels for undoing layouts.
11. `reaction_roles`: Message-to-role reaction triggers.
12. `giveaways`: Active giveaways, hosts, prizes, and allowed roles.
13. `awake_telemetry`: Server nodes telemetry heartbeats and pings.

---

## ⚙️ Quick Setup Guide

### 1. Discord Bot Setup
1. Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Open your application and navigate to the **Bot** tab:
   - Enable all **Privileged Gateway Intents** (Presence Intent, Server Members Intent, and Message Content Intent).
3. Generate an invite link in **OAuth2 -> URL Generator**:
   - Select Scopes: `bot`, `applications.commands`.
   - Select Bot Permissions: `Administrator`.
4. **Hierarchy Warning**: The bot's role in your Discord server's role list **MUST** be placed above all other administrator roles. The bot cannot manage or ban members with roles higher than its own.

### 2. Supabase Setup
1. Create a new project in [Supabase](https://supabase.com).
2. Go to the **SQL Editor** on the left menu.
3. Paste the contents of the [`database/schema.sql`](file:///c:/Users/acer/Desktop/kaizer%20k5/database/schema.sql) file and run it. This will create the required tables, enable RLS, and configure bypass policies.

### 3. Local Environment Variables
Create a `.env` file at the root folder of the project containing:
```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
DISCORD_BOT_TOKEN=your_discord_bot_token
DISCORD_APP_ID=your_discord_app_id
DISCORD_PUBLIC_KEY=your_discord_public_key
DEVELOPER_IDS=your_discord_user_id
```

### 4. Running the Application Locally
First, install the dependencies:
```bash
pip install -r requirements.txt
```

Launch the application runner:
```bash
python main.py
```
This boots both the Discord Gateway client and the Flask dashboard server on `http://127.0.0.1:8000`.

---

## 🛠️ Discord Commands

All administration commands require **Administrator** permissions:
- `.dashboard` - Generates a 6-digit login PIN and DMs it to the administrator to access the web panel.
- `.help` - Displays the category list.
- `.help <category_name>` - Displays sorted commands for a cog with previous/next page buttons.
- `.whitelist @User` - Adds a user to the whitelist (immunity from anti-nuke triggers).
- `.unwhitelist @User` - Removes a user from the whitelist.
- `.logs` - Returns the last 5 security incidents.

---

## 📦 Deployment to Render
This project contains a [`render.yaml`](file:///c:/Users/acer/Desktop/kaizer%20k5/render.yaml) file for blueprint deployments:
1. Push this workspace to your GitHub repository.
2. Link your GitHub account to [Render](https://render.com).
3. Click **New +** -> **Blueprint Route** and select your repository.
4. Input your environment credentials under Render's environment section and deploy.
