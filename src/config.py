import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

def clean_env_var(val):
    if val is None:
        return None
    val_str = str(val).strip()
    if (val_str.startswith('"') and val_str.endswith('"')) or (val_str.startswith("'") and val_str.endswith("'")):
        return val_str[1:-1].strip()
    return val_str

# Supabase Configurations
SUPABASE_URL = clean_env_var(os.getenv("SUPABASE_URL"))
SUPABASE_ANON_KEY = clean_env_var(os.getenv("SUPABASE_ANON_KEY"))
SUPABASE_SERVICE_ROLE_KEY = clean_env_var(os.getenv("SUPABASE_SERVICE_ROLE_KEY"))
SUPABASE_SECRET_KEY = clean_env_var(os.getenv("SUPABASE_SECRET_KEY"))
SUPABASE_PUBLISHABLE_KEY = clean_env_var(os.getenv("SUPABASE_PUBLISHABLE_KEY"))

DISCORD_APP_ID = clean_env_var(os.getenv("DISCORD_APP_ID"))
DISCORD_BOT_TOKEN = clean_env_var(os.getenv("DISCORD_BOT_TOKEN"))
DISCORD_CLIENT_SECRET = clean_env_var(os.getenv("DISCORD_CLIENT_SECRET"))

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


def check_and_reload():
    global SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_SECRET_KEY, SUPABASE_PUBLISHABLE_KEY
    global DISCORD_APP_ID, DISCORD_BOT_TOKEN, DISCORD_CLIENT_SECRET, DEVELOPER_ID, IS_CONFIGURED
    if not IS_CONFIGURED:
        from dotenv import load_dotenv
        from supabase import create_client
        
        load_dotenv(dotenv_path=env_path, override=True)
        
        url = clean_env_var(os.getenv("SUPABASE_URL"))
        key = clean_env_var(os.getenv("SUPABASE_SERVICE_ROLE_KEY"))
        token = clean_env_var(os.getenv("DISCORD_BOT_TOKEN"))
        
        if url and key and token:
            SUPABASE_URL = url
            SUPABASE_SERVICE_ROLE_KEY = key
            DISCORD_BOT_TOKEN = token
            SUPABASE_ANON_KEY = clean_env_var(os.getenv("SUPABASE_ANON_KEY"))
            SUPABASE_SECRET_KEY = clean_env_var(os.getenv("SUPABASE_SECRET_KEY"))
            SUPABASE_PUBLISHABLE_KEY = clean_env_var(os.getenv("SUPABASE_PUBLISHABLE_KEY"))
            DISCORD_APP_ID = clean_env_var(os.getenv("DISCORD_APP_ID"))
            DISCORD_CLIENT_SECRET = clean_env_var(os.getenv("DISCORD_CLIENT_SECRET"))
            DEVELOPER_ID = clean_env_var(os.getenv("DEVELOPER_ID", ""))
            
            if not DISCORD_APP_ID and DISCORD_BOT_TOKEN:
                try:
                    import base64
                    token_parts = DISCORD_BOT_TOKEN.split('.')
                    if len(token_parts) > 0:
                        client_id_b64 = token_parts[0]
                        padding = len(client_id_b64) % 4
                        if padding:
                            client_id_b64 += '=' * (4 - padding)
                        decoded_bytes = base64.b64decode(client_id_b64)
                        decoded_id = decoded_bytes.decode('utf-8').strip()
                        if decoded_id.isdigit():
                            DISCORD_APP_ID = decoded_id
                except Exception:
                    pass
            
            IS_CONFIGURED = True
            
            # Re-initialize Supabase client in db_client
            from src.db import client as db_client
            try:
                db_client.supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
                db_client.logger.info("Successfully re-initialized Supabase client dynamically.")
            except Exception as e:
                db_client.logger.critical(f"Failed to initialize Supabase client: {e}")


