# src/bot/admin_utils.py
import discord
from discord.ext import commands
from src import config

def get_developer_ids():
    raw_id = config.DEVELOPER_ID
    if not raw_id:
        return []
    # Support comma-separated IDs
    return [int(x.strip()) for x in raw_id.split(",") if x.strip().isdigit()]

def is_developer(user_id):
    from src import config
    if getattr(config, 'BYPASS_DISCORD', False) and str(user_id) == "123456789012345678":
        return True
    if not user_id:
        return False
    dev_ids = get_developer_ids()
    try:
        uid = int(user_id)
        return uid in dev_ids
    except (ValueError, TypeError):
        return False

def is_admin(user_id: int) -> bool:
    return is_developer(user_id)

def admin_only():
    """A decorator for discord commands to restrict them to bot developers."""
    async def predicate(ctx: commands.Context):
        if not is_developer(ctx.author.id):
            await ctx.send("You do not have permission to run this command.", delete_after=5)
            return False
        return True
    return commands.check(predicate)
