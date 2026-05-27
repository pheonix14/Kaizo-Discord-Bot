import requests

CLIENT_ID = "1507250208495505478"
CLIENT_SECRET = "9CaSTWNQmj-cN9JKkWPaiK2qlkxbMFSd"

data = {
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "grant_type": "authorization_code",
    "code": "fake_code_12345",
    "redirect_uri": "http://127.0.0.1:8000/callback"
}

headers = {"Content-Type": "application/x-www-form-urlencoded"}
resp = requests.post("https://discord.com/api/oauth2/token", data=data, headers=headers)

print(f"Status Code: {resp.status_code}")
print(f"Response: {resp.text}")
