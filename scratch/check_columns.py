import requests
import json
import sys
sys.path.append(".")
import logger

url = f"{logger.SUPABASE_URL}/rest/v1/"
headers = {
    "apikey": logger.SUPABASE_KEY,
    "Authorization": f"Bearer {logger.SUPABASE_KEY}"
}

print("Fetching OpenAPI schema from Supabase...")
r = requests.get(url, headers=headers, timeout=10)
if r.status_code == 200:
    schema = r.json()
    definitions = schema.get("definitions", {})
    for t in ["members", "member_servers", "member_history"]:
        if t in definitions:
            print(f"\nTable: {t}")
            props = definitions[t].get("properties", {})
            for p, pinfo in props.items():
                print(f"  - {p}: {pinfo.get('type')} ({pinfo.get('format', 'no format')})")
        else:
            print(f"\nTable: {t} not found.")
else:
    print(r.text)
