"""
Download all Pokemon official artwork sprites from PokeAPI GitHub CDN.
Saves to static/pokemon/{name}.png  (served as /static/pokemon/{name}.png)
Run once: python download_pokemon.py
"""
import requests, os, time, sys

OUT = os.path.join(os.path.dirname(__file__), "static", "pokemon")
os.makedirs(OUT, exist_ok=True)

BASE_SPRITE = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{id}.png"
BASE_SPRITE_FALLBACK = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{id}.png"

print("Fetching Pokémon list from PokeAPI...")
try:
    r = requests.get("https://pokeapi.co/api/v2/pokemon?limit=2000", timeout=15)
    data = r.json()
    pokemon = data.get("results", [])
except Exception as e:
    print(f"Failed to fetch list: {e}")
    sys.exit(1)

print(f"Found {len(pokemon)} Pokémon. Downloading images...")

ok, skip, fail = 0, 0, 0

for p in pokemon:
    name = p["name"]                         # e.g. "bulbasaur", "mr-mime"
    pid  = p["url"].rstrip("/").split("/")[-1]  # numeric ID from URL

    outfile = os.path.join(OUT, f"{name}.png")
    if os.path.exists(outfile) and os.path.getsize(outfile) > 500:
        skip += 1
        continue

    # Try official artwork first, fallback to normal sprite
    downloaded = False
    for url in [BASE_SPRITE.format(id=pid), BASE_SPRITE_FALLBACK.format(id=pid)]:
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200 and len(resp.content) > 500:
                with open(outfile, "wb") as f:
                    f.write(resp.content)
                ok += 1
                downloaded = True
                break
        except Exception:
            pass

    if not downloaded:
        fail += 1
        print(f"  FAIL: {name} (#{pid})")
    else:
        sys.stdout.write(f"\r  OK: {ok} downloaded | {skip} skipped | {fail} failed    ")
        sys.stdout.flush()

    time.sleep(0.03)  # ~30ms between requests — polite rate

print(f"\n\nDone! {ok} downloaded, {skip} already existed, {fail} failed.")
print(f"Images saved to: {OUT}")
