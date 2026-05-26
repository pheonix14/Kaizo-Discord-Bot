import discum, os, re, time, random, glob, threading, uuid, requests
from typing import Optional
from datetime import datetime, timedelta
from pokemon_loader import load_pokemon_list
from logger import (log_event, increment_caught, increment_fault, log_catch,
                    get_tokens, get_spam_config, set_status, log_history,
                    get_owo_config, save_tokens, get_image_config, get_break_config)

POKETWO_ID = "716390085896962058"
OWO_ID     = "408785106942164992"
CHAT_DIR   = "chat"
HF_MODEL   = "imjeffhi/pokemon_classifier"
HF_API     = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
_classifier_lock = threading.Lock()

# ── Advanced Image Catch Queue ────────────────────────────────────────────────
# When advanced_mode is ON: one account at a time gets the image catcher,
# others wait in a queue (their spawn is kept alive by _hint_runner sleeping).
import queue as _queue_module
_adv_queue: "_queue_module.Queue[tuple]" = _queue_module.Queue()
_adv_queue_result: dict = {}   # node_id -> threading.Event (set when result is ready)
_adv_queue_result_lock = threading.Lock()
_ADV_INTER_SLOT_SLEEP = 8.0    # seconds between slots

ULTRA_BEASTS = {793,794,795,796,797,798,799,803,804,805,806,
                892,896,897,898,905,1001,1002,1003,1004,1005,1006,1007,1008,1009,1010}

# ── Chat messages ─────────────────────────────────────────────────────────────
# Handled per-node in BotNode._pick_send_msg and _pick_spam_msg

# ── PokeAPI ───────────────────────────────────────────────────────────────────
def _poke_name(name:str)->str:
    n=name.lower().strip()
    subs=[(" ","-"),(".",""),("'",""),(":",""),(chr(9792),"-f"),(chr(9794),"-m"),(chr(233),"e"),(chr(226),"a"),(chr(232),"e"),(chr(8217),"")]
    for a,b in subs: n=n.replace(a,b)
    return n.replace("--","-").strip("-")

def _fetch_poke(name:str)->dict:
    try:
        api=_poke_name(name)
        r=requests.get(f"https://pokeapi.co/api/v2/pokemon/{api}",timeout=6)
        if r.status_code!=200: return {}
        d=r.json()
        pid=d["id"]
        sr=requests.get(f"https://pokeapi.co/api/v2/pokemon-species/{pid}",timeout=6)
        s=sr.json() if sr.status_code==200 else {}
        leg=s.get("is_legendary",False)
        myth=s.get("is_mythical",False)
        ub=pid in ULTRA_BEASTS
        rarity="mythical" if myth else "legendary" if leg else "ultra_beast" if ub else "common"
        return {
            "pokemon_id":pid,
            "types":[t["type"]["name"] for t in d["types"]],
            "is_legendary":leg,"is_mythical":myth,"is_ultra_beast":ub,"rarity":rarity,
            "sprite":d["sprites"].get("front_default",""),
            "art":d["sprites"].get("other",{}).get("official-artwork",{}).get("front_default",""),
            "shiny_art":d["sprites"].get("other",{}).get("official-artwork",{}).get("front_shiny",""),
        }
    except: return {}

# ── Node registry ─────────────────────────────────────────────────────────────
_nodes:dict = {}
_nlock = threading.Lock()

# ── Advanced Queue Worker ─────────────────────────────────────────────────────
def _adv_queue_worker():
    """Global daemon: processes image-catch requests one account at a time.
    Each slot: classify → set result event → sleep 8s → next slot.
    """
    log_event("Advanced Image Queue worker started.", "info")
    while True:
        try:
            # Block until a slot request arrives
            node_id, img_url, hf_token, result_event = _adv_queue.get(block=True, timeout=2)
        except _queue_module.Empty:
            continue
        except Exception:
            continue

        try:
            with _nlock:
                node = _nodes.get(node_id)
            if node is None or not node.catching:
                # Node gone or already resolved
                with _adv_queue_result_lock:
                    _adv_queue_result[node_id] = []
                result_event.set()
                continue

            node._log("[AdvQueue] Slot acquired — running image classification.", "info")
            try:
                res = node._classify_pokemon(img_url, hf_token)
            except Exception as e:
                node._log(f"[AdvQueue] Classification error: {e}", "error")
                res = []

            with _adv_queue_result_lock:
                _adv_queue_result[node_id] = res or []
            result_event.set()

            node._log(f"[AdvQueue] Done. Sleeping {_ADV_INTER_SLOT_SLEEP}s before next slot.", "info")
            time.sleep(_ADV_INTER_SLOT_SLEEP)
        except Exception as e:
            log_event(f"[AdvQueue] Worker loop error: {e}", "error")
            try:
                result_event.set()   # Always unblock waiter
            except: pass

class BotNode:
    _local_classifier = None

    def __init__(self,cfg:dict):
        self.id=cfg["id"]; self.token=cfg["token"]
        self.label=cfg.get("label",self.id[:8])
        self.guild_id=cfg.get("guild_id","").strip()
        self.channel_id=cfg.get("channel_id","").strip()
        self.bot=discum.Client(token=self.token,log=False)
        self.catching = False
        self.user_profile = {}
        self.balances = cfg.get("balances", {"pokecoins": 0, "cowoncy": 0, "last_sync": "Never"})
        self._clk = threading.Lock()
        self._spam_running=cfg.get("spam_active", False)
        self._owo_running=cfg.get("owo_active", False)
        self._slash_running=cfg.get("slash_active", True)
        self.owo_channel_id = cfg.get("owo_channel_id", "").strip()
        self._spam_thread:Optional[threading.Thread]=None
        self._owo_thread:Optional[threading.Thread]=None
        self._slash_thread:Optional[threading.Thread]=None
        self._owo_last_run = cfg.get("owo_last_run", {})
        self._slash_last_run = cfg.get("slash_last_run", {})
        self._pending_ch=""
        self._pending_name=""
        self._pending_matches=[]
        self._pending_match_idx=0
        self._pending_shiny=False
        self._pending_hint=""
        self._pending_img=""
        self._spawn_time=0
        self._hint_count = 0
        self._last_hint_time = 0
        self._owo_cooldown_until = 0
        self._hint_event = threading.Event()  # fired when Pokétwo replies with a hint
        # Restore captcha state from Supabase on startup
        from logger import get_captcha_data
        _cap_d = get_captcha_data()
        _active_caps = _cap_d.get("active", {})
        if self.label in _active_caps:
            self._captcha_detected = True
            self._captcha_url = _active_caps[self.label].get("url", "")
            self._captcha_time = _active_caps[self.label].get("time", "")
        else:
            self._captcha_detected = False        # blocks re-engagement after captcha
            self._captcha_url = ""
            self._captcha_time = ""
        self._captcha_factor = 1.0            # adaptive humanizer speed cooldown scale factor
        self._session_caught = 0             # tracks catches for 50-catch cooldown
        # Per-model live status tracking (for image.html dashboard)
        self._model_statuses = {}            # {model_id: {status, label, score, elapsed_ms}}
        self._total_ai_catches = 0           # lifetime AI catches this session
        self._total_ai_conf_sum = 0.0        # sum of confidence for avg calculation
        self._last_classify_ms = 0           # ms taken by last successful classification
        self._consecutive_image_failures = 0

        self._msg_running = cfg.get("msg_active", False)
        self.msg_channel_id = cfg.get("msg_channel_id", "").strip()
        self.msg_delay = int(cfg.get("msg_delay", 30))
        self.msg_random_delay = cfg.get("msg_random_delay", False)
        self._msg_thread:Optional[threading.Thread]=None

        # Initialize safe non-blocking Send Queue
        import queue
        self._send_queue = queue.PriorityQueue()
        self._queue_counter = 0
        self._queue_running = True
        self._queue_thread = threading.Thread(target=self._process_send_queue, daemon=True, name=f"queue-{self.label[:8]}")
        self._queue_thread.start()
        
        # Catch event synchronization fields
        self._catch_response_event = threading.Event()
        self._last_catch_response = None
        self._catch_thread = None
        
        # Auto-resume based on persistent config
        if self._spam_running: self._start_spam()
        if self._owo_running: self._start_owo()
        if self._slash_running: self._start_slash()
        if self._msg_running: self._start_msg()

    def resume_from_captcha(self):
        """Resets captcha state and force-restarts all loops + immediate rescan."""
        self._captcha_detected = False
        self._captcha_url = ""
        self._captcha_time = ""

        # Dial down speed after clearing to avoid immediate re-flag
        self._captcha_factor = min(3.0, self._captcha_factor + 0.6)
        self._log(f"Captcha cleared. Resuming. Cooldown scale: {self._captcha_factor:.2f}x", "success")

        # ── 1. Revive send queue thread if it died ─────────────────────────────
        if not (getattr(self, '_queue_thread', None) and self._queue_thread.is_alive()):
            self._log("Send Queue thread was dead — restarting...", "warning")
            self._queue_running = True
            self._queue_thread = threading.Thread(
                target=self._process_send_queue, daemon=True,
                name=f"queue-{self.label[:8]}")
            self._queue_thread.start()

        # ── 2. Force-restart loops that are dead or need kicking ───────────────
        toks = get_tokens()
        for t in toks:
            if t["id"] == self.id:
                if t.get("spam_active"):
                    if not (getattr(self, '_spam_thread', None) and self._spam_thread.is_alive()):
                        self._log("Spam thread dead — restarting...", "warning")
                        self._spam_running = True
                        self._spam_thread = threading.Thread(target=self._spam_loop, daemon=True)
                        self._spam_thread.start()
                    else:
                        self._log("Spam thread alive — queue unblocked, will resume.", "info")
                if t.get("owo_active"):
                    if not (getattr(self, '_owo_thread', None) and self._owo_thread.is_alive()):
                        self._log("OwO thread dead — restarting...", "warning")
                        self._owo_running = True
                        self._owo_thread = threading.Thread(target=self._owo_loop, daemon=True)
                        self._owo_thread.start()
                    else:
                        self._log("OwO thread alive — queue unblocked, will resume.", "info")
                if t.get("slash_active", True): self._start_slash()
                if t.get("msg_active"): self._start_msg()
                break

        # ── 3. Immediate rescan for pending spawns ─────────────────────────────
        threading.Thread(
            target=self._scan_channel, daemon=True,
            name=f"rescan-{self.label[:8]}").start()
        self._log("Immediate rescan triggered for pending spawns.", "info")

    def _sync_state(self):
        toks = get_tokens()
        for t in toks:
            if t["id"] == self.id:
                t["spam_active"] = self._spam_running
                t["owo_active"] = self._owo_running
                t["slash_active"] = self._slash_running
                t["owo_channel_id"] = self.owo_channel_id
                t["msg_active"] = self._msg_running
                t["msg_channel_id"] = self.msg_channel_id
                t["msg_delay"] = self.msg_delay
                t["msg_random_delay"] = getattr(self, "msg_random_delay", False)
                t["owo_last_run"] = self._owo_last_run
                t["slash_last_run"] = self._slash_last_run
                t["balances"] = self.balances
        save_tokens(toks)

    def _send(self, channel_id, message, origin="engine"):
        """Safely queue message to prevent gateway clashes, spam blocking, or rate limits."""
        if not channel_id or not message: return
        
        # Priorities:
        # 0: catch, spawn, manual (Must be sent instantly!)
        # 1: owo, slash, msg, balance (High priority)
        # 2: spam (Low priority)
        priority = 2
        o_lower = origin.lower()
        if any(x in o_lower for x in ["catch", "spawn", "manual"]):
            priority = 0
        elif any(x in o_lower for x in ["owo", "slash", "msg", "balance", "bal", "info"]):
            priority = 1
            
        self._queue_counter += 1
        self._send_queue.put((priority, self._queue_counter, (channel_id, message, origin)))

    def _process_send_queue(self):
        """Processes the queued messages sequentially. Self-healing — restarts on crash."""
        self._log("Safe Priority Send Queue background runner initialized.", "success")
        while self._queue_running:
            try:
                try:
                    priority, counter, item = self._send_queue.get(timeout=1.0)
                except:
                    continue

                try:
                    ch, msg, origin = item

                    # ── Block: captcha active (Only drop Pokétwo catch/spawn commands) ──
                    if self._captcha_detected and origin in ["catch", "spawn", "hint"]:
                        print(f"[warning] Send Queue: Pokétwo Captcha active. Dropping queued Pokétwo '{origin}' message.")
                        self._send_queue.task_done()
                        continue

                    if self._is_mimic_sleeping():
                        self._log(f"Send Queue: Mimic Auto-Sleep. Dropping '{origin}'.", "info")
                        self._send_queue.task_done()
                        continue

                    if self._is_on_break() and origin not in ["manual", "spawn", "catch"]:
                        self._log(f"Send Queue: Human break active. Dropping '{origin}'.", "info")
                        self._send_queue.task_done()
                        continue

                    # ── Dispatch ─────────────────────────────────────────────
                    resp = self.bot.sendMessage(ch, msg)
                    sc = getattr(resp, 'status_code', None)
                    if sc and sc not in [200, 201]:
                        try:    err_txt = resp.json()
                        except: err_txt = getattr(resp, 'text', str(resp))
                        self._log(f"[{origin.upper()}] HTTP {sc}: {err_txt}", "error")
                    else:
                        self._log(f"[{origin.upper()}] → {ch}: {msg}",
                                  "success" if origin in ["catch", "spawn"] else "info")

                    # Dynamic inter-message delay
                    if origin in ["catch", "spawn"]:
                        time.sleep(0.3)
                    elif origin == "spam":
                        time.sleep(0.05) # spam loop handles its own timing
                    else:
                        factor = getattr(self, "_captcha_factor", 1.0)
                        time.sleep(random.uniform(1.5, 3.2) * factor)
                except Exception as e:
                    self._log(f"Send Queue dispatch error: {e}", "error")
                finally:
                    try: self._send_queue.task_done()
                    except: pass
            except Exception as fatal:
                # Outer guard — keeps thread alive even if something catastrophic happens
                self._log(f"Send Queue FATAL (recovering): {fatal}", "error")
                time.sleep(1)

    def _is_on_break(self):
        try:
            cfg = get_break_config()
            if not cfg.get("enabled", True): return False
            now = datetime.now()
            start_str = cfg.get("start_time", "02:00")
            duration = int(cfg.get("duration", 10))
            start_time = datetime.strptime(start_str, "%H:%M").replace(year=now.year, month=now.month, day=now.day)
            end_time = start_time + timedelta(minutes=duration)
            
            if start_time <= now <= end_time: return True
            # Handle overnight breaks
            if start_time > end_time:
                end_time += timedelta(days=1)
                if start_time <= now <= end_time: return True
        except Exception as e:
            pass
        return False

    def _is_mimic_sleeping(self) -> bool:
        """
        Determines if the account is currently inside its Mimic Auto-Sleep window.
        Uses the shared config but shifts/jitters sleep start times slightly per token for humanized realism.
        """
        try:
            from logger import get_mimic_config
            mcfg = get_mimic_config()
            as_cfg = mcfg.get("auto_sleep", {})
            if not as_cfg.get("enabled", True):
                return False

            now = datetime.now()
            
            # Extract daily active operating hours
            active_start = int(as_cfg.get("active_start_hour", 8))
            active_end = int(as_cfg.get("active_end_hour", 22))
            
            # Use token's distinct hash to inject a persistent yet different start shift (e.g. +/- 45 mins)
            # This makes all multi-accounts wake up and fall asleep at slightly different moments!
            token_seed = sum(ord(c) for c in self.id) % 90 - 45 # -45 to +45 minutes
            shift_minutes = token_seed
            
            # Calculate sleep times based on when active operating hours end
            # Inactive window start: active_end
            # Inactive window end: active_start next day
            now_minute_val = now.hour * 60 + now.minute
            
            sleep_start_minutes = (active_end * 60) + shift_minutes
            sleep_end_minutes = (active_start * 60) + shift_minutes
            
            if sleep_start_minutes > sleep_end_minutes:
                # Standard overnight sleep (e.g. 10 PM to 8 AM)
                if now_minute_val >= sleep_start_minutes or now_minute_val < sleep_end_minutes:
                    return True
            else:
                # Sleep interval spans inside a single calendar day
                if sleep_start_minutes <= now_minute_val < sleep_end_minutes:
                    return True
        except Exception as e:
            pass
        return False

    def stop(self):
        self.stop_spam()
        self.stop_owo()
        self.stop_msg()
        self._slash_running = False
        self._queue_running = False
        try: self.bot.gateway.close()
        except: pass
        self._log("Node fully terminated.", "warning")

    def _log(self,m,t="info"): log_event(m,t,self.label)

    def stop_owo(self): 
        if self._owo_running:
            self._owo_running = False
            self._log("OwO Loop: Stopped", "warning")
            self._sync_state()

    def stop_spam(self):
        if self._spam_running:
            self._spam_running = False
            self._log("Spam Loop: Stopped", "warning")
            self._sync_state()

    def stop_msg(self):
        if self._msg_running:
            self._msg_running = False
            self._log("Msg Loop: Stopped", "warning")
            self._sync_state()

    def _start_msg(self):
        if self._msg_thread and self._msg_thread.is_alive(): return
        self._msg_running = True
        self._msg_thread = threading.Thread(target=self._msg_loop, daemon=True)
        self._msg_thread.start()
        self._log("Msg Loop: Thread launched.", "success")
        self._sync_state()

    def start_msg(self):
        self._start_msg()

    def _pick_send_msg(self):
        DEFAULT_MSGS = [
            "hey sup guys", "anyone active here?", "what are you all doing?", "how is the day going?",
            "that sounds cool", "lol that is so true", "wait, really?", "i didn't know that",
            "bruh moment right there", "no way, are you serious?", "i am so tired today", "just finished lunch",
            "any plans for the weekend?", "that's crazy", "haha nice one", "damn, that's wild",
            "i need some coffee tbh", "same here lol", "yeah i agree", "not gonna lie, that is awesome",
            "what game are we playing?", "has anyone seen the new movie?", "weather is nice today",
            "just chillin here", "wb back!", "good morning everyone", "hope you all have a great day",
            "gimme a second", "lmao so funny", "i am back now", "what's the topic today?",
            "hmmm let me think", "honestly same", "absolutely", "i doubt that tbh",
            "who is online?", "feel like playing something", "well that sucks", "congrats!",
            "that's a huge W", "oof, tough luck", "makes sense to me", "let's goooo",
            "wait what happened?", "i was away for a bit", "hello hello", "hope you're doing well",
            "could be better", "it is what it is", "nevermind then", "peace out guys",
            "talk to you later", "catch you guys later!"
        ]

        if not hasattr(self, '_sent_msg_history'):
            self._sent_msg_history = []
            
        now = time.time()
        if not hasattr(self, '_cached_send_msgs') or now - getattr(self, '_last_send_msg_load', 0) > 10:
            self._last_send_msg_load = now
            path_user = os.path.join("chat", f"send_{self.label}.txt")
            path_label = os.path.join("chat", f"{self.label}.txt")
            path_global = os.path.join("chat", "send.txt")
            
            target_path = path_global
            if os.path.exists(path_user): target_path = path_user
            elif os.path.exists(path_label): target_path = path_label

            try:
                if not os.path.exists(target_path) and target_path == path_global:
                    os.makedirs("chat", exist_ok=True)
                    with open(path_global, "w", encoding="utf-8") as f:
                        f.write("\n".join(DEFAULT_MSGS) + "\n")
                
                with open(target_path, "r", encoding="utf-8") as f:
                    lines = list(set([l.strip() for l in f if l.strip()]))
                
                if len(lines) < 10:
                    lines = list(set(lines + DEFAULT_MSGS))
                self._cached_send_msgs = lines
            except Exception as e:
                self._log(f"Failed to load send messages: {e}", "warning")
                self._cached_send_msgs = DEFAULT_MSGS

        lines = self._cached_send_msgs

        if lines:
            # Anti-repetition sliding window of 40
            recent_40 = self._sent_msg_history[-40:]
            allowed_lines = [l for l in lines if l not in recent_40]
            
            # Fallback to avoid the last sent message if lines are few
            if not allowed_lines:
                last_one = recent_40[-1] if recent_40 else None
                allowed_lines = [l for l in lines if l != last_one]
            
            if not allowed_lines:
                allowed_lines = lines
            
            chosen = random.choice(allowed_lines)
            self._sent_msg_history.append(chosen)
            
            # Cap memory to last 100 entries
            if len(self._sent_msg_history) > 100:
                self._sent_msg_history = self._sent_msg_history[-100:]
            return chosen
        return ""

    def _msg_loop(self):
        self._log("Msg Loop: Thread initialized.", "success")
        while self._msg_running:
            if self.catching:
                time.sleep(2); continue

            if self._is_on_break():
                self._log("Msg Loop paused: Human break active.", "info")
                time.sleep(30); continue

            ch_raw = self.msg_channel_id or self.channel_id
            if not ch_raw:
                self._log("Msg Loop: No channel configured. Pausing...", "warning")
                time.sleep(10); continue
            
            # Allow multiple channels (comma-separated)
            ch_list = [c.strip() for c in ch_raw.split(",") if c.strip()]
            if not ch_list: continue

            msg = self._pick_send_msg()
            if not msg:
                self._log("Msg Loop: send.txt is empty or missing. Pausing...", "warning")
                time.sleep(10); continue

            # Queue messages safely for ALL channels in the list
            for ch in ch_list:
                try:
                    self._send(ch, msg, origin="msg")
                except Exception as e:
                    self._log(f"Msg Loop queuing failed for channel {ch}: {e}", "error")

            delay = self.msg_delay if self.msg_delay > 0 else 30
            if getattr(self, "msg_random_delay", False):
                # Unpredictable natural delay between 50% and 200% of the base delay
                sleep_time = max(5, random.randint(int(delay * 0.5), int(delay * 2.0)))
                self._log(f"Msg Loop: Randomized sleep triggered. Waiting {sleep_time}s before next loop.", "info")
            else:
                sleep_time = delay + random.randint(-2, 2)
                if sleep_time < 5: sleep_time = 5

            for _ in range(int(sleep_time)):
                if not self._msg_running: break
                time.sleep(1)

    def get_guilds_and_channels(self):
        guilds_dict = {}
        errors = []

        # ── Strategy 1: Try discum REST API (always works even without gateway) ─
        try:
            r = self.bot.getGuilds()
            if r.status_code == 200:
                api_guilds = r.json()
                for g in api_guilds:
                    g_id = g.get("id", "")
                    g_name = g.get("name", g_id)
                    # Optimize: Do not query channels list for every guild to prevent rate-limits and lag!
                    guilds_dict[g_id] = {
                        "id": g_id,
                        "name": g_name,
                        "channels": []
                    }
            else:
                errors.append(f"getGuilds HTTP {r.status_code}")
        except Exception as e:
            errors.append(f"REST API error: {e}")

        # ── Strategy 2: Merge/Fallback to gateway session cache ──────────
        # session.guilds can throw KeyError: 'guilds' if READY event hasn't
        # populated settings_ready yet — use safe access.
        try:
            try:
                session_guilds = self.bot.gateway.session.guilds
            except (KeyError, AttributeError):
                session_guilds = {}
            if session_guilds:
                for g_id, g_info in session_guilds.items():
                    channels = []
                    raw_chs = g_info.get("channels", {})
                    if isinstance(raw_chs, dict):
                        for ch_id, ch_info in raw_chs.items():
                            if isinstance(ch_info, dict):
                                ch_type = ch_info.get("type", -1)
                                if ch_type in [0, 5]:
                                    channels.append({
                                        "id": ch_id,
                                        "name": ch_info.get("name", ch_id)
                                    })
                    
                    if g_id in guilds_dict:
                        if not guilds_dict[g_id]["channels"] and channels:
                            guilds_dict[g_id]["channels"] = sorted(channels, key=lambda x: x["name"])
                    else:
                        guilds_dict[g_id] = {
                            "id": g_id,
                            "name": g_info.get("name", g_id) if isinstance(g_info, dict) else g_id,
                            "channels": sorted(channels, key=lambda x: x["name"])
                        }
        except Exception as e:
            errors.append(f"Gateway cache error: {e}")

        if errors:
            self._log(f"get_guilds_and_channels errors: {'; '.join(errors)}", "warning")

        return sorted(list(guilds_dict.values()), key=lambda x: x["name"])

    def _in_scope(self,msg:dict)->bool:
        if not self.guild_id and not self.channel_id: return True
        if self.channel_id and msg.get("channel_id")==self.channel_id: return True
        if self.guild_id and msg.get("guild_id")==self.guild_id: return True
        return False

    def _guess(self, hint_text: str) -> list:
        """Returns potential matches sorted: base name first, forms second, megas/z/gmax last."""
        # Form suffixes that should be deprioritized unless hint contains a hyphen
        MEGA_FORMS = {"-mega", "-mega-x", "-mega-y", "-primal", "-gmax", "-gigantamax", "-eternamax"}
        Z_FORMS    = {"-z"}  # e.g. lucario-mega-z
        # Regional/form variants that ARE valid and should be tried normally
        REGIONAL   = {"galarian", "alolan", "hisuian", "paldean", "johtonian", "kantonian"}

        def _sort_key(name: str) -> int:
            nl = name.lower()
            # Exact base name (no hyphen at all) → highest priority
            if "-" not in nl: return 0
            # Regional/form variants (galarian-x, x-galar, etc.) → second
            if any(r in nl for r in REGIONAL): return 1
            # Other single-hyphen forms (rotom-heat, wormadam-plant) → third
            parts = nl.split("-")
            if len(parts) == 2: return 2
            # Mega / primal / gmax / z → deprioritize
            if any(nl.endswith(s) for s in MEGA_FORMS): return 10
            if any(s in nl for s in Z_FORMS): return 9
            # Other multi-part names → fourth
            return 3

        try:
            m = re.search(r"The pok[eé]mon is (.+?)[\.!\)]", hint_text, re.IGNORECASE)
            if not m:
                if "_" in hint_text: cleaned_hint = hint_text
                else: return []
            else:
                cleaned_hint = m.group(1)

            # Does the hint itself suggest a multi-word / hyphenated form?
            hint_has_space = " " in cleaned_hint.strip()

            hint = re.sub(r"[^a-zA-Z0-9_]", "", cleaned_hint).lower()
            if not hint: return []

            pl = load_pokemon_list()
            matches = []

            # Pass 1: Strict Match — strip ALL non-alphanumeric from both sides, compare lengths
            for name in pl:
                target = re.sub(r"[^a-zA-Z0-9]", "", name).lower()
                if len(target) == len(hint):
                    if all(h == "_" or h == c for h, c in zip(hint, target)):
                        matches.append(name)

            # Pass 2: Partial/Fallback — try matching each word segment of the hint
            if not matches:
                hint_segments = [re.sub(r"[^a-zA-Z0-9_]", "", s).lower() for s in re.split(r"[\s\-]+", cleaned_hint)]
                for name in pl:
                    target_segments = [re.sub(r"[^a-zA-Z0-9]", "", s).lower() for s in re.split(r"[\s\-]+", name)]
                    for hs in hint_segments:
                        if not hs or hs.count("_") == len(hs): continue
                        for ts in target_segments:
                            if len(ts) == len(hs) and all(h == "_" or h == c for h, c in zip(hs, ts)):
                                matches.append(name)

            # De-duplicate
            matches = list(dict.fromkeys(matches))

            # If hint has NO space/hyphen hint of a form, filter out mega forms first
            # and insert the base name at the very front if available
            if not hint_has_space:
                base_names = [n for n in matches if "-" not in n.lower()]
                form_names = [n for n in matches if "-" in n.lower()]
                # Always try base names before any form variants
                matches = base_names + sorted(form_names, key=_sort_key)
            else:
                matches = sorted(matches, key=_sort_key)

            return matches
        except Exception as e:
            self._log(f"Guessing error: {e}", "error")
            return []

    def _record(self,name:str,success:bool,reason:str,ch:str,shiny:bool,hint:str,pdata:dict):
        if getattr(self, "_is_image_catch", False):
            if success:
                self._consecutive_image_failures = 0
            else:
                self._consecutive_image_failures = getattr(self, "_consecutive_image_failures", 0) + 1

        entry_id = str(uuid.uuid4())[:8]
        
        # Determine the best image URL
        # Priority: 1) Real-time Discord embed image (from discum, always available instantly)
        #           2) PokeAPI official artwork
        #           3) PokeAPI sprite CDN fallback
        best_img = self._pending_img  # live Discord image captured via discum
        if not best_img:
            best_img = pdata.get("art", "")
        if not best_img and pdata.get("pokemon_id"):
            best_img = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{pdata['pokemon_id']}.png"

        entry={
            "id":entry_id,
            "datetime":datetime.now().isoformat(timespec="seconds"),
            "time":datetime.now().strftime("%H:%M:%S"),
            "pokemon_name":name,
            "display_name":name.replace("-"," ").title() if name else "Unknown",
            "caught_by":self.label,
            "channel_id":ch,
            "success":success,
            "failure_reason":reason if not success else None,
            "is_shiny":shiny,
            "hint":hint,
            "level": pdata.get("level", "1"),
            "iv": pdata.get("iv", "??%"),
            "discord_img": best_img,
            "is_image_catch": getattr(self, "_is_image_catch", False),
            "confidence": getattr(self, "_pending_conf", 0),
            **pdata
        }
        log_history(entry)

    def _handle_spawn(self, ch: str, shiny: bool = False):
        if self._captcha_detected:
            self._log("Spawn detected but captcha is active. Ignoring.", "warning")
            return
        with self._clk:
            if self.catching and self._pending_ch == ch and time.time() - getattr(self, "_spawn_time", 0) < 5:
                # Prevent race condition: double spawn trigger from scan + message
                return
            self.catching = True
            self._spawn_time = time.time()
            self._pending_ch = ch
            self._pending_shiny = shiny
            self._pending_name = ""
            self._processed = False
            self._is_image_catch = False
            self._pending_conf = 0
            self._hint_count = 0
            self._last_hint_time = 0
        self._hint_event.clear()
        self._pending_hint = ""
        self._pending_matches = []
        self._pending_match_idx = 0
        threading.Thread(target=self._hint_runner, args=(ch,), daemon=True).start()

    def _hint_runner(self, ch):
        """
        Sends max 2-3 hints. After each hint, waits for Pokétwo's reply using _hint_event.
        As soon as a reply arrives, _on_message catches immediately — runner gives it space.
        Exits on: caught, fled, captcha, or max hints reached.
        """
        def _alive():
            return self.catching and not self._captcha_detected

        def _wait(secs):
            deadline = time.time() + secs
            while time.time() < deadline:
                if not _alive(): return False
                time.sleep(0.3)
            return _alive()

        # ── Image catch ─────────────────────────────────────────────────
        icfg = get_image_config()
        from logger import get_mimic_config
        mcfg = get_mimic_config()
        c_rand = mcfg.get("catch_randomizer", {})
        min_conf = float(c_rand.get("min_confidence", 0.72)) if c_rand.get("enabled", True) else 0.72
        
        img_url = self._pending_img
        advanced_mode = icfg.get("advanced_mode", False)
        
        use_image = True
        if icfg.get("enabled") and advanced_mode and getattr(self, "_consecutive_image_failures", 0) > 2:
            self._log(f"Image Catcher bypassed ({self._consecutive_image_failures} consecutive failures). Falling back to Hint Mode!", "warning")
            use_image = False

        res = None
        if icfg.get("enabled") and use_image and (icfg.get("hf_token") or icfg.get("local_mode")) and img_url:
            if advanced_mode:
                # ── Advanced Queue Mode: queue up, wait for our slot ──────────
                self._log("[AdvQueue] Submitting to Advanced Image Queue...", "info")
                result_event = threading.Event()
                _adv_queue.put((self.id, img_url, icfg.get("hf_token", ""), result_event))
                # Wait up to 120s for our classification slot (queue could be long)
                result_event.wait(timeout=120)
                if not _alive():
                    # Caught/fled while waiting in queue
                    with _adv_queue_result_lock:
                        _adv_queue_result.pop(self.id, None)
                    return
                with _adv_queue_result_lock:
                    res = _adv_queue_result.pop(self.id, [])
                self._log(f"[AdvQueue] Slot completed — resuming catch logic.", "info")
            else:
                # ── Standard Mode: use simple shared lock ─────────────────────
                with _classifier_lock:
                    res = self._classify_pokemon(img_url, icfg.get("hf_token", ""))

        if res:
            # Extract up to 2 unique predictions with score > 0.3
            ai_guesses = []
            for pred in res:
                lbl = pred.get("label", "").replace("_", " ").title()
                score = pred.get("score", 0)
                if score > 0.3:
                    norm = self._normalize_ai_label(lbl).replace("-", " ").title()
                    if norm not in ai_guesses:
                        ai_guesses.append(norm)
            
            if ai_guesses:
                top_pred = res[0]
                conf = top_pred.get("score", 0)
                if conf > min_conf:
                    self._log(f"Image match ({conf:.1%}): {ai_guesses[0]}", "success")
                    self._pending_name = ai_guesses[0]; self._pending_conf = conf
                    self._is_image_catch = True
                    
                    # Populate top 2 AI guesses
                    self._pending_matches = ai_guesses[:2]
                    self._pending_match_idx = 0
                    self._pending_ch = ch
                    
                    try:
                        self._start_catch_loop(ch, self._pending_matches)
                        # Wait until catching completes or captcha detected
                        while self.catching and not self._captcha_detected:
                            if not _wait(1): break
                        if not self.catching:
                            self._processed = True; return
                    except Exception as ex:
                        self._log(f"AI Catch sequence error: {ex}", "error")
                else:
                    self._log(f"Low confidence ({conf:.1%}). Match: {ai_guesses[0]}", "warning")

        if not _alive(): return

        # Reintroduced the 20-second wait fallback to give AI and manual catching plenty of time before requesting hints.
        if icfg.get("enabled"):
            self._log("AI catcher pending. Waiting 20 seconds before requesting hint...", "info")
            if not _wait(20): return

        if not _alive(): return

        # ── Pre-scan: catch existing hint in channel before sending any ─────────
        try:
            resp = self.bot.getMessages(ch, num=10)
            if resp and resp.status_code == 200:
                for m in reversed(resp.json()):
                    if m.get("author", {}).get("id") != POKETWO_ID: continue
                    mc = m.get("content", "").lower()
                    if "you caught" in mc or "fled" in mc or "got away" in mc:
                        with self._clk: self.catching = False
                        return
                    if "the pok" in mc and "mon is" in mc:
                        self._log("Existing hint found — catching immediately.", "spawn")
                        hint_txt = m.get("content", "")
                        self._pending_hint = hint_txt
                        matches = self._guess(hint_txt)
                        if matches:
                            self._pending_matches = matches
                            self._pending_match_idx = 0
                            self._start_catch_loop(ch, matches)
                            # Wait until catching completes or captcha detected
                            while self.catching and not self._captcha_detected:
                                if not _wait(1): break
                        else:
                            with self._clk: self.catching = False
                        return
        except: pass

        if not _alive(): return

        # ── Hint loop: max 2-3 randomly, stop on first Pokétwo reply ────────
        from logger import get_mimic_config
        mcfg = get_mimic_config()
        c_rand = mcfg.get("catch_randomizer", {})
        a_capt = mcfg.get("adaptive_captcha", {})
        
        # Adaptive captcha factors
        factor = getattr(self, "_captcha_factor", 1.0)
        
        # 1. Skip Spawn — driven by catch_rate (preferred) or legacy skip_chance
        if c_rand.get("enabled", True):
            catch_rate = float(c_rand.get("catch_rate", 95))  # 0-100, new slider
            # Backward-compat: if catch_rate is set, derive skip_chance from it
            if "catch_rate" in c_rand:
                skip_chance = 100.0 - catch_rate
            else:
                skip_chance = float(c_rand.get("skip_chance", 5.0))
            if random.uniform(0, 100) < skip_chance:
                self._log(f"Mimic: Skipped spawn (Catch Rate {catch_rate:.0f}% — rolled skip).", "info")
                with self._clk: self.catching = False
                return

        # 2. Dynamic initial delay before requesting hint
        if c_rand.get("enabled", True):
            min_delay = float(c_rand.get("min_catch_delay", 0.5))
            max_delay = float(c_rand.get("max_catch_delay", 2.0))
            init_delay = random.uniform(min_delay, max_delay) * factor
            _wait(init_delay)

        max_hints = random.randint(2, 3)
        base_gap = 30
        if c_rand.get("enabled", True):
            min_gap = float(c_rand.get("min_hint_delay", 25.0))
            max_gap = float(c_rand.get("max_hint_delay", 35.0))
            base_gap = random.uniform(min_gap, max_gap)
            
            # 3. Hint Rate — probability we request a hint at all (0-100%)
            hint_rate = float(c_rand.get("hint_rate", 80))  # new slider
            if random.uniform(0, 100) > hint_rate:
                self._log(f"Mimic: Skipping hint request this spawn (Hint Rate {hint_rate:.0f}%).", "info")
                # Wait passively for Pokétwo to auto-reveal or another node to catch
                _wait(60)
                if self.catching:
                    with self._clk: self.catching = False
                return

        # Adaptive Captcha Slowdown Penalty
        if a_capt.get("enabled", True) and factor > 1.0:
            slowdown = float(a_capt.get("hint_slowdown_seconds", 15))
            base_gap += slowdown * (factor - 1.0)
            self._log(f"Adaptive Humanizer: Slowing down hint gaps to {base_gap:.1f}s", "info")

        for i in range(max_hints):
            if not _alive(): return

            try:
                self._send(ch, f"<@{POKETWO_ID}> h", origin="spawn")
                self._hint_count += 1
                self._log(f"Hint {self._hint_count}/{max_hints} sent", "spawn")
            except: return

            self._hint_event.clear()
            got_reply = self._hint_event.wait(timeout=base_gap)
            self._hint_event.clear()

            if not _alive(): return

            if got_reply:
                # Pokétwo replied — _on_message is handling the catch right now
                self._log("Hint reply received — catch in progress.", "spawn")
                _wait(45)  # Give catch logic up to 45s to complete
                return

        # All hints sent, no reply — wait for a late response
        if _alive():
            self._log("Max hints sent. Awaiting late response (60s).", "spawn")
            _wait(60)
            
        # Fallback to clear lock if runner exits without catch
        if self.catching:
            with self._clk: self.catching = False
            self._log("Hint runner finished, lock released.", "info")


    def _normalize_ai_label(self, raw_label: str) -> str:
        """Validates AI output against pokemon.txt. Returns best matching name."""
        from pokemon_loader import load_pokemon_list
        clean = raw_label.lower().replace("_", "-").replace(" ", "-").strip()
        pl = load_pokemon_list()
        if clean in pl:
            return clean
        base = clean.split("-")[0]
        candidates = [p for p in pl if p.startswith(base)]
        if candidates:
            return candidates[0]
        return clean

    def _classify_pokemon(self, image_url, hf_token):
        # All original models kept as requested
        models = [
            "skshmjn/Pokemon-classifier-gen9-1025",
            "imjeffhi/pokemon_classifier",
            "dima806/pokemons_1000_types_image_detection",
            "abhishek/pokemon-classifier",
        ]
        qwen_models = [
            "Qwen/Qwen2-VL-7B-Instruct",
            "Qwen/Qwen2-VL-2B-Instruct",
        ]

        all_model_ids = [m.split("/")[-1] for m in models + qwen_models]
        for mid in all_model_ids:
            self._model_statuses[mid] = {"status": "QUERYING", "label": "", "score": 0, "elapsed_ms": 0}

        try:
            import concurrent.futures, base64, time as _time
            t0 = _time.time()
            
            # Re-read config fresh so new tokens are immediately used
            icfg = get_image_config()
            hf_token = icfg.get("hf_token", "").strip()
            local_mode = icfg.get("local_mode", False)
            local_engine = icfg.get("local_engine", "onnx")

            if "RENDER" in os.environ:
                if local_engine == "pytorch":
                    self._log("PyTorch local engine is disabled on Render to prevent OOM. Falling back to lightweight ONNX engine.", "warning")
                    local_engine = "onnx"

            def run_local_onnx_catcher_sync():
                self._log("Running classification locally via ONNX Runtime...", "info")
                import io, os, json
                
                try:
                    import numpy as np
                    import onnxruntime as ort
                    from PIL import Image
                except ImportError:
                    self._log("ONNX Runtime or NumPy is not installed! Run 'pip install onnxruntime numpy' to use ONNX mode.", "error")
                    return []
                
                # Model paths
                onnx_dir = "./onnx_model"
                onnx_path = os.path.join(onnx_dir, "model.onnx")
                config_path = os.path.join(onnx_dir, "config.json")
                
                if not os.path.exists(onnx_path):
                    onnx_path = "./model.onnx"
                    config_path = "./config.json"
                    
                if not os.path.exists(onnx_path):
                    self._log("model.onnx not found! Export your model and place it in './onnx_model/' to enable lightweight catching.", "warning")
                    return []
                
                # Fetch image
                r_img = requests.get(image_url, timeout=10)
                if not r_img or r_img.status_code != 200:
                    return []
                
                t_inf_start = _time.time()
                
                # Preprocess image for ViT (224x224, mean=0.5, std=0.5, HWC -> CHW)
                try:
                    img = Image.open(io.BytesIO(r_img.content)).convert("RGB")
                    img = img.resize((224, 224), Image.Resampling.BILINEAR)
                    img_data = np.array(img, dtype=np.float32) / 255.0
                    mean = np.array([0.5, 0.5, 0.5], dtype=np.float32)
                    std = np.array([0.5, 0.5, 0.5], dtype=np.float32)
                    img_data = (img_data - mean) / std
                    img_data = img_data.transpose((2, 0, 1))
                    img_data = np.expand_dims(img_data, axis=0)
                except Exception as pe:
                    self._log(f"ONNX Preprocessing error: {pe}", "error")
                    return []
                
                # Run Inference Session
                try:
                    session = ort.InferenceSession(onnx_path)
                    input_name = session.get_inputs()[0].name
                    outputs = session.run(None, {input_name: img_data})
                    logits = outputs[0][0]
                except Exception as se:
                    self._log(f"ONNX Session run error: {se}", "error")
                    return []
                
                # Softmax top index
                top_idx = int(np.argmax(logits))
                exp_logits = np.exp(logits - np.max(logits))
                probs = exp_logits / np.sum(exp_logits)
                score = float(probs[top_idx])
                
                # Map label
                label = f"class_{top_idx}"
                if os.path.exists(config_path):
                    try:
                        with open(config_path, "r", encoding="utf-8") as f:
                            cfg_data = json.load(f)
                            id2label = cfg_data.get("id2label", {})
                            label = id2label.get(str(top_idx), id2label.get(top_idx, label))
                    except: pass
                
                name_classified = self._normalize_ai_label(label).replace("-", " ").title()
                score = round(score, 3)
                elapsed = int((_time.time() - t_inf_start) * 1000)
                
                self._log(f"⚡ Winner [Local ONNX AI]: {name_classified} ({score:.1%}) in {elapsed}ms", "success")
                self._last_classify_ms = elapsed
                self._total_ai_catches += 1
                self._total_ai_conf_sum += score
                
                for mid in all_model_ids:
                    if mid == "pokemon_classifier":
                        self._model_statuses[mid] = {
                            "status": "SUCCESS",
                            "label": name_classified,
                            "score": score,
                            "elapsed_ms": elapsed
                        }
                    else:
                        self._model_statuses[mid] = {
                            "status": "STANDBY",
                            "label": "API Standby",
                            "score": 0,
                            "elapsed_ms": 0
                        }
                return [{"label": label.lower().replace(" ", "-"), "score": score}]

            def run_local_catcher_sync():
                self._log("Running classification locally via PyTorch...", "info")
                import io
                from PIL import Image
                
                if BotNode._local_classifier is None:
                    self._log("Warming up local AI model (transformers pipeline)...", "warning")
                    from transformers import pipeline
                    BotNode._local_classifier = pipeline("image-classification", model="imjeffhi/pokemon_classifier")
                    self._log("Local AI model loaded successfully!", "success")
                
                r_img = requests.get(image_url, timeout=10)
                if not r_img or r_img.status_code != 200:
                    return []
                
                t_inf = _time.time()
                img = Image.open(io.BytesIO(r_img.content))
                res = BotNode._local_classifier(img)
                elapsed = int((_time.time() - t0) * 1000)
                
                if res and len(res) > 0:
                    top = res[0]
                    name_classified = self._normalize_ai_label(top["label"]).replace("-", " ").title()
                    score = round(top["score"], 3)
                    
                    self._log(f"⚡ Winner [Local PyTorch AI]: {name_classified} ({score:.1%}) in {elapsed}ms", "success")
                    self._last_classify_ms = elapsed
                    self._total_ai_catches += 1
                    self._total_ai_conf_sum += score
                    
                    for mid in all_model_ids:
                        if mid == "pokemon_classifier":
                            self._model_statuses[mid] = {
                                "status": "SUCCESS",
                                "label": name_classified,
                                "score": score,
                                "elapsed_ms": elapsed
                            }
                        else:
                            self._model_statuses[mid] = {
                                "status": "STANDBY",
                                "label": "API Standby",
                                "score": 0,
                                "elapsed_ms": 0
                            }
                    return [{"label": top["label"].lower().replace(" ", "-"), "score": score}]
                return []

            if local_mode or not hf_token:
                try:
                    if local_engine == "pytorch":
                        local_res = run_local_catcher_sync()
                    else:
                        local_res = run_local_onnx_catcher_sync()
                    if local_res:
                        return local_res
                except Exception as le:
                    self._log(f"Local classification failed: {le}", "error")
                    if not hf_token:
                        return []

            r = requests.get(image_url, timeout=10)
            if not r or r.status_code != 200:
                for mid in all_model_ids:
                    self._model_statuses[mid] = {"status": "OFFLINE", "label": "", "score": 0, "elapsed_ms": 0}
                return []
                
            img_bytes = r.content
            b64_img = base64.b64encode(img_bytes).decode("utf-8")
            headers = {"Authorization": f"Bearer {hf_token}"}
            best_result = []

            def fetch_classifier(model):
                mid = model.split("/")[-1]
                t_start = _time.time()
                
                STRATEGIES = [
                    {
                        "url": f"https://router.huggingface.co/hf-inference/models/{model}",
                        "headers": {**headers, "Content-Type": "image/png"},
                        "data": img_bytes,
                        "json": None,
                    },
                    {
                        "url": f"https://api-inference.huggingface.co/models/{model}",
                        "headers": {**headers, "Content-Type": "image/png"},
                        "data": img_bytes,
                        "json": None,
                    },
                    {
                        "url": f"https://api-inference.huggingface.co/models/{model}",
                        "headers": {**headers, "Content-Type": "application/json"},
                        "data": None,
                        "json": {"inputs": f"data:image/png;base64,{b64_img}"},
                    },
                ]
                
                for attempt, strategy in enumerate(STRATEGIES):
                    try:
                        resp = requests.post(
                            strategy["url"],
                            headers=strategy["headers"],
                            data=strategy.get("data"),
                            json=strategy.get("json"),
                            timeout=20
                        )
                        elapsed = int((_time.time() - t_start) * 1000)
                        
                        if resp.status_code == 200:
                            data = resp.json()
                            if isinstance(data, list) and len(data) > 0:
                                top = data[0]
                                if "label" in top and "score" in top and top["score"] > 0.3:
                                    clean_label = self._normalize_ai_label(top["label"])
                                    self._model_statuses[mid] = {
                                        "status": "SUCCESS",
                                        "label": clean_label.replace("-", " ").title(),
                                        "score": round(top["score"], 3),
                                        "elapsed_ms": elapsed
                                    }
                                    data[0]["label"] = clean_label
                                    return data, model
                        elif resp.status_code == 503:
                            self._model_statuses[mid] = {"status": "LOADING", "label": "Warming up...", "score": 0, "elapsed_ms": elapsed}
                            _time.sleep(4)
                            # Retry this exact strategy once on warmup
                            resp2 = requests.post(strategy["url"], headers=strategy["headers"], data=strategy.get("data"), json=strategy.get("json"), timeout=20)
                            if resp2.status_code == 200:
                                data = resp2.json()
                                if isinstance(data, list) and len(data) > 0 and data[0].get("score", 0) > 0.3:
                                    clean_label = self._normalize_ai_label(data[0]["label"])
                                    self._model_statuses[mid] = {"status": "SUCCESS", "label": clean_label.replace("-", " ").title(), "score": round(data[0]["score"], 3), "elapsed_ms": elapsed}
                                    data[0]["label"] = clean_label
                                    return data, model
                    except Exception as ex:
                        pass # Ignore and proceed to next strategy
                        
                elapsed = int((_time.time() - t_start) * 1000)
                self._model_statuses[mid] = {"status": "OFFLINE", "label": "All strategies failed", "score": 0, "elapsed_ms": elapsed}
                return None, model

            def fetch_qwen_vlm(model):
                mid = model.split("/")[-1]
                t_start = _time.time()
                ext = image_url.split(".")[-1].split("?")[0] or "png"
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/{ext};base64,{b64_img}"}},
                        {"type": "text", "text": "What Pokemon is in this image? Reply with ONLY the Pokemon name, nothing else."}
                    ]}],
                    "max_tokens": 20
                }
                
                endpoints = [
                    f"https://router.huggingface.co/hf-inference/models/{model}/v1/chat/completions",
                    f"https://api-inference.huggingface.co/models/{model}/v1/chat/completions",
                ]
                
                for endpoint in endpoints:
                    for retry in range(2):
                        try:
                            resp = requests.post(
                                endpoint,
                                headers={**headers, "Content-Type": "application/json"},
                                json=payload, timeout=25)
                            elapsed = int((_time.time() - t_start) * 1000)
                            if resp.status_code == 200:
                                data = resp.json()
                                name = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                                name = name.replace("*", "").replace(".", "").strip()
                                if name and len(name) < 40:
                                    clean_label = self._normalize_ai_label(name)
                                    self._log(f"VLM {mid} identified: {clean_label}", "success")
                                    VLM_CONFIDENCE = 0.78
                                    self._model_statuses[mid] = {
                                        "status": "SUCCESS",
                                        "label": clean_label.title(),
                                        "score": VLM_CONFIDENCE,
                                        "elapsed_ms": elapsed
                                    }
                                    return [{"label": clean_label, "score": VLM_CONFIDENCE}], model
                            elif resp.status_code == 503:
                                self._model_statuses[mid] = {"status": "LOADING", "label": "Warming up...", "score": 0, "elapsed_ms": elapsed}
                                _time.sleep(5)
                                continue # retry
                            else:
                                break # break retry loop, try next endpoint
                        except Exception as ex:
                            break
                            
                elapsed = int((_time.time() - t_start) * 1000)
                self._model_statuses[mid] = {"status": "OFFLINE", "label": "All endpoints failed", "score": 0, "elapsed_ms": elapsed}
                return None, model

            all_futures = {}
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(models) + len(qwen_models)) as executor:
                for m in models:    all_futures[executor.submit(fetch_classifier, m)] = m
                for m in qwen_models: all_futures[executor.submit(fetch_qwen_vlm, m)] = m

                results = []
                completed, pending = concurrent.futures.wait(
                    all_futures.keys(),
                    timeout=5.5,
                    return_when=concurrent.futures.ALL_COMPLETED
                )
                
                # Cancel pending ones immediately to save resources
                for f in pending:
                    try: f.cancel()
                    except: pass
                
                for future in completed:
                    try:
                        res_data, model_name = future.result()
                        if res_data:
                            results.append((res_data, model_name))
                    except Exception as e:
                        pass
                
                if results:
                    # Sort by confidence score descending so the most confident prediction wins
                    results.sort(key=lambda x: x[0][0].get("score", 0), reverse=True)
                    best_result, model_name = results[0]
                    top = best_result[0]
                    elapsed_total = int((_time.time() - t0) * 1000)
                    self._log(f"⚡ Winner [{model_name.split('/')[-1]}]: {top['label']} ({top['score']:.1%}) in {elapsed_total}ms", "success")
                    self._last_classify_ms = elapsed_total
                    self._total_ai_catches += 1
                    self._total_ai_conf_sum += top["score"]
                else:
                    best_result = []

            for mid in all_model_ids:
                if self._model_statuses.get(mid, {}).get("status") == "QUERYING":
                    self._model_statuses[mid] = {"status": "TIMEOUT", "label": "No response", "score": 0, "elapsed_ms": 0}

            if not best_result:
                try:
                    if local_engine == "pytorch":
                        if "RENDER" in os.environ:
                            self._log("Hugging Face API yielded no hits on Render. PyTorch local fallback skipped to prevent OOM. Falling back instantly to Hint solver...", "warning")
                        else:
                            self._log("Hugging Face API yielded no hits. Invoking Local PyTorch Fallback...", "warning")
                            fallback_res = run_local_catcher_sync()
                            if fallback_res:
                                return fallback_res
                    else:
                        # ONNX mode or default - safe on both local and Render!
                        self._log("Hugging Face API yielded no hits. Invoking Local ONNX Fallback...", "warning")
                        fallback_res = run_local_onnx_catcher_sync()
                        if fallback_res:
                            return fallback_res
                except Exception as le:
                    self._log(f"Local Fallback failed: {le}", "error")

            return best_result
        except Exception as e:
            self._log(f"Overall classification error: {e}", "error")
            for mid in all_model_ids:
                self._model_statuses[mid] = {"status": "ERROR", "label": str(e)[:30], "score": 0, "elapsed_ms": 0}
            return []


    def _start_catch_loop(self, ch, matches):
        if not matches:
            with self._clk:
                self.catching = False
            return
        
        self._catch_response_event.clear()
        self._last_catch_response = None
        
        self._catch_thread = threading.Thread(
            target=self._catch_loop_runner,
            args=(ch, matches),
            daemon=True,
            name=f"catch-{self.label[:8]}"
        )
        self._catch_thread.start()

    def _catch_loop_runner(self, ch, matches):
        self._log(f"Catch loop runner started with {len(matches)} matches: {matches}", "info")
        
        for idx, name in enumerate(matches):
            if not self.catching or self._captcha_detected:
                self._log("Catch runner stopping: no longer catching or captcha detected.", "info")
                return

            self._pending_name = name
            
            # Try up to 2 times (try once, and if no response try once more, then nothing)
            max_attempts = 2
            
            for attempt in range(max_attempts):
                if not self.catching or self._captcha_detected:
                    return
                
                self._log(f"Attempting catch (match {idx+1}/{len(matches)}, try {attempt+1}) → {name}", "catch")
                self._catch_response_event.clear()
                self._last_catch_response = None
                
                try:
                    self._send(ch, f"<@{POKETWO_ID}> c {name}", origin="catch")
                except Exception as e:
                    self._log(f"Send catch error: {e}", "error")
                    break
                
                # Wait for response with an 8.0-second timeout
                got_response = self._catch_response_event.wait(timeout=8.0)
                
                if got_response:
                    resp_type = self._last_catch_response
                    self._log(f"Received catch response: {resp_type}", "info")
                    
                    if resp_type in ["caught", "fled"]:
                        with self._clk:
                            self.catching = False
                        return
                    elif resp_type == "wrong":
                        # Wrong guess: proceed to next match (after the 10-16s delay below)
                        break
                else:
                    self._log(f"No response from Poketwo on try {attempt+1} for {name}.", "warning")
                    if attempt == 0:
                        self._log("Retrying once more...", "info")
                        continue
                    else:
                        self._log("Second try timed out. Giving up.", "warning")
                        self._record(name, False, "No Response", ch, self._pending_shiny, self._pending_hint, {})
                        with self._clk:
                            self.catching = False
                        return
            
            # If we broke out due to wrong guess and there are more matches left,
            # wait 10-16 seconds before proceeding to the next match
            if idx < len(matches) - 1 and self.catching and not self._captcha_detected:
                gap = random.uniform(10.0, 16.0)
                self._log(f"Sleeping {gap:.2f}s before sending next catch request...", "info")
                
                deadline = time.time() + gap
                while time.time() < deadline:
                    if not self.catching or self._captcha_detected:
                        return
                    time.sleep(0.5)
        
        # If we exhausted all matches and didn't catch the pokemon
        if self.catching and not self._captcha_detected:
            if self._is_image_catch:
                self._log("AI catch attempts failed (attempts exhausted). Falling back to Hint solver...", "warning")
                self._is_image_catch = False
                self._pending_matches = []
                self._pending_match_idx = 0
                try:
                    self._send(ch, f"<@{POKETWO_ID}> h", origin="spawn")
                    self._hint_count = 1
                except Exception as e:
                    self._log(f"Failed to request hint fallback: {e}", "error")
            else:
                self._log("All hint matches exhausted. Failed to catch.", "warning")
                self._record(self._pending_name, False, "Exhausted", ch, self._pending_shiny, self._pending_hint, {})
                with self._clk:
                    self.catching = False


    def _on_message(self, resp):
        if not resp.event.message: return
        try:
            msg     = resp.parsed.auto()
            content = msg.get("content", "")
            cl      = content.lower()
            ch      = msg.get("channel_id", "")
            author  = msg.get("author", {}).get("id", "")
            author_name = msg.get("author", {}).get("username", "")
            embeds  = msg.get("embeds", []) or []
            def _push_balance_to_sb():
                try:
                    from logger import save_single_token, get_tokens as _gt
                    for _t in _gt():
                        if _t["id"] == self.id:
                            _t["balances"]  = self.balances
                            _t["pokecoins"] = self.balances.get("pokecoins", 0)
                            _t["cowoncy"]   = self.balances.get("cowoncy",   0)
                            _t["last_sync"] = self.balances.get("last_sync", "")
                            # Also persist avatar if available
                            if self.user_profile.get("avatar"):
                                _t.setdefault("user_profile", {})
                                _t["user_profile"]["avatar"] = self.user_profile["avatar"]
                            save_single_token(_t)
                            break
                except Exception as _e:
                    self._log(f"Supabase balance push error: {_e}", "error")

            # ── Build full text to scan (content + all embed fields) ──────────
            text_to_scan = content
            for _e in embeds:
                text_to_scan += " " + (_e.get("title","") or "")
                text_to_scan += " " + (_e.get("description","") or "")
                for _f in (_e.get("fields") or []):
                    text_to_scan += " " + (_f.get("name","") or "")
                    text_to_scan += " " + (_f.get("value","") or "")

            # Strip custom Discord emojis (e.g. <:cowoncy:416043450337853441>) to avoid matching snowflakes
            text_to_scan = re.sub(r"<a?:[a-zA-Z0-9_]+:[0-9]+>", "", text_to_scan)

            is_bot_msg = author in [POKETWO_ID, OWO_ID] or "owo" in author_name or "poketwo" in author_name
            recently_synced = time.time() - getattr(self, "_expecting_balance_sync", 0) < 90

            # ── Only log debug when it could be a relevant bot message ─────────
            if is_bot_msg:
                self._log(f"[BAL SCAN] Author={author_name}({author}) Text={repr(text_to_scan[:80])}", "info")

            # ── Quest Detection (Pokétwo only) ────────────────────────────────
            if is_bot_msg and (author == POKETWO_ID or "poketwo" in author_name):
                if "completed the quest" in cl and "received" in cl:
                    if self._is_message_for_me(msg, text_to_scan):
                        quest_text = " ".join(text_to_scan.split())
                        self._log(f"Quest Completed: {quest_text}", "success")
                        from logger import log_history
                        log_history({
                            "id": str(uuid.uuid4())[:8],
                            "datetime": datetime.now().isoformat(timespec="seconds"),
                            "time": datetime.now().strftime("%H:%M:%S"),
                            "display_name": "QUEST COMPLETED",
                            "pokemon_name": "quest",
                            "caught_by": self.label,
                            "channel_id": ch,
                            "success": True,
                            "failure_reason": quest_text,
                            "is_quest": True
                        })

            # ── POKÉCOINS — only from Pokétwo bot ─────────────────────────────
            if is_bot_msg and (author == POKETWO_ID or "poketwo" in author_name):
                m_pk = (
                    re.search(r"Pok[e\u00e9]coins\s*[\n:]*\s*([\d,]+)", text_to_scan, re.I) or
                    re.search(r"([\d,]+)\s*Pok[e\u00e9]coins", text_to_scan, re.I) or
                    re.search(r"balance\s*[\n:]*\s*([\d,]+)", text_to_scan, re.I)
                )
                if m_pk and recently_synced:
                    with _nlock: node_count = len(_nodes)
                    belongs_to_other = False
                    with _nlock:
                        for _oid, _on in _nodes.items():
                            if _oid == self.id: continue
                            _oname   = _on.user_profile.get("username","").lower()
                            _oglobal = _on.user_profile.get("global_name","").lower()
                            if (_oname and _oname in text_to_scan.lower()) or \
                               (_oglobal and _oglobal in text_to_scan.lower()):
                                belongs_to_other = True; break
                    if not belongs_to_other and (node_count == 1 or self._is_message_for_me(msg, text_to_scan)):
                        val = int(m_pk.group(1).replace(",",""))
                        self.balances["pokecoins"] = val
                        self.balances["last_sync"]  = datetime.now().strftime("%H:%M:%S")
                        self._log(f"Treasury Updated: {val:,} Pok\u00e9coins \u2713", "success")
                        _push_balance_to_sb()
                    elif belongs_to_other:
                        self._log("Pok\u00e9coins detected but belongs to another node. Skipping.", "info")

            # ── COWONCY — scan ALL messages during sync window ─────────────────
            if recently_synced:
                m_owo = (
                    re.search(r"you currently have\s*[\*_\s]*([\d,]+)", text_to_scan, re.I) or
                    re.search(r"currently have\s*[\*_\s]*([\d,]+)", text_to_scan, re.I) or
                    re.search(r"have\s*[\*_\s]*([\d,]+)", text_to_scan, re.I) or
                    re.search(r"([\d,]+)\s*[\*_\s]*cowoncy", text_to_scan, re.I) or
                    re.search(r"cowoncy[:\s]*[\*_\s]*([\d,]+)", text_to_scan, re.I) or
                    re.search(r"cash[:\s]*[\*_\s]*([\d,]+)", text_to_scan, re.I)
                )
                if m_owo:
                    with _nlock: node_count = len(_nodes)
                    belongs_to_other = False
                    with _nlock:
                        for _oid, _on in _nodes.items():
                            if _oid == self.id: continue
                            _oname   = _on.user_profile.get("username","").lower()
                            _oglobal = _on.user_profile.get("global_name","").lower()
                            if (_oname and _oname in text_to_scan.lower()) or \
                               (_oglobal and _oglobal in text_to_scan.lower()):
                                belongs_to_other = True; break
                    # Accept if: only node, OR message is addressed to me
                    # For OwO, also accept if it's from OwO bot directly
                    from_owo  = (author == OWO_ID or "owo" in author_name)
                    for_me    = self._is_message_for_me(msg, text_to_scan)
                    if not belongs_to_other and (node_count == 1 or for_me or from_owo):
                        val = int(m_owo.group(1).replace(",",""))
                        self.balances["cowoncy"]   = val
                        self.balances["last_sync"]  = datetime.now().strftime("%H:%M:%S")
                        self._log(f"Treasury Updated: {val:,} Cowoncy \u2713", "success")
                        _push_balance_to_sb()
                    elif belongs_to_other:
                        self._log("Cowoncy detected but belongs to another node. Skipping.", "info")

            # ── OwO ratelimit detection ──────────────────────────────────────────
            owo_rl_phrases = ["slow your roll","woah calm","too fast","slow down","you're sending","sending messages too quickly"]
            if any(p in cl for p in owo_rl_phrases) and ("owo" in author_name or author == OWO_ID):
                self._owo_cooldown_until = time.time() + 30
                self._log("OwO ratelimit \u2014 backing off 30s", "warning")


            # ── Captcha Detection ────────────────────────────────────────────
            if "verify.poketwo.net" in content or "verify.poketwo.net" in str(embeds) or "beep boop" in cl or "please solve" in cl:
                captcha_url = ""
                if "verify.poketwo.net" in content:
                    m = re.search(r"(https://verify.poketwo.net/captcha/\d+)", content)
                    if m: captcha_url = m.group(1)
                elif embeds:
                    for e in embeds:
                        if "verify.poketwo.net" in (e.get("url", "") or ""):
                            captcha_url = e.get("url")
                            break
                
                self._log(f"⚠️ CAPTCHA REQUIRED: {captcha_url or 'Link in message'}", "error")
                log_event(f"CRITICAL: {self.label} reached a Captcha wall. Pausing catcher for this token.", "error")

                # Store captcha in DB so dashboard can show it per-token
                from logger import set_captcha
                set_captcha(captcha_url, self.label, self.id)

                # Permanently block this token from re-engaging spawns
                self._captcha_detected = True
                self._captcha_url = captcha_url
                self._captcha_time = datetime.now().strftime("%H:%M:%S")

                # Halt catching for THIS token only (locally, without syncing False to DB)
                # Keep spam, owo, and slash running!
                with self._clk: self.catching = False
                
                # Record as special history entry
                log_history({
                    "id": str(uuid.uuid4())[:8],
                    "datetime": datetime.now().isoformat(timespec="seconds"),
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "display_name": "CAPTCHA DETECTED",
                    "pokemon_name": "captcha",
                    "caught_by": self.label,
                    "channel_id": ch,
                    "success": False,
                    "failure_reason": "Captcha Required",
                    "captcha_url": captcha_url,
                    "is_captcha": True
                })
                return

            if not self._in_scope(msg): return
            aid=msg.get("author",{}).get("id","")
            if aid!=POKETWO_ID: return

            # ── Spawn detection ──────────────────────────────────────────────
            if not self.catching:
                is_spawn = False
                
                # Check message content
                if "wild pok" in cl and "appeared" in cl:
                    is_spawn = True
                
                # Check embeds
                img_url = ""
                for e in embeds:
                    url = e.get("image", {}).get("url", "")
                    if url: img_url = url
                    
                    et = (e.get("title", "") or "").lower()
                    ed = (e.get("description", "") or "").lower()
                    if "wild pok" in et and "appeared" in et:
                        is_spawn = True
                    if "wild pok" in ed and "appeared" in ed:
                        is_spawn = True
                
                # Check attachments
                if not img_url:
                    attachments = msg.get("attachments", []) or []
                    for a in attachments:
                        url = a.get("url", "")
                        if url: img_url = url
                
                if aid == POKETWO_ID and img_url:
                    is_spawn = True

                if is_spawn:
                    shiny = "shiny" in cl or "✨" in content
                    for e in embeds:
                        et = (e.get("title", "") or "").lower()
                        ed = (e.get("description", "") or "").lower()
                        if "shiny" in et or "✨" in et or "shiny" in ed or "✨" in ed:
                            shiny = True
                            
                    self._pending_img = img_url
                    self._log(f"Spawn detected! Image URL: {img_url}", "spawn")
                    self._handle_spawn(ch, shiny)
                    return

            # ── Hint received ────────────────────────────────────────────────
            if self.catching and ch==self._pending_ch:
                if "the pok" in cl and "mon is" in cl:
                    # Signal hint runner FIRST — stop it from sending more hints
                    self._hint_event.set()
                    hint_txt=content
                    if not hint_txt and embeds:
                        hint_txt=embeds[0].get("description","")
                    matches=self._guess(hint_txt)
                    self._pending_hint=hint_txt
                    if matches:
                        self._pending_matches=matches
                        self._pending_match_idx=0
                        self._start_catch_loop(ch, matches)
                    else:
                        self._log(f"No match for hint. Hint runner will continue.", "warning")
                    return

                # ── Wrong guess ──────────────────────────────────────────────────
                if "that is the wrong pokémon" in cl or "incorrect" in cl:
                    self._log("Wrong guess received from Poketwo", "warning")
                    self._last_catch_response = "wrong"
                    self._catch_response_event.set()
                    return

                # ── Caught ───────────────────────────────────────────────────────
                if "you caught" in cl:
                    try:
                        # Extract level and name (stop at parenthesis or exclamation)
                        m = re.search(r"caught a level (\d+)\s+([^!(]+)", content, re.IGNORECASE)
                        lvl = m.group(1) if m else "1"
                        name = m.group(2).strip() if m else self._pending_name
                        name = re.sub(r"<a?:\w+:\d+>", "", name).strip()
                        
                        iv_match = re.search(r"\(([\d.]+)\s*%\)", content)
                        iv = f"{iv_match.group(1)}%" if iv_match else "??%"
                        
                        self._log(f"Catch Verified: {name.title()} (Lvl {lvl} | {iv})", "success")
                        increment_caught(self.label)
                        self._session_caught = getattr(self, '_session_caught', 0) + 1
                        
                        # Fetch extra data and record
                        pdata = _fetch_poke(name)
                        pdata["level"] = lvl
                        pdata["iv"] = iv
                        self._record(name, True, "", ch, self._pending_shiny, self._pending_hint, pdata)
                        
                    except Exception as e:
                        self._log(f"Caught but record failed: {e}", "warning")
                    finally:
                        self._last_catch_response = "caught"
                        self._catch_response_event.set()
                        with self._clk: self.catching = False
                    return

                # ── Ratelimit ──────────────────────────────────────────────────
                if "sending commands too quickly" in cl:
                    self._log("Hint ratelimited — flagging error and waiting", "warning")
                    self._last_catch_response = "wrong"
                    self._catch_response_event.set()
                    return

                # ── Fled ─────────────────────────────────────────────────────────
                if "fled" in cl or "got away" in cl:
                    self._log("Pokémon fled. Resetting state.","warning")
                    pdata = _fetch_poke(self._pending_name) if self._pending_name else {}
                    self._record(self._pending_name, False, "Fled", ch, self._pending_shiny, self._pending_hint, pdata)
                    self._last_catch_response = "fled"
                    self._catch_response_event.set()
                    with self._clk: self.catching=False
                    return

        except Exception as e:
            self._log(f"Handler error: {e}","error")

    def _scan_channel(self):
        if not self.channel_id: return
        if self._captcha_detected: return
        self._log("Scan started... Checking recent messages for uncaught Pokémon.", "info")
        try:
            # ── Fetch more messages so spawns buried under spam are found ──────
            msgs_resp = self.bot.getMessages(self.channel_id, num=50)
            if not msgs_resp or msgs_resp.status_code != 200:
                sc = msgs_resp.status_code if msgs_resp else 'No Response'
                if sc == 401:
                    self._log("CRITICAL: Token is Invalid/Unauthorized. Stopping node.", "error")
                    self.stop(); return
                self._log(f"Scan API Error: {sc}. Retrying...", "warning")
                return
            msgs = msgs_resp.json()
            if not msgs:
                self._log("Scan: No messages found in channel. Resuming loops.", "info")
                with self._clk: self.catching = False
                return

            # ── Discord messages arrive newest-first ─────────────────────────
            # Walk the list to find:
            #   1. The MOST RECENT spawn message (from Pokétwo with image)
            #   2. The MOST RECENT catch/fled confirmation message
            # Then decide: if the catch confirmation is NEWER than the spawn
            #               (= lower index in list) → spawn is resolved.
            #              If the spawn is NEWER (= lower index) → catch it!

            most_recent_spawn   = None   # (msg, img_url, msg_id_int)
            most_recent_catch_id = None  # snowflake int of latest "you caught/fled"

            for m in msgs:   # newest → oldest
                content = m.get("content", "").lower()
                embeds  = m.get("embeds", []) or []
                mid_int = int(m.get("id", "0"))
                is_pk2  = m.get("author", {}).get("id") == POKETWO_ID

                if is_pk2:
                    # Record first (newest) catch/fled we encounter
                    if most_recent_catch_id is None:
                        if ("you caught" in content or "fled" in content
                                or "got away" in content):
                            most_recent_catch_id = mid_int
                            continue   # keep scanning — there may be a newer spawn

                # Check for spawn indicators
                img_url = ""
                for e in embeds:
                    u = e.get("image", {}).get("url", "")
                    if u: img_url = u
                if not img_url:
                    for a in (m.get("attachments") or []):
                        u = a.get("url", "")
                        if u: img_url = u

                is_spawn = False
                if "wild pok" in content and "appeared" in content:
                    is_spawn = True
                for e in embeds:
                    et = (e.get("title","") or "").lower()
                    ed = (e.get("description","") or "").lower()
                    if "wild pok" in et and "appeared" in et: is_spawn = True
                    if "wild pok" in ed and "appeared" in ed: is_spawn = True
                if is_pk2 and img_url:
                    is_spawn = True

                if is_spawn and most_recent_spawn is None:
                    most_recent_spawn = (m, img_url, mid_int)
                    break   # Found the most-recent spawn, no need to go further

            if most_recent_spawn:
                spawn_msg, img_url, spawn_id = most_recent_spawn

                # If the most recent catch message is NEWER than the spawn
                # (higher snowflake = sent later), the spawn is already resolved
                if most_recent_catch_id and most_recent_catch_id > spawn_id:
                    self._log("Spawn already caught/fled (catch msg is newer). Resuming loops.", "info")
                    with self._clk: self.catching = False
                    return

                # Sanity check: skip spawns older than 5 minutes
                # Discord snowflake epoch: 1420070400000 ms
                DISCORD_EPOCH = 1420070400000
                spawn_ts_ms = (spawn_id >> 22) + DISCORD_EPOCH
                age_s = (time.time() * 1000 - spawn_ts_ms) / 1000
                if age_s > 300:
                    self._log(f"Spawn is {age_s:.0f}s old — too stale to attempt. Skipping.", "info")
                    with self._clk: self.catching = False
                    return

                self._pending_img = img_url
                if not self.catching:
                    self._log(f"Uncaught spawn found ({age_s:.0f}s old). Engaging catcher.", "info")
                    self._handle_spawn(self.channel_id,
                                       "shiny" in spawn_msg.get("content","").lower())
            else:
                if self.catching:
                    self._log("Scan: No pending spawn found. Releasing catch lock.", "info")
                    with self._clk: self.catching = False
        except Exception as e:
            self._log(f"Scan failed: {e}", "error")
            with self._clk: self.catching = False

    # ── Spam ──────────────────────────────────────────────────────────────────
    def _pick_spam_msg(self, custom:str)->str:
        if custom: return custom
        now = time.time()
        if not hasattr(self, '_cached_spam_msgs') or now - getattr(self, '_last_spam_msg_load', 0) > 10:
            self._last_spam_msg_load = now
            path_user = os.path.join("chat", f"messages_{self.label}.txt")
            path_label = os.path.join("chat", f"{self.label}.txt")
            path_global = os.path.join("chat", "messages.txt")
            
            target_path = path_global
            if os.path.exists(path_user): target_path = path_user
            elif os.path.exists(path_label): target_path = path_label

            msgs = []
            try:
                if os.path.exists(target_path):
                    with open(target_path, "r", encoding="utf-8") as f:
                        msgs = [l.strip() for l in f if l.strip()]
            except: pass
            
            if not msgs:
                msgs = ["honestly i hate mondays 💖", "sis whats poppin !?", "tbh honest dont forget to drink water pls"]
            self._cached_spam_msgs = msgs

        return random.choice(self._cached_spam_msgs)

    def _spam_loop(self):
        self._log("Spam Loop: Thread initialized.", "success")
        while self._spam_running:
            if self.catching:
                time.sleep(2); continue

            # 50-catch milestone cooldown (4-8 random minutes)
            if getattr(self, '_session_caught', 0) >= 50:
                cooldown = random.uniform(240, 480)
                self._log(f"50-catch milestone! Taking a {cooldown/60:.1f}min cooldown.", "warning")
                self._session_caught = 0
                time.sleep(cooldown)
                continue

            if self._is_on_break():
                self._log("Spam paused: Human break active.", "info")
                time.sleep(30); continue
                
            cfg=get_spam_config()
            msg=self._pick_spam_msg(cfg.get("message","").strip())
            
            # Apply Adaptive Captcha Slowdown Penalty to Spam Speed
            from logger import get_mimic_config
            mcfg = get_mimic_config()
            a_capt = mcfg.get("adaptive_captcha", {})
            factor = getattr(self, "_captcha_factor", 1.0)
            
            speed=float(cfg.get("speed",5))
            if a_capt.get("enabled", True) and factor > 1.0:
                mult = float(a_capt.get("spam_slowdown_multiplier", 1.5))
                # Slower speed = higher sleep delay between messages
                speed = speed * (mult * (factor - 0.4))
                self._log(f"Adaptive Humanizer: Slowing down spam rate. Adjusted interval: {speed:.2f}s", "info")
            
            if not self.channel_id: 
                self._log("No channel assigned. Fetching a random fallback channel...", "warning")
                try:
                    guilds_resp = self.bot.getGuilds()
                    if guilds_resp and guilds_resp.status_code == 200:
                        guilds = guilds_resp.json()
                        if guilds:
                            g = random.choice(guilds)
                            c_resp = self.bot.getGuildChannels(g["id"])
                            if c_resp and c_resp.status_code == 200:
                                tcs = [c for c in c_resp.json() if c.get("type") == 0]
                                if tcs:
                                    self.channel_id = random.choice(tcs)["id"]
                                    self._log(f"Fallback Channel assigned: {self.channel_id}", "success")
                except: pass
                
                if not self.channel_id:
                    self._log("Spam: No channel configured and random fallback failed.", "warning")
                    time.sleep(5); continue
                
            try: 
                self._send(self.channel_id, msg, origin="spam")
            except Exception as e:
                self._log(f"Spam queue failed: {e}", "error")
            
            # High speed support
            sleep_time = max(0.01, speed)
            time.sleep(sleep_time)
        self._log("Spam Loop: Stopped", "warning")

    def sync_balances(self):
        if self.catching:
            self._log("Balance sync running concurrently alongside active catch lock.", "info")
            
        pk_ch = self.channel_id
        owo_ch = self.owo_channel_id if self.owo_channel_id else self.channel_id
        
        if not pk_ch:
            pk_ch = self.owo_channel_id
            owo_ch = self.owo_channel_id
            
        if not pk_ch:
            self._log("Cannot sync balances: No channel ID configured for this node.", "warning")
            return
            
        self._log(f"Initiating Balance Sync (Sending in: {pk_ch})", "info")
        self._expecting_balance_sync = time.time()
        
        try: 
            self._send(pk_ch, f"<@{POKETWO_ID}> bal", origin="manual")
        except Exception as e: self._log(f"Sync Error (PK): {e}", "error")
            
        time.sleep(2.5)
        
        try: 
            self._send(owo_ch, "owo cash", origin="manual")
        except Exception as e: self._log(f"Sync Error (OwO): {e}", "error")

    def _start_spam(self):
        if self._spam_thread and self._spam_thread.is_alive(): return
        self._spam_running = True
        self._log("Spam Loop: Started", "success")
        self._spam_thread = threading.Thread(target=self._spam_loop, daemon=True)
        self._spam_thread.start()
        self._sync_state()

    def stop_spam(self): 
        self._spam_running=False
        self._sync_state()

    # ── OwO Loop ──────────────────────────────────────────────────────────────
    def _owo_loop(self):
        self._log("OwO Loop: Thread initialized.", "success")
        while self._owo_running:
            if self.catching:
                time.sleep(2); continue

            # OwO ratelimit backoff
            if time.time() < self._owo_cooldown_until:
                remaining = int(self._owo_cooldown_until - time.time())
                if remaining % 15 == 0:  # log every 15s to avoid spam
                    self._log(f"OwO on cooldown: {remaining}s remaining", "warning")
                time.sleep(5); continue

            if self._is_on_break():
                self._log("OwO paused: Human break active.", "info")
                time.sleep(30); continue

            cfg = get_owo_config()
            if not cfg.get("enabled", True):
                self._log("OwO Loop: Not running (Disabled)", "warning")
                time.sleep(10); continue

            target_ch = self.owo_channel_id or self.channel_id
            if not target_ch:
                self._log("OwO Loop: No channel configured", "warning")
                time.sleep(10); continue

            # Build commands from flat config
            commands_def = [
                {'id': 'hunt', 'cmd': 'owo h'}, {'id': 'battle', 'cmd': 'owo b'},
                {'id': 'daily', 'cmd': 'owo daily'}, {'id': 'lootbox', 'cmd': 'owo lb all'},
                {'id': 'pray', 'cmd': 'owo pray'}, {'id': 'curse', 'cmd': 'owo curse'},
                {'id': 'cf', 'cmd': 'owo cf X', 'isAmt': True}, {'id': 'slots', 'cmd': 'owo s X', 'isAmt': True},
                {'id': 'quest', 'cmd': 'owo quest'}, {'id': 'buy', 'cmd': 'owo buy 1'},
                {'id': 'sell', 'cmd': 'owo sell all'}, {'id': 'sacrifice', 'cmd': 'owo sacrifice all'},
                {'id': 'inv', 'cmd': 'owo inv'}, {'id': 'equip', 'cmd': 'owo equip 1'},
                {'id': 'autohunt', 'cmd': 'owo autohunt'}, {'id': 'owodex', 'cmd': 'owo owodex'},
                {'id': 'crate', 'cmd': 'owo crate all'}, {'id': 'battlesetting', 'cmd': 'owo battlesetting'},
                {'id': 'team', 'cmd': 'owo team'}, {'id': 'weapon', 'cmd': 'owo weapon'},
                {'id': 'dismantle', 'cmd': 'owo dismantle all'}, {'id': 'lottery', 'cmd': 'owo lottery 1'},
                {'id': 'blackjack', 'cmd': 'owo bj 1'}, {'id': '8b', 'cmd': 'owo 8b test'},
                {'id': 'cookie', 'cmd': 'owo cookie'}, {'id': 'ship', 'cmd': 'owo ship @user'},
                {'id': 'marry', 'cmd': 'owo marry @user'}, {'id': 'profile', 'cmd': 'owo profile'},
                {'id': 'level', 'cmd': 'owo level'}, {'id': 'pat', 'cmd': 'owo pat @user'},
                {'id': 'hug', 'cmd': 'owo hug @user'}, {'id': 'kiss', 'cmd': 'owo kiss @user'}
            ]
            for k, v in cfg.items():
                if k.startswith("custom_") and k.endswith("_cmd"):
                    commands_def.append({'id': k.replace("_cmd", ""), 'cmd': v})

            cmds = []
            for c in commands_def:
                if cfg.get(c['id'], False):
                    c['enabled'] = True
                    c['cooldown'] = float(cfg.get(f"{c['id']}_cd", 60))
                    cmds.append(c)

            if not cmds:
                self._log("OwO Loop: No commands enabled", "warning")
                time.sleep(10); continue

            now = time.time()
            executed = False
            cmds_run = 0
            
            from logger import get_mimic_config
            mcfg = get_mimic_config()
            o_rand = mcfg.get("owo_randomizer", {})
            a_capt = mcfg.get("adaptive_captcha", {})
            
            factor = getattr(self, "_captcha_factor", 1.0)
            
            if o_rand.get("enabled", True):
                bl_min = int(o_rand.get("burst_limit_min", 1))
                bl_max = int(o_rand.get("burst_limit_max", 4))
                burst_limit = random.randint(bl_min, bl_max)
            else:
                burst_limit = 3

            cmds_to_run = list(cmds)
            if o_rand.get("enabled", True) and o_rand.get("shuffle_commands", True):
                random.shuffle(cmds_to_run)

            for c in cmds_to_run:
                if not self._owo_running or self.catching: break

                base_cd = c['cooldown']
                if a_capt.get("enabled", True) and factor > 1.0:
                    added_minutes = float(a_capt.get("owo_cooldown_increase_minutes", 10))
                    base_cd += added_minutes * 60 * (factor - 1.0)

                if now - self._owo_last_run.get(c['id'], 0) >= base_cd:
                    try:
                        cmd_str = c['cmd']
                        if c.get('isAmt'):
                            amt = cfg.get(f"{c['id']}_amount", 1)
                            cmd_str = cmd_str.replace("X", str(amt))

                        self._send(target_ch, cmd_str, origin="owo")
                        self._owo_last_run[c['id']] = time.time()
                        executed = True
                        cmds_run += 1
                        if cmds_run >= burst_limit:
                            break
                            
                        if o_rand.get("enabled", True):
                            min_gap = float(o_rand.get("min_cmd_gap", 1.0))
                            max_gap = float(o_rand.get("max_cmd_gap", 4.0))
                            gap = random.uniform(min_gap, max_gap) * factor
                        else:
                            gap = random.uniform(2.5, 4.0)
                        time.sleep(gap)
                    except Exception as e:
                        self._log(f"OwO execute failed: {e}", "error")

            if executed:
                if o_rand.get("enabled", True):
                    min_bg = float(o_rand.get("min_burst_gap", 8.0))
                    max_bg = float(o_rand.get("max_burst_gap", 18.0))
                    burst_gap = random.uniform(min_bg, max_bg) * factor
                else:
                    burst_gap = random.uniform(14.0, 20.0)
                time.sleep(burst_gap)
            else:
                time.sleep(1)
        self._log("OwO Loop: Thread terminated.", "warning")
            
    def _start_owo(self):
        if self._owo_thread and self._owo_thread.is_alive(): return
        self._owo_running = True
        self._log("OwO Loop: Started", "success")
        self._owo_thread = threading.Thread(target=self._owo_loop, daemon=True)
        self._owo_thread.start()
        self._sync_state()
        
    # ── Slash Loop ────────────────────────────────────────────────────────────
    def _slash_loop(self):
        from logger import get_slash_config
        self._log("Slash/Bump loop started", "info")
        while self._slash_running:
            if self.catching: time.sleep(1); continue
            cfg = get_slash_config()
            if not cfg.get("enabled"): time.sleep(10); continue
            if not self.channel_id: time.sleep(1); continue
            
            now = time.time()
            cmds = cfg.get("commands", [])
            for c in cmds:
                if c.get("enabled"):
                    cd = float(c.get("cd", 7200))
                    cid = c.get("id")
                    if now - self._slash_last_run.get(cid, 0) >= cd:
                        cmd_text = c.get("cmd", "/bump")
                        self._log(f"Executing slash/bump: {cmd_text}", "info")
                        try:
                            self._send(self.channel_id, cmd_text, origin="slash")
                            self._slash_last_run[cid] = now
                            time.sleep(5)
                        except Exception as e:
                            self._log(f"Slash error: {e}", "error")
            time.sleep(5)

    def _start_slash(self):
        if self._slash_thread and self._slash_thread.is_alive(): return
        self._slash_running = True
        self._slash_thread = threading.Thread(target=self._slash_loop, daemon=True)
        self._slash_thread.start()
        self._sync_state()

    def stop_slash(self):
        self._slash_running = False
        self._sync_state()

    def _scan_loop(self):
        while True:
            # Catch Watchdog: Recover if stuck in catching state > 60s
            if self.catching and time.time() - self._spawn_time > 60:
                self._log("Catch watchdog timeout (>60s). Resetting state.", "warning")
                with self._clk: self.catching = False
                try: self._send(self.channel_id, f"<@{POKETWO_ID}> h", origin="spawn")
                except: pass

            time.sleep(10)
            if self.channel_id:
                try:
                    self._scan_channel()
                except: pass

    def fetch_user_profile(self):
        """Fetches the authenticated user profile details from Discord REST API."""
        try:
            r = self.bot.s.get("https://discord.com/api/v9/users/@me")
            if r.status_code == 200:
                profile = r.json()
                self.user_profile = profile
                self._log(f"Profile synced: {profile.get('username')} ({profile.get('id')})", "success")
                avatar_id = profile.get("avatar")
                user_id = profile.get("id")
                if avatar_id:
                    self.user_profile["avatar"] = f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_id}.png"
                else:
                    self.user_profile["avatar"] = "https://cdn.discordapp.com/embed/avatars/0.png"
                self._sync_state()
        except Exception as e:
            self._log(f"Failed to fetch user profile: {e}", "warning")

    def run(self):
        self.fetch_user_profile()
        self.bot.gateway.subscribeToGuildEvents()
        self.bot.gateway.command({"function":self._on_message,"name":"MESSAGE_CREATE"})
        
        threading.Thread(target=self._scan_loop, daemon=True).start()
        
        if getattr(self, '_spam_running', False): self._start_spam()
        if getattr(self, '_owo_running', False): self._start_owo()
        if getattr(self, '_slash_running', True): self._start_slash()
        
        self._log("Gateway connecting...","info")
        self.bot.gateway.run()

    def _is_message_for_me(self, msg: dict, text_to_scan: str) -> bool:
        my_id = self.user_profile.get("id", "")
        if not my_id:
            return False
            
        # 1. Direct Mentions check
        mentions = msg.get("mentions", []) or []
        if any(str(m.get("id")) == str(my_id) for m in mentions):
            return True
            
        # 2. Discord Message Reference / Reply check
        ref = msg.get("referenced_message")
        if ref and str(ref.get("author", {}).get("id")) == str(my_id):
            return True
            
        # 3. Text checks (username, global_name, label, id)
        content_lower = text_to_scan.lower()
        my_name = self.user_profile.get("username", "").lower()
        my_global = self.user_profile.get("global_name", "").lower()
        my_label = self.label.lower()
        
        if my_name and my_name in content_lower: return True
        if my_global and my_global in content_lower: return True
        if str(my_id) in content_lower: return True
        if my_label and my_label in content_lower: return True
        if self.id in content_lower: return True
        return False

    def fetch_discord_history(self):
        if not self.channel_id: return
        self._log("Syncing history from Discord...", "info")
        try:
            resp = self.bot.getMessages(self.channel_id, num=100)
            if resp.status_code != 200: return
            messages = resp.json()
            
            new_entries = []
            for m in messages:
                content = m.get("content", "").lower()
                author = m.get("author", {}).get("id", "")
                embeds = m.get("embeds", [])
                timestamp = m.get("timestamp")
                
                if author == POKETWO_ID and "you caught" in content:
                    try:
                        reg = re.search(r"caught a level (\d+)\s+(.+?)[\!\.]", content, re.IGNORECASE)
                        lvl = reg.group(1) if reg else "1"
                        name = reg.group(2).strip() if reg else "Unknown"
                        name = re.sub(r"<a?:\w+:\d+>", "", name).strip()
                        
                        img = ""
                        if embeds: img = embeds[0].get("image", {}).get("url", "")
                        
                        from datetime import timezone
                        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                        if (datetime.now(timezone.utc) - dt).days > 7: continue
                        
                        entry = {
                            "id": m["id"][:8],
                            "datetime": dt.isoformat(),
                            "time": dt.strftime("%H:%M:%S"),
                            "pokemon_name": name,
                            "display_name": name.replace("-", " ").title(),
                            "caught_by": self.label,
                            "channel_id": self.channel_id,
                            "success": True,
                            "is_shiny": "shiny" in content,
                            "level": lvl,
                            "discord_img": img,
                            **_fetch_poke(name)
                        }
                        new_entries.append(entry)
                    except: pass
            
            if new_entries:
                from logger import log_history_batch
                log_history_batch(new_entries)
                self._log(f"Synced {len(new_entries)} entries from Discord", "success")
        except Exception as e:
            self._log(f"History sync failed: {e}", "error")

# ── Pokemon List Auto-Update ──────────────────────────────────────────────────
def _update_pokemon_list():
    while True:
        try:
            log_event("Updating Pokemon database from PokeAPI...","info")
            r=requests.get("https://pokeapi.co/api/v2/pokemon?limit=2000",timeout=10)
            if r.status_code==200:
                names=[p["name"] for p in r.json()["results"]]
                with open("pokemon.txt","w",encoding="utf-8") as f:
                    f.write("\n".join(names))
                log_event(f"Database updated: {len(names)} Pokemons cached.","success")
        except Exception as e: log_event(f"Update failed: {e}","error")
        time.sleep(86400)

# ── Public API ────────────────────────────────────────────────────────────────
def start_spam_for(tid):
    with _nlock: 
        n=_nodes.get(tid)
        if n: 
            n.catching = False # Force release catch lock on manual start
            n._start_spam()
    _sync_persistence()

def stop_spam_for(tid):
    with _nlock:
        n=_nodes.get(tid)
        if n: n.stop_spam()
    _sync_persistence()

def start_spam_all():
    with _nlock: nl=list(_nodes.values())
    for n in nl: 
        n._start_spam()
    _sync_persistence()

def stop_spam_all():
    with _nlock: nl=list(_nodes.values())
    for n in nl: n.stop_spam()
    _sync_persistence()

def start_owo_for(tid):
    with _nlock:
        n=_nodes.get(tid)
        if n: n._start_owo()
    _sync_persistence()

def stop_owo_for(tid):
    with _nlock:
        n=_nodes.get(tid)
        if n: n.stop_owo()
    _sync_persistence()

def start_owo_all():
    with _nlock: nl=list(_nodes.values())
    for n in nl: 
        n._start_owo()
    _sync_persistence()

def stop_owo_all():
    with _nlock: nl=list(_nodes.values())
    for n in nl: n.stop_owo()
    _sync_persistence()

def _sync_persistence():
    tokens = get_tokens()
    with _nlock:
        for t in tokens:
            n = _nodes.get(t["id"])
            if n:
                t["spam_active"] = n._spam_running
                t["owo_active"] = n._owo_running
                t["balances"] = n.balances
                t["owo_channel_id"] = n.owo_channel_id
                t["channel_id"] = n.channel_id
                t["owo_last_run"] = n._owo_last_run
                t["slash_last_run"] = n._slash_last_run
                t["msg_active"] = getattr(n, "_msg_running", False)
                t["msg_channel_id"] = getattr(n, "msg_channel_id", "")
                t["msg_delay"] = getattr(n, "msg_delay", 30)
                t["msg_random_delay"] = getattr(n, "msg_random_delay", False)
    save_tokens(tokens)
    log_event("Engine and UI synchronized successfully.", "success")

def resume_all_captchas():
    with _nlock: nl = list(_nodes.values())
    for n in nl:
        if n._captcha_detected:
            n.resume_from_captcha()
    from logger import clear_captcha
    clear_captcha()

def resume_captcha_for(tid):
    label = tid[:8]
    with _nlock:
        n = _nodes.get(tid)
        if n:
            label = n.label
            if n._captcha_detected:
                n.resume_from_captcha()
    from logger import resolve_captcha_in_history
    resolve_captcha_in_history(label)


def sync_all_balances():
    with _nlock: nl = list(_nodes.values())
    threads = []
    for n in nl:
        t = threading.Thread(target=n.sync_balances, daemon=True)
        t.start()
        threads.append(t)
    for t in threads:
        t.join(timeout=10.0)

def sync_all_history():
    with _nlock: nl = list(_nodes.values())
    for n in nl: n.fetch_discord_history()

def get_node(tid):
    with _nlock:
        return _nodes.get(tid)

def get_node_statuses()->list:
    with _nlock:
        return [{"id":n.id,"label":n.label,"spamming":n._spam_running,"owo_running":n._owo_running,
                 "catching":n.catching,"guild_id":n.guild_id,"channel_id":n.channel_id,
                 "profile":n.user_profile, "balances": n.balances,
                 "captcha_detected": n._captcha_detected,
                 "captcha_url": getattr(n, "_captcha_url", ""),
                 "captcha_time": getattr(n, "_captcha_time", ""),
                 "msg_running": getattr(n, "_msg_running", False)}
                for n in _nodes.values()]

# ── Heartbeat ─────────────────────────────────────────────────────────────────
def _heartbeat():
    threading.Thread(target=_update_pokemon_list, daemon=True).start()
    # Initial history sync after startup
    time.sleep(15)
    sync_all_history()
    
    while True:
        try:
            tokens=get_tokens()
            cfg_ids={t["id"] for t in tokens}
            with _nlock: live=set(_nodes.keys())
            active_ids = {t["id"] for t in tokens if t.get("active", True)}
            
            for cfg in tokens:
                if not cfg.get("active",True): continue
                if cfg["id"] not in live:
                    node=BotNode(cfg)
                    with _nlock: _nodes[cfg["id"]]=node
                    threading.Thread(target=node.run,daemon=True,name=f"node-{cfg['id'][:8]}").start()
                    log_event(f"Node started: {cfg.get('label','?')}","success")
                    time.sleep(5.5)
            
            with _nlock:
                # Stop nodes that are either removed from DB or marked inactive
                for tid in live:
                    if tid not in active_ids:
                        n=_nodes.pop(tid,None)
                        if n: n.stop(); log_event(f"Node deactivated/stopped: {n.label}","warning")
            
            set_status(f"Online - {len(_nodes)} node(s)")
            time.sleep(10) # Check every 10s for node changes
        except Exception as e:
            log_event(f"Heartbeat error: {e}","error")
        time.sleep(10)

def start():
    log_event("Fafnir Engine starting...","info")
    # Start the global Advanced Image Catch Queue worker
    threading.Thread(target=_adv_queue_worker, daemon=True, name="AdvImageQueue").start()
    t=threading.Thread(target=_heartbeat,daemon=True,name="heartbeat")
    t.start()

def get_node(tid):
    with _nlock:
        return _nodes.get(tid)
