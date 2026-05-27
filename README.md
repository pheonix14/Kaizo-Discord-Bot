# 🛡️ Project Kaizer K5 - Discord Security Guard & Admin Suite

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)
[![Run on Replit](https://replit.com/badge/github/username/repo)](https://replit.com/new/github/username/repo)
[![Deploy to Wasmer](https://img.shields.io/badge/Deploy_to_Wasmer-black?logo=wasmer&logoColor=white)](https://wasmer.io)

Project Kaizer K5 is a high-fidelity Discord server protection bot and administrative dashboard. It tracks and mitigates nuke attempts (mass bans, mass kicks, mass channel/role deletions, rogue bot invites) in real-time, backed by a secure Supabase database and a responsive glassmorphic web interface.

---

## 🌟 Key Features & Systems

### 1. Security & Anti-Nuke
- **Mass Ban/Kick Protection**: Bans any administrator who exceeds a customizable limit within a specified timeframe, and automatically unbans/re-invites victims.
- **Mass Channel/Role Deletion Protection**: Restores channels/roles deleted by unauthorized administrators and strips their permissions.
- **Anti-Bot Invitation**: Instantly bans unauthorized bots invited to the server and the administrator who invited them.
- **Anti-Spam / Anti-Raid**: Advanced anti-spam and anti-raid parameters managed via K4 Defense (`.k4defence`).

### 2. Upgraded Paginated Help Systems
All major cogs now support interactive, paginated lists with `◀ Previous` (blue) and `Next ▶` (grey) buttons. Only the command author can interact with the buttons:
- **`Utility`** (`.util`, `/util`): Paginated commands with direct aliases (e.g. `/ping`, `.uptime`).
- **`Moderation`** (`.mod`, `/mod`): Paginated overview for all kick, ban, mute, and warn commands.
- **`Fun`** (`.fun`): Paginated overview for game commands.
- **`Economy`** (`.economy`): Paginated overview for wallet, bank, shop, items, and gambling.
- **`Music`** (`.music`, `/music`): Paginated lists for player control, playlists, filters, and downloads.
- **`Temp VC`** (`.voice`, `/voice`, `.vc`, `/vc`): Paginated commands for temporary voice channels and setup.
- **`Tickets`** (`.tickets`, `/tickets`): Paginated commands for ticket setup, user access, and transcripts.
- **`Welcome`** (`.welcome`, `/welcome`): Paginated help for procedural cards, Themes, Fonts, and custom templates.
- **`Logging`** (`.logging`, `/logging`, `.logs`, `/logs`): Paginated setups for channels and logs.
- **`AutoMod`** (`.automod`, `/automod`): Paginated listings of security states, whitelist, and K4 Defense parameters.
- **`Giveaways`** (`.giveaways`, `/giveaways`): Paginated commands for starting, ending, and rerolling giveaways.
- **`Server Builder`** (`.builder`, `/builder`): Paginated layouts for exporting, importing, cloning, and auditing guild layouts.
- **`Live Stats`** (`.stats`): Paginated live member counter configuration guides.

### 3. Direct Command Aliases
All commands under utility, fun, and economy cogs can be executed directly without writing their cog prefixes (e.g., `/ping` instead of `/utility ping`, `/bal` or `.bal` instead of `/economy balance`, `/work` instead of `/economy work`).

### 4. Interactive Web Dashboard
A gorgeous, glassmorphic dark-mode web console (`http://localhost:8000`) containing:
- **Server Selector**: Easy login via secure 6-digit Discord PINs (`k!dashboard`).
- **Leveling Customization**: Dynamic drop-down channel selectors to configure default announcement channels for member level-ups.
- **Giveaway Scheduler**: GMT/UTC real-time clocks and a interactive visual calendar start and end date selector.
- **Real-Time Security Logs (`/logs`)**:
  - Upgraded luxury theme inspired by modern high-end showcase pages.
  - Interactive custom cursor tracker, vignettes, noise grains, and dynamic radial color bleeds.
  - Interactive preloader animation.
  - Glowing Glassmorphic log terminal displaying severity colors (`type-critical`, `type-warn`, `type-info`) and custom scrollbars.
  - Real-time polling engine updating logs every 3 seconds from Supabase.
  - HTML5 browser push notifications and animated sliding toasts (`#notif-toast`) to alert server administrators immediately when events are caught.

---

## 🛠️ Quick Setup Guide

### 1. Discord Bot Setup
1. Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Enable **Privileged Gateway Intents** (Presence Intent, Server Members Intent, and Message Content Intent) in the **Bot** tab.
3. Invite the bot using: `https://discord.com/oauth2/authorize?client_id=<YOUR_CLIENT_ID>&permissions=8&scope=bot%20applications.commands`.
4. **Hierarchy warning**: The bot's role **MUST** be placed above all other administrators' roles in your server settings.

### 2. Supabase Database Setup
1. Create a project in [Supabase](https://supabase.com).
2. Copy the contents of the database schema file and execute them in the **SQL Editor** to create tables and configure Row Level Security (RLS).

### 3. Environment Variables
Your `.env` file should contain:
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_ANON_KEY`: Your Supabase anonymous key
- `SUPABASE_SERVICE_ROLE_KEY`: Your Supabase service role key (bypasses RLS for system operations)
- `DISCORD_BOT_TOKEN`: Your Discord bot token
- `DISCORD_APP_ID`: Your Discord application ID
- `FLASK_SECRET_KEY`: Web session secret key

### 4. Running Locally
Install requirements:
```bash
pip install -r requirements.txt
```
Run bot & web server:
```bash
python main.py
```

---

## 💻 Discord Commands

All admin commands require **Administrator** permissions on the target server.
- `.dashboard` / `k!dashboard` - Generates a 6-digit login PIN and DMs it to the admin.
- `.stats` / `.automod` / `.builder` / `.giveaways` / `.welcome` / `.tickets` / `.voice` / `.logging` - Displays interactive paginated help overviews.
- `.ping` / `.uptime` / `.info` - Direct utility commands.
- `.bal` / `.work` / `.daily` / `.shop` - Direct economy commands.
- `.slots` / `.blackjack` / `.coinflip` - Direct gambling commands.
