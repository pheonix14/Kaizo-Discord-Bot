import discord
from discord.ext import commands
from discord import app_commands
from src.db import client as db_client

class TempVCCog(commands.Cog, name="Temp VC"):
    """Temporary Voice Channels commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.active_roles = {}

    async def cleanup_temp_vc_roles(self, guild: discord.Guild, channel_id: int):
        vc_id = channel_id
        roles_info = self.active_roles.get(vc_id)
        owner_role = None
        joiner_role = None
        
        if roles_info:
            owner_role = guild.get_role(roles_info["owner"])
            joiner_role = guild.get_role(roles_info["joiner"])
            
        if not owner_role or not joiner_role:
            # Reconstruct roles by scanning guild roles matching owner's name pattern
            res = db_client.supabase.table("temp_voice_channels").select("*").eq("channel_id", str(vc_id)).execute()
            if res.data:
                owner_id = int(res.data[0]["owner_id"])
                owner = guild.get_member(owner_id)
                if not owner:
                    try:
                        owner = await guild.fetch_member(owner_id)
                    except:
                        owner = None
                owner_display = owner.display_name if owner else "Unknown"
                
                owner_role_name = f"{owner_display} vc"
                joiner_role_name = f"{owner_display}'s vc"
                
                for r in guild.roles:
                    if r.name == owner_role_name:
                        owner_role = r
                    elif r.name == joiner_role_name:
                        joiner_role = r
                        
                if owner_role and joiner_role:
                    self.active_roles[vc_id] = {"owner": owner_role.id, "joiner": joiner_role.id}
                    
        if owner_role:
            try:
                await owner_role.delete(reason="Temp VC deleted/closed")
            except Exception:
                pass
        if joiner_role:
            try:
                await joiner_role.delete(reason="Temp VC deleted/closed")
            except Exception:
                pass
                
        if vc_id in self.active_roles:
            del self.active_roles[vc_id]

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot:
            return

        # 1. Check if they joined a Voice Channel
        if after.channel and before.channel != after.channel:
            settings = db_client.get_guild_settings(member.guild.id)
            lobby_id = settings.get("tempvc_join_channel") or settings.get("temp_vc_lobby")
            is_enabled = settings.get("tempvc_enabled", True)
            
            # Case A: Joined the Lobby/Creator channel
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
                    # Create Owner and Joiner temporary roles first
                    owner_role_name = f"{member.display_name} vc"
                    joiner_role_name = f"{member.display_name}'s vc"
                    
                    owner_role = await member.guild.create_role(name=owner_role_name, reason="Temp VC Owner Role")
                    joiner_role = await member.guild.create_role(name=joiner_role_name, reason="Temp VC Joiner Role")
                    
                    # Create temporary voice channel
                    new_vc = await member.guild.create_voice_channel(name=vc_name, category=category, user_limit=user_limit)
                    
                    self.active_roles[new_vc.id] = {"owner": owner_role.id, "joiner": joiner_role.id}
                    
                    # Assign owner role to the creator
                    try:
                        await member.add_roles(owner_role, reason="Assigned Temp VC Owner Role")
                    except Exception:
                        pass
                    
                    # Move member to the new voice channel
                    await member.move_to(new_vc)
                    
                    # Register in database
                    db_client.supabase.table("temp_voice_channels").insert({
                        "channel_id": str(new_vc.id),
                        "guild_id": str(member.guild.id),
                        "owner_id": str(member.id)
                    }).execute()
                    
                except discord.Forbidden:
                    pass
                except Exception:
                    pass
                return

            # Case B: Joined an existing temporary VC (not lobby)
            vc_id = after.channel.id
            vc_data = db_client.supabase.table("temp_voice_channels").select("*").eq("channel_id", str(vc_id)).execute()
            if vc_data.data:
                owner_id = int(vc_data.data[0]["owner_id"])
                
                # Find roles
                roles_info = self.active_roles.get(vc_id)
                owner_role = None
                joiner_role = None
                
                if roles_info:
                    owner_role = member.guild.get_role(roles_info["owner"])
                    joiner_role = member.guild.get_role(roles_info["joiner"])
                    
                if not owner_role or not joiner_role:
                    owner_name = member.guild.get_member(owner_id)
                    if not owner_name:
                        try:
                            owner_name = await member.guild.fetch_member(owner_id)
                        except:
                            owner_name = None
                    owner_display = owner_name.display_name if owner_name else "Unknown"
                    
                    owner_role_name = f"{owner_display} vc"
                    joiner_role_name = f"{owner_display}'s vc"
                    
                    for r in member.guild.roles:
                        if r.name == owner_role_name:
                            owner_role = r
                        elif r.name == joiner_role_name:
                            joiner_role = r
                    
                    if owner_role and joiner_role:
                        self.active_roles[vc_id] = {"owner": owner_role.id, "joiner": joiner_role.id}
                
                # Assign role depending on whether they are owner or joiner
                if member.id == owner_id:
                    if owner_role:
                        try:
                            await member.add_roles(owner_role, reason="Joined own Temp VC")
                        except Exception:
                            pass
                else:
                    if joiner_role:
                        try:
                            await member.add_roles(joiner_role, reason="Joined Temp VC")
                        except Exception:
                            pass

        # 2. Check if they left/moved from a Voice Channel
        if before.channel and before.channel != after.channel:
            vc_id = before.channel.id
            vc_data = db_client.supabase.table("temp_voice_channels").select("*").eq("channel_id", str(vc_id)).execute()
            if vc_data.data:
                owner_id = int(vc_data.data[0]["owner_id"])
                
                # Find roles
                roles_info = self.active_roles.get(vc_id)
                owner_role = None
                joiner_role = None
                
                if roles_info:
                    owner_role = member.guild.get_role(roles_info["owner"])
                    joiner_role = member.guild.get_role(roles_info["joiner"])
                    
                if not owner_role or not joiner_role:
                    owner_name = member.guild.get_member(owner_id)
                    if not owner_name:
                        try:
                            owner_name = await member.guild.fetch_member(owner_id)
                        except:
                            owner_name = None
                    owner_display = owner_name.display_name if owner_name else "Unknown"
                    
                    owner_role_name = f"{owner_display} vc"
                    joiner_role_name = f"{owner_display}'s vc"
                    
                    for r in member.guild.roles:
                        if r.name == owner_role_name:
                            owner_role = r
                        elif r.name == joiner_role_name:
                            joiner_role = r
                    
                    if owner_role and joiner_role:
                        self.active_roles[vc_id] = {"owner": owner_role.id, "joiner": joiner_role.id}
                
                # Remove roles from member
                if owner_role:
                    try:
                        await member.remove_roles(owner_role, reason="Left Temp VC")
                    except Exception:
                        pass
                if joiner_role:
                    try:
                        await member.remove_roles(joiner_role, reason="Left Temp VC")
                    except Exception:
                        pass
                
                # If channel is empty, delete channel and roles
                if len(before.channel.members) == 0:
                    await self.cleanup_temp_vc_roles(member.guild, vc_id)
                    try:
                        await before.channel.delete()
                    except discord.Forbidden:
                        pass
                    except Exception:
                        pass
                    
                    db_client.supabase.table("temp_voice_channels").delete().eq("channel_id", str(vc_id)).execute()

    def get_user_vc(self, member: discord.Member):
        if not member.voice or not member.voice.channel:
            return None
        res = db_client.supabase.table("temp_voice_channels").select("*").eq("channel_id", str(member.voice.channel.id)).execute()
        if res.data and res.data[0]["owner_id"] == str(member.id):
            return member.voice.channel
        return None

    @commands.hybrid_group(name="vc", description="Temp VC management commands.", fallback="help")
    async def vc_group(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @vc_group.command(name="setup", description="Setup the Temp VC system.")
    @commands.has_permissions(administrator=True)
    async def vc_setup(self, ctx: commands.Context):
        category = await ctx.guild.create_category("Temporary Channels")
        creator = await ctx.guild.create_voice_channel("Join to Create", category=category)
        db_client.update_guild_settings(ctx.guild.id, {
            "temp_vc_lobby": str(creator.id),
            "temp_vc_category": str(category.id)
        })
        await ctx.send(embed=discord.Embed(description=f"Temp VC system created. Join {creator.mention} to start.", color=discord.Color.green()))

    @vc_group.command(name="lock", description="Lock your Temp VC.")
    async def vc_lock(self, ctx: commands.Context):
        vc = self.get_user_vc(ctx.author)
        if not vc:
            return await ctx.send("You don't own the Temp VC you are in.", ephemeral=True)
        await vc.set_permissions(ctx.guild.default_role, connect=False)
        await ctx.send(embed=discord.Embed(description="VC locked.", color=discord.Color.red()), ephemeral=True)

    @vc_group.command(name="unlock", description="Unlock your Temp VC.")
    async def vc_unlock(self, ctx: commands.Context):
        vc = self.get_user_vc(ctx.author)
        if not vc:
            return await ctx.send("You don't own the Temp VC you are in.", ephemeral=True)
        await vc.set_permissions(ctx.guild.default_role, connect=None)
        await ctx.send(embed=discord.Embed(description="VC unlocked.", color=discord.Color.green()), ephemeral=True)

    @vc_group.command(name="name", description="Change your Temp VC name.")
    @app_commands.describe(name="New VC name")
    async def vc_name(self, ctx: commands.Context, name: str):
        vc = self.get_user_vc(ctx.author)
        if not vc:
            return await ctx.send("You don't own the Temp VC you are in.", ephemeral=True)
        await vc.edit(name=name)
        await ctx.send(embed=discord.Embed(description=f"VC renamed to **{name}**.", color=discord.Color.green()), ephemeral=True)

    @vc_group.command(name="limit", description="Set user limit for your Temp VC.")
    @app_commands.describe(limit="User limit (0 for unlimited)")
    async def vc_limit(self, ctx: commands.Context, limit: int):
        vc = self.get_user_vc(ctx.author)
        if not vc:
            return await ctx.send("You don't own the Temp VC you are in.", ephemeral=True)
        if limit < 0 or limit > 99:
            return await ctx.send("Limit must be between 0 and 99.", ephemeral=True)
        await vc.edit(user_limit=limit)
        await ctx.send(embed=discord.Embed(description=f"User limit set to **{limit}**.", color=discord.Color.green()), ephemeral=True)

    @vc_group.command(name="kick", description="Kick a user from your Temp VC.")
    @app_commands.describe(member="Member to kick")
    async def vc_kick(self, ctx: commands.Context, member: discord.Member):
        vc = self.get_user_vc(ctx.author)
        if not vc:
            return await ctx.send("You don't own the Temp VC you are in.", ephemeral=True)
        if member not in vc.members:
            return await ctx.send("That member is not in your VC.", ephemeral=True)
        await member.move_to(None)
        await ctx.send(embed=discord.Embed(description=f"Kicked {member.mention} from your VC.", color=discord.Color.orange()), ephemeral=True)

    @vc_group.command(name="hide", description="Hide your Temp VC from others.")
    async def vc_hide(self, ctx: commands.Context):
        vc = self.get_user_vc(ctx.author)
        if not vc:
            return await ctx.send("You don't own the Temp VC you are in.", ephemeral=True)
        await vc.set_permissions(ctx.guild.default_role, view_channel=False)
        await ctx.send(embed=discord.Embed(description="VC is now hidden.", color=discord.Color.dark_gray()), ephemeral=True)

    @vc_group.command(name="unhide", description="Unhide your Temp VC.")
    async def vc_unhide(self, ctx: commands.Context):
        vc = self.get_user_vc(ctx.author)
        if not vc:
            return await ctx.send("You don't own the Temp VC you are in.", ephemeral=True)
        await vc.set_permissions(ctx.guild.default_role, view_channel=None)
        await ctx.send(embed=discord.Embed(description="VC is now visible.", color=discord.Color.green()), ephemeral=True)

    @vc_group.command(name="ban", description="Ban a user from your Temp VC.")
    async def vc_ban(self, ctx: commands.Context, member: discord.Member):
        vc = self.get_user_vc(ctx.author)
        if not vc:
            return await ctx.send("You don't own the Temp VC you are in.", ephemeral=True)
        await vc.set_permissions(member, connect=False, view_channel=False)
        if member in vc.members:
            await member.move_to(None)
        await ctx.send(embed=discord.Embed(description=f"Banned {member.mention} from your VC.", color=discord.Color.red()), ephemeral=True)

    @vc_group.command(name="unban", description="Unban a user from your Temp VC.")
    async def vc_unban(self, ctx: commands.Context, member: discord.Member):
        vc = self.get_user_vc(ctx.author)
        if not vc:
            return await ctx.send("You don't own the Temp VC you are in.", ephemeral=True)
        await vc.set_permissions(member, overwrite=None)
        await ctx.send(embed=discord.Embed(description=f"Unbanned {member.mention} from your VC.", color=discord.Color.green()), ephemeral=True)

    @vc_group.command(name="invite", description="Invite a user to your locked Temp VC.")
    async def vc_invite(self, ctx: commands.Context, member: discord.Member):
        vc = self.get_user_vc(ctx.author)
        if not vc:
            return await ctx.send("You don't own the Temp VC you are in.", ephemeral=True)
        await vc.set_permissions(member, connect=True, view_channel=True)
        await ctx.send(embed=discord.Embed(description=f"Allowed {member.mention} to join your VC.", color=discord.Color.green()), ephemeral=True)

    @vc_group.command(name="claim", description="Claim ownership of the Temp VC if the owner left.")
    async def vc_claim(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send("You are not in a Temp VC.", ephemeral=True)
            
        vc = ctx.author.voice.channel
        res = db_client.supabase.table("temp_voice_channels").select("*").eq("channel_id", str(vc.id)).execute()
        if not res.data:
            return await ctx.send("This is not a Temp VC.", ephemeral=True)
            
        owner_id = res.data[0]["owner_id"]
        owner = ctx.guild.get_member(int(owner_id))
        
        if owner and owner in vc.members:
            return await ctx.send("The owner is still in the VC.", ephemeral=True)
            
        db_client.supabase.table("temp_voice_channels").update({"owner_id": str(ctx.author.id)}).eq("channel_id", str(vc.id)).execute()
        await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} is now the owner of this Temp VC.", color=discord.Color.gold()))

    # ── Admin Temp VC ────────────────────────────────────────────────────────
    
    @commands.hybrid_group(name="tempvc", description="Admin Temp VC management.", fallback="help")
    @commands.has_permissions(administrator=True)
    async def tempvc_group(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)
            
    @tempvc_group.command(name="list", description="List all active Temp VCs.")
    async def tempvc_list(self, ctx: commands.Context):
        res = db_client.supabase.table("temp_voice_channels").select("*").eq("guild_id", str(ctx.guild.id)).execute()
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
        res = db_client.supabase.table("temp_voice_channels").select("*").eq("channel_id", str(channel.id)).execute()
        if not res.data:
            return await ctx.send("That is not a Temp VC.")
            
        # Clean up roles
        await self.cleanup_temp_vc_roles(ctx.guild, channel.id)
        
        try:
            await channel.delete()
        except discord.Forbidden:
            pass
        except Exception:
            pass
            
        db_client.supabase.table("temp_voice_channels").delete().eq("channel_id", str(channel.id)).execute()
        await ctx.send(embed=discord.Embed(description="✅ Force closed Temp VC and deleted associated roles.", color=discord.Color.green()))

async def setup(bot: commands.Bot):
    await bot.add_cog(TempVCCog(bot))
