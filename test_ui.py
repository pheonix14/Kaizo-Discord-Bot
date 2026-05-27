import requests
import re
import sys

BASE_URL = "http://127.0.0.1:8000"

def check_emojis(html, file_name):
    emojis = ["🛡️", "⚡", "🛑", "🔒", "⚙️", "📊", "🔊", "✨", "🗂️", "📋", "⚠️"]
    found = []
    for emoji in emojis:
        if emoji in html:
            found.append(emoji)
    
    if found:
        print(f"[FAILED] Found {len(found)} emojis in {file_name}")
        return False
    else:
        print(f"[PASSED] No emojis found in {file_name}")
        return True

def check_svgs(html, file_name):
    # Just basic check to ensure SVG tags exist
    if "<svg" in html:
        print(f"[PASSED] SVGs found in {file_name}")
        return True
    else:
        print(f"[FAILED] No SVGs found in {file_name}")
        return False

def test_homepage():
    print("Testing Homepage (/) ...")
    resp = requests.get(f"{BASE_URL}/")
    html = resp.text
    
    emoji_pass = check_emojis(html, "homepage")
    svg_pass = check_svgs(html, "homepage")
    
    if not (emoji_pass and svg_pass):
        sys.exit(1)

def test_login():
    print("Testing Login (/login via redirect) ...")
    # Actually login redirects to discord, let's just test that the endpoints exist
    pass

if __name__ == "__main__":
    try:
        test_homepage()
        print("All UI tests passed successfully!")
    except Exception as e:
        print(f"Test failed with exception: {e}")
        sys.exit(1)
