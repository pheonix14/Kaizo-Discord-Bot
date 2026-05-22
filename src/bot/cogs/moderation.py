import discord
from discord.ext import commands
from discord import app_commands
import datetime

class ModerationCog(commands.Cog, name="Moderation"):
    """Commands for server moderators."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="kick", description="Kick a member from the server.")
    @commands.has_permissions(kick_members=True)
    @app_commands.describe(member="The member to kick", reason="The reason for kicking")
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.send("You cannot kick someone with a higher or equal role than you.")
        try:
            await member.kick(reason=reason)
            await ctx.send(embed=discord.Embed(description=f"✅ Kicked **{member}**. Reason: {reason}", color=discord.Color.orange()))
        except discord.Forbidden:
            await ctx.send("I do not have permission to kick that member.")

    @commands.hybrid_command(name="ban", description="Ban a member from the server.")
    @commands.has_permissions(ban_members=True)
    @app_commands.describe(member="The member to ban", reason="The reason for banning")
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.send("You cannot ban someone with a higher or equal role than you.")
        try:
            await member.ban(reason=reason)
            await ctx.send(embed=discord.Embed(description=f"✅ Banned **{member}**. Reason: {reason}", color=discord.Color.red()))
        except discord.Forbidden:
            await ctx.send("I do not have permission to ban that member.")

    @commands.hybrid_command(name="unban", description="Unban a user by their ID.")
    @commands.has_permissions(ban_members=True)
    @app_commands.describe(user_id="The ID of the user to unban", reason="The reason for unbanning")
    async def unban(self, ctx: commands.Context, user_id: str, *, reason: str = "No reason provided"):
        try:
            user = await self.bot.fetch_user(int(user_id))
            await ctx.guild.unban(user, reason=reason)
            await ctx.send(embed=discord.Embed(description=f"✅ Unbanned **{user}**. Reason: {reason}", color=discord.Color.green()))
        except ValueError:
            await ctx.send("Please provide a valid user ID.")
        except discord.NotFound:
            await ctx.send("That user is not banned.")
        except discord.Forbidden:
            await ctx.send("I do not have permission to unban users.")

    @commands.hybrid_command(name="timeout", description="Timeout a member.")
    @commands.has_permissions(moderate_members=True)
    @app_commands.describe(member="The member to timeout", minutes="Duration in minutes", reason="The reason")
    async def timeout(self, ctx: commands.Context, member: discord.Member, minutes: int, *, reason: str = "No reason provided"):
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.send("You cannot timeout someone with a higher or equal role than you.")
        duration = datetime.timedelta(minutes=minutes)
        try:
            await member.timeout(duration, reason=reason)
            await ctx.send(embed=discord.Embed(description=f"✅ Timed out **{member}** for {minutes}m. Reason: {reason}", color=discord.Color.orange()))
        except discord.Forbidden:
            await ctx.send("I do not have permission to timeout that member.")

    @commands.hybrid_command(name="untimeout", description="Remove a timeout from a member.")
    @commands.has_permissions(moderate_members=True)
    @app_commands.describe(member="The member to remove timeout from", reason="The reason")
    async def untimeout(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.send("You cannot manage this user.")
        try:
            await member.timeout(None, reason=reason)
            await ctx.send(embed=discord.Embed(description=f"✅ Removed timeout from **{member}**. Reason: {reason}", color=discord.Color.green()))
        except discord.Forbidden:
            await ctx.send("I do not have permission to remove timeout from that member.")

    @commands.hybrid_command(name="purge", description="Delete multiple messages in a channel.")
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(amount="Number of messages to delete")
    async def purge(self, ctx: commands.Context, amount: int):
        if amount <= 0 or amount > 100:
            return await ctx.send("Please specify an amount between 1 and 100.")
        deleted = await ctx.channel.purge(limit=amount + 1)  # +1 to include the command message
        await ctx.send(embed=discord.Embed(description=f"✅ Deleted {len(deleted)-1} messages.", color=discord.Color.green()), delete_after=5)

    @commands.hybrid_command(name="lock", description="Lock the current channel.")
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx: commands.Context):
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(embed=discord.Embed(description="🔒 Channel locked.", color=discord.Color.red()))

    @commands.hybrid_command(name="unlock", description="Unlock the current channel.")
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx: commands.Context):
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = None
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(embed=discord.Embed(description="🔓 Channel unlocked.", color=discord.Color.green()))

    @commands.hybrid_command(name="slowmode", description="Set the slowmode delay for the channel.")
    @commands.has_permissions(manage_channels=True)
    @app_commands.describe(seconds="Delay in seconds")
    async def slowmode(self, ctx: commands.Context, seconds: int):
        if seconds < 0 or seconds > 21600:
            return await ctx.send("Slowmode must be between 0 and 21600 seconds.")
        await ctx.channel.edit(slowmode_delay=seconds)
        await ctx.send(embed=discord.Embed(description=f"✅ Slowmode set to {seconds} seconds.", color=discord.Color.blue()))

async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationCog(bot))
