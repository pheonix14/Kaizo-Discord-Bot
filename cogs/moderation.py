import disnake
from disnake.ext import commands
import datetime
import asyncio
import re
from collections import defaultdict

# Spam tracking dictionaries
# user_id -> list of message timestamps
user_message_times = defaultdict(list)
# user_id -> list of {content, channel_id, timestamp}
user_message_history = defaultdict(list)

SPAM_LIMIT = 5           # Max messages before mute
SPAM_TIME_WINDOW = 5     # Seconds window for message limit
DUPLICATE_LIMIT = 3      # Same message across channels
MUTE_DURATION_MINS = 10  # Auto-mute duration

class Moderation(commands.Cog):
    """
    Ultimate Anti-Spam, Raid Protection, and Moderation Engine.
    """
    def __init__(self, bot):
        self.bot = bot

    async def auto_mute(self, message: disnake.Message, reason: str):
        """
        Applies a Discord built-in timeout to the user.
        """
        duration = datetime.timedelta(minutes=MUTE_DURATION_MINS)
        try:
            await message.author.timeout(duration=duration, reason=reason)
            
            embed = disnake.Embed(
                title="SPAM PROTECTION TRIGGERED",
                description=f"**User:** {message.author.mention}\n**Action:** Auto-Muted ({MUTE_DURATION_MINS} mins)\n**Reason:** {reason}",
                color=0xef4444 # Red for warning
            )
            await message.channel.send(embed=embed)
            
            # Optionally DM the user
            try:
                await message.author.send(f"You have been auto-muted in **{message.guild.name}** for {MUTE_DURATION_MINS} minutes. Reason: {reason}")
            except:
                pass
        except disnake.Forbidden:
            pass # Bot doesn't have permissions to timeout this user (e.g., they are Admin)

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.author.bot or not message.guild:
            return

        # --- Link & Blacklist Protection ---
        # Basic link regex
        url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        if url_pattern.search(message.content):
            # Check if user has permission to post links
            if not message.author.guild_permissions.manage_messages:
                await message.delete()
                await message.channel.send(f"{message.author.mention}, you are not allowed to post links here.", delete_after=5)
                return

        user_id = message.author.id
        now = datetime.datetime.utcnow()

        # 1. Track rapid message spam
        user_message_times[user_id].append(now)
        # Remove timestamps older than SPAM_TIME_WINDOW
        user_message_times[user_id] = [t for t in user_message_times[user_id] if (now - t).total_seconds() <= SPAM_TIME_WINDOW]
        
        if len(user_message_times[user_id]) >= SPAM_LIMIT:
            user_message_times[user_id].clear() # Reset to prevent multiple triggers
            await self.auto_mute(message, "Sending messages too quickly (Rapid Spam).")
            return

        # 2. Track duplicate cross-channel/same-channel spam
        history = user_message_history[user_id]
        history.append({'content': message.content, 'channel_id': message.channel.id, 'timestamp': now})
        
        # Keep only the last 10 messages for analysis
        if len(history) > 10:
            history.pop(0)
            
        # Count identical messages sent within the last 60 seconds
        recent_duplicates = [m for m in history if m['content'].lower() == message.content.lower() and (now - m['timestamp']).total_seconds() <= 60]
        
        if len(recent_duplicates) >= DUPLICATE_LIMIT:
            user_message_history[user_id].clear() # Reset
            await self.auto_mute(message, "Sending duplicate messages across channels (Copy-Paste Spam).")
            return

    # --- Standard Moderation Commands ---

    @commands.slash_command(name="mute", description="Mutes a user for a specific duration.")
    @commands.default_member_permissions(moderate_members=True)
    async def mute(self, inter: disnake.ApplicationCommandInteraction, user: disnake.Member, minutes: int, reason: str = "No reason provided."):
        duration = datetime.timedelta(minutes=minutes)
        await user.timeout(duration=duration, reason=reason)
        
        embed = disnake.Embed(title="USER MUTED", color=0x2b2d31)
        embed.add_field(name="User", value=user.mention, inline=True)
        embed.add_field(name="Duration", value=f"{minutes} minutes", inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        await inter.response.send_message(embed=embed)

    @commands.slash_command(name="unmute", description="Removes mute from a user.")
    @commands.default_member_permissions(moderate_members=True)
    async def unmute(self, inter: disnake.ApplicationCommandInteraction, user: disnake.Member):
        await user.timeout(duration=None, reason="Manual unmute.")
        await inter.response.send_message(f"{user.mention} has been unmuted.", ephemeral=True)

    @commands.slash_command(name="kick", description="Kicks a user from the server.")
    @commands.default_member_permissions(kick_members=True)
    async def kick(self, inter: disnake.ApplicationCommandInteraction, user: disnake.Member, reason: str = "No reason provided."):
        await user.kick(reason=reason)
        await inter.response.send_message(f"Kicked {user.mention}. Reason: {reason}", ephemeral=True)

    @commands.slash_command(name="ban", description="Bans a user from the server.")
    @commands.default_member_permissions(ban_members=True)
    async def ban(self, inter: disnake.ApplicationCommandInteraction, user: disnake.Member, reason: str = "No reason provided."):
        await user.ban(reason=reason)
        await inter.response.send_message(f"Banned {user.mention}. Reason: {reason}", ephemeral=True)

def setup(bot):
    bot.add_cog(Moderation(bot))
