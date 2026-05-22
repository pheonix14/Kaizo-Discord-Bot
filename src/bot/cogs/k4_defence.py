import discord
from discord.ext import commands
from discord import app_commands
import time
import hashlib
from typing import Dict, List, Tuple
from src.db import client as db_client

class K4DefenceCog(commands.Cog, name="K4 Defence"):
    """Advanced anti-spam and anti-raid protection system."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # user_id -> list of message records: (channel_id, timestamp, content_hash)
        self.message_cache: Dict[str, List[Tuple[str, float, str]]] = {}
        # user_id -> list of message IDs for rapid deletion
        self.message_objects: Dict[str, List[discord.Message]] = {}

    def get_content_hash(self, message: discord.Message) -> str:
        """Create a hash representing the message content and attachments."""
        content = message.content or ""
        attachments = "".join([a.url for a in message.attachments])
        return hashlib.md5((content + attachments).encode('utf-8')).hexdigest()

    async def punish_user(self, member: discord.Member, guild: discord.Guild, reason: str):
        """Mutes the user permanently and logs to modlog."""
        settings = db_client.get_guild_settings(str(guild.id))
        mute_role_id = settings.get("mute_role")
        
        # 1. Assign Mute Role
        if mute_role_id:
            role = guild.get_role(int(mute_role_id))
            if role:
                try:
                    await member.add_roles(role, reason=f"K4 Defence triggered: {reason}")
                except discord.Forbidden:
                    pass
        
        # 2. Log to Mod Log
        modlog_id = settings.get("mod_log_channel")
        if modlog_id:
            modlog = guild.get_channel(int(modlog_id))
            if modlog:
                embed = discord.Embed(
                    title="🛡️ K4 Defence Triggered",
                    description=f"**User:** {member.mention} ({member.id})\n**Action:** Muted\n**Reason:** {reason}\n*User must open a ticket to appeal.*",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow()
                )
                try:
                    await modlog.send(embed=embed)
                except discord.Forbidden:
                    pass
                    
        # 3. Log to DB Protection Logs
        db_client.log_protection_event(str(guild.id), "k4_defence", str(self.bot.user.id), "System", "Muted", f"Target: {member.id}. Reason: {reason}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        settings = db_client.get_guild_settings(str(message.guild.id))
        if not settings.get("k4_defence_enabled", False):
            return

        user_id = str(message.author.id)
        current_time = time.time()
        content_hash = self.get_content_hash(message)

        # Initialize cache for user
        if user_id not in self.message_cache:
            self.message_cache[user_id] = []
            self.message_objects[user_id] = []

        # Add current message
        self.message_cache[user_id].append((str(message.channel.id), current_time, content_hash))
        self.message_objects[user_id].append(message)

        # Clean up cache older than 15 seconds
        cutoff = current_time - 15.0
        self.message_cache[user_id] = [m for m in self.message_cache[user_id] if m[1] >= cutoff]
        self.message_objects[user_id] = [m for m in self.message_objects[user_id] if m.created_at.timestamp() >= cutoff]

        recent_messages = self.message_cache[user_id]

        triggered = False
        reason = ""

        # RULE 1: Cross-channel Exact Match Spam (3+ channels in 15 seconds)
        # Find all channels where this specific hash was sent
        channels_with_hash = set(m[0] for m in recent_messages if m[2] == content_hash)
        if len(channels_with_hash) >= 3:
            triggered = True
            reason = "Sent exact same message/image in 3+ channels simultaneously."

        # RULE 2: Rapid Speed Spam (5+ messages within 3 seconds)
        fast_cutoff = current_time - 3.0
        fast_messages = [m for m in recent_messages if m[1] >= fast_cutoff]
        if len(fast_messages) >= 5:
            triggered = True
            reason = "Rapid fire spam (5+ messages in 3 seconds)."

        if triggered:
            # 1. Punish User
            await self.punish_user(message.author, message.guild, reason)
            
            # 2. Delete all flagged messages
            for msg in self.message_objects[user_id]:
                try:
                    await msg.delete()
                except discord.NotFound:
                    pass # Already deleted
                except discord.Forbidden:
                    pass
            
            # 3. Clear cache for this user so we don't double-trigger
            self.message_cache[user_id] = []
            self.message_objects[user_id] = []

    # ── Commands ─────────────────────────────────────────────────────────────

    @commands.hybrid_group(name="k4defence", description="K4 Defence anti-spam/anti-raid system.", fallback="help")
    @commands.has_permissions(administrator=True)
    async def k4defence(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @k4defence.command(name="enable", description="Enable K4 Defence system.")
    @commands.has_permissions(administrator=True)
    async def enable(self, ctx: commands.Context):
        # We need to gracefully handle if the DB column isn't added yet
        try:
            db_client.update_guild_settings(ctx.guild.id, {"k4_defence_enabled": True})
            await ctx.send(embed=discord.Embed(description="✅ **K4 Defence has been ENABLED.**", color=discord.Color.green()))
        except Exception as e:
            await ctx.send(embed=discord.Embed(description="⚠️ Database error. Ensure `k4_defence_enabled` column exists in Supabase.", color=discord.Color.red()))

    @k4defence.command(name="disable", description="Disable K4 Defence system.")
    @commands.has_permissions(administrator=True)
    async def disable(self, ctx: commands.Context):
        try:
            db_client.update_guild_settings(ctx.guild.id, {"k4_defence_enabled": False})
            await ctx.send(embed=discord.Embed(description="❌ **K4 Defence has been DISABLED.**", color=discord.Color.red()))
        except Exception as e:
            await ctx.send(embed=discord.Embed(description="⚠️ Database error.", color=discord.Color.red()))

    @k4defence.command(name="status", description="Check if K4 Defence is currently active.")
    @commands.has_permissions(administrator=True)
    async def status(self, ctx: commands.Context):
        settings = db_client.get_guild_settings(str(ctx.guild.id))
        is_enabled = settings.get("k4_defence_enabled", False)
        
        status_text = "🟢 **ENABLED**" if is_enabled else "🔴 **DISABLED**"
        embed = discord.Embed(
            title="🛡️ K4 Defence Status",
            description=f"Current Status: {status_text}\n\n*If triggered, K4 Defence automatically deletes spam and permanently mutes the user.*",
            color=discord.Color.green() if is_enabled else discord.Color.red()
        )
        
        mute_role_id = settings.get("mute_role")
        if mute_role_id:
            embed.add_field(name="Mute Role", value=f"<@&{mute_role_id}>", inline=False)
        else:
            embed.add_field(name="⚠️ Mute Role Missing", value="No mute role configured! K4 Defence will delete messages but cannot mute users. Please set a mute role via Dashboard or `/automod modlog_set`.", inline=False)
            
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(K4DefenceCog(bot))
