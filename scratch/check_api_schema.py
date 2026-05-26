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
try:
    r = requests.get(url, headers=headers, timeout=10)
    if r.status_code == 200:
        schema = r.json()
        definitions = schema.get("definitions", {})
        print("\nExposed Tables in Schema:")
        for table in sorted(definitions.keys()):
            print(f" - {table}")
    else:
        print(f"Error fetching schema: {r.status_code}")
        print(r.text)
except Exception as e:
    print(f"Request failed: {e}")
