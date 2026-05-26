import requests
import json

try:
    print("--- SCAN DEBUG ---")
    r = requests.get("http://127.0.0.1:8085/api/scan/debug", timeout=5)
    print(r.status_code)
    print(json.dumps(r.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")

try:
    print("\n--- NODE STATUSES & CAPTCHA ---")
    r = requests.get("http://127.0.0.1:8085/api/data", timeout=5)
    print(r.status_code)
    data = r.json()
    print(json.dumps(data.get("nodes"), indent=2))
except Exception as e:
    print(f"Error: {e}")
