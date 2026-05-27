import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from src.db import client as db_client

class VoiceHelpView(discord.ui.View):
    def __init__(self, author_id: int):
        super().__init__(timeout=60.0)
        self.author_id = author_id
        self.current_page = 0
        
        self.pages = [
            # Page 1
            {
                "title": "🔊 KAIZER K5 - User VC Commands (Page 1/2)",
                "description": "Manage your temporary voice channel. You must own the channel to use these.",
                "fields": [
                    {"name": "• vc lock", "value": "Lock your voice channel so default members cannot join.\n*Usage:* `.vc lock` or `/vc lock`"},
                    {"name": "• vc unlock", "value": "Unlock your voice channel.\n*Usage:* `.vc unlock` or `/vc unlock`"},
                    {"name": "• vc name <new_name>", "value": "Rename your voice channel.\n*Usage:* `.vc name Chill Lounge`"},
                    {"name": "• vc limit <count>", "value": "Set a user limit for your channel (0 for unlimited, max 99).\n*Usage:* `.vc limit 5`"},
                    {"name": "• vc kick <member>", "value": "Kick a member out of your voice channel.\n*Usage:* `.vc kick @Member`"},
                    {"name": "• vc ban <member> / vc unban <member>", "value": "Ban or unban a member from entering your channel.\n*Usage:* `.vc ban @Member`"},
                    {"name": "• vc hide / vc unhide", "value": "Hide your channel from the channel list or make it visible again.\n*Usage:* `.vc hide`"},
                    {"name": "• vc invite <member>", "value": "Permit a user to join your locked/hidden voice channel.\n*Usage:* `.vc invite @Member`"},
                    {"name": "• vc claim", "value": "Claim ownership of the voice channel if the previous owner left."}
                ]
            },
            # Page 2
            {
                "title": "⚙️ KAIZER K5 - Admin VC Setup (Page 2/2)",
                "description": "Administrator setup and management commands.",
                "fields": [
                    {"name": "• vc setup", "value": "Automatically setup Creator Lobby Voice Channel and Category.\n*Permissions Required:* `Administrator`\n*Usage:* `.vc setup`"},
                    {"name": "• tempvc list", "value": "List all active temporary voice channels and owners.\n*Permissions Required:* `Administrator`"},
                    {"name": "• tempvc forceclose <channel>", "value": "Force delete an active temporary voice channel.\n*Permissions Required:* `Administrator`"}
                ]
            }
        ]

    def make_embed(self) -> discord.Embed:
        page_data = self.pages[self.current_page]
        embed = discord.Embed(
            title=page_data["title"],
            description=page_data["description"],
            color=0x2ECC71
        )
        for f in page_data["fields"]:
            embed.add_field(name=f["name"], value=f["value"], inline=False)
        embed.set_footer(text="KAIZER K5 • Use the buttons below to navigate pages")
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

    @discord.ui.button(label="◀ Previous", style=discord.ButtonStyle.primary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
        else:
            self.current_page = len(self.pages) - 1
        await interaction.response.edit_message(embed=self.make_embed(), view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
        else:
            self.current_page = 0
        await interaction.response.edit_message(embed=self.make_embed(), view=self)


class TempVCCog(commands.Cog, name="Temp VC"):
    """Temporary Voice Channels commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot:
            return

        # Check if they joined the creator channel
        if after.channel:
            settings = await asyncio.to_thread(db_client.get_guild_settings, member.guild.id)
            # Default to checking tempvc_join_channel from UI, fallback to temp_vc_lobby from setup command
            lobby_id = settings.get("tempvc_join_channel") or settings.get("temp_vc_lobby")
            
            # Make sure system is enabled (dashboard checkbox or assume True if using command setup)
            is_enabled = settings.get("tempvc_enabled", True)
            
            if is_enabled and lobby_id and str(lobby_id) == str(after.channel.id):
                cat_id = settings.get("tempvc_category") or settings.get("temp_vc_category")
                category = member.guild.get_channel(int(cat_id)) if cat_id else after.channel.category
                
                name_template = settings.get("tempvc_name_template") or settings.get("temp_vc_name_format") or "{user}'s Lounge"
                vc_name = name_template.replace("{user}", member.display_name)
                
                # Fetch user limit
                user_limit = settings.get("tempvc_default_limit") or settings.get("temp_vc_default_limit", 0)
                try:
                    user_limit = int(user_limit)
                except ValueError:
                    user_limit = 0
                
                try:
                    new_vc = await member.guild.create_voice_channel(name=vc_name, category=category, user_limit=user_limit)
                    await member.move_to(new_vc)
                    await asyncio.to_thread(
                        db_client.supabase.table("temp_voice_channels").insert({
                            "channel_id": str(new_vc.id),
                            "guild_id": str(member.guild.id),
                            "owner_id": str(member.id)
                        }).execute
                    )
                except discord.Forbidden:
                    pass

        # Check if they left a temp VC and it's empty
        if before.channel:
            vc_data = await asyncio.to_thread(db_client.supabase.table("temp_voice_channels").select("*").eq("channel_id", str(before.channel.id)).execute)
            if vc_data.data:
                if len(before.channel.members) == 0:
                    try:
                        await before.channel.delete()
                        await asyncio.to_thread(db_client.supabase.table("temp_voice_channels").delete().eq("channel_id", str(before.channel.id)).execute)
                    except discord.Forbidden:
                        pass

    async def get_user_vc(self, member: discord.Member):
        if not member.voice or not member.voice.channel:
            return None
        res = await asyncio.to_thread(db_client.supabase.table("temp_voice_channels").select("*").eq("channel_id", str(member.voice.channel.id)).execute)
        if res.data and res.data[0]["owner_id"] == str(member.id):
            return member.voice.channel
        return None

    @commands.hybrid_group(name="vc", description="Temp VC management commands.", fallback="help")
    async def vc_group(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            view = VoiceHelpView(ctx.author.id)
            msg = await ctx.send(embed=view.make_embed(), view=view)
            view.message = msg

    @commands.hybrid_command(name="voice", aliases=["temp_vc"], description="Show temporary voice channel help.")
    async def voice_command(self, ctx: commands.Context):
        view = VoiceHelpView(ctx.author.id)
        msg = await ctx.send(embed=view.make_embed(), view=view)
        view.message = msg

    @vc_group.command(name="setup", description="Setup the Temp VC system.")
    @commands.has_permissions(administrator=True)
    async def vc_setup(self, ctx: commands.Context):
        category = await ctx.guild.create_category("Temporary Channels")
        creator = await ctx.guild.create_voice_channel("Join to Create", category=category)
        await asyncio.to_thread(db_client.update_guild_settings, ctx.guild.id, {
            "temp_vc_lobby": str(creator.id),
            "temp_vc_category": str(category.id)
        })
        await ctx.send(embed=discord.Embed(description=f"Temp VC system created. Join {creator.mention} to start.", color=discord.Color.green()))

    @vc_group.command(name="lock", description="Lock your Temp VC.")
    async def vc_lock(self, ctx: commands.Context):
        vc = await self.get_user_vc(ctx.author)
        if not vc:
            return await ctx.send("You don't own the Temp VC you are in.", ephemeral=True)
        await vc.set_permissions(ctx.guild.default_role, connect=False)
        await ctx.send(embed=discord.Embed(description="VC locked.", color=discord.Color.red()), ephemeral=True)

    @vc_group.command(name="unlock", description="Unlock your Temp VC.")
    async def vc_unlock(self, ctx: commands.Context):
        vc = await self.get_user_vc(ctx.author)
        if not vc:
            return await ctx.send("You don't own the Temp VC you are in.", ephemeral=True)
        await vc.set_permissions(ctx.guild.default_role, connect=None)
        await ctx.send(embed=discord.Embed(description="VC unlocked.", color=discord.Color.green()), ephemeral=True)

    @vc_group.command(name="name", description="Change your Temp VC name.")
    @app_commands.describe(name="New VC name")
    async def vc_name(self, ctx: commands.Context, name: str):
        vc = await self.get_user_vc(ctx.author)
        if not vc:
            return await ctx.send("You don't own the Temp VC you are in.", ephemeral=True)
        await vc.edit(name=name)
        await ctx.send(embed=discord.Embed(description=f"VC renamed to **{name}**.", color=discord.Color.green()), ephemeral=True)

    @vc_group.command(name="limit", description="Set user limit for your Temp VC.")
    @app_commands.describe(limit="User limit (0 for unlimited)")
    async def vc_limit(self, ctx: commands.Context, limit: int):
        vc = await self.get_user_vc(ctx.author)
        if not vc:
            return await ctx.send("You don't own the Temp VC you are in.", ephemeral=True)
        if limit < 0 or limit > 99:
            return await ctx.send("Limit must be between 0 and 99.", ephemeral=True)
        await vc.edit(user_limit=limit)
        await ctx.send(embed=discord.Embed(description=f"User limit set to **{limit}**.", color=discord.Color.green()), ephemeral=True)

    @vc_group.command(name="kick", description="Kick a user from your Temp VC.")
    @app_commands.describe(member="Member to kick")
    async def vc_kick(self, ctx: commands.Context, member: discord.Member):
        vc = await self.get_user_vc(ctx.author)
        if not vc:
            return await ctx.send("You don't own the Temp VC you are in.", ephemeral=True)
        if member not in vc.members:
            return await ctx.send("That member is not in your VC.", ephemeral=True)
        await member.move_to(None)
        await ctx.send(embed=discord.Embed(description=f"Kicked {member.mention} from your VC.", color=discord.Color.orange()), ephemeral=True)

    @vc_group.command(name="hide", description="Hide your Temp VC from others.")
    async def vc_hide(self, ctx: commands.Context):
        vc = await self.get_user_vc(ctx.author)
        if not vc:
            return await ctx.send("You don't own the Temp VC you are in.", ephemeral=True)
        await vc.set_permissions(ctx.guild.default_role, view_channel=False)
        await ctx.send(embed=discord.Embed(description="VC is now hidden.", color=discord.Color.dark_gray()), ephemeral=True)

    @vc_group.command(name="unhide", description="Unhide your Temp VC.")
    async def vc_unhide(self, ctx: commands.Context):
        vc = await self.get_user_vc(ctx.author)
        if not vc:
            return await ctx.send("You don't own the Temp VC you are in.", ephemeral=True)
        await vc.set_permissions(ctx.guild.default_role, view_channel=None)
        await ctx.send(embed=discord.Embed(description="VC is now visible.", color=discord.Color.green()), ephemeral=True)

    @vc_group.command(name="ban", description="Ban a user from your Temp VC.")
    async def vc_ban(self, ctx: commands.Context, member: discord.Member):
        vc = await self.get_user_vc(ctx.author)
        if not vc:
            return await ctx.send("You don't own the Temp VC you are in.", ephemeral=True)
        await vc.set_permissions(member, connect=False, view_channel=False)
        if member in vc.members:
            await member.move_to(None)
        await ctx.send(embed=discord.Embed(description=f"Banned {member.mention} from your VC.", color=discord.Color.red()), ephemeral=True)

    @vc_group.command(name="unban", description="Unban a user from your Temp VC.")
    async def vc_unban(self, ctx: commands.Context, member: discord.Member):
        vc = await self.get_user_vc(ctx.author)
        if not vc:
            return await ctx.send("You don't own the Temp VC you are in.", ephemeral=True)
        await vc.set_permissions(member, overwrite=None)
        await ctx.send(embed=discord.Embed(description=f"Unbanned {member.mention} from your VC.", color=discord.Color.green()), ephemeral=True)

    @vc_group.command(name="invite", description="Invite a user to your locked Temp VC.")
    async def vc_invite(self, ctx: commands.Context, member: discord.Member):
        vc = await self.get_user_vc(ctx.author)
        if not vc:
            return await ctx.send("You don't own the Temp VC you are in.", ephemeral=True)
        await vc.set_permissions(member, connect=True, view_channel=True)
        await ctx.send(embed=discord.Embed(description=f"Allowed {member.mention} to join your VC.", color=discord.Color.green()), ephemeral=True)

    @vc_group.command(name="claim", description="Claim ownership of the Temp VC if the owner left.")
    async def vc_claim(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send("You are not in a Temp VC.", ephemeral=True)
            
        vc = ctx.author.voice.channel
        res = await asyncio.to_thread(db_client.supabase.table("temp_voice_channels").select("*").eq("channel_id", str(vc.id)).execute)
        if not res.data:
            return await ctx.send("This is not a Temp VC.", ephemeral=True)
            
        owner_id = res.data[0]["owner_id"]
        owner = ctx.guild.get_member(int(owner_id))
        
        if owner and owner in vc.members:
            return await ctx.send("The owner is still in the VC.", ephemeral=True)
            
        await asyncio.to_thread(db_client.supabase.table("temp_voice_channels").update({"owner_id": str(ctx.author.id)}).eq("channel_id", str(vc.id)).execute)
        await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} is now the owner of this Temp VC.", color=discord.Color.gold()))

    # ── Admin Temp VC ────────────────────────────────────────────────────────
    
    @commands.hybrid_group(name="tempvc", description="Admin Temp VC management.", fallback="help")
    @commands.has_permissions(administrator=True)
    async def tempvc_group(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            view = VoiceHelpView(ctx.author.id)
            view.current_page = 1  # Start on Page 2 (Admin setup)
            msg = await ctx.send(embed=view.make_embed(), view=view)
            view.message = msg
            
    @tempvc_group.command(name="list", description="List all active Temp VCs.")
    async def tempvc_list(self, ctx: commands.Context):
        res = await asyncio.to_thread(db_client.supabase.table("temp_voice_channels").select("*").eq("guild_id", str(ctx.guild.id)).execute)
        if not res.data:
            return await ctx.send("There are no active Temp VCs.")
            
        desc = ""
        for v in res.data:
            chan = ctx.guild.get_channel(int(v['channel_id']))
            owner = ctx.guild.get_member(int(v['owner_id']))
            if chan:
                desc += f"{chan.mention} — Owner: {owner.mention if owner else 'Unknown'}\n"
                
        await ctx.send(embed=discord.Embed(title="Active Temp VCs", description=desc, color=0x3498DB))

    @tempvc_group.command(name="forceclose", description="Force delete an active Temp VC.")
    async def tempvc_close(self, ctx: commands.Context, channel: discord.VoiceChannel):
        res = await asyncio.to_thread(db_client.supabase.table("temp_voice_channels").select("*").eq("channel_id", str(channel.id)).execute)
        if not res.data:
            return await ctx.send("That is not a Temp VC.")
            
        await channel.delete()
        await asyncio.to_thread(db_client.supabase.table("temp_voice_channels").delete().eq("channel_id", str(channel.id)).execute)
        await ctx.send(embed=discord.Embed(description="✅ Force closed Temp VC.", color=discord.Color.green()))

async def setup(bot: commands.Bot):
    await bot.add_cog(TempVCCog(bot))
