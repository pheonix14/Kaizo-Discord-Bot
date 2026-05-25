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

# Extract Client/App ID from Bot Token if not explicitly set
if not DISCORD_APP_ID and DISCORD_BOT_TOKEN:
    try:
        import base64
        token_parts = DISCORD_BOT_TOKEN.split('.')
        if len(token_parts) > 0:
            client_id_b64 = token_parts[0]
            # Add base64 padding if necessary
            padding = len(client_id_b64) % 4
            if padding:
                client_id_b64 += '=' * (4 - padding)
            decoded_bytes = base64.b64decode(client_id_b64)
            decoded_id = decoded_bytes.decode('utf-8').strip()
            if decoded_id.isdigit():
                DISCORD_APP_ID = decoded_id
    except Exception:
        pass

# HOST_URL will be defined after HOST and PORT
HOST = os.getenv("HOST", "127.0.0.1")

# Web Configurations
PORT = int(os.getenv("PORT", 8000))
display_host = HOST
if display_host == "0.0.0.0":
    display_host = "127.0.0.1"
HOST_URL = os.getenv("HOST_URL", f"http://{display_host}:{PORT}")

# Developer / admin user IDs (comma-separated Discord IDs)
DEVELOPER_ID = str(os.getenv("DEVELOPER_ID", "")).strip()

# Validation
IS_CONFIGURED = True
if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY or not DISCORD_BOT_TOKEN:
    import logging
    logging.getLogger("kaizer_k5.config").warning(
        "Missing configuration (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, or DISCORD_BOT_TOKEN). "
        "Application will start in SETUP MODE."
    )
    IS_CONFIGURED = False

