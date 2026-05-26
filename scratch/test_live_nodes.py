import requests
import json

try:
    r = requests.get("http://127.0.0.1:8085/api/image/live", timeout=5)
    print(f"Status: {r.status_code}")
    print("Live Nodes Response:")
    print(json.dumps(r.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")
