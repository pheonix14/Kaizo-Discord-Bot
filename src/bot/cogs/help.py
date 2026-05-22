import discord
from discord.ext import commands
from discord import app_commands
import psutil
import platform
import time

class HelpCog(commands.Cog, name="Help"):
    """Help, bot info, and documentation commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_time = time.time()
        
    # ── Help System ──────────────────────────────────────────────────────────
    
    @commands.hybrid_command(name="help", description="View the main help menu or info about a specific command.")
    @app_commands.describe(command="Specific command or category to get help for")
    async def help_cmd(self, ctx: commands.Context, command: str = None):
        if command:
            # Try to find command
            cmd = self.bot.get_command(command)
            if cmd:
                embed = discord.Embed(title=f"Command: {cmd.name}", description=cmd.help or cmd.description or "No description provided.", color=0x3498DB)
                usage = f"{ctx.prefix}{cmd.qualified_name} {cmd.signature}"
                embed.add_field(name="Usage", value=f"`{usage}`", inline=False)
                if cmd.aliases:
                    embed.add_field(name="Aliases", value=", ".join(cmd.aliases), inline=False)
                return await ctx.send(embed=embed)
                
            # Try to find cog/category
            cog = self.bot.get_cog(command.title())
            if cog:
                embed = discord.Embed(title=f"Category: {cog.qualified_name}", description=cog.description, color=0x3498DB)
                cmds = cog.get_commands()
                if cmds:
                    cmd_list = ", ".join(f"`{c.name}`" for c in cmds if not c.hidden)
                    embed.add_field(name="Commands", value=cmd_list or "None", inline=False)
                return await ctx.send(embed=embed)
                
            return await ctx.send("Command or category not found.")
            
        # Main help menu
        embed = discord.Embed(title="KAIZER K5 — Help Menu", description=f"Use `{ctx.prefix}help <command>` for more details.", color=0x3498DB)
        
        for cog_name, cog in self.bot.cogs.items():
            if cog_name.lower() in ["developer", "jishaku"]: # Hide dev cogs
                continue
            cmds = cog.get_commands()
            if not cmds:
                continue
            # Filter hidden
            visible = [c for c in cmds if not c.hidden]
            if not visible:
                continue
                
            embed.add_field(name=f"{cog_name} ({len(visible)})", value=cog.description or "No description.", inline=True)
            
        embed.set_footer(text="KAIZER K5 Bot")
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="commands", aliases=["cmds"], description="List all available commands.")
    async def commands_list(self, ctx: commands.Context):
        total = 0
        desc = ""
        for cog_name, cog in self.bot.cogs.items():
            if cog_name.lower() in ["developer"]:
                continue
            visible = [c for c in cog.get_commands() if not c.hidden]
            if visible:
                desc += f"**{cog_name}**: " + ", ".join(f"`{c.name}`" for c in visible) + "\n\n"
                total += len(visible)
                
        embed = discord.Embed(title=f"All Commands ({total})", description=desc, color=0x3498DB)
        await ctx.send(embed=embed)


    # ── Bot Stats & Info ─────────────────────────────────────────────────────

    @commands.hybrid_command(name="about", description="View about information for KAIZER K5.")
    async def about(self, ctx: commands.Context):
        embed = discord.Embed(
            title="About KAIZER K5", 
            description="A premium, highly-customizable multipurpose Discord bot built with Python.",
            color=0x2C2F33
        )
        embed.add_field(name="Developer", value="The KAIZER Team", inline=True)
        embed.add_field(name="Library", value=f"discord.py v{discord.__version__}", inline=True)
        embed.add_field(name="Servers", value=f"{len(self.bot.guilds):,}", inline=True)
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Invite Me", url="https://discord.com/api/oauth2/authorize?client_id=1234567890&permissions=8&scope=bot%20applications.commands"))
        view.add_item(discord.ui.Button(label="Support Server", url="https://discord.gg/kaizer"))
        view.add_item(discord.ui.Button(label="Dashboard", url="http://127.0.0.1:8000"))
        
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name="botinfo", description="Detailed bot statistics.")
    async def botinfo(self, ctx: commands.Context):
        mem = psutil.virtual_memory()
        cpu = psutil.cpu_percent()
        
        uptime_seconds = int(time.time() - self.start_time)
        m, s = divmod(uptime_seconds, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        uptime_str = f"{d}d {h}h {m}m"
        
        embed = discord.Embed(title="Bot Statistics", color=0x3498DB)
        embed.add_field(name="Bot Uptime", value=uptime_str, inline=True)
        embed.add_field(name="Ping", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="Servers", value=f"{len(self.bot.guilds):,}", inline=True)
        embed.add_field(name="Users", value=f"{sum(g.member_count for g in self.bot.guilds):,}", inline=True)
        embed.add_field(name="RAM Usage", value=f"{mem.percent}% ({mem.used // 1048576}MB)", inline=True)
        embed.add_field(name="CPU Usage", value=f"{cpu}%", inline=True)
        embed.add_field(name="Python", value=platform.python_version(), inline=True)
        embed.add_field(name="discord.py", value=discord.__version__, inline=True)
        embed.add_field(name="OS", value=platform.system(), inline=True)
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="status", description="Check the system status of the bot.")
    async def status(self, ctx: commands.Context):
        # Alias for botinfo but focused purely on performance
        await self.botinfo(ctx)

    # ── Links & Docs ─────────────────────────────────────────────────────────

    @commands.hybrid_command(name="invite", description="Get the invite link for KAIZER K5.")
    async def invite(self, ctx: commands.Context):
        embed = discord.Embed(title="Invite KAIZER K5", description="Click the button below to invite me to your server!", color=0x3498DB)
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Invite Link", url="https://discord.com/api/oauth2/authorize?client_id=1234567890&permissions=8&scope=bot%20applications.commands"))
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name="support", description="Get the support server link.")
    async def support(self, ctx: commands.Context):
        embed = discord.Embed(title="Support Server", description="Need help? Join our official support server!", color=0x3498DB)
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Join Support", url="https://discord.gg/kaizer"))
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name="vote", description="Vote for the bot.")
    async def vote(self, ctx: commands.Context):
        embed = discord.Embed(title="Vote for KAIZER K5", description="Support the bot by voting on Top.gg!", color=0x3498DB)
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Vote on Top.gg", url="https://top.gg/bot/1234567890/vote"))
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name="changelog", description="View recent updates to the bot.")
    async def changelog(self, ctx: commands.Context):
        log = (
            "**v1.5.0 - The Fun Update**\n"
            "- Added Hangman, Wordle, Trivia, TicTacToe\n"
            "- Added new Economy minigames (Slots, Blackjack)\n"
            "- Overhauled the Help Menu\n\n"
            "**v1.4.0 - Utility & Dashboard**\n"
            "- Added massive utility suite (weather, translate)\n"
            "- Fixed dashboard side menu UI issues\n\n"
            "**v1.3.0 - Security**\n"
            "- Added Anti-Nuke and Auto-Mod modules\n"
        )
        embed = discord.Embed(title="Changelog", description=log, color=0x3498DB)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="credits", description="View bot credits.")
    async def credits(self, ctx: commands.Context):
        desc = (
            "**Developers**: The KAIZER Team\n"
            "**Libraries**: `discord.py`, `Flask`, `Supabase`, `aiohttp`, `psutil`, `pyfiglet`\n"
            "**APIs used**: JokeAPI, UselessFacts, Meme-API, Quotable, wttr.in, OpenTDB\n"
        )
        embed = discord.Embed(title="Credits", description=desc, color=0x3498DB)
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))
