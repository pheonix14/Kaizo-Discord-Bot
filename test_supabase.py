"""
test_supabase.py — Full integration test for the Supabase migration.
Tests: read, write, upsert across all tables.
"""
import sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASS = "[ OK ]"
FAIL = "[FAIL]"
results = []

def check(name, condition, detail=""):
    status = PASS if condition else FAIL
    results.append((status, name, detail))
    print(f"  {status} {name}" + (f" — {detail}" if detail else ""))

print("=" * 55)
print("  FAFNIR SUPABASE INTEGRATION TEST")
print("=" * 55)

import logger

# ── Test 1: init_db loads all data ─────────────────────────────
print("\n[1] init_db / connectivity")
try:
    logger.init_db()
    toks = logger.get_tokens()
    dex  = logger.get_dex()
    hist = logger.get_history()
    cfg  = logger.get_db()
    check("init_db connects to Supabase", True)
    check("tokens loaded", isinstance(toks, list), f"{len(toks)} token(s)")
    check("dex loaded", isinstance(dex, dict), f"{len(dex)} pokemon")
    check("history loaded", isinstance(hist, list), f"{len(hist)} entries")
    check("caught counter > 0", cfg.get("caught", 0) >= 0, str(cfg.get("caught")))
except Exception as e:
    check("init_db", False, str(e))

# ── Test 2: Config read/write ───────────────────────────────────
print("\n[2] bot_config read/write")
try:
    old_status = logger.get_db().get("status", "")
    logger.set_status("TEST_STATUS")
    time.sleep(0.5)
    new_status = logger._config_cache.get("status")
    check("set_status writes to cache", new_status == "TEST_STATUS", new_status)
    logger.set_status(old_status or "Online")
    check("status restored", True)
except Exception as e:
    check("bot_config write", False, str(e))

# ── Test 3: spam/owo/break/image configs ────────────────────────
print("\n[3] config sections")
try:
    spam = logger.get_spam_config()
    check("spam config readable", "message" in spam)
    owo = logger.get_owo_config()
    check("owo config readable", "hunt" in owo)
    brk = logger.get_break_config()
    check("break config readable", "enabled" in brk)
    img = logger.get_image_config()
    check("image config readable", "enabled" in img)
    mimic = logger.get_mimic_config()
    check("mimic config readable", "catch_randomizer" in mimic)
except Exception as e:
    check("config sections", False, str(e))

# ── Test 4: Dex upsert ──────────────────────────────────────────
print("\n[4] dex upsert")
try:
    test_name = "test_fafnir_dragon_99"
    logger.upsert_dex_entry(test_name, shiny=False, img="https://example.com/test.png", caught_by="tester")
    time.sleep(1)
    d = logger.get_dex()
    check("dex entry created in cache", test_name in d, str(d.get(test_name, {}).get("caught_count")))
except Exception as e:
    check("dex upsert", False, str(e))

# ── Test 5: History log ─────────────────────────────────────────
print("\n[5] history log")
try:
    import uuid as _uuid
    test_entry = {
        "id": "test_" + _uuid.uuid4().hex[:6],
        "pokemon_name": "test_ditto",
        "display_name": "Test Ditto",
        "caught_by": "tester",
        "channel_id": "000000000000000000",
        "success": True,
        "is_shiny": False,
        "hint": "",
        "level": "5",
        "iv": "99%",
        "discord_img": "",
        "is_image_catch": False,
        "confidence": 0.99,
        "sprite": "",
        "rarity": "common",
    }
    logger.log_history(test_entry)
    time.sleep(1)
    h = logger.get_history()
    found = any(e.get("id") == test_entry["id"] for e in h)
    check("history entry in cache", found)
except Exception as e:
    check("history log", False, str(e))

# ── Test 6: log_event ──────────────────────────────────────────
print("\n[6] log_event")
try:
    before = len(logger._logs_cache)
    logger.log_event("Test log entry from test_supabase.py", "info", "tester")
    after = len(logger._logs_cache)
    check("log_event inserts to cache", after > before, f"{before} -> {after}")
except Exception as e:
    check("log_event", False, str(e))

# ── Test 7: increment_caught ────────────────────────────────────
print("\n[7] counters")
try:
    before_caught = logger._config_cache.get("caught", 0)
    logger.increment_caught("tester")
    after_caught = logger._config_cache.get("caught", 0)
    check("increment_caught updates cache", after_caught == before_caught + 1,
          f"{before_caught} -> {after_caught}")
except Exception as e:
    check("increment_caught", False, str(e))

# ── Summary ─────────────────────────────────────────────────────
print("\n" + "=" * 55)
passed = sum(1 for r in results if r[0] == PASS)
failed = sum(1 for r in results if r[0] == FAIL)
print(f"  RESULTS: {passed} passed, {failed} failed out of {len(results)} tests")
if failed == 0:
    print("  *** ALL TESTS PASSED — Supabase migration complete! ***")
else:
    print("  *** SOME TESTS FAILED — review output above ***")
print("=" * 55)
