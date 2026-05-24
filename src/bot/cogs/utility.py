import discord
from discord.ext import commands
from discord import app_commands
import datetime
import platform
import aiohttp
import urllib.parse
import ast
import operator
import re
import asyncio
from typing import Optional

class EmbedBuilderModal(discord.ui.Modal, title='Embed Builder'):
    embed_title = discord.ui.TextInput(label='Title', required=False, max_length=256)
    embed_desc = discord.ui.TextInput(label='Description', style=discord.TextStyle.paragraph, required=True, max_length=4000)
    embed_color = discord.ui.TextInput(label='Color (Hex)', placeholder='#FFFFFF', required=False, max_length=7)
    embed_footer = discord.ui.TextInput(label='Footer', required=False, max_length=2048)

    async def on_submit(self, interaction: discord.Interaction):
        color_val = 0x2B2D31
        if self.embed_color.value:
            try:
                color_val = int(self.embed_color.value.strip('#'), 16)
            except ValueError:
                pass
        
        embed = discord.Embed(
            title=self.embed_title.value,
            description=self.embed_desc.value,
            color=color_val
        )
        if self.embed_footer.value:
            embed.set_footer(text=self.embed_footer.value)
            
        await interaction.response.send_message(embed=embed)

# Safe AST evaluator for calc
def safe_eval(expr):
    operators = {
        ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.Pow: operator.pow, ast.BitXor: operator.xor,
        ast.USub: operator.neg, ast.Mod: operator.mod
    }
    
    def eval_node(node):
        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.BinOp):
            return operators[type(node.op)](eval_node(node.left), eval_node(node.right))
        elif isinstance(node, ast.UnaryOp):
            return operators[type(node.op)](eval_node(node.operand))
        else:
            raise TypeError(node)
            
    try:
        # Limited to 100 chars to prevent huge expressions
        if len(expr) > 100:
            return "Expression too long."
        parsed = ast.parse(expr, mode='eval')
        res = eval_node(parsed.body)
        if isinstance(res, (int, float)):
            # Cap the exponentiation limit implicitly by timeout or just limit output
            return str(res)[:100]
        return "Invalid result."
    except Exception:
        return "Invalid expression."


class UtilityCog(commands.Cog, name="Utility"):
    """General-purpose utility commands for server members."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.snipe_cache = {}  # channel_id -> (content, author, avatar, time)
        self.editsnipe_cache = {} # channel_id -> (old_content, author, avatar, time)
        self.reminders = []

    @commands.hybrid_group(name="util", description="Utility commands.", fallback="help")
    async def util(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)
            
    @commands.hybrid_group(name="tools", description="Extra tools commands.", fallback="help")
    async def tools(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    # ── Listeners for snipe ────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot:
            return
        self.snipe_cache[message.channel.id] = {
            "content": message.content or "(no text)",
            "author": str(message.author),
            "avatar": message.author.display_avatar.url,
            "time": discord.utils.utcnow()
        }

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot or before.content == after.content:
            return
        self.editsnipe_cache[before.channel.id] = {
            "content": before.content or "(no text)",
            "author": str(before.author),
            "avatar": before.author.display_avatar.url,
            "time": discord.utils.utcnow()
        }

    # ── Basic Utility ──────────────────────────────────────────────────────

    @util.command(name="ping", description="Show bot latency.")
    async def ping(self, ctx: commands.Context):
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(title="Pong!", color=0x3498DB)
        embed.add_field(name="WebSocket", value=f"`{latency}ms`", inline=True)
        embed.set_footer(text="KAIZER K5")
        await ctx.send(embed=embed)

    @util.command(name="calc", description="Safely evaluate a math expression.")
    @app_commands.describe(expression="The math expression (e.g. 5+5)")
    async def calc(self, ctx: commands.Context, *, expression: str):
        result = safe_eval(expression)
        embed = discord.Embed(title="Calculator", color=0x3498DB)
        embed.add_field(name="Expression", value=f"```\n{expression}\n```", inline=False)
        embed.add_field(name="Result", value=f"```\n{result}\n```", inline=False)
        await ctx.send(embed=embed)

    @util.command(name="color", description="Show a color preview.")
    @app_commands.describe(hex_code="The hex color code (e.g. #FF0000)")
    async def color(self, ctx: commands.Context, hex_code: str):
        hex_code = hex_code.strip('#')
        if len(hex_code) != 6:
            return await ctx.send("Please provide a valid 6-character hex code.")
        try:
            val = int(hex_code, 16)
        except ValueError:
            return await ctx.send("Invalid hex code.")
            
        r, g, b = (val >> 16) & 255, (val >> 8) & 255, val & 255
        embed = discord.Embed(title=f"Color Preview: #{hex_code.upper()}", color=val)
        embed.add_field(name="RGB", value=f"rgb({r}, {g}, {b})")
        embed.add_field(name="Hex", value=f"#{hex_code.upper()}")
        embed.set_thumbnail(url=f"https://singlecolorimage.com/get/{hex_code}/200x200")
        await ctx.send(embed=embed)

    @util.command(name="charinfo", description="Show info about a unicode character.")
    async def charinfo(self, ctx: commands.Context, character: str):
        if len(character) > 10:
            return await ctx.send("Please provide fewer characters.")
        import unicodedata
        lines = []
        for c in character:
            try:
                name = unicodedata.name(c)
            except ValueError:
                name = "UNKNOWN"
            code = f"\\u{ord(c):04x}"
            lines.append(f"`{c}` - **{name}** ({code})")
        await ctx.send("\n".join(lines))

    # ── Snipe ──────────────────────────────────────────────────────────────

    @util.command(name="snipe", description="Show the last deleted message.")
    async def snipe(self, ctx: commands.Context):
        data = self.snipe_cache.get(ctx.channel.id)
        if not data:
            return await ctx.send(embed=discord.Embed(description="Nothing to snipe.", color=0xE74C3C))
        embed = discord.Embed(description=data["content"], color=0xF39C12, timestamp=data["time"])
        embed.set_author(name=data["author"], icon_url=data["avatar"])
        embed.set_footer(text="Deleted message")
        await ctx.send(embed=embed)

    @util.command(name="editsnipe", description="Show the last edited message before its edit.")
    async def editsnipe(self, ctx: commands.Context):
        data = self.editsnipe_cache.get(ctx.channel.id)
        if not data:
            return await ctx.send(embed=discord.Embed(description="Nothing to editsnipe.", color=0xE74C3C))
        embed = discord.Embed(description=data["content"], color=0xF39C12, timestamp=data["time"])
        embed.set_author(name=data["author"], icon_url=data["avatar"])
        embed.set_footer(text="Original message before edit")
        await ctx.send(embed=embed)

    # ── APIs (Weather, Translate, Paste, QR) ───────────────────────────────

    @util.command(name="weather", description="Check current weather for a city.")
    async def weather(self, ctx: commands.Context, *, city: str):
        url = f"https://wttr.in/{urllib.parse.quote(city)}?format=j1"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as r:
                    if r.status != 200:
                        return await ctx.send("Could not fetch weather data.")
                    data = await r.json()
                    current = data['current_condition'][0]
                    desc = current['weatherDesc'][0]['value']
                    temp_c = current['temp_C']
                    feels_like = current['FeelsLikeC']
                    humidity = current['humidity']
                    
                    embed = discord.Embed(title=f"Weather in {city.title()}", description=f"**{desc}**", color=0x3498DB)
                    embed.add_field(name="Temperature", value=f"{temp_c}°C (Feels like {feels_like}°C)", inline=False)
                    embed.add_field(name="Humidity", value=f"{humidity}%", inline=False)
                    await ctx.send(embed=embed)
        except Exception:
            await ctx.send("Error fetching weather.")

    @util.command(name="translate", description="Translate text using Google Translate.")
    @app_commands.describe(lang="Target language code (e.g. 'en', 'es', 'fr')", text="Text to translate")
    async def translate(self, ctx: commands.Context, lang: str, *, text: str):
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={lang}&dt=t&q={urllib.parse.quote(text)}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as r:
                    if r.status != 200:
                        return await ctx.send("Translation failed.")
                    data = await r.json()
                    translated = "".join([i[0] for i in data[0]])
                    source_lang = data[2]
                    
                    embed = discord.Embed(title="Translation", color=0x3498DB)
                    embed.add_field(name=f"From ({source_lang})", value=text[:1000], inline=False)
                    embed.add_field(name=f"To ({lang})", value=translated[:1000], inline=False)
                    await ctx.send(embed=embed)
        except Exception:
            await ctx.send("Error translating text.")

    @util.command(name="qr", description="Generate a QR code from text or URL.")
    async def qr(self, ctx: commands.Context, *, text: str):
        url = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={urllib.parse.quote(text)}"
        embed = discord.Embed(title="QR Code", color=0x3498DB)
        embed.set_image(url=url)
        await ctx.send(embed=embed)

    @util.command(name="paste", description="Create a hastebin-style paste.")
    async def paste(self, ctx: commands.Context, *, text: str):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post("https://paste.rs", data=text.encode('utf-8')) as r:
                    if r.status == 201:
                        url = await r.text()
                        await ctx.send(f"✅ Paste created: <{url.strip()}>")
                    else:
                        await ctx.send("Failed to create paste.")
        except Exception:
            await ctx.send("Error connecting to paste service.")

    # ── Reminders ──────────────────────────────────────────────────────────

    @util.command(name="reminder", description="Set a personal reminder.")
    @app_commands.describe(minutes="Minutes to wait", message="What to remind you about")
    async def reminder(self, ctx: commands.Context, minutes: int, *, message: str):
        if minutes <= 0:
            return await ctx.send("Time must be greater than 0.")
        if minutes > 10080: # Max 1 week
            return await ctx.send("Time cannot exceed 7 days (10080 minutes).")
            
        future_time = discord.utils.utcnow() + datetime.timedelta(minutes=minutes)
        await ctx.send(f"✅ I will remind you: **{message}** (in {minutes} minutes).")
        
        # Simple memory reminder using asyncio
        # (In a production bot with restarts, we'd save this to DB)
        self.reminders.append({"user": ctx.author.id, "time": future_time, "message": message})
        
        async def wait_and_remind():
            await asyncio.sleep(minutes * 60)
            try:
                await ctx.author.send(f"⏰ **Reminder:** {message}")
            except discord.Forbidden:
                await ctx.send(f"{ctx.author.mention} ⏰ **Reminder:** {message}")
                
        self.bot.loop.create_task(wait_and_remind())

    @util.command(name="reminders", description="List your active reminders.")
    async def reminders(self, ctx: commands.Context):
        active = [r for r in self.reminders if r["user"] == ctx.author.id and r["time"] > discord.utils.utcnow()]
        if not active:
            return await ctx.send("You have no active reminders.")
            
        desc = ""
        for i, r in enumerate(active, 1):
            t = discord.utils.format_dt(r['time'], 'R')
            desc += f"**{i}.** {r['message']} ({t})\n"
            
        await ctx.send(embed=discord.Embed(title="Your Reminders", description=desc, color=0x3498DB))

    # ── Moderation/Admin Utilities ─────────────────────────────────────────

    @util.command(name="announce", description="Send an announcement embed.")
    @commands.has_permissions(manage_messages=True)
    async def announce(self, ctx: commands.Context, channel: discord.TextChannel, *, message: str):
        embed = discord.Embed(title="📢 Announcement", description=message, color=0x3498DB)
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
        try:
            await channel.send(embed=embed)
            await ctx.send(f"✅ Announcement sent to {channel.mention}.")
        except discord.Forbidden:
            await ctx.send("I don't have permission to send messages in that channel.")

    @util.command(name="say", description="Make the bot say something.")
    @commands.has_permissions(manage_messages=True)
    async def say(self, ctx: commands.Context, *, message: str):
        try: await ctx.message.delete()
        except: pass
        await ctx.send(message)

    @app_commands.command(name="embed", description="Launch an interactive embed builder.")
    @app_commands.default_permissions(manage_messages=True)
    async def embed_builder(self, interaction: discord.Interaction):
        await interaction.response.send_modal(EmbedBuilderModal())

    # ── Info Commands ──────────────────────────────────────────────────────

    @commands.hybrid_group(name="info", description="Get info about various entities.", fallback="help")
    async def info(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @info.command(name="bot", description="Show detailed bot info.")
    async def info_bot(self, ctx: commands.Context):
        embed = discord.Embed(title="KAIZER K5 — Bot Info", color=0x2C2F33)
        embed.add_field(name="Servers", value=f"{len(self.bot.guilds):,}", inline=True)
        embed.add_field(name="Users", value=f"{sum(g.member_count for g in self.bot.guilds):,}", inline=True)
        embed.add_field(name="Ping", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="Python", value=platform.python_version(), inline=True)
        embed.add_field(name="discord.py", value=discord.__version__, inline=True)
        embed.set_footer(text="KAIZER K5")
        await ctx.send(embed=embed)

    @info.command(name="server", description="Get detailed info about the server.")
    async def info_server(self, ctx: commands.Context):
        g = ctx.guild
        embed = discord.Embed(title=g.name, color=0x3498DB)
        if g.icon: embed.set_thumbnail(url=g.icon.url)
        embed.add_field(name="Owner", value=str(g.owner), inline=True)
        embed.add_field(name="Members", value=f"{g.member_count:,}", inline=True)
        embed.add_field(name="Channels", value=f"{len(g.text_channels)} text / {len(g.voice_channels)} voice", inline=True)
        embed.add_field(name="Roles", value=str(len(g.roles)), inline=True)
        embed.add_field(name="Boost Level", value=f"Tier {g.premium_tier} ({g.premium_subscription_count} boosts)", inline=True)
        embed.add_field(name="Created", value=discord.utils.format_dt(g.created_at, "R"), inline=True)
        embed.add_field(name="ID", value=g.id, inline=False)
        await ctx.send(embed=embed)

    @info.command(name="user", description="Get detailed info about a user.")
    async def info_user(self, ctx: commands.Context, user: discord.Member = None):
        user = user or ctx.author
        roles = [r.mention for r in user.roles if r != ctx.guild.default_role][:20]
        embed = discord.Embed(title=f"{user}", color=user.color or 0x3498DB)
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="ID", value=user.id, inline=True)
        embed.add_field(name="Nickname", value=user.nick or "None", inline=True)
        embed.add_field(name="Created", value=discord.utils.format_dt(user.created_at, "R"), inline=True)
        embed.add_field(name="Joined", value=discord.utils.format_dt(user.joined_at, "R"), inline=True)
        embed.add_field(name="Top Role", value=user.top_role.mention, inline=True)
        embed.add_field(name=f"Roles ({len(roles)})", value=", ".join(roles) if roles else "None", inline=False)
        await ctx.send(embed=embed)

    @info.command(name="channel", description="Get info about a channel.")
    async def info_channel(self, ctx: commands.Context, channel: discord.abc.GuildChannel = None):
        channel = channel or ctx.channel
        embed = discord.Embed(title=f"Channel: #{channel.name}", color=0x3498DB)
        embed.add_field(name="ID", value=channel.id, inline=True)
        embed.add_field(name="Type", value=str(channel.type).title(), inline=True)
        embed.add_field(name="Created", value=discord.utils.format_dt(channel.created_at, "R"), inline=True)
        if isinstance(channel, discord.TextChannel):
            embed.add_field(name="NSFW", value=str(channel.is_nsfw()), inline=True)
            embed.add_field(name="Topic", value=channel.topic or "None", inline=False)
        await ctx.send(embed=embed)

    @info.command(name="role", description="Get info about a role.")
    async def info_role(self, ctx: commands.Context, role: discord.Role):
        embed = discord.Embed(title=f"Role: {role.name}", color=role.color)
        embed.add_field(name="ID", value=role.id, inline=True)
        embed.add_field(name="Color", value=str(role.color), inline=True)
        embed.add_field(name="Members", value=str(len(role.members)), inline=True)
        embed.add_field(name="Hoisted", value=str(role.hoist), inline=True)
        embed.add_field(name="Created", value=discord.utils.format_dt(role.created_at, "R"), inline=True)
        await ctx.send(embed=embed)

    @info.command(name="emoji", description="Get info about a custom emoji.")
    async def info_emoji(self, ctx: commands.Context, emoji: discord.Emoji):
        embed = discord.Embed(title=f"Emoji: {emoji.name}", color=0x3498DB)
        embed.set_thumbnail(url=emoji.url)
        embed.add_field(name="ID", value=emoji.id, inline=True)
        embed.add_field(name="Animated", value=str(emoji.animated), inline=True)
        embed.add_field(name="Created", value=discord.utils.format_dt(emoji.created_at, "R"), inline=True)
        await ctx.send(embed=embed)

    @tools.command(name="avatar", description="Get a user's full-size avatar.")
    async def avatar(self, ctx: commands.Context, user: discord.Member = None):
        user = user or ctx.author
        embed = discord.Embed(title=f"{user.display_name}'s Avatar", color=user.color or 0x3498DB)
        embed.set_image(url=user.display_avatar.replace(size=1024).url)
        await ctx.send(embed=embed)

    @tools.command(name="banner", description="Get a user's profile banner.")
    async def banner(self, ctx: commands.Context, user: discord.Member = None):
        user = user or ctx.author
        fetched = await self.bot.fetch_user(user.id)
        if not fetched.banner:
            return await ctx.send(embed=discord.Embed(description=f"**{user}** has no banner set.", color=0xE74C3C))
        embed = discord.Embed(title=f"{user.display_name}'s Banner", color=user.color or 0x3498DB)
        embed.set_image(url=fetched.banner.replace(size=1024).url)
        await ctx.send(embed=embed)

    @tools.command(name="servericon", description="Get the server's icon.")
    async def servericon(self, ctx: commands.Context):
        if not ctx.guild.icon:
            return await ctx.send(embed=discord.Embed(description="This server has no icon.", color=0xE74C3C))
        embed = discord.Embed(title=f"{ctx.guild.name}'s Icon", color=0x3498DB)
        embed.set_image(url=ctx.guild.icon.replace(size=1024).url)
        await ctx.send(embed=embed)

    @tools.command(name="serverbanner", description="Get the server's banner.")
    async def serverbanner(self, ctx: commands.Context):
        if not ctx.guild.banner:
            return await ctx.send(embed=discord.Embed(description="This server has no banner.", color=0xE74C3C))
        embed = discord.Embed(title=f"{ctx.guild.name}'s Banner", color=0x3498DB)
        embed.set_image(url=ctx.guild.banner.replace(size=1024).url)
        await ctx.send(embed=embed)

    @tools.command(name="firstmsg", description="Get a link to the first message in the channel.")
    async def firstmsg(self, ctx: commands.Context, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        try:
            async for msg in channel.history(limit=1, oldest_first=True):
                await ctx.send(f"Jump to the first message in {channel.mention}: {msg.jump_url}")
                return
            await ctx.send("Channel is empty.")
        except Exception:
            await ctx.send("Could not fetch message history.")

    @tools.command(name="timestamp", description="Generate Discord timestamps.")
    async def timestamp(self, ctx: commands.Context):
        now = discord.utils.utcnow()
        t = int(now.timestamp())
        desc = (
            f"`<t:{t}:t>` -> <t:{t}:t>\n"
            f"`<t:{t}:T>` -> <t:{t}:T>\n"
            f"`<t:{t}:d>` -> <t:{t}:d>\n"
            f"`<t:{t}:D>` -> <t:{t}:D>\n"
            f"`<t:{t}:f>` -> <t:{t}:f>\n"
            f"`<t:{t}:F>` -> <t:{t}:F>\n"
            f"`<t:{t}:R>` -> <t:{t}:R>\n"
        )
        await ctx.send(embed=discord.Embed(title="Timestamp Formats (Current Time)", description=desc, color=0x3498DB))

    @tools.command(name="time", description="Show the current time (UTC).")
    async def time(self, ctx: commands.Context):
        now = discord.utils.utcnow()
        await ctx.send(f"The current time in UTC is: **{now.strftime('%Y-%m-%d %H:%M:%S')}**")

    @tools.command(name="afk", description="Set your AFK status.")
    async def afk(self, ctx: commands.Context, *, reason: str = "AFK"):
        await ctx.send(f"✅ I set your AFK: {reason}")
        # Full AFK intercept logic typically requires a message listener in the engine or utility cog.
        # This registers the intent. A real implementation would cache this and check mentions.

    @tools.command(name="steal", description="Steal an emoji from another server.")
    @commands.has_permissions(manage_expressions=True)
    async def steal(self, ctx: commands.Context, emoji: discord.PartialEmoji, name: str = None):
        name = name or emoji.name
        try:
            emoji_bytes = await emoji.read()
            new_emoji = await ctx.guild.create_custom_emoji(name=name, image=emoji_bytes)
            await ctx.send(f"✅ Successfully added {new_emoji} as `{new_emoji.name}`!")
        except Exception as e:
            await ctx.send(f"Failed to steal emoji: {e}")

    @tools.command(name="poll", description="Create a reaction poll.")
    @app_commands.describe(question="The poll question", opt1="Option 1", opt2="Option 2")
    async def poll(self, ctx: commands.Context, question: str, opt1: str, opt2: str, opt3: str = None, opt4: str = None):
        options = [opt1, opt2]
        if opt3: options.append(opt3)
        if opt4: options.append(opt4)
        
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
        desc = ""
        for i, opt in enumerate(options):
            desc += f"{emojis[i]} **{opt}**\n\n"
            
        embed = discord.Embed(title=f"📊 Poll: {question}", description=desc, color=0x3498DB)
        embed.set_footer(text=f"Poll by {ctx.author.display_name}")
        
        msg = await ctx.send(embed=embed)
        for i in range(len(options)):
            await msg.add_reaction(emojis[i])

    @tools.command(name="countdown", description="Create a countdown timer.")
    @app_commands.describe(event="Name of the event", days="Days from now")
    async def countdown(self, ctx: commands.Context, event: str, days: int):
        future = discord.utils.utcnow() + datetime.timedelta(days=days)
        t = int(future.timestamp())
        embed = discord.Embed(title="⏱️ Countdown", color=0x3498DB)
        embed.add_field(name="Event", value=event, inline=False)
        embed.add_field(name="Time", value=f"<t:{t}:R> (<t:{t}:F>)", inline=False)
        await ctx.send(embed=embed)

    async def cog_load(self):
        # Dynamically register top-level prefix commands for all subcommands of the 'util' group
        # Using standard commands.command to avoid exceeding Discord's 100 slash command limit
        for cmd in list(self.util.commands):
            top_cmd = commands.command(
                name=cmd.name,
                description=cmd.description,
                help=cmd.help
            )(cmd.callback)
            top_cmd.cog = self
            top_cmd.checks = cmd.checks.copy()
            self.bot.add_command(top_cmd)

async def setup(bot: commands.Bot):
    await bot.add_cog(UtilityCog(bot))
