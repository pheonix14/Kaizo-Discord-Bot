import urllib.request
try:
    req = urllib.request.urlopen("http://localhost:8085/", timeout=5)
    html = req.read().decode('utf-8')
    with open("downloaded_index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Downloaded index.html successfully.")
except Exception as e:
    print(f"Failed to fetch: {e}")
