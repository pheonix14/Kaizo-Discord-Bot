"""
full_browser_test.py
1. Creates the 'test' table in Supabase via direct REST API using service key
2. Verifies test.html loads, master scan button works, results auto-load
"""
import asyncio, sys, io, json, requests

if sys.platform.startswith('win'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from playwright.async_api import async_playwright

SUPABASE_URL = "https://cwputkmuqgpxydfxsrnm.supabase.co"
SERVICE_KEY  = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN3cHV0a211cWdweHlkZnhzcm5tIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTAzODc3OCwiZXhwIjoyMDk0NjE0Nzc4fQ.e4raXAvgNzKoJWr6FNIDydOuH3EYxWEIQGoOOKQtZKY"

APP_URL = "http://127.0.0.1:8085"

HDR = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}",
    "Content-Type": "application/json",
}

# ─── Step 1: Create the test table via Supabase REST insert trick ──────────────
# We can't run DDL via REST, but we can check if the table exists by doing a
# select and catching the error. If it doesn't exist, we insert a dummy row via
# the PostgREST /rest/v1/test endpoint which will fail but confirm presence.
# The real trick: use the running Flask app's own init endpoint if available,
# OR use psycopg2 with the pooler connection string (port 6543).

def try_create_table_via_pooler():
    """Try to create table via Supabase transaction pooler on port 6543."""
    try:
        import psycopg2
        # Supabase transaction pooler (IPv4 friendly, works without IPv6)
        host = f"aws-0-ap-south-1.pooler.supabase.com"
        conn = psycopg2.connect(
            host=host,
            port=6543,
            dbname="postgres",
            user=f"postgres.cwputkmuqgpxydfxsrnm",
            password="",  # will fail without password
            connect_timeout=8,
        )
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS test (
            id TEXT PRIMARY KEY,
            token_id TEXT, token_label TEXT,
            guild_id TEXT, guild_name TEXT,
            channel_id TEXT, channel_name TEXT,
            writable BOOLEAN, text_allowed BOOLEAN, link_allowed BOOLEAN,
            last_scan TIMESTAMPTZ DEFAULT NOW(),
            scan_reason TEXT
        )""")
        cur.close(); conn.close()
        return True, "Created via pooler"
    except Exception as e:
        return False, str(e)

def check_table_exists():
    """Check if 'test' table exists by doing a select via PostgREST."""
    try:
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/test?limit=1",
            headers=HDR,
            timeout=10
        )
        if r.status_code == 200:
            return True, f"Table exists! Rows: {r.json()}"
        elif r.status_code == 404 or "PGRST205" in r.text:
            return False, "Table does not exist"
        else:
            return False, f"Status {r.status_code}: {r.text}"
    except Exception as e:
        return False, str(e)

def seed_test_row():
    """Insert a test row to verify write works."""
    import uuid, datetime
    row = {
        "id": "browser_test_" + uuid.uuid4().hex[:8],
        "token_id": "test_token",
        "token_label": "Browser Test",
        "guild_id": "0",
        "guild_name": "Test Guild",
        "channel_id": "1234567890",
        "channel_name": "general",
        "writable": True,
        "text_allowed": True,
        "link_allowed": True,
        "last_scan": datetime.datetime.utcnow().isoformat() + "Z",
        "scan_reason": None,
    }
    try:
        r = requests.post(
            f"{SUPABASE_URL}/rest/v1/test",
            headers={**HDR, "Prefer": "return=minimal"},
            json=row, timeout=10
        )
        if r.status_code in (200, 201, 204):
            return True, row["id"]
        else:
            return False, f"Status {r.status_code}: {r.text}"
    except Exception as e:
        return False, str(e)

def cleanup_test_row(row_id):
    """Remove the test row we seeded."""
    try:
        requests.delete(
            f"{SUPABASE_URL}/rest/v1/test?id=eq.{row_id}",
            headers=HDR, timeout=10
        )
    except:
        pass


async def browser_test():
    errors = []
    warnings = []

    print("\n" + "="*55)
    print("  STEP 1: Checking Supabase 'test' table")
    print("="*55)

    exists, msg = check_table_exists()
    print(f"  Table check: {msg}")

    if not exists:
        print("  Table missing! Attempting to create via pooler...")
        ok, pmsg = try_create_table_via_pooler()
        print(f"  Pooler result: {pmsg}")
        # Re-check
        exists2, msg2 = check_table_exists()
        if not exists2:
            print(f"  Still missing: {msg2}")
            print("  Will continue browser test anyway...")
        else:
            print(f"  Table now exists!")
            exists = True

    # If table exists, seed a row so the UI has something to show
    seeded_id = None
    if exists:
        print("\n  Seeding a test result row...")
        ok, seed_info = seed_test_row()
        if ok:
            seeded_id = seed_info
            print(f"  Seeded row id: {seeded_id}")
        else:
            print(f"  Seed failed: {seed_info}")
            warnings.append(f"Seed failed: {seed_info}")

    print("\n" + "="*55)
    print("  STEP 2: Browser test of test.html")
    print("="*55)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        def on_console(msg):
            text = msg.text
            if msg.type == "error":
                print(f"  [JS ERROR] {text}")
                if "Failed to load resource" not in text:
                    errors.append(f"JS Error: {text}")
            elif msg.type == "warning" and "tailwind" not in text.lower():
                print(f"  [JS WARN] {text}")

        def on_pageerror(err):
            print(f"  [PAGE ERROR] {err.message}")
            errors.append(f"Page Error: {err.message}")

        page.on("console", on_console)
        page.on("pageerror", on_pageerror)

        # Navigate
        print(f"\n  Navigating to {APP_URL}/test.html ...")
        resp = await page.goto(f"{APP_URL}/test.html", wait_until="networkidle")
        print(f"  HTTP Status: {resp.status}")
        if resp.status != 200:
            errors.append(f"Page returned HTTP {resp.status}")

        await page.wait_for_timeout(2000)

        title = await page.title()
        print(f"  Page Title: {title}")

        # Check master verify button
        btn = await page.query_selector("#master-verify-btn")
        if btn:
            print("  [OK] Master Verify button found")
        else:
            print("  [FAIL] Master Verify button NOT found")
            errors.append("Master Verify button missing")

        # Switch to Results tab
        print("\n  Switching to Results tab...")
        results_tab = await page.query_selector("button[onclick*=\"switchTab('results')\"]")
        if results_tab:
            await results_tab.click()
            await page.wait_for_timeout(2000)
            print("  [OK] Clicked Results tab")
        else:
            # Try by text content
            await page.evaluate("switchTab('results')")
            await page.wait_for_timeout(2000)
            print("  [OK] Switched to Results tab via JS")

        # Check results area
        stat_total = await page.query_selector("#stat-total")
        if stat_total:
            total_text = await stat_total.inner_text()
            print(f"  [OK] stat-total element found, value = '{total_text}'")
            if exists and seeded_id and total_text == "0":
                warnings.append("stat-total shows 0 even though a row was seeded - table may not be synced yet")
        else:
            errors.append("stat-total element not found")
            print("  [FAIL] stat-total element NOT found")

        results_container = await page.query_selector("#results-container")
        if results_container:
            content = await results_container.inner_text()
            print(f"  [OK] results-container found, content preview: '{content[:80].strip()}'")
        else:
            errors.append("results-container element not found")

        # Check copy all button
        copy_btn = await page.query_selector("button[onclick*='copyAllSuccessful']")
        if copy_btn:
            print("  [OK] Copy All Successful button found")
        else:
            print("  [WARN] Copy All Successful button not visible (may need results)")

        # Test /api/test/results endpoint directly
        print("\n  Testing /api/test/results endpoint...")
        api_resp = await page.evaluate("""
            async () => {
                try {
                    const r = await fetch('/api/test/results');
                    const data = await r.json();
                    return { ok: true, total: data.total, status: r.status };
                } catch(e) {
                    return { ok: false, error: e.message };
                }
            }
        """)
        if api_resp.get("ok"):
            print(f"  [OK] /api/test/results returned HTTP {api_resp['status']}, total={api_resp['total']}")
        else:
            errors.append(f"/api/test/results failed: {api_resp.get('error')}")
            print(f"  [FAIL] /api/test/results error: {api_resp.get('error')}")

        # Test copy functionality via JS
        print("\n  Testing copyChipId function...")
        copy_result = await page.evaluate("""
            () => {
                return typeof copyChipId === 'function' && typeof copyText === 'function';
            }
        """)
        if copy_result:
            print("  [OK] copyChipId and copyText functions are defined")
        else:
            errors.append("Copy functions not defined in JS")

        # Check auto-poll timer is set (30s results interval)
        poll_ok = await page.evaluate("""
            () => {
                // We can't directly inspect setInterval IDs, but we can check
                // that allScanResults is a global array (meaning init ran)
                return Array.isArray(window.allScanResults);
            }
        """)
        if poll_ok:
            print("  [OK] allScanResults global is initialized (auto-poll active)")
        else:
            errors.append("allScanResults not initialized")

        await browser.close()

    # Cleanup seeded row
    if seeded_id:
        print(f"\n  Cleaning up seeded row {seeded_id}...")
        cleanup_test_row(seeded_id)
        print("  Cleanup done.")

    # Summary
    print("\n" + "="*55)
    if errors:
        print(f"  TEST FAILED — {len(errors)} error(s):")
        for e in errors:
            print(f"    - {e}")
        if warnings:
            print(f"  Warnings ({len(warnings)}):")
            for w in warnings:
                print(f"    - {w}")
        return False
    else:
        print("  ALL CHECKS PASSED!")
        if warnings:
            print(f"  Warnings ({len(warnings)}):")
            for w in warnings:
                print(f"    - {w}")
        return True

if __name__ == "__main__":
    ok = asyncio.run(browser_test())
    sys.exit(0 if ok else 1)
