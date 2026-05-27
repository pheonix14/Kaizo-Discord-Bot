import urllib.request
import json

# Test the roles API
guild_id = None

# First try to get guild ID from config/session
try:
    with open('src/config.py', 'r') as f:
        content = f.read()
    print("Config content (first 200 chars):", content[:200])
except Exception as e:
    print("Config error:", e)

# Try hitting the API to test
test_urls = [
    'http://127.0.0.1:8000/health',
    'http://127.0.0.1:8000/api/status',
]

for url in test_urls:
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = resp.read().decode('utf-8')
            print(f'\n{url} -> STATUS {resp.status}')
            print(data[:300])
    except Exception as e:
        print(f'\n{url} -> ERROR: {e}')
