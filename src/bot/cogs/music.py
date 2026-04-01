import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio
import math
import os
import uuid
import re

def clean_error_message(error):
    # Remove ANSI escape sequences
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    cleaned = ansi_escape.sub('', str(error))
    # Strip standard yt-dlp error prefixes
    cleaned = re.sub(r'^(?i)(?:youtube:\s*|ytdl:\s*|error:\s*|[a-z0-9_-]+:\s*)+', '', cleaned)
    return cleaned.strip()

# --- YTDL Config ---
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'noprogress': True,
    'referer': 'https://www.youtube.com/',
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration', 0)
        self.requester = data.get('requester')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False, requester=None, filters=None):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        
        ff_opts = ffmpeg_options.copy()
        if filters:
            ff_opts['options'] += f' -af "{filters}"'

        source = discord.FFmpegPCMAudio(filename, **ff_opts)
        data['requester'] = requester
        return cls(source, data=data)

class MusicDownloadView(discord.ui.View):
    def __init__(self, ctx, cog, entries):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.cog = cog
        self.entries = entries
        for i, entry in enumerate(entries):
            btn = discord.ui.Button(label=f"Track {i+1}", style=discord.ButtonStyle.primary, custom_id=f"dl_{i}")
            btn.callback = self.make_callback(entry)
            self.add_item(btn)

    def make_callback(self, entry):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.ctx.author.id:
                return await interaction.response.send_message("Only the requester can select a track.", ephemeral=True)
            
            await interaction.response.edit_message(content=f"Downloading **{entry.get('title')}**... Please wait.", embed=None, view=None)
            
            filename = f"{uuid.uuid4().hex}"
            
            player = self.cog.get_player(self.ctx.guild.id)
            preferred_quality = getattr(player, "quality", "192")
            
            dl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f"{filename}.%(ext)s",
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': preferred_quality,
                }],
                'quiet': True,
                'no_warnings': True
            }
            
            try:
                def run_dl():
                    with yt_dlp.YoutubeDL(dl_opts) as ydl:
                        ydl.download([entry['webpage_url']])
                        
                await self.ctx.bot.loop.run_in_executor(None, run_dl)
                
                final_file = f"{filename}.mp3"
                if os.path.exists(final_file):
                    file_size = os.path.getsize(final_file)
                    if file_size > 25 * 1024 * 1024: # 25MB limit
                        await interaction.message.edit(content="The audio file exceeds Discord's 25MB limit.")
                    else:
                        await interaction.message.edit(content=f"Downloaded **{entry.get('title')}**", attachments=[discord.File(final_file)])
                    os.remove(final_file)
                else:
                    await interaction.message.edit(content="Failed to generate mp3 file.")
            except Exception as e:
                await interaction.message.edit(content=f"Error during download: {clean_error_message(e)}")
        return callback

class ServerMusicPlayer:
    def __init__(self, bot, guild_id):
        self.bot = bot
        self.guild_id = guild_id
        self.queue = []
        self.current = None
        self.volume = 1.0
        self.filters = {}
        self.loop_mode = "off"
        self.quality = "192"
        self.is_playing = asyncio.Event()

    def get_filter_string(self):
        active = []
        if self.filters.get('8d'): active.append('apulsator=hz=0.08')
        if self.filters.get('bassboost'): active.append(f"bass=g={self.filters['bassboost']}")
        if self.filters.get('chipmunk'): active.append('asetrate=48000*1.5,aresample=48000,atempo=1/1.5')
        if self.filters.get('echo'): active.append('aecho=0.8:0.9:1000:0.3')
        if self.filters.get('karaoke'): active.append('stereotools=mlev=0.015625')
        if self.filters.get('nightcore'): active.append('asetrate=48000*1.25,aresample=48000,atempo=1/1.25')
        if self.filters.get('slowed'): active.append('asetrate=48000*0.8,aresample=48000,atempo=1/0.8')
        if self.filters.get('speed'): active.append(f"atempo={self.filters['speed']}")
        if self.filters.get('tremolo'): active.append('tremolo=f=5.0:d=0.5')
        if self.filters.get('vaporwave'): active.append('asetrate=48000*0.75,aresample=48000,atempo=1/0.75')
        if self.filters.get('vibrato'): active.append('vibrato=f=6.5:d=0.5')
        return ",".join(active) if active else None


class MusicHelpView(discord.ui.View):
    def __init__(self, author_id: int):
        super().__init__(timeout=60.0)
        self.author_id = author_id
        self.current_page = 0
        
        self.pages = [
            # Page 1
            {
                "title": "[MUSIC] Kaizo - Music Playback (Page 1/2)",
                "description": "Control audio playback in your voice channels.",
                "fields": [
                    {"name": "• join", "value": "Make the bot join your current voice channel.\n*Usage:* `.music join` or `/music join`"},
                    {"name": "• leave", "value": "Disconnect the bot from VC and clear the queue.\n*Usage:* `.music leave` or `/music leave`"},
                    {"name": "• play <query>", "value": "Play a track from YouTube (searches or direct URL).\n*Usage:* `.music play chill beats`"},
                    {"name": "• pause / resume", "value": "Pause or resume the current playing track.\n*Usage:* `.music pause`, `.music resume`"},
                    {"name": "• stop", "value": "Stop playback and clear the guild queue.\n*Usage:* `.music stop`"},
                    {"name": "• skip", "value": "Skip the currently playing song.\n*Usage:* `.music skip`"},
                    {"name": "• nowplaying", "value": "Display details about the currently playing song.\n*Aliases:* `np`"},
                    {"name": "• queue", "value": "List the upcoming tracks in the queue."},
                    {"name": "• volume <level>", "value": "Adjust the bot playback volume (1-200).\n*Usage:* `.music volume 80`"},
                    {"name": "• loop <off/song/queue>", "value": "Set loop mode for the current song or entire queue.\n*Usage:* `.music loop song`"}
                ]
            },
            # Page 2
            {
                "title": "[SETTINGS] Kaizo - Audio Filters & Download (Page 2/2)",
                "description": "Apply advanced DSP filters and download songs directly.",
                "fields": [
                    {"name": "• 8d <state>", "value": "Toggle the 8D audio rotation filter.\n*Usage:* `.music 8d true`"},
                    {"name": "• bassboost [level]", "value": "Apply bass boost filter (level 1-30, or 0 to disable).\n*Usage:* `.music bassboost 15`"},
                    {"name": "• nightcore <state> / vaporwave <state>", "value": "Apply speed/pitch-shifting filters.\n*Usage:* `.music nightcore true`"},
                    {"name": "• filter_off", "value": "Clear all active audio filters."},
                    {"name": "• playlist_save <name> / playlist_load <name>", "value": "Save your current queue or load a saved playlist.\n*Usage:* `.music playlist_save mylist`"},
                    {"name": "• playlist_list", "value": "List all your saved music playlists."},
                    {"name": "• download <query>", "value": "Search and download any YouTube song directly to Discord as an MP3.\n*Usage:* `.music download lofi hiphop`"},
                    {"name": "• quality <kbps>", "value": "Set session download audio quality (e.g. 192, 320)."},
                    {"name": "• search <query>", "value": "Search YouTube for top 5 results and choose which one to play."}
                ]
            }
        ]

    def make_embed(self) -> discord.Embed:
        page_data = self.pages[self.current_page]
        embed = discord.Embed(
            title=page_data["title"],
            description=page_data["description"],
            color=0x3498DB
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


class MusicCog(commands.Cog, name="Music"):
    """Music playback and advanced audio filters."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.players = {}

    def get_player(self, guild_id):
        if guild_id not in self.players:
            self.players[guild_id] = ServerMusicPlayer(self.bot, guild_id)
        return self.players[guild_id]

    async def play_next(self, ctx):
        player = self.get_player(ctx.guild.id)
        
        if player.loop_mode == "song" and player.current:
            # Replay the same song
            song = player.current['data']
        elif len(player.queue) > 0:
            song = player.queue.pop(0)
            if player.loop_mode == "queue":
                player.queue.append(song)
        else:
            player.current = None
            return await ctx.send("Queue finished.")

        player.current = song
        
        try:
            filters = player.get_filter_string()
            source = await YTDLSource.from_url(song['url'], loop=self.bot.loop, stream=True, requester=song['requester'], filters=filters)
            source.volume = player.volume
            
            ctx.voice_client.play(source, after=lambda e: self.bot.loop.create_task(self.play_next(ctx)))
            await ctx.send(embed=discord.Embed(description=f"Now Playing: **{source.title}**\nRequested by: {source.requester.mention}", color=0x3498DB))
        except Exception as e:
            await ctx.send(f"Error playing track: {clean_error_message(e)}")
            await self.play_next(ctx)

    # ── Group ────────────────────────────────────────────────────────────────
    
    @commands.hybrid_group(name="music", description="Music commands.", fallback="help")
    async def music(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            view = MusicHelpView(ctx.author.id)
            msg = await ctx.send(embed=view.make_embed(), view=view)
            view.message = msg

    # ── Core Controls ────────────────────────────────────────────────────────

    @music.command(name="join", description="Join your voice channel.")
    async def join(self, ctx: commands.Context):
        if not ctx.author.voice:
            return await ctx.send("You are not connected to a voice channel.")
        channel = ctx.author.voice.channel
        
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)
        
        await channel.connect()
        await ctx.send(embed=discord.Embed(description=f"Joined {channel.mention}", color=discord.Color.green()))

    @music.command(name="leave", description="Leave the voice channel.")
    async def leave(self, ctx: commands.Context):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            player = self.get_player(ctx.guild.id)
            player.queue.clear()
            player.current = None
            await ctx.send(embed=discord.Embed(description="Disconnected.", color=discord.Color.green()))
        else:
            await ctx.send("I am not in a voice channel.")

    @music.command(name="play", description="Play a song from YouTube.")
    @app_commands.describe(query="Song name or URL")
    async def play(self, ctx: commands.Context, *, query: str):
        if not ctx.voice_client:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                return await ctx.send("You need to be in a voice channel to play music.")
                
        msg = await ctx.send(embed=discord.Embed(description=f"Searching for `{query}`...", color=0x3498DB))
        
        try:
            is_url = query.startswith("http://") or query.startswith("https://")
            search_query = query if is_url else f"ytsearch:{query}"
            
            loop = self.bot.loop or asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(search_query, download=False))
            if 'entries' in data:
                if not data['entries']:
                    return await msg.edit(content="No results found.", embed=None)
                data = data['entries'][0]
                
            song = {
                'url': data['webpage_url'],
                'title': data['title'],
                'requester': ctx.author,
                'data': data
            }
            
            player = self.get_player(ctx.guild.id)
            player.queue.append(song)
            
            await msg.edit(embed=discord.Embed(description=f"Added **{song['title']}** to the queue!", color=discord.Color.green()))
            
            if not ctx.voice_client.is_playing():
                await self.play_next(ctx)
                
        except Exception as e:
            await msg.edit(content=f"Error finding track: {clean_error_message(e)}", embed=None)

    @music.command(name="skip", description="Skip the currently playing song.")
    async def skip(self, ctx: commands.Context):
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            return await ctx.send("Nothing is playing right now.")
        
        ctx.voice_client.stop()
        await ctx.send(embed=discord.Embed(description="Skipped.", color=discord.Color.green()))

    @music.command(name="stop", description="Stop music and clear the queue.")
    async def stop(self, ctx: commands.Context):
        if ctx.voice_client:
            player = self.get_player(ctx.guild.id)
            player.queue.clear()
            ctx.voice_client.stop()
            await ctx.send(embed=discord.Embed(description="Stopped the music and cleared the queue.", color=discord.Color.red()))

    @music.command(name="pause", description="Pause the current song.")
    async def pause(self, ctx: commands.Context):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send(embed=discord.Embed(description="Paused the music.", color=discord.Color.orange()))

    @music.command(name="resume", description="Resume the paused song.")
    async def resume(self, ctx: commands.Context):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send(embed=discord.Embed(description="Resumed the music.", color=discord.Color.green()))

    @music.command(name="queue", description="Show the current music queue.")
    async def queue(self, ctx: commands.Context):
        player = self.get_player(ctx.guild.id)
        if not player.queue and not player.current:
            return await ctx.send("The queue is empty.")
            
        desc = ""
        if player.current:
            desc += f"**Currently Playing:**\n{player.current['title']} - {player.current['requester'].mention}\n\n"
            
        if player.queue:
            desc += "**Up Next:**\n"
            for i, song in enumerate(player.queue[:10]):
                desc += f"{i+1}. {song['title']} - {song['requester'].mention}\n"
                
            if len(player.queue) > 10:
                desc += f"\n*...and {len(player.queue) - 10} more*"
                
        await ctx.send(embed=discord.Embed(title="Music Queue", description=desc, color=0x3498DB))

    @music.command(name="nowplaying", aliases=["np"], description="Show the currently playing song.")
    async def np(self, ctx: commands.Context):
        player = self.get_player(ctx.guild.id)
        if not player.current:
            return await ctx.send("Nothing is playing right now.")
            
        embed = discord.Embed(title="Now Playing", description=f"**{player.current['title']}**", color=0x3498DB)
        embed.set_footer(text=f"Requested by {player.current['requester'].display_name}")
        await ctx.send(embed=embed)

    @music.command(name="volume", description="Set the bot's volume.")
    @app_commands.describe(level="Volume level (1-100)")
    async def volume(self, ctx: commands.Context, level: int):
        if level < 1 or level > 200:
            return await ctx.send("Volume must be between 1 and 200.")
            
        player = self.get_player(ctx.guild.id)
        player.volume = level / 100.0
        if ctx.voice_client and ctx.voice_client.source:
            ctx.voice_client.source.volume = player.volume
            
        await ctx.send(embed=discord.Embed(description=f"Volume set to **{level}%**.", color=discord.Color.blue()))

    @music.command(name="loop", description="Toggle loop for current song or queue.")
    @app_commands.choices(mode=[
        app_commands.Choice(name="Off", value="off"),
        app_commands.Choice(name="Song", value="song"),
        app_commands.Choice(name="Queue", value="queue"),
    ])
    async def loop(self, ctx: commands.Context, mode: str):
        player = self.get_player(ctx.guild.id)
        player.loop_mode = mode
        await ctx.send(embed=discord.Embed(description=f"Loop mode set to: **{mode}**", color=0x3498DB))

    # ── Filters ──────────────────────────────────────────────────────────────
    
    async def apply_filter(self, ctx, filter_name: str, value=True):
        player = self.get_player(ctx.guild.id)
        player.filters[filter_name] = value
        await ctx.send(embed=discord.Embed(description=f"Filter `{filter_name}` set. (Will apply to the next track).", color=0x9B59B6))

    @music.command(name="8d", description="Toggle 8D audio filter.")
    async def filter_8d(self, ctx: commands.Context, state: bool):
        await self.apply_filter(ctx, '8d', state)

    @music.command(name="bassboost", description="Set bass boost level.")
    async def filter_bass(self, ctx: commands.Context, level: int = 15):
        await self.apply_filter(ctx, 'bassboost', level if level > 0 else False)

    @music.command(name="nightcore", description="Toggle Nightcore filter.")
    async def filter_nightcore(self, ctx: commands.Context, state: bool):
        await self.apply_filter(ctx, 'nightcore', state)

    @music.command(name="vaporwave", description="Toggle Vaporwave filter.")
    async def filter_vaporwave(self, ctx: commands.Context, state: bool):
        await self.apply_filter(ctx, 'vaporwave', state)

    @music.command(name="filter_off", description="Turn off all filters.")
    async def filter_off(self, ctx: commands.Context):
        player = self.get_player(ctx.guild.id)
        player.filters.clear()
        await ctx.send(embed=discord.Embed(description="All filters cleared. (Will apply to the next track).", color=discord.Color.green()))

    # ── Playlists ────────────────────────────────────────────────────────────

    @music.command(name="playlist_save", description="Save your current queue as a playlist.")
    async def playlist_save(self, ctx: commands.Context, name: str):
        player = self.get_player(ctx.guild.id)
        if not player.queue and not player.current:
            return await ctx.send("Your queue is empty.")
            
        tracks = []
        if player.current: tracks.append(player.current)
        tracks.extend(player.queue)
        
        from src.db import client as db_client
        success = await asyncio.to_thread(db_client.save_playlist, str(ctx.guild.id), str(ctx.author.id), name, tracks)
        if success:
            await ctx.send(embed=discord.Embed(description=f"Saved playlist **{name}** with {len(tracks)} tracks.", color=discord.Color.green()))
        else:
            await ctx.send("Failed to save playlist.")

    @music.command(name="playlist_list", description="List your saved playlists.")
    async def playlist_list(self, ctx: commands.Context):
        from src.db import client as db_client
        playlists = await asyncio.to_thread(db_client.list_playlists, str(ctx.guild.id), str(ctx.author.id))
        if not playlists:
            return await ctx.send("You have no saved playlists.")
            
        desc = "\n".join(f"- **{p['name']}**" for p in playlists)
        await ctx.send(embed=discord.Embed(title="Your Playlists", description=desc, color=0x3498DB))

    @music.command(name="playlist_load", description="Load a saved playlist into your queue.")
    async def playlist_load(self, ctx: commands.Context, name: str):
        from src.db import client as db_client
        playlist = await asyncio.to_thread(db_client.get_playlist, str(ctx.guild.id), name, str(ctx.author.id))
        
        if not playlist:
            return await ctx.send("Playlist not found.")
            
        if not ctx.voice_client:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                return await ctx.send("You need to be in a voice channel.")
                
        player = self.get_player(ctx.guild.id)
        tracks = playlist.get("music_playlist_tracks", [])
        
        if not tracks:
            return await ctx.send("Playlist is empty.")
            
        # Reconstruct songs
        for track in sorted(tracks, key=lambda t: t['position']):
            song = {
                'url': track['url'],
                'title': track['title'],
                'requester': ctx.author,
                'data': {'title': track['title'], 'url': track['url']}
            }
            player.queue.append(song)
            
        await ctx.send(embed=discord.Embed(description=f"Loaded **{len(tracks)}** tracks from **{name}** into the queue.", color=discord.Color.green()))
        
        if not ctx.voice_client.is_playing():
            await self.play_next(ctx)

    # ── Downloader ───────────────────────────────────────────────────────────

    @music.command(name="download", description="Search and download a track directly to Discord as an MP3.")
    @app_commands.describe(query="Search query for the song")
    async def download(self, ctx: commands.Context, *, query: str):
        msg = await ctx.send(embed=discord.Embed(description=f"Searching for top 5 results for `{query}`...", color=0x3498DB))
        
        try:
            loop = self.bot.loop or asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch5:{query}", download=False))
            
            entries = data.get('entries', [])
            if not entries:
                return await msg.edit(embed=discord.Embed(description="No results found.", color=discord.Color.red()))
                
            desc = ""
            for i, entry in enumerate(entries):
                duration = entry.get('duration', 0)
                mins, secs = divmod(duration, 60)
                desc += f"**Track {i+1}:** {entry.get('title')} (`{mins}:{secs:02d}`)\n\n"
                
            embed = discord.Embed(title="Select a track to download", description=desc, color=0x3498DB)
            embed.set_footer(text="Click the corresponding button below. Max duration ~15 mins (25MB limit).")
            
            view = MusicDownloadView(ctx, self, entries)
            await msg.edit(embed=embed, view=view)
            
        except Exception as e:
            await msg.edit(content=f"Error finding track: {clean_error_message(e)}", embed=None)

    @music.command(name="quality", description="Set the default audio download quality for this session.")
    @app_commands.describe(kbps="Quality in kbps (e.g. 96, 128, 192, 256, 320)")
    @app_commands.choices(kbps=[
        app_commands.Choice(name="64 Kbps", value="64"),
        app_commands.Choice(name="96 Kbps", value="96"),
        app_commands.Choice(name="128 Kbps", value="128"),
        app_commands.Choice(name="192 Kbps (Default)", value="192"),
        app_commands.Choice(name="256 Kbps", value="256"),
        app_commands.Choice(name="320 Kbps (HQ)", value="320"),
    ])
    async def quality(self, ctx: commands.Context, kbps: str):
        player = self.get_player(ctx.guild.id)
        player.quality = kbps
        await ctx.send(embed=discord.Embed(description=f"[VOICE] Session audio download quality set to **{kbps} Kbps**.", color=0x3498DB))

    @music.command(name="search", description="Search YouTube and select a track to play.")
    @app_commands.describe(query="Search keywords")
    async def search(self, ctx: commands.Context, *, query: str):
        if not ctx.voice_client:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                return await ctx.send("You need to be in a voice channel to play music.")
                
        msg = await ctx.send(embed=discord.Embed(description=f"Searching for top 5 results for `{query}`...", color=0x3498DB))
        
        try:
            loop = self.bot.loop or asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch5:{query}", download=False))
            
            entries = data.get('entries', [])
            if not entries:
                return await msg.edit(embed=discord.Embed(description="No results found.", color=discord.Color.red()))
                
            desc = ""
            for i, entry in enumerate(entries):
                duration = entry.get('duration', 0)
                mins, secs = divmod(duration, 60)
                desc += f"**{i+1}.** {entry.get('title')} (`{mins}:{secs:02d}`)\n\n"
                
            embed = discord.Embed(title="Select a track to play", description=desc, color=0x3498DB)
            
            class MusicPlaySearchView(discord.ui.View):
                def __init__(self, cog, entries):
                    super().__init__(timeout=60)
                    self.cog = cog
                    self.entries = entries
                    
                    for idx, entry in enumerate(entries):
                        btn = discord.ui.Button(label=f"Play {idx+1}", style=discord.ButtonStyle.primary, custom_id=f"playsearch_{idx}")
                        btn.callback = self.make_callback(entry)
                        self.add_item(btn)
                        
                def make_callback(self, entry):
                    async def callback(interaction: discord.Interaction):
                        if interaction.user != ctx.author:
                            return await interaction.response.send_message("Only the requester can select a track.", ephemeral=True)
                            
                        await interaction.response.edit_message(content=f"Selected **{entry.get('title')}**! Adding to queue...", embed=None, view=None)
                        
                        song = {
                            'url': entry['webpage_url'],
                            'title': entry['title'],
                            'requester': ctx.author,
                            'data': entry
                        }
                        player = self.cog.get_player(ctx.guild.id)
                        player.queue.append(song)
                        
                        if not ctx.voice_client.is_playing():
                            await self.cog.play_next(ctx)
                            
                    return callback
                    
            view = MusicPlaySearchView(self, entries)
            await msg.edit(embed=embed, view=view)
            
        except Exception as e:
            await msg.edit(content=f"Error finding tracks: {clean_error_message(e)}", embed=None)

async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot))
