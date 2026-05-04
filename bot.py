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
        logger.info("[ STARTING KAIZER X CORE ]")
        logger.info(f"Instance ID: {bot.instance_id}")
        logger.info(f"Logged in as: {bot.user.name} ({bot.user.id})")
        logger.info("====================================")
        
        try:
            db_setup.init_db()
        except Exception as e:
            logger.error(f"CRITICAL: Database initialization failed: {e}")
        
        cogs_dir = os.path.join(os.path.dirname(__file__), 'cogs')
        if os.path.exists(cogs_dir):
            for filename in os.listdir(cogs_dir):
                if filename.endswith('.py') and not filename.startswith('__'):
                    try:
                        bot.load_extension(f'cogs.{filename[:-3]}')
                        logger.info(f"[+] Loaded Module: {filename}")
                    except Exception as e:
                        logger.error(f"[-] Failed to load Module {filename}: {e}")
        else:
            logger.warning("Cogs directory not found.")

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
            logger.critical(f"FATAL: {e}")
            sys.exit(1)
    else:
        logger.critical("CRITICAL ERROR: No Discord Token Provided.")
        sys.exit(1)


