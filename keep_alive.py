from flask import Flask, send_from_directory, jsonify, request
from threading import Thread
import threading, os, json, uuid
import logger, engine, pokemon_loader, data
from datetime import datetime

app = Flask(__name__, template_folder="templates", static_folder="static")

@app.route("/static/<path:path>")
def send_static(path):
    return send_from_directory("static", path)
START_TIME = datetime.now()
METRICS = {
    "pings": 0,
    "requests": 0
}

@app.before_request
def count_request():
    METRICS["requests"] += 1

@app.errorhandler(Exception)
def handle_exception(e):
    # Pass through HTTP errors
    if hasattr(e, 'code'):
        return jsonify({"error": str(e), "status": "Error"}), e.code
    # Handle non-HTTP exceptions
    return jsonify({"error": "Internal Server Error", "details": str(e), "status": "Critical"}), 500

@app.route("/api/ping")
def simple_ping():
    return jsonify({"status": "Success", "timestamp": datetime.now().isoformat()})

def _tpl(f): return send_from_directory("templates", f)

@app.route("/")          
def home():       return _tpl("index.html")
@app.route("/config")    
def config_p():   return _tpl("config.html")
@app.route("/spam")      
def spam_p():     return _tpl("spam.html")
@app.route("/history")   
def history_p():  return _tpl("history.html")
@app.route("/owo")   
def owo_p():      return _tpl("owo.html")
@app.route("/slash")
def slash_p():    return _tpl("slash.html")
LAST_AWAKE_URL = None

def update_awake_url(url):
    global LAST_AWAKE_URL
    if url and url != LAST_AWAKE_URL:
        LAST_AWAKE_URL = url
        try:
            mimcfg = logger.get_mimic_config()
            if isinstance(mimcfg, dict):
                mimcfg["awake_url"] = url
                logger.save_mimic_config(mimcfg)
        except Exception as e:
            print(f"[Save Awake URL Error] {e}", flush=True)

def get_peers_from_db():
    try:
        mimcfg = logger.get_mimic_config()
        if isinstance(mimcfg, dict):
            peers = mimcfg.get("awake_peers", [])
            if isinstance(peers, list):
                return [p.strip() for p in peers if isinstance(p, str) and p.strip()]
    except Exception as e:
        print(f"[Get Peers Error] {e}", flush=True)
    return []

def merge_peers(peer_urls):
    if not peer_urls:
        return
    try:
        mimcfg = logger.get_mimic_config()
        if not isinstance(mimcfg, dict):
            mimcfg = {}
        
        current_peers = mimcfg.get("awake_peers", [])
        if not isinstance(current_peers, list):
            current_peers = []
            
        current_peers = [p.strip().rstrip('/') for p in current_peers if p.strip()]
        
        changed = False
        for url in peer_urls:
            if not isinstance(url, str):
                continue
            url = url.strip().rstrip('/')
            if not url:
                continue
            norm_url = url
            if norm_url.startswith("http://"):
                norm_url = norm_url[7:]
            elif norm_url.startswith("https://"):
                norm_url = norm_url[8:]
            
            exists = False
            for p in current_peers:
                p_norm = p
                if p_norm.startswith("http://"):
                    p_norm = p_norm[7:]
                elif p_norm.startswith("https://"):
                    p_norm = p_norm[8:]
                if p_norm == norm_url:
                    exists = True
                    break
            
            if not exists:
                full_url = url
                if not full_url.startswith("http"):
                    full_url = "https://" + full_url
                current_peers.append(full_url)
                changed = True
                
        if changed:
            mimcfg["awake_peers"] = current_peers
            logger.save_mimic_config(mimcfg)
            print(f"[P2P] Merged peers list: {current_peers}", flush=True)
    except Exception as e:
        print(f"[Merge Peers Error] {e}", flush=True)

@app.route("/hook")
@app.route("/hook.html")
@app.route("/hook/")
def hook_p():
    METRICS["pings"] += 1
    
    # Process P2P headers
    awake_url = request.headers.get("X-Awake-URL")
    peers_header = request.headers.get("X-Peers")
    
    if awake_url:
        update_awake_url(awake_url)
        merge_peers([awake_url])
    if peers_header:
        try:
            peer_list = [p.strip() for p in peers_header.split(',') if p.strip()]
            merge_peers(peer_list)
        except Exception as e:
            print(f"[Hook Peers Parse Error] {e}", flush=True)
            
    return _tpl("hook.html")

@app.route("/image")
@app.route("/image/")
@app.route("/image.html")
@app.route("/imaeg")
@app.route("/img")
@app.route("/vision")
def image_p():    return _tpl("image.html")
@app.route("/msg")
def msg_p():      return _tpl("msg.html")
@app.route("/mimic")
def mimic_p():    return _tpl("mimic.html")
@app.route("/captcha")
@app.route("/captcha.html")
@app.route("/captcha/")
def captcha_p():  return _tpl("captcha.html")
@app.route("/pokedex")
@app.route("/dex")
@app.route("/dex.html")
@app.route("/dex.html/")
def pokedex_p():  return _tpl("pokedex.html")
@app.route("/bal")
@app.route("/bal.html")
@app.route("/balance")
def bal_p():       return _tpl("bal.html")
@app.route("/favicon.ico")
def fav():        return send_from_directory(".","favicon.ico",mimetype="image/vnd.microsoft.icon")

# ── Awake Resiliency Config Route ─────────────────────────────────────────────
@app.route("/api/awake/config", methods=["GET", "POST"])
def api_awake_config():
    if request.method == "POST":
        try:
            data = request.json
            mimcfg = logger.get_mimic_config()
            if not isinstance(mimcfg, dict):
                mimcfg = {}
            
            if "awake_url" in data:
                global LAST_AWAKE_URL
                url = data["awake_url"].strip()
                LAST_AWAKE_URL = url
                mimcfg["awake_url"] = url
            if "awake_peers" in data:
                peers = data["awake_peers"]
                if isinstance(peers, list):
                    mimcfg["awake_peers"] = [p.strip() for p in peers if isinstance(p, str) and p.strip()]
            if "p2p_mesh" in data:
                mimcfg["p2p_mesh"] = bool(data["p2p_mesh"])
                
            logger.save_mimic_config(mimcfg)
            return jsonify({"ok": True})
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 400
    else:
        try:
            mimcfg = logger.get_mimic_config()
            if not isinstance(mimcfg, dict):
                mimcfg = {}
            return jsonify({
                "awake_url": mimcfg.get("awake_url", ""),
                "awake_peers": mimcfg.get("awake_peers", []),
                "p2p_mesh": mimcfg.get("p2p_mesh", True)
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

# ── Metrics ───────────────────────────────────────────────────────────────────
@app.route("/api/hook")
def api_hook():
    METRICS["pings"] += 1
    
    awake_url = request.headers.get("X-Awake-URL")
    peers_header = request.headers.get("X-Peers")
    
    if awake_url:
        update_awake_url(awake_url)
        merge_peers([awake_url])
    if peers_header:
        try:
            peer_list = [p.strip() for p in peers_header.split(',') if p.strip()]
            merge_peers(peer_list)
        except:
            pass
            
    peers = get_peers_from_db()
    if LAST_AWAKE_URL and LAST_AWAKE_URL not in peers:
        peers.append(LAST_AWAKE_URL)
        
    return jsonify({
        "status": "pulse received", 
        "timestamp": datetime.now().isoformat(),
        "peers": peers
    })

@app.route("/api/metrics")
def api_metrics():
    uptime = datetime.now() - START_TIME
    days = uptime.days
    hours, rem = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    uptime_str = f"{days}d {hours}h {minutes}m {seconds}s" if days > 0 else f"{hours}h {minutes}m {seconds}s"
    
    return jsonify({
        "pings": METRICS["pings"],
        "requests": METRICS["requests"],
        "uptime": uptime_str,
        "start_time": START_TIME.isoformat(),
        "status": "Healthy"
    })

# ── Dashboard ─────────────────────────────────────────────────────────────────
@app.route("/api/data")
def api_data():
    try:
        # Use logger's cached database instead of direct file access
        d = logger.get_db().copy()
        d["nodes"] = engine.get_node_statuses()
        d["environment"] = "Render" if "RENDER" in os.environ else "Local"
        
        # Ensure only 100 logs are sent
        if "logs" in d:
            d["logs"] = d["logs"][:100]
            
        return jsonify(d)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── History ───────────────────────────────────────────────────────────────────
@app.route("/api/history")
def api_history():
    page=int(request.args.get("page",1))
    per=int(request.args.get("per",20))
    h=logger.get_history()
    start=(page-1)*per
    return jsonify({"items":h[start:start+per],"total":len(h),"pages":-(-len(h)//per)})

@app.route("/api/history/clear",methods=["POST"])
def clear_history():
    logger._write_hist([]) # Clear the history file
    return jsonify({"ok":True})

# ── Tokens ────────────────────────────────────────────────────────────────────
@app.route("/api/tokens",methods=["GET"])
def get_tokens(): return jsonify(logger.get_tokens())

@app.route("/api/tokens",methods=["POST"])
def add_token():
    b=request.get_json(force=True)
    token_str = b.get("token","").strip()
    if not token_str: return jsonify({"error":"token required"}),400
    if len(token_str) < 40: return jsonify({"error":"Invalid token format. Discord tokens are longer."}),400
    
    tokens=logger.get_tokens()
    edit_id = b.get("id")
    existing = None
    if edit_id:
        existing = next((t for t in tokens if t["id"] == edit_id), None)
    if not existing:
        existing = next((t for t in tokens if t["token"] == token_str), None)
        
    if existing:
        existing.update({
            "token": token_str,
            "label": b.get("label", existing["label"]),
            "guild_id": b.get("guild_id", existing["guild_id"]).strip(),
            "channel_id": b.get("channel_id", existing["channel_id"]).strip(),
            "active": True
        })
        logger.save_tokens(tokens)
        logger.log_event(f"Token updated: {existing['label']}","success")
        return jsonify(existing), 200

    new={"id":str(uuid.uuid4()),"token":token_str,
         "label":b.get("label",f"Token {len(tokens)+1}"),
         "guild_id":b.get("guild_id","").strip(),"channel_id":b.get("channel_id","").strip(),"active":True}
    tokens.append(new); logger.save_tokens(tokens)
    logger.log_event(f"Token added: {new['label']}","success")
    return jsonify(new),201

@app.route("/api/tokens/<tid>",methods=["DELETE"])
def del_token(tid):
    logger.delete_token(tid)
    return jsonify({"ok":True})

@app.route("/api/tokens/<tid>/toggle",methods=["POST"])
def tog_token(tid):
    toks=logger.get_tokens()
    for t in toks:
        if t["id"]==tid: t["active"]=not t.get("active",True)
    logger.save_tokens(toks); return jsonify({"ok":True})

# ── Spam ──────────────────────────────────────────────────────────────────────
@app.route("/api/spam/config",methods=["GET"])
def get_scfg(): return jsonify(logger.get_spam_config())

@app.route("/api/spam/config",methods=["POST"])
def set_scfg():
    b=request.get_json(force=True); cfg=logger.get_spam_config()
    cfg.update({k:b[k] for k in ["message","speed","count","cooldown_after_catch"] if k in b})
    logger.save_spam_config(cfg); return jsonify(cfg)

@app.route("/api/spam/start",methods=["POST"])
def spam_start():
    b=request.get_json(force=True); ids=b.get("ids","all")
    if ids=="all": engine.start_spam_all()
    else:
        for i in ids: engine.start_spam_for(i)
    return jsonify({"ok":True})

@app.route("/api/spam/stop",methods=["POST"])
def spam_stop():
    b=request.get_json(force=True); ids=b.get("ids","all")
    if ids=="all": engine.stop_spam_all()
    else:
        for i in ids: engine.stop_spam_for(i)
    return jsonify({"ok":True})

# ── OwO ───────────────────────────────────────────────────────────────────────
@app.route("/api/owo/config",methods=["GET"])
def get_ocfg(): return jsonify(logger.get_owo_config())

@app.route("/api/owo/config",methods=["POST"])
def set_ocfg():
    b=request.get_json(force=True); cfg=logger.get_owo_config()
    cfg.update(b) # Trust the UI to send valid commands
    logger.save_owo_config(cfg); return jsonify(cfg)

@app.route("/api/owo/start",methods=["POST"])
def owo_start():
    b=request.get_json(force=True); ids=b.get("ids","all")
    if ids=="all": engine.start_owo_all()
    else:
        for i in ids: engine.start_owo_for(i)
    return jsonify({"ok":True})

@app.route("/api/owo/stop",methods=["POST"])
def owo_stop():
    b=request.get_json(force=True); ids=b.get("ids","all")
    if ids=="all": engine.stop_owo_all()
    else:
        for i in ids: engine.stop_owo_for(i)
    return jsonify({"ok":True})

@app.route("/api/owo/node_config", methods=["POST"])
def set_node_ocfg():
    b = request.get_json(force=True)
    tid = b.get("id")
    ch = b.get("owo_channel_id", "").strip()
    if not tid: return jsonify({"error": "id required"}), 400
    
    toks = logger.get_tokens()
    for t in toks:
        if t["id"] == tid:
            t["owo_channel_id"] = ch
            # Update live node if exists
            n = engine.get_node(tid)
            if n: n.owo_channel_id = ch
    logger.save_tokens(toks)
    engine._sync_persistence()
    return jsonify({"ok": True})

# ── Slash ─────────────────────────────────────────────────────────────────────
@app.route("/api/slash/config",methods=["GET"])
def get_slash_cfg(): return jsonify(logger.get_slash_config())

@app.route("/api/slash/config",methods=["POST"])
def set_slash_cfg():
    b=request.get_json(force=True); cfg=logger.get_slash_config()
    cfg.update({k:b[k] for k in ["enabled","commands"] if k in b})
    logger.save_slash_config(cfg); return jsonify(cfg)

# ── Image ─────────────────────────────────────────────────────────────────────
@app.route("/api/image/config",methods=["GET"])
def get_icfg(): return jsonify(logger.get_image_config())

@app.route("/api/image/config",methods=["POST"])
def set_icfg():
    b=request.get_json(force=True); cfg=logger.get_image_config()
    cfg.update({k:b[k] for k in ["enabled","hf_token","local_mode","local_engine","advanced_mode"] if k in b})
    logger.save_image_config(cfg); return jsonify(cfg)

@app.route("/api/image/live", methods=["GET"])
def get_image_live():
    """Returns real-time vision analysis status across all nodes."""
    nodes = engine.get_node_statuses()
    live_nodes = []
    for n in nodes:
        node_obj = engine.get_node(n["id"])
        if node_obj:
            ai_catches = getattr(node_obj, "_total_ai_catches", 0)
            conf_sum   = getattr(node_obj, "_total_ai_conf_sum", 0.0)
            avg_conf   = round(conf_sum / ai_catches, 3) if ai_catches > 0 else 0
            live_nodes.append({
                "id":             n["id"],
                "label":          n["label"],
                "catching":       node_obj.catching,
                "pending_name":   getattr(node_obj, "_pending_name", ""),
                "pending_img":    getattr(node_obj, "_pending_img", ""),
                "pending_conf":   getattr(node_obj, "_pending_conf", 0),
                "hint_count":     getattr(node_obj, "_hint_count", 0),
                "is_image_catch": getattr(node_obj, "_is_image_catch", False),
                "spawn_time":     getattr(node_obj, "_spawn_time", 0),
                "model_statuses": getattr(node_obj, "_model_statuses", {}),
                "total_ai_catches": ai_catches,
                "avg_conf":       avg_conf,
                "last_classify_ms": getattr(node_obj, "_last_classify_ms", 0),
            })
    return jsonify({"nodes": live_nodes, "timestamp": datetime.now().isoformat()})

# ── Break ─────────────────────────────────────────────────────────────────────
@app.route("/api/break/config",methods=["GET"])
def get_bcfg(): return jsonify(logger.get_break_config())

@app.route("/api/break/config",methods=["POST"])
def set_bcfg():
    b=request.get_json(force=True); cfg=logger.get_break_config()
    cfg.update({k:b[k] for k in ["enabled","start_time","duration"] if k in b})
    logger.save_break_config(cfg); return jsonify(cfg)

# ── Mimic ─────────────────────────────────────────────────────────────────────
@app.route("/api/mimic/config",methods=["GET"])
def get_mimcfg(): return jsonify(logger.get_mimic_config())

@app.route("/api/mimic/config",methods=["POST"])
def set_mimcfg():
    b=request.get_json(force=True)
    logger.save_mimic_config(b)
    return jsonify({"ok": True})

@app.route("/api/balance/sync",methods=["POST"])
def sync_bal():
    engine.sync_all_balances()
    return jsonify({"ok":True})

@app.route("/api/balance/check",methods=["POST"])
def balance_check():
    """Trigger an immediate balance fetch for all nodes.
    Sends p!bal + owo cash via Discord, waits for OwO/Poketwo to reply (up to 8s),
    then returns the freshly parsed balances."""
    import time as _time
    try:
        engine.sync_all_balances()
        # Wait for Discord replies — OwO typically replies within 1-2s
        # We wait 8s to be safe (e.g. slow network or busy channel)
        _time.sleep(8)
        # Force cache invalidation so we read fresh data from Supabase
        logger.invalidate_tokens_cache()
        tokens = logger.get_tokens()
        nodes  = engine.get_node_statuses()
        results = []
        for t in tokens:
            n   = next((x for x in nodes if x["id"] == t["id"]), {})
            bal = n.get("balances") or t.get("balances") or {}
            results.append({
                "id":        t["id"],
                "label":     t.get("label", t["id"][:8]),
                "avatar":    (n.get("profile") or {}).get("avatar", ""),
                "username":  (n.get("profile") or {}).get("username", t.get("label", "?")),
                "active":    t.get("active", True),
                "pokecoins": bal.get("pokecoins", 0),
                "cowoncy":   bal.get("cowoncy", 0),
                "last_sync": bal.get("last_sync", "Never"),
            })
        return jsonify({"ok": True, "results": results, "checked_at": datetime.now().isoformat()})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/balance/data",methods=["GET"])
def balance_data():
    """Return latest stored balance data from engine in-memory state (live, no Supabase round-trip)."""
    nodes  = engine.get_node_statuses()
    tokens = logger.get_tokens()
    results = []
    for n in nodes:
        t   = next((x for x in tokens if x["id"] == n["id"]), {})
        bal = n.get("balances") or t.get("balances") or {}
        results.append({
            "id":        n["id"],
            "label":     n.get("label", n["id"][:8]),
            "avatar":    (n.get("profile") or {}).get("avatar", ""),
            "username":  (n.get("profile") or {}).get("username", t.get("label", "?")),
            "active":    t.get("active", True),
            "pokecoins": bal.get("pokecoins", 0),
            "cowoncy":   bal.get("cowoncy", 0),
            "last_sync": bal.get("last_sync", "Never"),
        })
    total_pk  = sum(r["pokecoins"] for r in results)
    total_owo = sum(r["cowoncy"]   for r in results)
    return jsonify({"ok": True, "results": results, "total_pokecoins": total_pk, "total_cowoncy": total_owo})

@app.route("/api/tokens/invalidate", methods=["POST"])
def invalidate_token_cache():
    """Force Supabase re-read on next token fetch (used after deletes)."""
    logger.invalidate_tokens_cache()
    return jsonify({"ok": True})

# ── Captcha ───────────────────────────────────────────────────────────────────
@app.route("/api/captcha/clear", methods=["POST"])
def clear_captcha():
    engine.resume_all_captchas()
    from logger import resolve_captcha_in_history
    nodes = engine.get_node_statuses()
    for n in nodes:
        resolve_captcha_in_history(n["label"])
    return jsonify({"ok": True})

@app.route("/api/captcha/clear/<tid>", methods=["POST"])
def clear_captcha_for(tid):
    engine.resume_captcha_for(tid)
    # Mark this token's history entries as resolved
    from logger import resolve_captcha_in_history
    toks = logger.get_tokens()
    for t in toks:
        if t["id"] == tid:
            resolve_captcha_in_history(t.get("label", tid[:8]))
            break
    return jsonify({"ok": True})

@app.route("/api/captcha/history", methods=["GET"])
def get_captcha_history():
    from logger import get_captcha_history as _gch
    return jsonify({"history": _gch()})

@app.route("/api/captcha/history/clear", methods=["POST"])
def clear_captcha_history():
    from logger import clear_captcha_history as _cch
    _cch()
    return jsonify({"ok": True})


# ── Msg Loop ──────────────────────────────────────────────────────────────────
@app.route("/api/msg/channels/<tid>", methods=["GET"])
def get_node_channels(tid):
    n = engine.get_node(tid)
    if not n: return jsonify({"error": "Node not found"}), 404
    try:
        guilds = n.get_guilds_and_channels()
        return jsonify({"guilds": guilds, "count": len(guilds)})
    except Exception as e:
        return jsonify({"error": str(e), "guilds": []}), 500

@app.route("/api/msg/start", methods=["POST"])
def msg_start():
    b = request.get_json(force=True); ids = b.get("ids", "all")
    if ids == "all":
        for n in engine._nodes.values(): n.start_msg()
    else:
        for i in ids:
            n = engine.get_node(i)
            if n: n.start_msg()
    engine._sync_persistence()
    return jsonify({"ok": True})

@app.route("/api/msg/stop", methods=["POST"])
def msg_stop():
    b = request.get_json(force=True); ids = b.get("ids", "all")
    if ids == "all":
        for n in engine._nodes.values(): n.stop_msg()
    else:
        for i in ids:
            n = engine.get_node(i)
            if n: n.stop_msg()
    engine._sync_persistence()
    return jsonify({"ok": True})

@app.route("/api/msg/node_config", methods=["POST"])
def set_node_msgcfg():
    b = request.get_json(force=True)
    tid = b.get("id")
    ch = b.get("msg_channel_id", "").strip()
    delay = int(b.get("msg_delay", 30))
    is_random = bool(b.get("msg_random_delay", False))
    if not tid: return jsonify({"error": "id required"}), 400
    
    toks = logger.get_tokens()
    for t in toks:
        if t["id"] == tid:
            t["msg_channel_id"] = ch
            t["msg_delay"] = delay
            t["msg_random_delay"] = is_random
            # Update live node if exists
            n = engine.get_node(tid)
            if n:
                n.msg_channel_id = ch
                n.msg_delay = delay
                n.msg_random_delay = is_random
    logger.save_tokens(toks)
    engine._sync_persistence()
    return jsonify({"ok": True})

@app.route("/api/msg/send_txt", methods=["GET"])
def get_send_txt():
    path = os.path.join("chat", "send.txt")
    if not os.path.exists(path):
        os.makedirs("chat", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write("dont check my bio\nhey sup\n")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return jsonify({"content": content})

@app.route("/api/msg/send_txt", methods=["POST"])
def save_send_txt():
    b = request.get_json(force=True)
    content = b.get("content", "")
    path = os.path.join("chat", "send.txt")
    os.makedirs("chat", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return jsonify({"ok": True})


# ── Pokédex ───────────────────────────────────────────────────────────────────
@app.route("/api/dex", methods=["GET"])
def get_dex():
    q = request.args.get("q", "").lower().strip()
    all_names = pokemon_loader.load_pokemon_list()
    caught_stats = logger.get_dex()
    
    entries = []
    for name in all_names:
        key = name.lower().strip()
        if key in caught_stats:
            entry = caught_stats[key]
        else:
            entry = {
                "name": key,
                "display_name": name.title().replace("-", " "),
                "caught_count": 0,
                "shiny_count": 0,
                "first_caught": None,
                "last_caught": None,
                "notes": "",
                "favorite": False,
                "img": ""
            }
        
        if q:
            match_name = entry.get("name", "").lower()
            match_disp = entry.get("display_name", "").lower()
            match_notes = entry.get("notes", "").lower()
            if q not in match_name and q not in match_disp and q not in match_notes:
                continue
                
        entries.append(entry)
        
    entries.sort(key=lambda x: (not x.get("favorite", False), -x.get("caught_count", 0), x.get("name", "")))
    return jsonify({"entries": entries, "total": len(entries)})

@app.route("/api/dex/<name>", methods=["POST"])
def upsert_dex(name):
    b = request.get_json(force=True)
    key = name.lower().strip()
    if not key:
        return jsonify({"error": "Name is required"}), 400
        
    pokemon_loader.add_custom_pokemon(key)
    
    d = logger.get_dex()
    existing = d.get(key, {
        "name": key,
        "display_name": name.title().replace("-", " "),
        "caught_count": 0,
        "shiny_count": 0,
        "first_caught": datetime.now().isoformat(),
        "last_caught": datetime.now().isoformat(),
        "notes": "",
        "favorite": False,
        "img": ""
    })
    
    existing.update({k: b[k] for k in ["display_name", "notes", "favorite", "img",
                                        "caught_count", "shiny_count"] if k in b})
    d[key] = existing
    logger.save_dex(d)
    return jsonify(existing)

@app.route("/api/dex/<name>", methods=["DELETE"])
def delete_dex(name):
    key = name.lower().strip()
    if not key:
        return jsonify({"error": "Name is required"}), 400
        
    pokemon_loader.remove_custom_pokemon(key)
    
    d = logger.get_dex()
    d.pop(key, None)
    logger.save_dex(d)
    return jsonify({"ok": True})

@app.route("/api/dex/backfill", methods=["POST"])
def backfill_dex():
    logger.backfill_dex_from_history()
    return jsonify({"ok": True, "total": len(logger.get_dex())})

# ── Reset ─────────────────────────────────────────────────────────────────────
@app.route("/api/reset",methods=["POST"])
def reset():
    logger._write({"caught": 0, "faults": 0})
    logger._logs_cache.clear()
    return jsonify({"ok":True})

# ── Test & Verification ────────────────────────────────────────────────────────
@app.route("/test")
@app.route("/test.html")
@app.route("/test/")
@app.route("/tets")
@app.route("/tets.html")
def test_p():      return _tpl("test.html")

# ── Check single channel (returns writable, text_allowed, link_allowed) ────────
@app.route("/api/test/check-channel", methods=["POST"])
def check_channel():
    import time as _time
    b = request.get_json(force=True)
    tid = b.get("token_id")
    ch_id = b.get("channel_id")
    save = b.get("save", False)           # persist result to Supabase?
    guild_id = b.get("guild_id", "")
    guild_name = b.get("guild_name", "")
    ch_name = b.get("channel_name", "")
    token_label = b.get("token_label", "")

    if not tid or not ch_id:
        return jsonify({"error": "token_id and channel_id are required"}), 400

    n = engine.get_node(tid)
    if not n:
        return jsonify({"error": "Node not found"}), 404

    writable = False
    text_allowed = False
    link_allowed = False
    reason = ""

    # Test 1: plain text
    try:
        resp = n.bot.sendMessage(ch_id, "xtreme connectivity check")
        if resp.status_code in [200, 201]:
            text_allowed = True
            writable = True
            msg_id = resp.json().get("id")
            if msg_id:
                n.bot.deleteMessage(ch_id, msg_id)
        else:
            reason = f"HTTP {resp.status_code}"
    except Exception as e:
        reason = str(e)

    # Test 2: link (only if text worked)
    if writable:
        try:
            resp2 = n.bot.sendMessage(ch_id, "https://discord.gg/xtreme-test")
            if resp2.status_code in [200, 201]:
                link_allowed = True
                msg_id2 = resp2.json().get("id")
                if msg_id2:
                    n.bot.deleteMessage(ch_id, msg_id2)
        except Exception:
            link_allowed = False

    result = {
        "writable": writable,
        "text_allowed": text_allowed,
        "link_allowed": link_allowed,
        "reason": reason,
    }

    # Persist to Supabase `test` table if requested
    if save:
        from datetime import datetime as _dt
        row_id = f"{tid[:8]}_{ch_id}"
        row = {
            "id":           row_id,
            "token_id":     tid,
            "token_label":  token_label or tid[:8],
            "guild_id":     guild_id,
            "guild_name":   guild_name,
            "channel_id":   ch_id,
            "channel_name": ch_name,
            "writable":     writable,
            "text_allowed": text_allowed,
            "link_allowed": link_allowed,
            "last_scan":    _dt.utcnow().isoformat(),
            "scan_reason":  reason,
        }
        Thread(target=logger.save_test_result, args=(row,), daemon=True).start()

    return jsonify(result)


# ── Master scan: all live tokens, all their channels, in parallel ──────────────
@app.route("/api/test/master-scan", methods=["POST"])
def master_scan():
    """
    Scans ALL channels across ALL (or specified) live token nodes.
    Saves every result to Supabase `test` table.
    Returns results immediately as JSON.
    """
    import concurrent.futures
    from datetime import datetime as _dt
    b = request.get_json(force=True)
    token_ids = b.get("token_ids", [])   # empty = all live nodes

    nodes_to_scan = []
    all_tokens = {t["id"]: t for t in logger.get_tokens()}

    if token_ids:
        for tid in token_ids:
            n = engine.get_node(tid)
            if n:
                nodes_to_scan.append((tid, n, all_tokens.get(tid, {})))
    else:
        with engine._nlock:
            for tid, n in engine._nodes.items():
                nodes_to_scan.append((tid, n, all_tokens.get(tid, {})))

    if not nodes_to_scan:
        return jsonify({"error": "No live nodes found"}), 404

    all_results = []   # flat list of channel result dicts

    def scan_channel(tid, n, tok, guild, ch):
        ch_id = ch["id"]
        ch_name = ch["name"]
        guild_id = guild["id"]
        guild_name = guild["name"]
        token_label = tok.get("label", tid[:8])
        row_id = f"{tid[:8]}_{ch_id}"

        writable = False
        text_allowed = False
        link_allowed = False
        reason = ""
        try:
            r = n.bot.sendMessage(ch_id, "xtreme scan")
            if r.status_code in [200, 201]:
                text_allowed = True
                writable = True
                mid = r.json().get("id")
                if mid:
                    n.bot.deleteMessage(ch_id, mid)
            else:
                reason = f"HTTP {r.status_code}"
        except Exception as e:
            reason = str(e)

        if writable:
            try:
                r2 = n.bot.sendMessage(ch_id, "https://discord.gg/xtreme-scan")
                if r2.status_code in [200, 201]:
                    link_allowed = True
                    mid2 = r2.json().get("id")
                    if mid2:
                        n.bot.deleteMessage(ch_id, mid2)
            except Exception:
                link_allowed = False

        row = {
            "id":           row_id,
            "token_id":     tid,
            "token_label":  token_label,
            "guild_id":     guild_id,
            "guild_name":   guild_name,
            "channel_id":   ch_id,
            "channel_name": ch_name,
            "writable":     writable,
            "text_allowed": text_allowed,
            "link_allowed": link_allowed,
            "last_scan":    _dt.utcnow().isoformat(),
            "scan_reason":  reason,
        }
        logger.save_test_result(row)
        return row

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        futs = []
        for tid, n, tok in nodes_to_scan:
            try:
                guilds = n.get_guilds_and_channels()
            except Exception:
                continue
            for guild in guilds:
                for ch in guild.get("channels", []):
                    futs.append(pool.submit(scan_channel, tid, n, tok, guild, ch))

        for f in concurrent.futures.as_completed(futs):
            try:
                all_results.append(f.result())
            except Exception:
                pass

    return jsonify({"ok": True, "total": len(all_results), "results": all_results})


# ── Background queued master scan (6-9s gaps, persistent across page reloads) ──
import random as _random
_scan_jobs = {}   # job_id -> { status, total, done, results, errors, log }
_scan_jobs_lock = threading.Lock()

def _queued_scan_worker(job_id: str, nodes_to_scan: list):
    """Sequential background scanner. 6-9s gap between each message. Runs even if browser closes."""
    import time as _time
    from datetime import datetime as _dt

    def _update(patch: dict):
        with _scan_jobs_lock:
            if job_id in _scan_jobs:
                _scan_jobs[job_id].update(patch)

    def _log(msg: str):
        with _scan_jobs_lock:
            if job_id in _scan_jobs:
                _scan_jobs[job_id]["log"].append(msg)
                # cap log at 500 entries
                if len(_scan_jobs[job_id]["log"]) > 500:
                    _scan_jobs[job_id]["log"] = _scan_jobs[job_id]["log"][-500:]

    # Build full channel task list first
    tasks = []
    for tid, n, tok in nodes_to_scan:
        try:
            guilds = n.get_guilds_and_channels()
        except Exception as e:
            _log(f"[{tok.get('label', tid[:8])}] Failed to load guilds: {e}")
            continue
        for guild in guilds:
            for ch in guild.get("channels", []):
                tasks.append((tid, n, tok, guild, ch))

    _update({"total": len(tasks), "status": "running"})
    _log(f"Starting scan: {len(tasks)} channels across {len(nodes_to_scan)} token(s)")

    results = []
    for i, (tid, n, tok, guild, ch) in enumerate(tasks):
        with _scan_jobs_lock:
            if _scan_jobs.get(job_id, {}).get("cancelled"):
                _log("Scan cancelled by user.")
                break

        ch_id = ch["id"]
        ch_name = ch.get("name", ch_id)
        guild_id = guild["id"]
        guild_name = guild.get("name", guild_id)
        token_label = tok.get("label", tid[:8])
        row_id = f"{tid[:8]}_{ch_id}"

        writable = False
        text_allowed = False
        link_allowed = False
        reason = ""

        _log(f"[{token_label}] #{ch_name} ({ch_id}) — sending text...")

        # Test 1: plain text
        try:
            r = n.bot.sendMessage(ch_id, "xtreme connectivity check")
            if r.status_code in [200, 201]:
                text_allowed = True
                writable = True
                mid = r.json().get("id")
                _log(f"[{token_label}] #{ch_name} — text ✓, deleting...")
                gap1 = _random.uniform(6, 9)
                _time.sleep(gap1)
                if mid:
                    try:
                        n.bot.deleteMessage(ch_id, mid)
                    except Exception:
                        pass
            else:
                reason = f"HTTP {r.status_code}"
                _log(f"[{token_label}] #{ch_name} — text ✗ ({reason})")
        except Exception as e:
            reason = str(e)
            _log(f"[{token_label}] #{ch_name} — text error: {reason}")

        # 6-9s gap before link test
        if writable:
            gap2 = _random.uniform(6, 9)
            _log(f"[{token_label}] #{ch_name} — waiting {gap2:.1f}s before link test...")
            _time.sleep(gap2)
            try:
                r2 = n.bot.sendMessage(ch_id, "https://discord.gg/xtreme-test")
                if r2.status_code in [200, 201]:
                    link_allowed = True
                    mid2 = r2.json().get("id")
                    _log(f"[{token_label}] #{ch_name} — link ✓, deleting...")
                    gap3 = _random.uniform(6, 9)
                    _time.sleep(gap3)
                    if mid2:
                        try:
                            n.bot.deleteMessage(ch_id, mid2)
                        except Exception:
                            pass
                else:
                    _log(f"[{token_label}] #{ch_name} — link ✗ (HTTP {r2.status_code})")
            except Exception:
                link_allowed = False

        row = {
            "id":           row_id,
            "token_id":     tid,
            "token_label":  token_label,
            "guild_id":     guild_id,
            "guild_name":   guild_name,
            "channel_id":   ch_id,
            "channel_name": ch_name,
            "writable":     writable,
            "text_allowed": text_allowed,
            "link_allowed": link_allowed,
            "last_scan":    _dt.utcnow().isoformat(),
            "scan_reason":  reason,
        }
        logger.save_test_result(row)
        results.append(row)

        status_icon = "✓" if writable else "✗"
        _log(f"[{token_label}] #{ch_name} — {status_icon} writable={writable} text={text_allowed} link={link_allowed}")

        _update({"done": i + 1, "results": list(results)})

        # Gap between channels (6-9s) — only if not last
        if i < len(tasks) - 1:
            gap = _random.uniform(6, 9)
            _log(f"Waiting {gap:.1f}s before next channel...")
            _time.sleep(gap)

    _update({"status": "done", "done": len(tasks), "results": list(results)})
    _log(f"Scan complete. {sum(1 for r in results if r['writable'])} writable / {len(results)} total channels.")


@app.route("/api/test/master-scan-queued", methods=["POST"])
def master_scan_queued():
    """
    Starts a background sequential scan with 6-9s gaps.
    Returns a job_id immediately. Poll /api/test/scan-status/<job_id> for progress.
    """
    b = request.get_json(force=True)
    token_ids = b.get("token_ids", [])   # empty = all live nodes

    nodes_to_scan = []
    all_tokens = {t["id"]: t for t in logger.get_tokens()}

    if token_ids:
        for tid in token_ids:
            n = engine.get_node(tid)
            if n:
                nodes_to_scan.append((tid, n, all_tokens.get(tid, {})))
    else:
        with engine._nlock:
            for tid, n in engine._nodes.items():
                nodes_to_scan.append((tid, n, all_tokens.get(tid, {})))

    if not nodes_to_scan:
        return jsonify({"error": "No live nodes found"}), 404

    job_id = str(uuid.uuid4())[:12]
    with _scan_jobs_lock:
        _scan_jobs[job_id] = {
            "status":    "starting",
            "total":     0,
            "done":      0,
            "cancelled": False,
            "results":   [],
            "log":       [],
            "token_ids": token_ids or list(engine._nodes.keys()),
        }

    t = threading.Thread(
        target=_queued_scan_worker,
        args=(job_id, nodes_to_scan),
        daemon=True,
        name=f"master-scan-{job_id[:6]}"
    )
    t.start()

    return jsonify({"ok": True, "job_id": job_id})


@app.route("/api/test/scan-status/<job_id>", methods=["GET"])
def scan_status(job_id):
    with _scan_jobs_lock:
        job = _scan_jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    # Return lightweight copy (exclude large results list from log endpoint)
    since_log = int(request.args.get("since_log", 0))
    return jsonify({
        "status":   job["status"],
        "total":    job["total"],
        "done":     job["done"],
        "results":  job["results"],
        "log":      job["log"][since_log:],
        "log_total": len(job["log"]),
    })


@app.route("/api/test/scan-cancel/<job_id>", methods=["POST"])
def scan_cancel(job_id):
    with _scan_jobs_lock:
        if job_id in _scan_jobs:
            _scan_jobs[job_id]["cancelled"] = True
            return jsonify({"ok": True})
    return jsonify({"error": "Job not found"}), 404


# ── Get saved test results ─────────────────────────────────────────────────────
@app.route("/api/test/results", methods=["GET"])
def get_test_results():
    token_id = request.args.get("token_id")
    results = logger.get_test_results()
    if token_id:
        results = [r for r in results if r.get("token_id") == token_id]
    return jsonify({"results": results, "total": len(results)})


# ── Clear test results ─────────────────────────────────────────────────────────
@app.route("/api/test/results/clear", methods=["POST"])
def clear_test_results():
    b = request.get_json(force=True)
    token_id = b.get("token_id")
    if token_id:
        logger.clear_test_results_for_token(token_id)
    else:
        logger.clear_all_test_results()
    return jsonify({"ok": True})

@app.route("/api/test/send-and-delete", methods=["POST"])
def send_and_delete_test():
    import random
    b = request.get_json(force=True)
    tid = b.get("token_id")
    channel_ids = b.get("channel_ids", [])
    guild_id = b.get("guild_id")
    msg_type = b.get("type", "both") # "text", "link", "both"
    custom_text = b.get("text", "").strip()
    custom_link = b.get("link", "").strip()
    
    if not tid:
        return jsonify({"error": "token_id is required"}), 400
        
    n = engine.get_node(tid)
    if not n:
        return jsonify({"error": "Node not found"}), 404
        
    try:
        resolved_channels = []
        if not channel_ids and guild_id:
            guilds = n.get_guilds_and_channels()
            guild = next((g for g in guilds if g["id"] == guild_id), None)
            if guild:
                resolved_channels = guild.get("channels", [])
        elif channel_ids:
            guilds = n.get_guilds_and_channels()
            all_channels = {}
            for g in guilds:
                for ch in g.get("channels", []):
                    all_channels[ch["id"]] = ch["name"]
            for cid in channel_ids:
                resolved_channels.append({
                    "id": cid,
                    "name": all_channels.get(cid, cid)
                })
                
        if not resolved_channels:
            return jsonify({"error": "No channels specified or resolved"}), 400
            
        results = []
        
        default_texts = [
            "Just checking the server connectivity.",
            "Testing node channel permissions.",
            "System telemetry scan in progress.",
            "Xtreme performance test.",
            "Organic latency test."
        ]
        default_links = [
            "https://discord.gg/xtreme",
            "https://github.com/google/xtreme",
            "https://xtreme-project.local"
        ]
        
        text_to_send = custom_text or random.choice(default_texts)
        link_to_send = custom_link or random.choice(default_links)
        
        if msg_type == "text":
            payload = text_to_send
        elif msg_type == "link":
            payload = link_to_send
        else: # both
            payload = f"{text_to_send} {link_to_send}"
            
        for ch in resolved_channels:
            ch_id = ch["id"]
            ch_name = ch["name"]
            try:
                resp = n.bot.sendMessage(ch_id, payload)
                if resp.status_code in [200, 201]:
                    msg_id = resp.json().get("id")
                    if msg_id:
                        n.bot.deleteMessage(ch_id, msg_id)
                    results.append({"channel_id": ch_id, "name": ch_name, "success": True})
                else:
                    results.append({"channel_id": ch_id, "name": ch_name, "success": False, "reason": f"HTTP {resp.status_code}"})
            except Exception as ex:
                results.append({"channel_id": ch_id, "name": ch_name, "success": False, "reason": str(ex)})
                
        return jsonify({"ok": True, "results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── Server & Member Scanner Dashboard Routes ───────────────────────────
def handle_scanner_error(e):
    err_str = str(e)
    # Catch all known Supabase schema-missing patterns
    schema_missing_signals = [
        "PGRST205", "schema cache", "public.scanned_", "public.scan_config",
        "relation \"scanned", "does not exist", "42703", "42P01",
        "undefined_table", "undefined_column"
    ]
    if any(sig in err_str for sig in schema_missing_signals):
        return jsonify({
            "ok": False,
            "error": "DATABASE_TABLES_MISSING",
            "message": "Scanner tables not found in Supabase database. Please copy the SQL statements in supabase_schema_additions.sql and run them in your Supabase SQL Editor to initialize."
        })
    return jsonify({"error": err_str}), 500

@app.route("/data")
@app.route("/data.html")
def data_page():
    return _tpl("data.html")

@app.route("/api/scan/config", methods=["GET", "POST"])
def api_scan_config():
    if request.method == "POST":
        try:
            b = request.get_json(force=True)
            logger.log_event(f"Scanner Config Saved: auto_scan={b.get('auto_scan')}, selected_tokens={b.get('selected_tokens')}", "info")
            data.save_scan_config(b)
            return jsonify({"ok": True})
        except Exception as e:
            return handle_scanner_error(e)
    else:
        try:
            return jsonify(data.get_scan_config())
        except Exception as e:
            return handle_scanner_error(e)

@app.route("/api/scan/status", methods=["GET"])
def api_scan_status():
    try:
        with data._scans_lock:
            state = {}
            for (token_id, guild_id), val in data.ACTIVE_SCANS.items():
                state[f"{token_id}:{guild_id}"] = val
        
        # Add diagnostics
        nodes_diag = {}
        for tid in [t["id"] for t in logger.get_tokens()]:
            node = engine.get_node(tid)
            if node:
                try:
                    sr = node.bot.gateway.session.settings_ready
                    srs = node.bot.gateway.session.settings_ready_supp
                    nodes_diag[tid] = {
                        "connected": node.bot.gateway.connected,
                        "ready_flag": node.bot.gateway.READY,
                        "sr_type": str(type(sr)),
                        "sr_keys": list(sr.keys()) if isinstance(sr, dict) else None,
                        "srs_keys": list(srs.keys()) if isinstance(srs, dict) else None
                    }
                except Exception as ex:
                    nodes_diag[tid] = {"error": str(ex)}
            else:
                nodes_diag[tid] = {"status": "not_active_in_engine"}

        return jsonify({"scans": state, "diagnostics": nodes_diag})
    except Exception as e:
        return handle_scanner_error(e)

@app.route("/api/scan/debug", methods=["GET"])
def api_scan_debug():
    try:
        debug_info = {}
        for tid in [t["id"] for t in logger.get_tokens()]:
            node = engine.get_node(tid)
            if node:
                gw = node.bot.gateway
                debug_info[node.label] = {
                    "token_id": tid,
                    "connected": gw.connected,
                    "ready": gw.READY,
                    "session_id": getattr(gw, "session_id", None),
                    "sequence": getattr(gw, "sequence", 0),
                    "has_session_obj": gw.session is not None,
                    "session_class": str(type(gw.session)),
                    "sr_is_dict": isinstance(gw.session._settings_ready, dict),
                    "sr_len": len(gw.session._settings_ready) if isinstance(gw.session._settings_ready, dict) else -1,
                    "sr_keys": list(gw.session._settings_ready.keys())[:15] if isinstance(gw.session._settings_ready, dict) else [],
                    "srs_len": len(gw.session._settings_ready_supp) if isinstance(gw.session._settings_ready_supp, dict) else -1,
                    "srs_keys": list(gw.session._settings_ready_supp.keys())[:15] if isinstance(gw.session._settings_ready_supp, dict) else [],
                }
            else:
                debug_info[tid] = "not_active"
        return jsonify(debug_info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/scan/user/<uid>/profile", methods=["POST"])
def api_scan_user_profile(uid):
    try:
        bio = data.fetch_user_bio_now(uid)
        return jsonify({"ok": True, "bio": bio})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.route("/api/scan/start", methods=["POST"])
def api_scan_start():
    try:
        b = request.get_json(force=True)
        guild_ids = b.get("guild_ids", [])
        token_ids = b.get("token_ids", [])
        
        if not guild_ids:
            return jsonify({"error": "guild_ids required"}), 400
        
        # If no token_ids provided, use all active ones
        if not token_ids:
            tokens = logger.get_tokens()
            token_ids = [t["id"] for t in tokens if t.get("active", True)]
            
        success_count = 0
        for gid in guild_ids:
            # Find which token is in this guild
            target_token = None
            guild_name = None
            for tid in token_ids:
                node = engine.get_node(tid)
                if node:
                    guilds = node.get_guilds_and_channels()
                    g_match = next((g for g in guilds if g["id"] == gid), None)
                    if g_match:
                        target_token = tid
                        guild_name = g_match["name"]
                        break
            
            if target_token:
                if data.trigger_guild_scan(target_token, gid, guild_name):
                    success_count += 1
                    
        return jsonify({"ok": True, "triggered": success_count})
    except Exception as e:
        return handle_scanner_error(e)

@app.route("/api/scan/stop", methods=["POST"])
def api_scan_stop():
    try:
        with data._scans_lock:
            for k in list(data.ACTIVE_SCANS.keys()):
                data.ACTIVE_SCANS[k]["status"] = "stopped"
        invalidate_servers_cache()
        return jsonify({"ok": True})
    except Exception as e:
        return handle_scanner_error(e)

# ── In-memory TTL cache for the expensive servers endpoint ──────────────
_servers_cache_data = None
_servers_cache_ts   = 0.0
_SERVERS_CACHE_TTL  = 25  # seconds

@app.route("/api/scan/servers", methods=["GET"])
def api_scan_servers():
    global _servers_cache_data, _servers_cache_ts
    import time as _time_mod
    try:
        # Serve from cache if fresh
        now = _time_mod.time()
        if _servers_cache_data is not None and (now - _servers_cache_ts) < _SERVERS_CACHE_TTL:
            return jsonify({"servers": _servers_cache_data, "cached": True})

        tokens = logger.get_tokens()
        active_tids = [t["id"] for t in tokens if t.get("active", True)]

        guilds_map = {}
        for tid in active_tids:
            node = engine.get_node(tid)
            if node:
                guilds = node.get_guilds_and_channels()
                for g in guilds:
                    g_id = g["id"]
                    member_count = 0
                    icon_url = ""
                    try:
                        g_obj = node.bot.gateway.session.guild(g_id)
                        if g_obj:
                            try:
                                mc = g_obj.memberCount
                                member_count = mc if mc else 0
                            except (KeyError, AttributeError):
                                member_count = 0
                            try:
                                icon_hash = g_obj.icon
                                if icon_hash:
                                    icon_url = f"https://cdn.discordapp.com/icons/{g_id}/{icon_hash}.png"
                            except (KeyError, AttributeError):
                                pass
                    except Exception:
                        pass

                    if g_id not in guilds_map:
                        guilds_map[g_id] = {
                            "id":           g_id,
                            "name":         g["name"],
                            "member_count": member_count,
                            "icon":         icon_url,
                            "tokens":       [tid]
                        }
                    else:
                        guilds_map[g_id]["tokens"].append(tid)
                        if member_count > guilds_map[g_id]["member_count"]:
                            guilds_map[g_id]["member_count"] = member_count

        scanned_guilds = {}
        try:
            res = logger._sb.table("scanned_guilds").select("id,name,icon,invite_link,last_scanned").execute()
            if res.data:
                for g in res.data:
                    scanned_guilds[g["id"]] = g
        except:
            pass

        cfg = data.get_scan_config()
        priority_guilds = cfg.get("priority_guilds", [])

        result = []
        for gid, ginfo in guilds_map.items():
            db_info = scanned_guilds.get(gid, {})
            result.append({
                **ginfo,
                "invite_link":  db_info.get("invite_link", "No Invite Link"),
                "last_scanned": db_info.get("last_scanned"),
                "priority":     gid in priority_guilds
            })

        # Store in cache
        _servers_cache_data = result
        _servers_cache_ts   = now

        return jsonify({"servers": result})
    except Exception as e:
        logger.log_event(f"Servers API Error: {e}", "error")
        return handle_scanner_error(e)

def invalidate_servers_cache():
    """Call after a scan completes or priority changes to force refresh."""
    global _servers_cache_data
    _servers_cache_data = None


@app.route("/api/scan/priority", methods=["POST"])
def api_scan_priority():
    try:
        b = request.get_json(force=True)
        gid = b.get("guild_id")
        if not gid:
            return jsonify({"error": "guild_id required"}), 400

        cfg = data.get_scan_config()
        priority_guilds = cfg.get("priority_guilds", [])

        if gid in priority_guilds:
            priority_guilds.remove(gid)
        else:
            priority_guilds.append(gid)

        cfg["priority_guilds"] = priority_guilds
        data.save_scan_config(cfg)
        invalidate_servers_cache()  # force refresh so priority star updates
        return jsonify({"ok": True, "priority": gid in priority_guilds})
    except Exception as e:
        return handle_scanner_error(e)

@app.route("/api/scan/search", methods=["GET"])
def api_scan_search():
    try:
        q = request.args.get("q", "").strip()
        sort_by = request.args.get("sort", "username")
        filter_type = request.args.get("filter", "all")
        
        if not q:
            # No query — return 50 most recently updated users
            try:
                res = logger._sb.table("scanned_users").select("*").order("updated_at", desc=True).limit(50).execute()
                users = res.data or []
            except Exception as e:
                err_msg = str(e)
                if any(sig in err_msg for sig in ["PGRST205", "schema cache", "scanned_", "does not exist", "42P01"]):
                    raise e
                users = []
        else:
            matched_users = {}
            q_safe = q.replace("'", "''")  # basic escape for ilike

            # ── Phase 1: Search TEXT columns (safe for PostgREST ilike) ──────────
            try:
                res_users = logger._sb.table("scanned_users").select("*").or_(
                    f"username.ilike.%{q_safe}%,custom_status.ilike.%{q_safe}%,bio.ilike.%{q_safe}%"
                ).execute()
                if res_users.data:
                    for u in res_users.data:
                        matched_users[u["id"]] = u
            except Exception as e:
                err_msg = str(e)
                if any(sig in err_msg for sig in ["PGRST205", "schema cache", "scanned_", "does not exist", "42P01"]):
                    raise e
                print(f"[Scanner Search] Text user query error: {e}", flush=True)

            # ── Phase 2: JSONB history search (Python-side) ────────────────────
            # Only runs when query >= 3 chars AND phase 1 returned < 20 results.
            # Avoids fetching 500 rows on every short/empty query.
            try:
                if len(q) >= 3 and len(matched_users) < 20:
                    all_users_res = logger._sb.table("scanned_users").select(
                        "id,username,avatar,bio,custom_status,status,bot,past_usernames,past_bios,updated_at"
                    ).order("updated_at", desc=True).limit(300).execute()
                    if all_users_res.data:
                        q_lower = q.lower()
                        for u in all_users_res.data:
                            if u["id"] in matched_users:
                                continue
                            past_names = u.get("past_usernames") or []
                            past_bios_list = u.get("past_bios") or []
                            if isinstance(past_names, list) and any(q_lower in str(n).lower() for n in past_names):
                                matched_users[u["id"]] = u
                            elif isinstance(past_bios_list, list) and any(q_lower in str(b).lower() for b in past_bios_list):
                                matched_users[u["id"]] = u
            except Exception as e:
                err_msg = str(e)
                if any(sig in err_msg for sig in ["PGRST205", "schema cache", "scanned_", "does not exist", "42P01"]):
                    raise e
                print(f"[Scanner Search] JSONB user history search error: {e}", flush=True)

            # ── Phase 3: Search scanned_members TEXT columns (nickname) ───────────
            try:
                res_members = logger._sb.table("scanned_members").select("user_id,past_nicknames").or_(
                    f"nickname.ilike.%{q_safe}%"
                ).execute()
                if res_members.data:
                    uids = list(set(m["user_id"] for m in res_members.data if m.get("user_id")))
                    uids_to_fetch = [uid for uid in uids if uid not in matched_users]
                    if uids_to_fetch:
                        batch_size = 400
                        for idx in range(0, len(uids_to_fetch), batch_size):
                            slice_ids = uids_to_fetch[idx:idx+batch_size]
                            res_m_users = logger._sb.table("scanned_users").select("*").in_("id", slice_ids).execute()
                            if res_m_users.data:
                                for u in res_m_users.data:
                                    matched_users[u["id"]] = u
            except Exception as e:
                err_msg = str(e)
                if any(sig in err_msg for sig in ["PGRST205", "schema cache", "scanned_", "does not exist", "42P01"]):
                    raise e
                print(f"[Scanner Search] Nickname query error: {e}", flush=True)

            # ── Phase 4: past_nicknames JSONB (Python-side) ──────────────────
            # Only runs when query >= 3 chars AND we have fewer than 20 total.
            try:
                if len(q) >= 3 and len(matched_users) < 20:
                    q_lower = q.lower()
                    all_members_res = logger._sb.table("scanned_members").select(
                        "user_id,past_nicknames"
                    ).not_.is_("past_nicknames", "null").limit(500).execute()
                    if all_members_res.data:
                        extra_uids = set()
                        for m in all_members_res.data:
                            uid = m.get("user_id")
                            if not uid or uid in matched_users:
                                continue
                            past_nicks = m.get("past_nicknames") or []
                            if isinstance(past_nicks, list) and any(q_lower in str(n).lower() for n in past_nicks):
                                extra_uids.add(uid)
                        if extra_uids:
                            extra_list = list(extra_uids)
                            for idx in range(0, len(extra_list), 400):
                                slice_ids = extra_list[idx:idx+400]
                                res_eu = logger._sb.table("scanned_users").select("*").in_("id", slice_ids).execute()
                                if res_eu.data:
                                    for u in res_eu.data:
                                        if u["id"] not in matched_users:
                                            matched_users[u["id"]] = u
            except Exception as e:
                err_msg = str(e)
                if any(sig in err_msg for sig in ["PGRST205", "schema cache", "scanned_", "does not exist", "42P01"]):
                    raise e
                print(f"[Scanner Search] Past nicknames JSONB search error: {e}", flush=True)

            users = list(matched_users.values())
        
        # ── Apply bot/human filter ────────────────────────────────────────────────
        if filter_type == "bots":
            users = [u for u in users if u.get("bot", False)]
        elif filter_type == "humans":
            users = [u for u in users if not u.get("bot", False)]
            
        user_ids = [u["id"] for u in users]
        
        # ── Fetch member records for spotted servers ──────────────────────────────
        members_map = {}
        if user_ids:
            batch_size = 400
            for i in range(0, len(user_ids), batch_size):
                slice_ids = user_ids[i:i+batch_size]
                try:
                    m_res = logger._sb.table("scanned_members").select("*").in_("user_id", slice_ids).execute()
                    if m_res.data:
                        for m in m_res.data:
                            uid = m["user_id"]
                            if uid not in members_map:
                                members_map[uid] = []
                            members_map[uid].append(m)
                except Exception as e:
                    print(f"[Scanner Search] Members fetch error: {e}", flush=True)

        # ── Fetch guild metadata (only needed columns) ───────────────────────────
        guilds_cache = {}
        try:
            g_res = logger._sb.table("scanned_guilds").select("id,name,icon,invite_link").execute()
            if g_res.data:
                for g in g_res.data:
                    guilds_cache[g["id"]] = g
        except Exception as e:
            print(f"[Scanner Search] Guilds cache error: {e}", flush=True)
            
        # ── Assemble final results ────────────────────────────────────────────────
        results = []
        for u in users:
            uid = u["id"]
            user_memberships = members_map.get(uid, [])
            
            spotted_servers = []
            for m in user_memberships:
                gid = m.get("guild_id", "")
                g_meta = guilds_cache.get(gid, {})
                spotted_servers.append({
                    "guild_id": gid,
                    "guild_name": g_meta.get("name", "Unknown Guild"),
                    "guild_icon": g_meta.get("icon", ""),
                    "invite_link": g_meta.get("invite_link", "No Invite Link"),
                    "nickname": m.get("nickname"),
                    "joined_at": m.get("joined_at"),
                    "past_nicknames": m.get("past_nicknames") or [],
                    "last_seen": m.get("last_seen")
                })

            # Ensure spotted_servers is never missing (frontend crashes otherwise)
            results.append({
                **u,
                "past_usernames": u.get("past_usernames") or [],
                "past_bios": u.get("past_bios") or [],
                "spotted_servers": spotted_servers
            })
            
        # ── Sort ──────────────────────────────────────────────────────────────────
        if sort_by == "joined_at":
            results.sort(key=lambda u: min(
                [m.get("joined_at") or "9999" for m in members_map.get(u["id"], [])] or ["9999"]
            ))
        elif sort_by == "last_seen":
            results.sort(key=lambda u: u.get("updated_at") or "", reverse=True)
        else:
            results.sort(key=lambda u: (u.get("username") or "").lower())
            
        return jsonify({"results": results, "count": len(results)})
    except Exception as e:
        logger.log_event(f"Search API Error: {e}", "error")
        return handle_scanner_error(e)

# Export app for Gunicorn
application = app

def run_flask():
    t_outbound = Thread(target=outbound_ping_loop, daemon=True, name="AwakePinger")
    t_outbound.start()
    
    port = int(os.environ.get("PORT", 8085))
    app.run(host="0.0.0.0", port=port, use_reloader=False)

def outbound_ping_loop():
    import urllib.request
    import json
    import time
    global LAST_AWAKE_URL
    
    while True:
        targets_to_ping = []
        try:
            mimcfg = logger.get_mimic_config()
            if isinstance(mimcfg, dict):
                p2p_mesh = mimcfg.get("p2p_mesh", True)
                url = os.environ.get("AWAKE_URL") or mimcfg.get("awake_url") or LAST_AWAKE_URL
                if url:
                    targets_to_ping.append(url.strip())
                if p2p_mesh:
                    peers = mimcfg.get("awake_peers", [])
                    if isinstance(peers, list):
                        for p in peers:
                            if p and isinstance(p, str):
                                t_url = p.strip()
                                if t_url not in targets_to_ping:
                                    targets_to_ping.append(t_url)
        except Exception as e:
            print(f"[Outbound Ping Config Read Error] {e}", flush=True)
            url = os.environ.get("AWAKE_URL") or LAST_AWAKE_URL
            if url:
                targets_to_ping.append(url.strip())
                
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        self_url = os.environ.get("RENDER_EXTERNAL_URL")
        if self_url:
            headers["X-Awake-URL"] = self_url
            
        if targets_to_ping:
            headers["X-Peers"] = ",".join(targets_to_ping)
            
        for target in targets_to_ping:
            ping_url = target
            if not ping_url.startswith("http"):
                ping_url = "https://" + ping_url
            if ping_url.count('/') == 2:
                ping_url += "/api/hook"
                
            try:
                req_headers = dict(headers)
                req = urllib.request.Request(ping_url, headers=req_headers)
                with urllib.request.urlopen(req, timeout=5) as response:
                    body = response.read().decode('utf-8', errors='ignore')
                    if body:
                        try:
                            res_data = json.loads(body)
                            if isinstance(res_data, dict) and "peers" in res_data:
                                merge_peers(res_data["peers"])
                        except:
                            pass
            except Exception as e:
                pass
                
        time.sleep(20)

def keep_alive():
    """Starts the Flask server and the outbound awake pinger in background threads."""
    t = Thread(target=run_flask, daemon=True, name="FlaskServer")
    t.start()
    
    t_outbound = Thread(target=outbound_ping_loop, daemon=True, name="AwakePinger")
    t_outbound.start()
    
    return t
