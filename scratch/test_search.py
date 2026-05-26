import requests
import json

try:
    print("Testing search endpoint without queries...")
    r = requests.get("http://127.0.0.1:8085/api/scan/search", timeout=5)
    print(f"Status Code: {r.status_code}")
    print(f"Response: {r.text[:500]}")
    
    print("\nTesting search query 'andrew'...")
    r = requests.get("http://127.0.0.1:8085/api/scan/search?q=andrew", timeout=5)
    print(f"Status Code: {r.status_code}")
    print(f"Response: {r.text[:500]}")
except Exception as e:
    print(f"Error during test: {e}")
