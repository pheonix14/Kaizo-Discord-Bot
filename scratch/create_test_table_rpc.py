import requests
import sys

SUPABASE_URL  = "https://cwputkmuqgpxydfxsrnm.supabase.co"
SERVICE_KEY   = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN3cHV0a211cWdweHlkZnhzcm5tIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTAzODc3OCwiZXhwIjoyMDk0NjE0Nzc4fQ.e4raXAvgNzKoJWr6FNIDydOuH3EYxWEIQGoOOKQtZKY"

stmt = """CREATE TABLE IF NOT EXISTS test (
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

def run():
    print("Calling exec_sql RPC...")
    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/rpc/exec_sql",
        headers={
            "apikey": SERVICE_KEY,
            "Authorization": f"Bearer {SERVICE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        },
        json={"sql": stmt}
    )
    print(f"Status Code: {r.status_code}")
    if r.text:
        print(f"Response: {r.text}")
    if r.status_code in (200, 201, 204):
        print("Table 'test' created successfully via RPC!")
    else:
        print("Failed to create table via RPC.")

if __name__ == "__main__":
    run()
