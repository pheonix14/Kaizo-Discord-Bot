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

# Initialize Bot
intents = disnake.Intents.all()
bot = commands.Bot(
    command_prefix=commands.when_mentioned_or(Config.DEFAULT_PREFIX),
    intents=intents,
    help_command=None
)
bot.start_time = time.time()
bot.instance_id = args.id

@bot.event
async def on_ready():
    logger.info("====================================")
    logger.info("[ STARTING KAIZER X CORE ]")
    logger.info(f"Instance ID: {bot.instance_id}")
    logger.info(f"Logged in as: {bot.user.name} ({bot.user.id})")
    logger.info("====================================")
    
    # Initialize Pandas CSV Databases
    db_setup.init_db()
    
    # Load all modules (cogs) dynamically
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and not filename.startswith('__'):
            try:
                bot.load_extension(f'cogs.{filename[:-3]}')
                logger.info(f"[+] Loaded Module: {filename}")
            except Exception as e:
                logger.error(f"[-] Failed to load Module {filename}: {e}")

@bot.event
async def on_error(event, *args, **kwargs):
    logger.exception(f"Unhandled exception in {event}")

if __name__ == "__main__":
    if args.token and args.token != "YOUR_DISCORD_BOT_TOKEN_HERE":
        logger.info(f"Starting bot instance {args.id}...")
        bot.run(args.token)
    else:
        logger.critical("CRITICAL ERROR: No Discord Token Provided.")
        sys.exit(1)
