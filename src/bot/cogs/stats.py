import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
from src.db import client as db_client

class StatsHelpView(discord.ui.View):
    def __init__(self, author_id: int):
        super().__init__(timeout=60.0)
        self.author_id = author_id
        self.current_page = 0
        
        self.pages = [
            # Page 1
            {
                "title": "[STATS] Kaizo - Live Server Stats Setup (Page 1/2)",
                "description": "Auto-create and manage live-updating member counters.",
                "fields": [
                    {"name": "• stats setup", "value": "Auto-create the stats category and default counter channels.\n*Permissions Required:* `Administrator`\n*Usage:* `.stats setup` or `/stats setup`"},
                    {"name": "• stats refresh", "value": "Force an immediate manual update of all stat channels.\n*Permissions Required:* `Administrator`\n*Usage:* `.stats refresh` or `/stats refresh`"}
                ]
            },
            # Page 2
            {
                "title": "[SETTINGS] Kaizo - Stats Customization (Page 2/2)",
                "description": "Configure refresh intervals and format names.",
                "fields": [
                    {"name": "• stats format <stat_type> <format_string>", "value": "Change a stat channel's format. Supported types: `total`, `online`, `offline`, `invc`. Must include `{count}` or `{value}`.\n*Permissions Required:* `Administrator`\n*Usage:* `.stats format total 'Members: {count}'`"},
                    {"name": "• stats interval <minutes>", "value": "Set counter refresh interval (between 1 and 60 minutes).\n*Permissions Required:* `Administrator`\n*Usage:* `.stats interval 10`"}
                ]
            }
        ]

    def make_embed(self) -> discord.Embed:
        page_data = self.pages[self.current_page]
        embed = discord.Embed(
            title=page_data["title"],
            description=page_data["description"],
            color=0x1ABC9C
        )
        for f in page_data["fields"]:
            embed.add_field(name=f["name"], value=f["value"], inline=False)
        embed.set_footer(text="Kaizo • Use the buttons below to navigate pages")
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Only the person who ran the command can use these buttons.", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            if hasattr(self, 'message') and self.message:
                await self.message.edit(view=self)
        except:
            pass

    @discord.ui.button(label="[<] Previous", style=discord.ButtonStyle.primary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
        else:
            self.current_page = len(self.pages) - 1
        await interaction.response.edit_message(embed=self.make_embed(), view=self)

    @discord.ui.button(label="Next [>]", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
        else:
            self.current_page = 0
        await interaction.response.edit_message(embed=self.make_embed(), view=self)

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
                settings = await asyncio.to_thread(db_client.get_guild_settings, guild.id)
                if not settings:
                    continue

                # Total Members
                if settings.get("counter_total_chan_id"):
                    chan = guild.get_channel(int(settings["counter_total_chan_id"]))
                    if chan:
                        fmt = settings.get("counter_total_fmt", "Total: {count}")
                        val = guild.member_count
                        new_name = fmt.replace("{count}", str(val)).replace("{value}", str(val))
                        if chan.name != new_name:
                            await chan.edit(name=new_name)

                # Online Members
                if settings.get("counter_online_chan_id"):
                    chan = guild.get_channel(int(settings["counter_online_chan_id"]))
                    if chan:
                        online = sum(1 for m in guild.members if m.status != discord.Status.offline)
                        fmt = settings.get("counter_online_fmt", "Online: {count}")
                        new_name = fmt.replace("{count}", str(online)).replace("{value}", str(online))
                        if chan.name != new_name:
                            await chan.edit(name=new_name)

                # Offline Members
                if settings.get("counter_offline_chan_id"):
                    chan = guild.get_channel(int(settings["counter_offline_chan_id"]))
                    if chan:
                        offline = sum(1 for m in guild.members if m.status == discord.Status.offline)
                        fmt = settings.get("counter_offline_fmt", "Offline: {count}")
                        new_name = fmt.replace("{count}", str(offline)).replace("{value}", str(offline))
                        if chan.name != new_name:
                            await chan.edit(name=new_name)

                # In VC
                if settings.get("counter_invc_chan_id"):
                    chan = guild.get_channel(int(settings["counter_invc_chan_id"]))
                    if chan:
                        in_vc = sum(1 for m in guild.members if m.voice)
                        fmt = settings.get("counter_invc_fmt", "In VC: {count}")
                        new_name = fmt.replace("{count}", str(in_vc)).replace("{value}", str(in_vc))
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
            view = StatsHelpView(ctx.author.id)
            msg = await ctx.send(embed=view.make_embed(), view=view)
            view.message = msg

    @stats.command(name="setup", description="Auto-create all stat channels.")
    async def stats_setup(self, ctx: commands.Context):
        await ctx.send("Creating stats category and channels... Please wait.")
        
        category = await ctx.guild.create_category("[STATS] SERVER STATS")
        
        total_vc = await ctx.guild.create_voice_channel(f"Total: {ctx.guild.member_count}", category=category)
        await total_vc.set_permissions(ctx.guild.default_role, connect=False)
        
        online = sum(1 for m in ctx.guild.members if m.status != discord.Status.offline)
        online_vc = await ctx.guild.create_voice_channel(f"Online: {online}", category=category)
        await online_vc.set_permissions(ctx.guild.default_role, connect=False)
        
        await asyncio.to_thread(db_client.update_guild_settings, ctx.guild.id, {
            "counter_category_id": str(category.id),
            "counter_total_chan_id": str(total_vc.id),
            "counter_online_chan_id": str(online_vc.id)
        })
        
        await ctx.send(embed=discord.Embed(description="[SUCCESS] Live Stats channels have been created and locked.", color=discord.Color.green()))

    @stats.command(name="refresh", description="Force an immediate refresh of stat channels.")
    async def stats_refresh(self, ctx: commands.Context):
        await ctx.send("Forcing stats refresh...")
        guild = ctx.guild
        settings = await asyncio.to_thread(db_client.get_guild_settings, guild.id)
        updated = 0
        
        if settings:
            # Total
            if settings.get("counter_total_chan_id"):
                chan = guild.get_channel(int(settings["counter_total_chan_id"]))
                if chan:
                    fmt = settings.get("counter_total_fmt", "Total: {count}")
                    val = guild.member_count
                    new_name = fmt.replace("{count}", str(val)).replace("{value}", str(val))
                    if chan.name != new_name:
                        await chan.edit(name=new_name)
                        updated += 1
            # Online
            if settings.get("counter_online_chan_id"):
                chan = guild.get_channel(int(settings["counter_online_chan_id"]))
                if chan:
                    fmt = settings.get("counter_online_fmt", "Online: {count}")
                    val = sum(1 for m in guild.members if m.status != discord.Status.offline)
                    new_name = fmt.replace("{count}", str(val)).replace("{value}", str(val))
                    if chan.name != new_name:
                        await chan.edit(name=new_name)
                        updated += 1
            # Offline
            if settings.get("counter_offline_chan_id"):
                chan = guild.get_channel(int(settings["counter_offline_chan_id"]))
                if chan:
                    fmt = settings.get("counter_offline_fmt", "Offline: {count}")
                    val = sum(1 for m in guild.members if m.status == discord.Status.offline)
                    new_name = fmt.replace("{count}", str(val)).replace("{value}", str(val))
                    if chan.name != new_name:
                        await chan.edit(name=new_name)
                        updated += 1
            # In VC
            if settings.get("counter_invc_chan_id"):
                chan = guild.get_channel(int(settings["counter_invc_chan_id"]))
                if chan:
                    fmt = settings.get("counter_invc_fmt", "In VC: {count}")
                    val = sum(1 for m in guild.members if m.voice)
                    new_name = fmt.replace("{count}", str(val)).replace("{value}", str(val))
                    if chan.name != new_name:
                        await chan.edit(name=new_name)
                        updated += 1
                        
        await ctx.send(embed=discord.Embed(description=f"[SUCCESS] Stats refreshed. ({updated} channels updated)", color=discord.Color.green()))

    @stats.command(name="format", description="Change the name format of a stat channel.")
    @app_commands.describe(stat_type="Which stat to format (total, online, offline, invc)", fmt="Format e.g., 'Members: {count}'")
    async def stats_format(self, ctx: commands.Context, stat_type: str, fmt: str):
        if stat_type not in ["total", "online", "offline", "invc"]:
            return await ctx.send("Type must be `total`, `online`, `offline`, or `invc`.")
            
        if "{count}" not in fmt and "{value}" not in fmt:
            return await ctx.send("Format must include `{count}` or `{value}`.")
            
        await asyncio.to_thread(db_client.update_guild_settings, ctx.guild.id, {f"counter_{stat_type}_fmt": fmt})
        await ctx.send(embed=discord.Embed(description=f"[OK] Format for `{stat_type}` updated to `{fmt}`.\nRun `/stats refresh` to apply it immediately.", color=discord.Color.green()))

    @stats.command(name="interval", description="Set how often stats refresh (1-60 mins).")
    async def stats_interval(self, ctx: commands.Context, minutes: int):
        if minutes < 1 or minutes > 60:
            return await ctx.send("Interval must be between 1 and 60 minutes.")
            
        await asyncio.to_thread(db_client.update_guild_settings, ctx.guild.id, {"counter_refresh_interval": minutes})
        self.stats_loop.change_interval(minutes=minutes)
        await ctx.send(embed=discord.Embed(description=f"[OK] Stats will now refresh every {minutes} minutes.", color=discord.Color.green()))


async def setup(bot: commands.Bot):
    await bot.add_cog(StatsCog(bot))
