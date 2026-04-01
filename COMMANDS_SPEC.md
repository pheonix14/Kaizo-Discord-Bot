# Kaizo Discord Bot Full Specification

*The content below is the comprehensive command list, embed templates, database schema, web dashboard overview, OAuth2 flow, permission system, and status/info commands.*

---

## 1. BOT OVERVIEW

| Field | Value |
|---|---|
| Bot Name | Kaizo Discord Bot |
| Framework | discord.py (Python) OR discord.js v14 (Node.js) |
| Prefix Style | Custom per server (default: `!`) + Slash Commands (`/`) |
| Database | Supabase (PostgreSQL + Realtime) |
| Dashboard | Next.js / React web app synced to bot |
| Auth | Discord OAuth2 |
| Hosting | VPS / Railway / Render |
| Cache | Redis (optional, for cooldowns/ratelimits) |

---

## 2. TECH STACK

```
Bot:         discord.py 2.x OR discord.js v14
Database:    Supabase (PostgreSQL)
API Layer:   FastAPI (Python) OR Express (Node) — bridge between dashboard & bot
Dashboard:   Next.js 14 + Tailwind CSS
Auth:        Discord OAuth2 via next‑auth or passport.js
Real-time:   Supabase Realtime subscriptions
Cache:       Redis or Supabase edge functions
Deploy:      Docker + Railway / Render / VPS
```

---

## 3. CUSTOM PREFIX SYSTEM

*(Implementation snippet omitted for brevity – see earlier description.)*

---

## 4. COMMAND CATEGORIES & FULL COMMAND LIST

### 4.1 DEVELOPER / OWNER COMMANDS
| Command | Usage | Description |
|---|---|---|
| `dev eval` | `!dev eval <code>` | Execute arbitrary Python/JS code in bot context |
| `dev exec` | `!dev exec <code>` | Execute shell command on host machine |
| `dev reload` | `!dev reload <cog>` | Reload a specific cog/module without restart |
| `dev load` | `!dev load <cog>` | Load a new cog at runtime |
| `dev unload` | `!dev unload <cog>` | Unload an active cog |
| `dev shutdown` | `!dev shutdown` | Gracefully shut down the bot process |
| `dev restart` | `!dev restart` | Restart the bot process |
| `dev status` | `!dev status <type> <text>` | Change bot's Discord status/activity |
| `dev blacklist` | `!dev blacklist add/remove <user_id>` | Globally blacklist a user from all commands |
| `dev announce` | `!dev announce <message>` | Send a message to announcement channels in all guilds |
| `dev guilds` | `!dev guilds` | List all guilds the bot is currently in |
| `dev stats` | `!dev stats` | Global bot statistics (guilds, users, commands run, uptime) |
| `dev maintenance` | `!dev maintenance on/off` | Toggle maintenance mode (blocks all non‑dev commands) |
| `dev dm` | `!dev dm <user_id> <message>` | DM any user as the bot |
| `dev sql` | `!dev sql <query>` | Run raw SQL query on Supabase (READ ONLY enforced) |
| `dev sync` | `!dev sync [guild_id]` | Sync slash commands globally or for a specific guild |
| `dev cache` | `!dev cache clear` | Flush Redis / in‑memory caches |
| `dev error` | `!dev error` | View last N errors from error log |

*(Further categories truncated – full list available in the original specification.)*

---

## 5. EMBED TEMPLATES & STYLES

*(Templates 1‑12 as described in the spec.)*

---

## 6. SUPABASE DATABASE SCHEMA

*(SQL definitions for `guild_configs`, `users`, `guild_members`, `economy_transactions`, `cooldowns`, `shop_items`, `inventories`, `warnings`, `mod_cases`, `badges`, `user_badges`, `achievements`, `user_achievements`, `reminders`, `afk_status`, `bot_stats`, `command_usage`.)*

---

## 7. DASHBOARD WEBSITE (WEB SYNC)

*(Page overview, API endpoints, and component layout.)*

---

## 8. DISCORD OAUTH2 LOGIN FLOW

*(Step‑by‑step flow and Next.js implementation snippet.)*

---

## 9. PERMISSION SYSTEM

*(Hierarchy and decorator example.)*

---

## 10. BOT STATUS, ABOUT & PROFILE

*(Rotating statuses, `/about` embed, `/status` embed.)*

---

*End of specification.*
