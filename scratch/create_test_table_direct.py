"""
create_test_table_direct.py
Creates the `test` table in Supabase using psycopg2 direct connection.
"""
import sys
import os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SUPABASE_URL = "https://cwputkmuqgpxydfxsrnm.supabase.co"
SERVICE_KEY  = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN3cHV0a211cWdweHlkZnhzcm5tIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTAzODc3OCwiZXhwIjoyMDk0NjE0Nzc4fQ.e4raXAvgNzKoJWr6FNIDydOuH3EYxWEIQGoOOKQtZKY"
PROJECT_REF  = "cwputkmuqgpxydfxsrnm"

# Standard Supabase PostgreSQL connection string
# Host is: db.<project_ref>.supabase.co, port 5432
# User: postgres, Password: the DB password set in Supabase dashboard
# NOTE: Try to get it from environment first
DB_PASSWORD = os.environ.get("SUPABASE_DB_PASSWORD", "")

SQL = """CREATE TABLE IF NOT EXISTS test (
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
);"""

print("=" * 55)
print("  Creating 'test' table via Supabase Client")
print("=" * 55)

# Method 1: Try supabase-py client - insert a dummy row to test if table exists
try:
    from supabase import create_client
    sb = create_client(SUPABASE_URL, SERVICE_KEY)
    print("\n[1] Testing if 'test' table already exists...")
    result = sb.table("test").select("id").limit(1).execute()
    print(f"    Table EXISTS! Rows returned: {len(result.data)}")
    print("\n    'test' table is READY to use.")
    sys.exit(0)
except Exception as e:
    err = str(e)
    if "does not exist" in err or "relation" in err.lower() or "42P01" in err:
        print(f"    Table does NOT exist yet: {err}")
    else:
        print(f"    Error checking table: {err}")

# Method 2: Try psycopg2 direct connection
print("\n[2] Attempting psycopg2 direct connection...")
if not DB_PASSWORD:
    print("    No SUPABASE_DB_PASSWORD env var set.")
    print("    Trying with empty password (will likely fail)...")

try:
    import psycopg2
    conn_str = f"postgresql://postgres:{DB_PASSWORD}@db.{PROJECT_REF}.supabase.co:5432/postgres"
    print(f"    Connecting to: db.{PROJECT_REF}.supabase.co:5432")
    conn = psycopg2.connect(conn_str, connect_timeout=10)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(SQL)
    cur.close()
    conn.close()
    print("    SUCCESS: Table 'test' created via direct psycopg2 connection!")
    sys.exit(0)
except Exception as e:
    print(f"    psycopg2 failed: {e}")

print("\nAll methods failed. Please create the table manually in Supabase SQL Editor:")
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
