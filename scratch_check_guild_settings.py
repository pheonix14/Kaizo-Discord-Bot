import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.db.client import supabase

try:
    resp = supabase.table("guild_settings").select("*").limit(1).execute()
    print("Columns in guild_settings:")
    if resp.data:
        print(list(resp.data[0].keys()))
    else:
        print("No rows in guild_settings.")
except Exception as e:
    print("Error:", e)
