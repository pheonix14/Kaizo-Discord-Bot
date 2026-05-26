import threading
import urllib.request
import time
import json
import os
import sys

# DARK AWAKE | WASMER KERNEL V2
# Multi-Target Pulse Emitter | Proprietary Build
# FULLY SELF-SUSTAINING: Works even if wasmer.io is offline
# PERSISTENT: URLs added via UI survive container restarts

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TARGETS_FILE = os.path.join(BASE_DIR, "targets.json")

# ──────────────────────────────────────────────
# BUILTIN TARGETS — always present after every restart
# Add any URL here to make it permanent (no UI deletion survives restart for these)
# ──────────────────────────────────────────────
BUILTIN_TARGETS = [
    {
        "url": "https://xtreme-f6jh.onrender.com",
        "label": "CORE PULSE",
        "is_active": True
    },
    {
        "url": "https://xtreme-f6jh.onrender.com/hook",
        "label": "TELEMETRY HOOK",
        "is_active": True
    },
]

def make_target(url, label="", is_active=True):
    return {
        "url": url,
        "pings": 0,
        "success": 0,
        "last_ping": None,
        "is_active": is_active,
        "label": label
    }

# ──────────────────────────────────────────────
# SELF URL HELPERS
# ──────────────────────────────────────────────

def get_self_url():
    env_url = os.environ.get("SELF_URL") or os.environ.get("AWAKE_URL")
    if env_url:
        return env_url
    if os.path.exists(TARGETS_FILE):
        try:
            with open(TARGETS_FILE, 'r') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data.get("self_url")
        except:
            pass
    return None

def save_self_url(url):
    try:
        existing = _read_file_raw()
        existing["self_url"] = url
        _write_file_raw(existing)
    except:
        pass

# ──────────────────────────────────────────────
# RAW FILE HELPERS
# ──────────────────────────────────────────────

def _read_file_raw():
    """Read the full targets.json structure."""
    if os.path.exists(TARGETS_FILE):
        try:
            with open(TARGETS_FILE, 'r') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
                elif isinstance(data, list):
                    return {"self_url": None, "targets": data}
        except:
            pass
    return {"self_url": None, "targets": []}

def _write_file_raw(data):
    """Write the full targets.json structure atomically."""
    tmp = TARGETS_FILE + ".tmp"
    with open(tmp, 'w') as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, TARGETS_FILE)

# ──────────────────────────────────────────────
# TARGET PERSISTENCE — MERGE STRATEGY
# Builtin targets are ALWAYS injected.
# User-added targets from targets.json are MERGED in.
# Result: nothing is ever lost from the file, builtins always exist.
# ──────────────────────────────────────────────

def load_targets():
    """
    Load targets using a merge strategy:
    1. Start with BUILTIN_TARGETS (always present)
    2. Merge in any extra URLs from targets.json (user-added ones survive restarts)
    3. Merge in any extra URLs from AWAKE_TARGETS env var (optional override)
    """
    # Start with builtins
    seen_urls = set()
    merged = []

    for b in BUILTIN_TARGETS:
        url = b["url"].strip()
        if url not in seen_urls:
            seen_urls.add(url)
            merged.append(make_target(url, b.get("label", ""), b.get("is_active", True)))

    # Merge from file
    raw = _read_file_raw()
    file_targets = raw.get("targets", [])
    for t in file_targets:
        url = t.get("url", "").strip()
        if url and url not in seen_urls:
            seen_urls.add(url)
            merged.append({
                "url": url,
                "pings": 0,
                "success": 0,
                "last_ping": None,
                "is_active": t.get("is_active", True),
                "label": t.get("label", "")
            })

    # Merge from AWAKE_TARGETS env var (JSON array of URL strings or objects)
    env_targets_raw = os.environ.get("AWAKE_TARGETS", "")
    if env_targets_raw:
        try:
            env_targets = json.loads(env_targets_raw)
            if isinstance(env_targets, list):
                for item in env_targets:
                    if isinstance(item, str):
                        url = item.strip()
                        lbl = ""
                    elif isinstance(item, dict):
                        url = item.get("url", "").strip()
                        lbl = item.get("label", "")
                    else:
                        continue
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        merged.append(make_target(url, lbl))
        except Exception as e:
            print(f"[AWAKE] AWAKE_TARGETS parse error: {e}", flush=True)

    return merged

def save_targets():
    """
    Write ONLY the user-managed portion (merged list) back to targets.json.
    We save the full merged list so user-added URLs survive future restarts.
    """
    try:
        raw = _read_file_raw()
        raw["targets"] = watchdog_state["targets"]
        _write_file_raw(raw)
    except Exception as e:
        print(f"[AWAKE] Save error: {e}", flush=True)

# ──────────────────────────────────────────────
# GLOBAL STATE
# ──────────────────────────────────────────────

raw_config = _read_file_raw()

watchdog_state = {
    "targets": load_targets(),
    "logs": [],
    "pings_received": 0,
    "start_time": time.time(),
    "self_ping_count": 0,
    "self_ping_last": None,
    "ping_interval": raw_config.get("ping_interval", 30),
    "p2p_mesh": raw_config.get("p2p_mesh", True),
    "last_ping_cycle_time": 0
}

# Immediately persist the merged list so file stays up-to-date
save_targets()

def add_log(msg):
    timestamp = time.strftime("%H:%M:%S")
    entry = f"[{timestamp}] {msg}"
    watchdog_state["logs"].append(entry)
    if len(watchdog_state["logs"]) > 50:
        watchdog_state["logs"].pop(0)
    print(entry, flush=True)

# ──────────────────────────────────────────────
# P2P GOSSIP HELPERS
# ──────────────────────────────────────────────

def merge_peers(peer_list):
    if not watchdog_state.get("p2p_mesh", True):
        return
    if not peer_list or not isinstance(peer_list, list):
        return
    changed = False
    for url in peer_list:
        if not isinstance(url, str):
            continue
        url = url.strip()
        if not url:
            continue
        # Normalize: strip http://, https://, and trailing slash
        norm_url = url
        if norm_url.startswith("http://"):
            norm_url = norm_url[7:]
        elif norm_url.startswith("https://"):
            norm_url = norm_url[8:]
        norm_url = norm_url.rstrip("/")
        
        # Check if already present in targets
        exists = False
        for t in watchdog_state["targets"]:
            t_url = t["url"].strip()
            if t_url.startswith("http://"):
                t_url = t_url[7:]
            elif t_url.startswith("https://"):
                t_url = t_url[8:]
            t_url = t_url.rstrip("/")
            if t_url == norm_url:
                exists = True
                break
        if not exists:
            full_url = "https://" + norm_url
            watchdog_state["targets"].append(make_target(full_url, "PEER NODE", True))
            add_log(f"GOSSIP: Discovered peer {norm_url} via sync")
            changed = True
    if changed:
        save_targets()

# ──────────────────────────────────────────────
# PING UTILITY WITH RETRY
# ──────────────────────────────────────────────

def do_ping(ping_url, headers, max_retries=2):
    """Attempt a ping with retry + backoff. Returns (ok, status_code, body)."""
    last_error = None
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(ping_url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as response:
                status = response.status
                body = response.read().decode('utf-8', errors='ignore')
                return True, status, body
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(1)
    return False, str(last_error), None

# ──────────────────────────────────────────────
# MAIN PING LOOP AND PARALLEL EXECUTION
# ──────────────────────────────────────────────

def ping_single_target(target, headers):
    target["pings"] += 1
    url = target["url"].strip()
    ping_url = url
    if not ping_url.startswith("http"):
        ping_url = "https://" + ping_url
    if ping_url.count('/') == 2:
        ping_url += "/hook.html"
        
    ok, status, body = do_ping(ping_url, headers)
    target["last_ping"] = time.strftime("%H:%M:%S")
    if ok:
        target["success"] += 1
        if target["pings"] % 15 == 0:
            add_log(f"PULSE: Stable {target.get('label', 'Link')} -> {url}")
        # Parse body for peer lists if P2P mesh mode is active
        if watchdog_state.get("p2p_mesh", True) and body:
            try:
                data = json.loads(body)
                if isinstance(data, dict) and "peers" in data:
                    merge_peers(data["peers"])
            except:
                pass
    else:
        if target["pings"] % 5 == 0:
            add_log(f"FAIL: {url} - {str(status)[:80]}")

def run_ping_cycle_once():
    watchdog_state["last_ping_cycle_time"] = time.time()
    
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    self_url = get_self_url()
    if self_url:
        headers["X-Awake-URL"] = self_url
        
    # Gather other active peers to send in X-Peers header
    active_peers = [t["url"] for t in watchdog_state["targets"] if t.get("is_active")]
    if self_url and self_url not in active_peers:
        active_peers.append(self_url)
        
    threads = []
    for target in watchdog_state["targets"]:
        if not target.get("is_active"):
            continue
            
        t_headers = dict(headers)
        # Gossip sharing: filter this target itself out of X-Peers
        t_url = target["url"].strip()
        t_peers = [p for p in active_peers if p != t_url]
        if t_peers and watchdog_state.get("p2p_mesh", True):
            t_headers["X-Peers"] = ",".join(t_peers)
            
        t = threading.Thread(target=ping_single_target, args=(target, t_headers))
        t.start()
        threads.append(t)
        
    # Wait up to 3 seconds for them to run
    start_wait = time.time()
    for t in threads:
        remaining = 3.0 - (time.time() - start_wait)
        if remaining > 0:
            t.join(timeout=remaining)

def trigger_ping_cycle_if_needed(force=False):
    current_time = time.time()
    last_run = watchdog_state.get("last_ping_cycle_time", 0)
    interval = watchdog_state.get("ping_interval", 30)
    if force or (current_time - last_run >= interval):
        # Update last run time immediately to prevent multiple overlapping triggers
        watchdog_state["last_ping_cycle_time"] = current_time
        # Spawn thread to run ping cycle
        threading.Thread(target=run_ping_cycle_once, daemon=True, name="RequestPingCycle").start()

def ping_loop():
    add_log("SYSTEM: Heartbeat Kernel Initialized (standalone mode)")
    last_save_time = time.time()

    while True:
        # Periodic save every 30 seconds so user-added URLs are written to disk
        if watchdog_state["targets"] and time.time() - last_save_time > 30:
            save_targets()
            last_save_time = time.time()

        trigger_ping_cycle_if_needed()
        time.sleep(1)

# ──────────────────────────────────────────────
# INTERNAL SELF-PING LOOP (replaces wasmer.io cron)
# ──────────────────────────────────────────────

def self_ping_loop():
    time.sleep(10)
    add_log("SYSTEM: Internal self-ping engine started")

    while True:
        self_url = get_self_url()
        if self_url:
            try:
                ping_url = self_url.rstrip("/") + "/api/cron-pulse"
                req = urllib.request.Request(
                    ping_url,
                    headers={
                        "User-Agent": "AWAKE-Internal-Watchdog/2.0",
                        "X-Self-Ping": "true"
                    }
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    watchdog_state["self_ping_count"] += 1
                    watchdog_state["self_ping_last"] = time.strftime("%H:%M:%S")
                    if watchdog_state["self_ping_count"] % 10 == 0:
                        add_log(f"SYSTEM: Self-ping #{watchdog_state['self_ping_count']} OK")
            except Exception as e:
                pass
        time.sleep(55)

# ──────────────────────────────────────────────
# WSGI APPLICATION
# ──────────────────────────────────────────────

def app(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    method = environ.get('REQUEST_METHOD', 'GET')

    # Process P2P headers to auto-discover peers
    awake_url_header = environ.get('HTTP_X_AWAKE_URL')
    peers_header = environ.get('HTTP_X_PEERS')
    
    if awake_url_header:
        merge_peers([awake_url_header])
    if peers_header:
        try:
            peer_urls = [p.strip() for p in peers_header.split(',') if p.strip()]
            merge_peers(peer_urls)
        except:
            pass

    # Whenever a request is received, trigger a fast ping cycle if needed
    trigger_ping_cycle_if_needed()

    # Auto-detect & save self URL when hosted publicly
    host = environ.get('HTTP_HOST')
    if host and not host.startswith("localhost") and not host.startswith("127.0.0.1"):
        scheme = environ.get('wsgi.url_scheme', 'https')
        detected_url = f"{scheme}://{host}"
        try:
            if detected_url != get_self_url():
                save_self_url(detected_url)
        except:
            pass

    cors = [
        ('Access-Control-Allow-Origin', '*'),
        ('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
        ('Access-Control-Allow-Headers', 'Content-Type, X-Awake-URL, X-Peers'),
    ]

    if method == 'OPTIONS':
        start_response('204 No Content', cors)
        return [b'']

    # GET /
    if path == '/':
        try:
            template_path = os.path.join(BASE_DIR, 'templates', 'index.html')
            with open(template_path, 'r') as f:
                content = f.read().encode()
            start_response('200 OK', [('Content-Type', 'text/html')] + cors)
            return [content]
        except:
            start_response('200 OK', [('Content-Type', 'text/plain')] + cors)
            return [b"AWAKE KERNEL ONLINE. Templates missing."]

    # GET /api/status
    elif path == '/api/status':
        uptime_sec = int(time.time() - watchdog_state["start_time"])
        h, rem = divmod(uptime_sec, 3600)
        m, s = divmod(rem, 60)
        watchdog_state["uptime"] = f"{h}h {m}m {s}s"
        watchdog_state["self_url"] = get_self_url()
        start_response('200 OK', [('Content-Type', 'application/json')] + cors)
        return [json.dumps(watchdog_state).encode()]

    # GET /api/cron-pulse
    elif path == '/api/cron-pulse':
        def gen():
            add_log("SYSTEM: Cron pulse received. Maintaining active state...")
            for _ in range(15):
                yield b" "
                time.sleep(1)
            yield json.dumps({"status": "ok"}).encode()
        start_response('200 OK', [('Content-Type', 'application/json')] + cors)
        return gen()

    # Hook endpoint
    elif path in ('/api/hook', '/hook', '/hook.html'):
        watchdog_state["pings_received"] += 1
        if watchdog_state["pings_received"] % 10 == 0:
            add_log(f"INBOUND: Received {watchdog_state['pings_received']} heartbeats")
            
        # Compile active peers list to return
        peers = [t["url"] for t in watchdog_state["targets"] if t.get("is_active")]
        self_url = get_self_url()
        if self_url and self_url not in peers:
            peers.append(self_url)
            
        start_response('200 OK', [('Content-Type', 'application/json')] + cors)
        return [json.dumps({
            "status": "pulse received", 
            "node": "AWAKE-V2", 
            "peers": peers
        }).encode()]

    # POST /api/add
    elif path == '/api/add' and method == 'POST':
        try:
            length = int(environ.get('CONTENT_LENGTH', 0))
            data = json.loads(environ['wsgi.input'].read(length).decode('utf-8'))
            url = data.get('url', '').strip()

            if url and not any(t['url'] == url for t in watchdog_state["targets"]):
                watchdog_state["targets"].append(make_target(
                    url,
                    data.get('label', ''),
                    True
                ))
                add_log(f"SYSTEM: New pulse target deployed: {url}")
                save_targets()

            start_response('200 OK', [('Content-Type', 'application/json')] + cors)
            return [json.dumps({"success": True}).encode()]
        except Exception as e:
            start_response('400 Bad Request', cors)
            return [str(e).encode()]

    # POST /api/remove
    elif path == '/api/remove' and method == 'POST':
        try:
            length = int(environ.get('CONTENT_LENGTH', 0))
            data = json.loads(environ['wsgi.input'].read(length).decode('utf-8'))
            url = data.get('url', '')
            watchdog_state["targets"] = [t for t in watchdog_state["targets"] if t['url'] != url]
            add_log(f"SYSTEM: Target decommissioned: {url}")
            save_targets()
            start_response('200 OK', [('Content-Type', 'application/json')] + cors)
            return [json.dumps({"success": True}).encode()]
        except:
            start_response('400 Bad Request', cors)
            return [b"Error"]

    # POST /api/toggle
    elif path == '/api/toggle' and method == 'POST':
        try:
            length = int(environ.get('CONTENT_LENGTH', 0))
            data = json.loads(environ['wsgi.input'].read(length).decode('utf-8'))
            url = data.get('url', '')
            for t in watchdog_state["targets"]:
                if t['url'] == url:
                    t['is_active'] = not t['is_active']
                    add_log(f"SYSTEM: {url} -> {'ACTIVE' if t['is_active'] else 'PAUSED'}")
            save_targets()
            start_response('200 OK', [('Content-Type', 'application/json')] + cors)
            return [json.dumps({"success": True}).encode()]
        except:
            start_response('400 Bad Request', cors)
            return [b"Error"]

    # POST /api/set-self-url
    elif path == '/api/set-self-url' and method == 'POST':
        try:
            length = int(environ.get('CONTENT_LENGTH', 0))
            data = json.loads(environ['wsgi.input'].read(length).decode('utf-8'))
            url = data.get('url', '').strip()
            if url:
                save_self_url(url)
                add_log(f"SYSTEM: Configured self URL to {url}")
            start_response('200 OK', [('Content-Type', 'application/json')] + cors)
            return [json.dumps({"success": True}).encode()]
        except Exception as e:
            start_response('400 Bad Request', cors)
            return [str(e).encode()]

    # POST /api/set-config
    elif path == '/api/set-config' and method == 'POST':
        try:
            length = int(environ.get('CONTENT_LENGTH', 0))
            data = json.loads(environ['wsgi.input'].read(length).decode('utf-8'))
            if "ping_interval" in data:
                watchdog_state["ping_interval"] = int(data["ping_interval"])
            if "p2p_mesh" in data:
                watchdog_state["p2p_mesh"] = bool(data["p2p_mesh"])
            save_targets()
            add_log(f"SYSTEM: Updated config (interval={watchdog_state['ping_interval']}s, mesh={watchdog_state['p2p_mesh']})")
            start_response('200 OK', [('Content-Type', 'application/json')] + cors)
            return [json.dumps({"success": True}).encode()]
        except Exception as e:
            start_response('400 Bad Request', cors)
            return [str(e).encode()]

    start_response('404 Not Found', [('Content-Type', 'text/plain')] + cors)
    return [b"404 - Kernel Path Not Found"]


# ──────────────────────────────────────────────
# THREAD STARTUP
# ──────────────────────────────────────────────

threading.Thread(target=ping_loop, daemon=True, name="PingLoop").start()
threading.Thread(target=self_ping_loop, daemon=True, name="SelfPingLoop").start()

app = app  # Wasmer/Uvicorn WSGI alias

if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    PORT = int(os.environ.get("PORT", 8080))
    print(f"[AWAKE] Standalone server starting on port {PORT}", flush=True)
    print(f"[AWAKE] Loaded {len(watchdog_state['targets'])} target(s)", flush=True)
    print(f"[AWAKE] No wasmer.io required — fully self-sustaining", flush=True)
    with make_server('', PORT, app) as httpd:
        print(f"[AWAKE] GUI online → http://localhost:{PORT}", flush=True)
        httpd.serve_forever()
