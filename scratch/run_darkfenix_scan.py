import urllib.request
import json
import time

BASE_URL = "http://127.0.0.1:8085"

def trigger_scan():
    # Trigger scan on darkfenix2323's server
    payload = {
        "guild_ids": ["1504410729623719997"],
        "token_ids": ["9fdeb86a-18c2-4224-999e-ee300d4d8397"]
    }
    req = urllib.request.Request(
        f"{BASE_URL}/api/scan/start",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        r = urllib.request.urlopen(req)
        return json.loads(r.read().decode())
    except Exception as e:
        print("Error triggering scan:", e)
        return None

def check_status():
    try:
        r = urllib.request.urlopen(f"{BASE_URL}/api/scan/status")
        return json.loads(r.read().decode())
    except Exception as e:
        print("Error checking status:", e)
        return None

if __name__ == "__main__":
    print("Triggering scan...")
    res = trigger_scan()
    print("Trigger response:", res)
    if not res or not res.get("ok"):
        print("Failed to trigger scan.")
        exit(1)

    print("\nPolling status in real time for 15 seconds:")
    for i in range(15):
        time.sleep(1)
        status = check_status()
        scans = status.get("scans", {})
        if scans:
            for key, val in scans.items():
                print(f"Time: {i+1}s | Server: {val.get('guild_name')} | Status: {val.get('status')} | Scanned: {val.get('members_scanned')}/{val.get('total_members')}")
                if val.get("log"):
                    print("  Last log:", val["log"][0])
        else:
            print(f"Time: {i+1}s | No active scans.")
