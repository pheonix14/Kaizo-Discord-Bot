import requests
import json
import time

guild_id = "1396152575987941547"
cookies = {
    "session": json.dumps({"expires": time.time() + 3600})
}

try:
    res = requests.post(
        f"http://localhost:8000/api/guild/{guild_id}/server-action",
        cookies=cookies,
        json={"action": "server_export"}
    )
    print("Export Status Code:", res.status_code)
    data = res.json()
    print("Export Success:", data.get("success"))
    if data.get("success"):
        export_data = data.get("export_data", {})
        print("Roles count:", len(export_data.get("roles", [])))
        print("Roles names:", [r.get("name") for r in export_data.get("roles", [])])
        print("Categories count:", len(export_data.get("categories", [])))
        for cat in export_data.get("categories", []):
            print(f"Category: {cat.get('name')} (Channels: {len(cat.get('channels', []))})")
            for ch in cat.get("channels", []):
                print(f"  Chan: {ch.get('name')}, Type: {ch.get('type')}")
except Exception as e:
    print("Error:", e)
