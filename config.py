import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """
    Central configuration class for KAIZER X.
    Loads tokens and URLs securely from environment variables.
    """
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")
    REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:5000/callback")
    
    PORT = int(os.getenv("PORT", 5000))
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///kaizerx.db")
    
    # Custom Prefix Default
    DEFAULT_PREFIX = "!"
