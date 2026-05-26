import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
from logger import SUPABASE_URL, SUPABASE_KEY

HDR = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal",
}

def exec_sql(sql: str):
    url = f"{SUPABASE_URL}/pg/query"
    try:
        r = requests.post(url, headers=HDR, json={"query": sql}, timeout=15)
        print(f"SQL execution status: {r.status_code}")
        print(f"Response: {r.text}")
        return r.status_code in (200, 201)
    except Exception as e:
        print(f"Error executing SQL: {e}")
        return False

print("1. Checking scan_config table availability via PostgREST...")
res = requests.get(f"{SUPABASE_URL}/rest/v1/scan_config", headers=HDR)
print(f"Status Code: {res.status_code}")
print(f"Response: {res.text}")

print("\n2. Trying to reload schema cache via NOTIFY command...")
sql = "NOTIFY pgrst, 'reload schema';"
exec_sql(sql)

print("\n3. Re-checking scan_config table after reload...")
res = requests.get(f"{SUPABASE_URL}/rest/v1/scan_config", headers=HDR)
print(f"Status Code: {res.status_code}")
print(f"Response: {res.text}")
