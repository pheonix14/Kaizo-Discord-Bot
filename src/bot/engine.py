import logging
import os
import discord
from discord.ext import commands
from src import config
from src.db import client as db_client

# Configure Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kaizer_k5.engine")
logging.getLogger("httpx").setLevel(logging.WARNING)

async def get_dynamic_prefix(bot, message):
    if not message.guild:
        prefixes = ["k!", "!", ".", "/"]
    else:
        settings = db_client.get_guild_settings(message.guild.id)
        prefix_val = settings.get("prefix", "k!, !, ., /")
        if isinstance(prefix_val, list):
            prefixes = prefix_val
        elif isinstance(prefix_val, str):
            prefixes = [p.strip() for p in prefix_val.split(",") if p.strip()]
        else:
            prefixes = ["k!", "!", ".", "/"]
    return commands.when_mentioned_or(*prefixes)(bot, message)

class KaizerBot(commands.Bot):
    def __init__(self):
        # All intents are required for anti-nuke audit log and event checks
        intents = discord.Intents.all()
        super().__init__(
            command_prefix=get_dynamic_prefix, 
            intents=intents, 
            application_id=int_or_none(config.DISCORD_APP_ID)
        )
        self.help_command = None
        self.maintenance_mode = False
        self.global_blacklist = []
        
    async def setup_hook(self):
        cogs_dir = os.path.join(os.path.dirname(__file__), 'cogs')
        
        # Ensure cogs directory exists
        if not os.path.exists(cogs_dir):
            os.makedirs(cogs_dir)
            
        # Dynamically load all modular cogs
        for filename in os.listdir(cogs_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                cog_path = f"src.bot.cogs.{filename[:-3]}"
                try:
                    await self.load_extension(cog_path)
                    logger.info(f"Loaded cog: {cog_path}")
                except Exception as e:
                    logger.error(f"Failed to load cog {cog_path}: {e}")

    async def on_ready(self):
        logger.info(f"Kaizer K5 Engine connected to Discord as: {self.user} (ID: {self.user.id})")
        
        # Sync slash commands globally once the client is logged in and ready
        try:
            await self.tree.sync()
            logger.info("Application command tree synced globally in on_ready.")
        except Exception as e:
            logger.error(f"Failed to sync command tree in on_ready: {e}")
            
        # Verify and sync guild settings in DB for all active guilds
        for guild in self.guilds:
            db_client.get_guild_settings(guild.id, guild.name)
            logger.info(f"Synced guild settings for {guild.name} (ID: {guild.id})")

def int_or_none(val):
    try:
        return int(val) if val else None
    except ValueError:
        return None

# Create the bot instance
bot = KaizerBot()

# --- Global Command Checks (Supabase Sync) ---
async def check_command_access(guild_id: int, command_name: str, author: discord.Member) -> bool:
    """Checks if a command is enabled and if the user has permission to use it."""
    config = db_client.get_command_config(str(guild_id), command_name)
    if not config:
        return True # Default to enabled if not found

    if not config.get("enabled", True):
        return False

    perm_level = config.get("permission_level", "Everyone")
    if perm_level == "Owner" and author.id != author.guild.owner_id:
        return False
    if perm_level == "Admin" and not author.guild_permissions.administrator:
        return False
    if perm_level == "Mod" and not (author.guild_permissions.manage_messages or author.guild_permissions.manage_guild):
        return False

    # Check allowed_roles if specific roles are required
    allowed_roles = config.get("allowed_roles", [])
    if allowed_roles and not author.guild_permissions.administrator:
        has_role = any(str(role.id) in allowed_roles for role in author.roles)
        if not has_role:
            return False

    # Check allowed_channels
    # (Implementation for channels can be added here)

    return True

@bot.check
async def global_prefix_check(ctx: commands.Context):
    if not ctx.guild or not ctx.command:
        return True
    
    # Global maintenance mode check
    if bot.maintenance_mode and not await bot.is_owner(ctx.author):
        raise commands.CheckFailure("Bot is currently in maintenance mode.")
        
    # Global blacklist check
    if ctx.author.id in bot.global_blacklist:
        raise commands.CheckFailure("You have been globally blacklisted from using this bot.")
        
    has_access = await check_command_access(ctx.guild.id, ctx.command.qualified_name, ctx.author)
    if not has_access:
        raise commands.CheckFailure(f"The command `{ctx.command.qualified_name}` is disabled or you lack permission.")
    return True

@bot.tree.interaction_check
async def global_slash_check(interaction: discord.Interaction):
    if not interaction.guild or not interaction.command:
        return True
        
    if bot.maintenance_mode and not await bot.is_owner(interaction.user):
        await interaction.response.send_message("Bot is currently in maintenance mode.", ephemeral=True)
        return False
        
    if interaction.user.id in bot.global_blacklist:
        await interaction.response.send_message("You have been globally blacklisted from using this bot.", ephemeral=True)
        return False
        
    has_access = await check_command_access(interaction.guild.id, interaction.command.qualified_name, interaction.user)
    if not has_access:
        await interaction.response.send_message(f"The command `{interaction.command.qualified_name}` is disabled or you lack permission.", ephemeral=True)
        return False
    return True

@bot.event
async def on_command_error(ctx: commands.Context, error: Exception):
    if isinstance(error, commands.CheckFailure):
        await ctx.send(str(error))
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You do not have permission to use this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing argument. Usage: `{ctx.prefix}{ctx.command.name} [arguments]`")
    elif isinstance(error, commands.CommandNotFound):
        pass # Ignore command not found
    else:
        logger.error(f"Command Error: {error}")
        await ctx.send("An error occurred while executing that command.")
