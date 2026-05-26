"""
create_table_via_flask.py
Adds a temporary /api/admin/create-test-table endpoint to the running app
by calling it if it exists, or directly via the supabase client using a workaround.
"""
import sys, io, requests

if sys.platform.startswith('win'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

APP_URL = "http://127.0.0.1:8085"
SUPABASE_URL = "https://cwputkmuqgpxydfxsrnm.supabase.co"
SERVICE_KEY  = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN3cHV0a211cWdweHlkZnhzcm5tIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTAzODc3OCwiZXhwIjoyMDk0NjE0Nzc4fQ.e4raXAvgNzKoJWr6FNIDydOuH3EYxWEIQGoOOKQtZKY"

HDR = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}",
    "Content-Type": "application/json",
}

# ── Method 1: Try to insert a dummy row - PostgREST will auto-fail but tells us if table exists
print("Checking if 'test' table already exists...")
r = requests.get(f"{SUPABASE_URL}/rest/v1/test?select=id&limit=1", headers=HDR, timeout=10)
print(f"  GET /rest/v1/test -> {r.status_code}: {r.text[:200]}")

if r.status_code == 200:
    print("  Table EXISTS already!")
    sys.exit(0)

print("\nTable does not exist. Trying to create via Supabase Admin API...")

# ── Method 2: Use the Supabase admin API to run a query
# The auth.admin endpoint sometimes allows running SQL
endpoints_to_try = [
    (f"{SUPABASE_URL}/rest/v1/rpc/query", {"query": "SELECT 1"}),
]

# ── Method 3: Use the pg meta API (available in some Supabase configs)
print("\nTrying pg meta API...")
r2 = requests.post(
    f"{SUPABASE_URL}/pg/query",
    headers=HDR,
    json={"query": """CREATE TABLE IF NOT EXISTS test (
        id TEXT PRIMARY KEY,
        token_id TEXT, token_label TEXT,
        guild_id TEXT, guild_name TEXT,
        channel_id TEXT, channel_name TEXT,
        writable BOOLEAN, text_allowed BOOLEAN, link_allowed BOOLEAN,
        last_scan TIMESTAMPTZ DEFAULT NOW(),
        scan_reason TEXT
    )"""},
    timeout=15
)
print(f"  pg/query -> {r2.status_code}: {r2.text[:200]}")
if r2.status_code in (200, 201, 204):
    print("  Created via pg/query!")
    sys.exit(0)

# ── Method 4: Use the Flask app itself - call a special create-table endpoint
print("\nTrying Flask /api/admin/create-test-table...")
r3 = requests.post(f"{APP_URL}/api/admin/create-test-table", timeout=10)
print(f"  -> {r3.status_code}: {r3.text[:200]}")
if r3.status_code == 200:
    print("  Created via Flask admin endpoint!")
    sys.exit(0)

# ── Method 5: Insert into the existing Supabase and let PostgREST auto-create
# Actually this won't work without DDL access
print("\nAll automated methods failed.")
print("\n" + "="*55)
print("MANUAL STEP REQUIRED:")
print("="*55)
print("1. Go to: https://supabase.com/dashboard/project/cwputkmuqgpxydfxsrnm/sql/new")
print("2. Paste and run this SQL:")
print("""
CREATE TABLE IF NOT EXISTS test (
    id TEXT PRIMARY KEY,
    token_id TEXT,
    token_label TEXT,
    guild_id TEXT,
    guild_name TEXT,
    channel_id TEXT,
    channel_name TEXT,
    writable BOOLEAN,
    text_allowed BOOLEAN,
    link_allowed BOOLEAN,
    last_scan TIMESTAMPTZ DEFAULT NOW(),
    scan_reason TEXT
);
""")
