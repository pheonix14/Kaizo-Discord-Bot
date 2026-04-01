# Kaizo Discord Bot

An advanced, high-performance, modular Discord bot and synchronized web control dashboard built for modern communities. Designed with an ultra-clean, emoji-free interface, high-throughput moderation, and enterprise-grade security.

Developed and maintained with credits to **pheonix14**. Fully open source under the MIT License.

---

## Highlights

- Clean Zero-Emoji Architecture: Polished, professional text and ASCII styling across all embeds, logs, and dashboard views.
- Modular Cogs System: Dynamic command loading, enabling selective feature deployment.
- High-Performance Moderation & AutoMod: Anti-raid, anti-spam, invite filters, and real-time defense.
- Server Builder Studio: Automatic channel, role, category, and permission structure templates.
- Rich Interactive Dashboard: Responsive Flask/Jinja2 management panel for guild settings and analytics.
- Cloud Database: Supabase PostgreSQL integration with real-time state synchronization.
- Music & Audio Engine: Voice channel streaming powered by yt-dlp and PyNaCl.
- Complete Utility Suite: Giveaways, tickets, economy, leveling, reaction roles, and temporary voice channels.

---

## Repository Structure

```text
Kaizo-Discord-Bot/
|-- src/
|   |-- bot/
|   |   |-- cogs/             # Modular feature cogs (moderation, tickets, etc.)
|   |   |-- admin_commands.py # Bot owner & developer utilities
|   |   |-- anti_nuke.py      # Guild security protection
|   |   |-- builder.py        # Server setup engine
|   |   |-- engine.py         # Discord client lifecycle
|   |-- db/
|   |   |-- client.py         # Supabase connection client
|   |-- web/
|   |   |-- flask_app.py      # Web dashboard backend
|   |   |-- server.py         # Dashboard server runners
|   |-- config.py             # Configuration loader
|-- templates/                # Dashboard HTML templates
|-- static/                   # Dashboard styles and scripts
|-- main.py                   # Main unified launcher
|-- bot.py                    # Standalone bot launcher
|-- requirements.txt          # Python dependencies
|-- pyproject.toml            # Project configuration
|-- .env.example              # Environment variables template
|-- LICENSE                   # MIT License
```

---

## Getting Started

### 1. Prerequisites
- Python 3.11 or higher
- Discord Developer Bot Application & Token
- Supabase Project (Database URL and API Keys)

### 2. Clone the Repository
```bash
git clone https://github.com/pheonix14/Kaizo-Discord-Bot.git
cd Kaizo-Discord-Bot
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configuration
Copy the example environment template:
```bash
cp .env.example .env
```
Fill in the `.env` file with your credentials:
```env
DISCORD_APP_ID=your_discord_app_id
DISCORD_BOT_TOKEN=your_discord_bot_token
DISCORD_CLIENT_SECRET=your_discord_client_secret

SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

HOST=127.0.0.1
PORT=8000
DEVELOPER_ID=your_discord_user_id
```

### 5. Run the Bot & Dashboard
```bash
python main.py
```

To run only the Discord bot without the web server:
```bash
python bot.py
```

---

## Modules and Capabilities

| Category | Description |
|---|---|
| Moderation | Ban, kick, mute, warn, purge, slowmode, and audit logging |
| AutoMod | Automatic link filtering, caps limits, spam shields, and mention limits |
| Defense | K4 anti-nuke, anti-raid, and permission change interceptors |
| Server Builder | One-click server restructuring and category generation |
| Tickets | Interactive button-based support ticket lifecycle |
| Giveaways | UTC/Local synced multi-winner giveaway scheduler |
| Leveling & Economy | Member activity tracking, leveling formulas, and custom transactions |
| Temp Voice | Automatic dynamic private voice room creation and deletion |
| Dashboard | Real-time web panel for server owners and administrators |

---

## Credits & Author

- **Author**: [pheonix14](https://github.com/pheonix14)
- **Project**: Kaizo Discord Bot

---

## License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.
