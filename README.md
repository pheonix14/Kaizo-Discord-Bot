# 🌌 XTREME CORE
### Ultimate Multi-Token Discord Orchestration Engine

[![Python](https://img.shields.io/badge/Python-3.13%2B-ff2d55?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-Backend-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-0affe4?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com)
[![Engine](https://img.shields.io/badge/Engine-XTREME--X--25-8B5CF6?style=for-the-badge)](#)
[![License](https://img.shields.io/badge/License-Proprietary-EF4444?style=for-the-badge)](License.md)

---

<div align="center">

` ◈ XTREME ENGINE — THE ULTIMATE AUTOMATION MATRIX ◈ `

*Powered by the stabilized **XTREME Core** · Built for elite-tier multi-token automation*

</div>

---

## 📖 Overview

**XTREME CORE** is a high-performance, multi-token Discord automation suite engineered for premium bot interactions (Pokétwo, OwO, bump utilities). It features a local ONNX neural vision engine, full Supabase cloud database persistence, and a stunning glassmorphic web control center — all running from a single Python process.

---

## 🧬 System Architecture

```
                    ┌─────────────────────────────────────────┐
                    │        GLASSMORPHIC WEB DASHBOARD        │
                    │   Flask @ Port 8085 · Outfit + Glass UX  │
                    └────────────────────┬────────────────────┘
                                         │
                           ┌─────────────▼─────────────┐
                           │   SUPABASE CLOUD POSTGRES   │
                           │  tokens · test · dex · logs │
                           └─────────────┬─────────────┘
                                         │
                           ┌─────────────▼─────────────┐
                           │    XTREME NODE MANAGER    │
                           └────────┬──────────┬───────┘
                                    │          │
                ┌───────────────────┘          └───────────────────┐
                ▼                                                   ▼
    ┌─────────────────────┐                           ┌─────────────────────┐
    │    WORKER NODE 1     │          ···              │    WORKER NODE N     │
    │  discum · ONNX · DB  │                           │  discum · ONNX · DB  │
    └─────────────────────┘                           └─────────────────────┘
```

---

## ⚡ Core Engines

### ⚔️ ◈ Pokétwo Neural Catcher
* **ONNX Local Vision** — Deep-learning classification runs fully offline via `onnxruntime`, eliminating external API costs and latency.
* **Hyphen-Agnostic Solver** — Matches hint patterns regardless of spacing, symbols, or hidden characters.
* **Humanized Catch Delays** — Implements a randomized **10.0 to 16.0 seconds gap** between sequential guesses (if the previous guess was incorrect or triggered a speed warning) to mimic realistic human keystroke intervals.
* **Double-Try Failover** — Automatically retries a catch attempt once after an **8.0s no-response timeout**; safely aborts and releases locks on a second consecutive failure to prevent bot lockups.
* **Granular Telemetry** — Tracks caught/missed/shiny with level, IV, and rarity statistics.

### 💎 ⬡ OwO Treasury Matrix
* **Orchestration Loop** — Automatically runs `hunt`, `battle`, `daily`, `coinflip`, and `slots` commands under strict cooldown loops.
* **Live Aggregates** — Real-time Cowoncy balance visualization showing individual node metrics and overall global sum.
* **Intelligent Auto-Pause** — Instantly pauses loop operations upon captcha flag detection to protect the account from suspension.

### 🛡️ ◎ Mimic Humanizer
* **Activity Schedules** — Break scheduler with randomized idle frames simulating authentic human sleep/awake patterns.
* **Delay Variance** — Dynamic delay variance curves and random keystroke timings to evade modern heuristic bot detectors.
* **Gateway Watchdog** — Automatic gateway re-connection and heartbeat tracking on connectivity failures.

### 📡 ◉ P2P Resiliency Mesh
* **Mutual Watchdog** — Standalone WSGI keep-alive agent in `/awake` (Wasmer Edge / Render compatible).
* **Cross-Ping Loop** — Multi-node keep-alive ping loop between active nodes and awake servers for mutual anti-hibernation.
* **Auto-Discovery** — Zero-config peer list replication and URL auto-detection from `HTTP_HOST` headers.

---

## 🎛️ Dashboard Control Panels

| Route | Panel Name | Function |
|:---|:---|:---|
| `/` | **◈ Command Center** | Real-time live log stream console, active node statuses, global metrics, and diagnostic counters. |
| `/config` | **⬡ Identity Vault** | Safe token registration, assign guilds, define active channels, and check live Discord profiles. |
| `/test` | **◎ Permission Tester** | Supabase-backed multi-token channel scanner. Tests write/embed settings, reloads every 30s, and groups results. |
| `/captcha` | **◉ Captcha Monitor** | Live alert monitor, per-node flag status, direct solver linkage, and auto-pause settings. |
| `/dex` | **◫ 3D Pokédex** | Pokédex database supporting shiny tallies, caught tallies, custom entry notes, and favorites. |
| `/history` | **◎ Telemetry Logs** | Catch gallery with IV percentages, AI model classification details, and search filters. |
| `/owo` | **◈ Treasury Manager** | OwO command toggles, micro cooldown adjustments, and Cowoncy aggregate tracking. |
| `/spam` | **⬡ Level Booster** | Scheduled spammers with custom target channels and humanized delays. |
| `/msg` | **◎ Msg Loop Engine** | Channel loop generator running custom payloads under random delays. |
| `/hook` | **◉ Resiliency Mesh** | Heartbeat pings, Awake resilient mesh configs, and peer lists. |

---

## 🔬 Channel Tester & Captcha Monitor (New Features)

> [!NOTE]
> Major backend enhancements have been introduced to provide a robust, persistent scanner environment and real-time safety measures.

### 📂 Supabase Test Scanner Table
Scan results are now permanently saved to a dedicated table in Supabase, keeping scans available across page reloads and server restarts.

```sql
CREATE TABLE IF NOT EXISTS test (
    id           TEXT PRIMARY KEY,
    token_id     TEXT,
    token_label  TEXT,
    guild_id     TEXT,
    guild_name   TEXT,
    channel_id   TEXT,
    channel_name TEXT,
    writable     BOOLEAN,
    text_allowed BOOLEAN,
    link_allowed BOOLEAN,
    last_scan    TIMESTAMPTZ DEFAULT NOW(),
    scan_reason  TEXT
);
```

### ✨ Advanced Capabilities

* **Discord Profile Resolution** — The central engine now queries active node profiles on boot. Dashboard cards and scanner results group data by **authentic Discord usernames and avatars** instead of raw token hashes.
* **Automated Polling** — The `/test` panel auto-polls `/api/test/results` every **30 seconds** during scans for hands-off tracking.
* **Auto-Pause Captcha Flags** — Captcha warnings trigger visual overlays instantly, automatically freezing worker loops on the affected accounts and displaying immediate solve links.

---

## 🛠️ Setup Protocol

### 01 ◈ 1. Clone Vault
Clone the repository and enter the directory:
```bash
git clone https://github.com/xtreme/xtreme-project.git
cd xtreme-project
```

### 02 ⬡ 2. Packages
Install all required dependencies using `pip` or `uv` manager:
```bash
pip install -r requirements.txt
```

### 03 ◎ 3. Supabase Schema
Run the Supabase setup script once to bootstrap cloud database schema structures:
```bash
python setup_supabase.py
```

### 04 ◉ 4. Boot System
Fire up the local Flask server and launch the command center:
```bash
python main.py
```

---

## ☁️ Deployment

### Render
XTREME is fully compatible with Render web service environments:
```yaml
# render.yaml
buildCommand: pip install -r requirements.txt
startCommand: gunicorn -w 1 -b 0.0.0.0:$PORT main:keep_alive
```

### Docker
```bash
docker build -t xtreme-core .
docker run -p 8085:8085 xtreme-core
```

---

## 📜 License

**Closed Source · Proprietary Software**
© 2026 XTREME CORE · Created by **pheonix14**. All rights reserved.

Unauthorized distribution, copying, modification, or commercial use is strictly prohibited.

---

<div align="center">

*Developed and maintained by the **XTREME STUDIO***

*Created by **pheonix14***

</div>
