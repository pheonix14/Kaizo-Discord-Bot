import urllib.request
import json
try:
    req = urllib.request.urlopen("http://localhost:8085/api/data", timeout=5)
    print(f"Status Code: {req.getcode()}")
    data = json.loads(req.read().decode('utf-8'))
    print("Keys in data:", list(data.keys()))
    if "error" in data:
        print("API Error:", data["error"])
except Exception as e:
    print(f"Failed to fetch: {e}")
