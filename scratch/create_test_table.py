import requests
import sys

SUPABASE_URL = "https://cwputkmuqgpxydfxsrnm.supabase.co"
PROJECT_REF  = "cwputkmuqgpxydfxsrnm"
SERVICE_KEY  = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN3cHV0a211cWdweHlkZnhzcm5tIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTAzODc3OCwiZXhwIjoyMDk0NjE0Nzc4fQ.e4raXAvgNzKoJWr6FNIDydOuH3EYxWEIQGoOOKQtZKY"

HDR = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal",
}

sql = """CREATE TABLE IF NOT EXISTS test (
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
)"""

def exec_sql(query: str) -> bool:
    print("Trying Management API endpoint...")
    url = f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query"
    try:
        r = requests.post(url, headers={
            "Authorization": f"Bearer {SERVICE_KEY}",
            "Content-Type": "application/json",
        }, json={"query": query}, timeout=30)
        print(f"Management API status: {r.status_code}, response: {r.text}")
        if r.status_code in (200, 201):
            return True
    except Exception as e:
        print(f"Management API error: {e}")

    print("Trying REST shim fallback endpoint...")
    url2 = f"{SUPABASE_URL}/pg/query"
    try:
        r2 = requests.post(url2, headers=HDR, json={"query": query}, timeout=30)
        print(f"REST shim status: {r2.status_code}, response: {r2.text}")
        return r2.status_code in (200, 201)
    except Exception as e:
        print(f"REST shim error: {e}")
        return False

print("Creating 'test' table in Supabase...")
success = exec_sql(sql)
if success:
    print("SUCCESS: Table 'test' created successfully or already exists!")
else:
    print("FAILURE: Could not create 'test' table.")
