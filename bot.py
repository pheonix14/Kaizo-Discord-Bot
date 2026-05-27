import socket

# Monkey-patch socket.getaddrinfo to force IPv4 DNS resolution (prevents IPv6 getaddrinfo failed errors on Windows)
_original_getaddrinfo = socket.getaddrinfo
def _patched_getaddrinfo(*args, **kwargs):
    args = list(args)
    if 'family' in kwargs:
        kwargs['family'] = socket.AF_INET
    elif len(args) >= 3:
        args[2] = socket.AF_INET
    else:
        while len(args) < 3:
            args.append(0)
        args[2] = socket.AF_INET
    return _original_getaddrinfo(*args, **kwargs)
socket.getaddrinfo = _patched_getaddrinfo

import disnake
from disnake.ext import commands
import os
import sys
import time
import argparse
import logging
from config import Config
import database.db_setup as db_setup

# Parse Command Line Arguments for Multi-Bot Support
parser = argparse.ArgumentParser(description="KAIZER X Bot Instance")
parser.add_argument("--token", help="Discord Bot Token", default=Config.DISCORD_TOKEN)
parser.add_argument("--id", help="Bot Instance ID", default="main_bot")
args = parser.parse_args()

# Setup 100% Logging for this specific bot instance
log_file = os.path.join("logs", f"{args.id}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("BOT")

def create_bot(token, instance_id):
    """
    Creates and returns a bot instance.
    """
    intents = disnake.Intents.all()
    bot = commands.Bot(
        command_prefix=commands.when_mentioned_or(Config.DEFAULT_PREFIX),
        intents=intents,
        help_command=None
    )
    bot.start_time = time.time()
    bot.instance_id = instance_id
    bot.token = token

    @bot.event
    async def on_ready():
        logger.info("====================================")
        logger.info("[PROCESS] STARTING KAIZER X CORE")
        logger.info(f"[PROCESS] Instance ID: {bot.instance_id}")
        logger.info(f"[SUCCESS] Logged in as: {bot.user.name}")
        logger.info("====================================")
        
        try:
            logger.info("[PROCESS] Initializing Databases...")
            db_setup.init_db()
            logger.info("[SUCCESS] Databases Ready.")
        except Exception as e:
            logger.error(f"[ERROR] Database initialization failed: {e}")
        
        cogs_dir = os.path.join(os.path.dirname(__file__), 'cogs')
        if os.path.exists(cogs_dir):
            for filename in os.listdir(cogs_dir):
                if filename.endswith('.py') and not filename.startswith('__'):
                    logger.info(f"[PROCESS] Loading Module: {filename}...")
                    try:
                        bot.load_extension(f'cogs.{filename[:-3]}')
                        logger.info(f"[SUCCESS] Module {filename} is now PLUG-AND-PLAY active.")
                    except Exception as e:
                        logger.error(f"[ERROR] Failed to plug in {filename}: {e}. Skipping to next module.")
        else:
            logger.warning("[ERROR] Cogs directory not found. Running core only.")


    @bot.event
    async def on_error(event, *args, **kwargs):
        logger.exception(f"Unhandled exception in {event}")

    @bot.event
    async def on_disconnect():
        logger.warning(f"Bot {bot.instance_id} disconnected.")

    return bot

async def run_bot_instance(token, instance_id):
    """
    Coroutine to start a bot instance. Use this for Wasmer/In-process hosting.
    """
    bot = create_bot(token, instance_id)
    try:
        await bot.start(token)
    except Exception as e:
        logger.error(f"Bot {instance_id} encountered fatal error: {e}")

if __name__ == "__main__":
    token = args.token or os.getenv("DISCORD_TOKEN")
    if token and token != "YOUR_DISCORD_BOT_TOKEN_HERE":
        logger.info(f"Starting bot instance {args.id} in standalone mode...")
        bot = create_bot(token, args.id)
        try:
            bot.run(token)
        except Exception as e:
            logger.error(f"Failed to start bot instance {args.id}: {e}")
    else:
        logger.warning(f"No Discord Token provided for instance {args.id}. Bot is idle and waiting for token via Dashboard.")
        # Keep the process alive if needed, or just let it exit if it's meant to be managed by the dashboard



