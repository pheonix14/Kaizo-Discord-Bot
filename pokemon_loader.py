import requests, os

_poke_cache = []

def load_pokemon_list():
    global _poke_cache
    if _poke_cache: return _poke_cache
    
    if not os.path.exists("pokemon.txt") or os.path.getsize("pokemon.txt") < 500:
        update_pokemon_list()
        
    try:
        with open("pokemon.txt", "r", encoding="utf-8") as f:
            _poke_cache = [line.strip().lower() for line in f if line.strip()]
            return _poke_cache
    except:
        return []

def reload_pokemon_list():
    """Clears the internal cache and force-reloads the latest list from disk."""
    global _poke_cache
    _poke_cache = []
    return load_pokemon_list()

def add_custom_pokemon(name: str):
    """Adds a unique, clean lowercase pokemon name to pokemon.txt and invalidates cache."""
    name_clean = name.strip().lower().replace("_", "-").replace(" ", "-")
    if not name_clean: return False
    
    current = load_pokemon_list()
    if name_clean in current:
        return True # Already exists
        
    current.append(name_clean)
    # Write back maintaining alphabetical order or standard list order
    try:
        with open("pokemon.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(current))
        reload_pokemon_list()
        return True
    except Exception as e:
        print(f"[Loader] Failed to add custom pokemon: {e}")
        return False

def remove_custom_pokemon(name: str):
    """Removes a pokemon name from pokemon.txt and invalidates cache."""
    name_clean = name.strip().lower().replace("_", "-").replace(" ", "-")
    if not name_clean: return False
    
    current = load_pokemon_list()
    if name_clean not in current:
        return True # Not there anyway
        
    current.remove(name_clean)
    try:
        with open("pokemon.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(current))
        reload_pokemon_list()
        return True
    except Exception as e:
        print(f"[Loader] Failed to remove custom pokemon: {e}")
        return False

def update_pokemon_list():
    """Fetch latest pokemon list from PokeAPI (Gen 1-9)"""
    try:
        print("[Engine] Updating Pokémon database via PokéAPI...")
        r = requests.get("https://pokeapi.co/api/v2/pokemon-species?limit=2000", timeout=10)
        if r.status_code == 200:
            names = []
            for p in r.json()["results"]:
                n = p["name"]
                names.append(n)
                if "-" in n:
                    names.append(n.split("-")[0]) # Add base name (e.g. Aegislash)
            
            # Remove duplicates and titles
            names = list(set([n.title().replace("-", " ") for n in names]))
            
            # Write names clean (lowercase for matching)
            names_clean = sorted(list(set([n.lower().strip().replace(" ", "-") for n in names])))
            
            with open("pokemon.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(names_clean))
            print(f"[Engine] Database updated: {len(names_clean)} entries.")
            reload_pokemon_list()
            return True
    except Exception as e:
        print(f"[Engine] Update failed: {e}")
    return False

