import os
import sys
import json
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.web.flask_app import app

def run_test():
    guild_id = "1504410729623719997"
    client = app.test_client()

    # Set valid session cookie
    session_cookie = json.dumps({"expires": time.time() + 3600})
    client.set_cookie("session", session_cookie)

    print("Requesting server_export for guild...")
    resp = client.post(
        f"/api/guild/{guild_id}/server-action",
        data=json.dumps({"action": "server_export"}),
        content_type="application/json"
    )
    print("Status:", resp.status_code)
    try:
        data = json.loads(resp.data.decode('utf-8'))
        print("Success:", data.get("success"))
        if data.get("success"):
            export_data = data.get("export_data", {})
            print("Roles count:", len(export_data.get("roles", [])))
            print("Categories count:", len(export_data.get("categories", [])))
            print("Export data sample:", list(export_data.keys()))
        else:
            print("Error details:", data.get("error"))
    except Exception as e:
        print("Failed to parse response:", e)

if __name__ == "__main__":
    run_test()
