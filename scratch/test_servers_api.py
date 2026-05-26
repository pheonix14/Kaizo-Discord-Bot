import requests
import json
import sys

try:
    print("Fetching /api/tokens...")
    r_tokens = requests.get("http://127.0.0.1:8085/api/tokens", timeout=5)
    print(f"Tokens Status Code: {r_tokens.status_code}")
    print(f"Tokens Response: {r_tokens.text[:1000]}")
    
    print("\nFetching /api/scan/servers...")
    r_servers = requests.get("http://127.0.0.1:8085/api/scan/servers", timeout=5)
    print(f"Servers Status Code: {r_servers.status_code}")
    print(f"Servers Response: {r_servers.text[:1000]}")
except Exception as e:
    print(f"Error: {e}")
