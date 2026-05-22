import discord
from discord.ext import commands, tasks
from discord import app_commands
from src.db import client as db_client

class StatsCog(commands.Cog, name="Stats"):
    """Live Stats Voice Channels management."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.stats_loop.start()

    def cog_unload(self):
        self.stats_loop.cancel()

    @tasks.loop(minutes=10)
    async def stats_loop(self):
        for guild in self.bot.guilds:
            try:
                settings = db_client.get_guild_settings(guild.id)
                if not settings:
                    continue

                if settings.get("counter_total_chan_id"):
                    chan = guild.get_channel(int(settings["counter_total_chan_id"]))
                    if chan:
                        fmt = settings.get("counter_total_fmt", "Total: {count}")
                        new_name = fmt.replace("{count}", str(guild.member_count))
                        if chan.name != new_name:
                            await chan.edit(name=new_name)

                if settings.get("counter_online_chan_id"):
                    chan = guild.get_channel(int(settings["counter_online_chan_id"]))
                    if chan:
                        online = sum(1 for m in guild.members if m.status != discord.Status.offline)
                        fmt = settings.get("counter_online_fmt", "Online: {count}")
                        new_name = fmt.replace("{count}", str(online))
                        if chan.name != new_name:
                            await chan.edit(name=new_name)

                if settings.get("counter_invc_chan_id"):
                    chan = guild.get_channel(int(settings["counter_invc_chan_id"]))
                    if chan:
                        in_vc = sum(1 for m in guild.members if m.voice)
                        fmt = settings.get("counter_invc_fmt", "In VC: {count}")
                        new_name = fmt.replace("{count}", str(in_vc))
                        if chan.name != new_name:
                            await chan.edit(name=new_name)

            except Exception as e:
                print(f"Error updating stats for guild {guild.id}: {e}")

    @stats_loop.before_loop
    async def before_stats_loop(self):
        await self.bot.wait_until_ready()

    # ── Group ────────────────────────────────────────────────────────────────
    
    @commands.hybrid_group(name="stats", description="Live stats channels.", fallback="help")
    @commands.has_permissions(administrator=True)
    async def stats(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @stats.command(name="setup", description="Auto-create all stat channels.")
    async def stats_setup(self, ctx: commands.Context):
        await ctx.send("Creating stats category and channels... Please wait.")
        
        category = await ctx.guild.create_category("📊 SERVER STATS")
        
        total_vc = await ctx.guild.create_voice_channel(f"Total: {ctx.guild.member_count}", category=category)
        await total_vc.set_permissions(ctx.guild.default_role, connect=False)
        
        online = sum(1 for m in ctx.guild.members if m.status != discord.Status.offline)
        online_vc = await ctx.guild.create_voice_channel(f"Online: {online}", category=category)
        await online_vc.set_permissions(ctx.guild.default_role, connect=False)
        
        db_client.update_guild_settings(ctx.guild.id, {
            "counter_category_id": str(category.id),
            "counter_total_chan_id": str(total_vc.id),
            "counter_online_chan_id": str(online_vc.id)
        })
        
        await ctx.send(embed=discord.Embed(description="✅ Live Stats channels have been created and locked.", color=discord.Color.green()))

    @stats.command(name="refresh", description="Force an immediate refresh of stat channels.")
    async def stats_refresh(self, ctx: commands.Context):
        await ctx.send("Forcing stats refresh...")
        # Just call the loop body manually for this guild
        guild = ctx.guild
        settings = db_client.get_guild_settings(guild.id)
        updated = 0
        
        if settings.get("counter_total_chan_id"):
            chan = guild.get_channel(int(settings["counter_total_chan_id"]))
            if chan:
                fmt = settings.get("counter_total_fmt", "Total: {count}")
                new_name = fmt.replace("{count}", str(guild.member_count))
                if chan.name != new_name:
                    await chan.edit(name=new_name)
                    updated += 1
                    
        await ctx.send(embed=discord.Embed(description=f"✅ Stats refreshed. ({updated} channels updated)", color=discord.Color.green()))

    @stats.command(name="format", description="Change the name format of a stat channel.")
    @app_commands.describe(stat_type="Which stat to format (total, online, invc)", fmt="Format e.g., 'Members: {count}'")
    async def stats_format(self, ctx: commands.Context, stat_type: str, fmt: str):
        if stat_type not in ["total", "online", "invc"]:
            return await ctx.send("Type must be `total`, `online`, or `invc`.")
            
        if "{count}" not in fmt:
            return await ctx.send("Format must include `{count}`.")
            
        db_client.update_guild_settings(ctx.guild.id, {f"counter_{stat_type}_fmt": fmt})
        await ctx.send(embed=discord.Embed(description=f"✅ Format for `{stat_type}` updated to `{fmt}`.\nRun `/stats refresh` to apply it immediately.", color=discord.Color.green()))

    @stats.command(name="interval", description="Set how often stats refresh (1-60 mins).")
    async def stats_interval(self, ctx: commands.Context, minutes: int):
        if minutes < 1 or minutes > 60:
            return await ctx.send("Interval must be between 1 and 60 minutes.")
            
        db_client.update_guild_settings(ctx.guild.id, {"counter_refresh_interval": minutes})
        self.stats_loop.change_interval(minutes=minutes)
        await ctx.send(embed=discord.Embed(description=f"✅ Stats will now refresh every {minutes} minutes.", color=discord.Color.green()))


async def setup(bot: commands.Bot):
    await bot.add_cog(StatsCog(bot))
