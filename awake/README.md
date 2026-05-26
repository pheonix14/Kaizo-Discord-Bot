# 🛡️ AWAKE KERNEL V2
## Proprietary High-Frequency Pulse Emitter

> **[!] CLOSED SOURCE / PROPRIETARY SYSTEM**
> This software is part of the Dark X4 Automation Suite. Unauthorized distribution, reverse engineering, or modification is strictly prohibited.

### Overview
**AWAKE** is a zero-dependency, ultra-low-latency heartbeat service designed to prevent cloud-hosted applications (Render, Heroku, Glitch, etc.) from entering sleep mode. It utilizes a multi-threaded Python core to deliver high-frequency pings to multiple targets simultaneously.

### Key Features
- **Multi-Targeting**: Manage and monitor an unlimited number of keep-alive pulses from a single dashboard.
- **1Hz Pulse Frequency**: Pings targets every second to ensure maximum uptime and bypass aggressive sleeping policies.
- **Auto-Sync Logic**: Automatically targets `/hook` endpoints for seamless integration with Fafnir/Dark modules.
- **Real-Time Telemetry**: Live dashboard showing ping counts, status indicators, and kernel logs.
- **Zero Dependencies**: Pure Python implementation using standard libraries (`urllib`, `threading`) for 100% compatibility with **Wasmer** and other containerized runners.

### Deployment on Wasmer
The Awake Kernel is optimized for Wasmer execution.
```bash
wasmer deploy
```
*Note: Ensure `wasmer.toml` is present in the root directory.*

### API Specification
The Kernel exposes the following WSGI endpoints:

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/` | GET | Main Dashboard (UI) |
| `/api/status` | GET | Returns global state and target stats |
| `/api/add` | POST | Add a new target URL |
| `/api/remove` | POST | Terminate a pulse target |
| `/api/toggle` | POST | Pause/Resume a specific pulse |

### Target Synchronization
By default, if a bare domain is provided (e.g., `myapp.onrender.com`), the kernel will automatically append `/api/hook` to ensure synchronization with standard keep-alive listeners. To target a specific path, include the full URL.

---
**© 2026 DARK X4 SYSTEMS. ALL RIGHTS RESERVED.**
