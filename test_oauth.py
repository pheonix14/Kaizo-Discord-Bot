import requests
import sys

CLIENT_ID = "1507250208495505478"
TEST_URIS = [
    "http://127.0.0.1:5000/callback",
    "http://localhost:5000/callback",
    "http://127.0.0.1:8000/callback",
    "http://localhost:8000/callback",
    "http://127.0.0.1/callback",
    "http://localhost/callback",
    "https://kaizerk5.com/callback"
]

def test_uri(uri):
    url = f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={uri}&response_type=code&scope=identify%20guilds"
    print(f"Testing: {uri}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    resp = requests.get(url, headers=headers)
    if "Invalid OAuth2 redirect_uri" in resp.text:
        print(f"[FAILED] {uri} is INVALID")
        return False
    elif "Invalid OAuth2 Application" in resp.text:
        print(f"[FAILED] {uri} failed: Invalid Client ID")
        return False
    else:
        print(f"[PASSED] {uri} is VALID!")
        return True

valid_uris = []
for uri in TEST_URIS:
    if test_uri(uri):
        valid_uris.append(uri)

if valid_uris:
    print(f"\nFound Valid URIs: {valid_uris}")
else:
    print("\nNo valid URIs found among the test set.")
