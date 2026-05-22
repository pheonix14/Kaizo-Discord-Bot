import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Supabase Configurations
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")
SUPABASE_PUBLISHABLE_KEY = os.getenv("SUPABASE_PUBLISHABLE_KEY")

DISCORD_APP_ID = os.getenv("DISCORD_APP_ID")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")

# HOST_URL will be defined after HOST and PORT
HOST = os.getenv("HOST", "127.0.0.1")

# Web Configurations
PORT = int(os.getenv("PORT", 8000))
if HOST == "0.0.0.0":
    HOST = "127.0.0.1"
HOST_URL = os.getenv("HOST_URL", f"http://{HOST}:{PORT}")

# Developer / admin user IDs (comma-separated Discord IDs)
DEVELOPER_ID = str(os.getenv("DEVELOPER_ID", "")).strip()

# Validation
if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError("Missing Supabase configuration. Please check your .env file.")

if not DISCORD_BOT_TOKEN:
    raise ValueError("Missing Discord bot token. Please check your .env file.")
