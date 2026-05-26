import urllib.request
import json
import time

BASE_URL = "http://127.0.0.1:8085"

def get_data():
    try:
        r = urllib.request.urlopen(f"{BASE_URL}/api/data")
        return json.loads(r.read().decode())
    except Exception as e:
        print("Error getting data:", e)
        return None

def start_master_scan(token_ids):
    req = urllib.request.Request(
        f"{BASE_URL}/api/test/master-scan-queued",
        data=json.dumps({"token_ids": token_ids}).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    try:
        r = urllib.request.urlopen(req)
        return json.loads(r.read().decode())
    except Exception as e:
        print("Error starting scan:", e)
        return None

def check_status(job_id):
    try:
        r = urllib.request.urlopen(f"{BASE_URL}/api/test/scan-status/{job_id}")
        return json.loads(r.read().decode())
    except Exception as e:
        print("Error getting status:", e)
        return None

def cancel_scan(job_id):
    req = urllib.request.Request(
        f"{BASE_URL}/api/test/scan-cancel/{job_id}",
        data=b"{}",
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    try:
        r = urllib.request.urlopen(req)
        return json.loads(r.read().decode())
    except Exception as e:
        print("Error cancelling scan:", e)
        return None

if __name__ == "__main__":
    print("Checking active nodes...")
    data = get_data()
    if not data or not data.get("nodes"):
        print("No live nodes found in engine! Wait for engine to start.")
        exit(1)
        
    tids = [n["id"] for n in data["nodes"]]
    print(f"Found active nodes: {tids}")
    
    print("\nStarting Master Scan...")
    res = start_master_scan(tids)
    print("Response:", res)
    if not res or not res.get("ok"):
        print("Failed to start.")
        exit(1)
        
    job_id = res["job_id"]
    
    # Poll a few times
    for i in range(3):
        time.sleep(2)
        status = check_status(job_id)
        print(f"Poll {i+1}: Status={status.get('status')}, Done={status.get('done')}/{status.get('total')}")
        if status.get('log'):
            print("Logs:")
            for l in status['log']:
                print("  ", l)
                
    print("\nCancelling scan...")
    cancel_res = cancel_scan(job_id)
    print("Cancel Response:", cancel_res)
    
    # Poll after cancel
    for i in range(3):
        time.sleep(2)
        status = check_status(job_id)
        print(f"Poll {i+4} (after cancel): Status={status.get('status')}, Done={status.get('done')}/{status.get('total')}")
        if status.get('log'):
            print("Logs:")
            for l in status['log']:
                print("  ", l)
