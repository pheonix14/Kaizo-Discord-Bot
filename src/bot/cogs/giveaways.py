import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
import datetime
from src.db import client as db_client

class GiveawayView(discord.ui.View):
    def __init__(self, db_id: str, bot: commands.Bot):
        super().__init__(timeout=None)
        self.db_id = db_id
        self.bot = bot
        
        # Setup entry button with persistent custom ID
        self.enter_button = discord.ui.Button(
            label="Enter Giveaway",
            emoji="🎉",
            style=discord.ButtonStyle.primary,
            custom_id=f"giveaway_enter:{db_id}"
        )
        self.enter_button.callback = self.enter_giveaway_callback
        self.add_item(self.enter_button)

    async def enter_giveaway_callback(self, interaction: discord.Interaction):
        try:
            # Fetch latest giveaway status from Supabase
            res = db_client.supabase.table("giveaways").select("*").eq("id", self.db_id).execute()
            if not res.data:
                return await interaction.response.send_message("This giveaway has ended or does not exist.", ephemeral=True)
            
            data = res.data[0]
            embed_config = data.get("embed_config") or {}
            
            # Check if ended in config
            if embed_config.get("ended"):
                return await interaction.response.send_message("This giveaway has already ended.", ephemeral=True)
                
            # Verify timing
            end_time_str = data["end_time"]
            try:
                end_dt = datetime.datetime.fromisoformat(end_time_str.replace("Z", "+00:00"))
            except Exception:
                return await interaction.response.send_message("Invalid timing configuration for this giveaway.", ephemeral=True)
                
            now_dt = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
            if now_dt >= end_dt:
                return await interaction.response.send_message("This giveaway has already ended.", ephemeral=True)
                
            guild = interaction.guild
            member = interaction.user
            if not isinstance(member, discord.Member):
                member = guild.get_member(member.id) or await guild.fetch_member(member.id)
                
            # Validate role restriction settings
            if data.get("restrict_roles_enabled") and data.get("allowed_roles"):
                allowed_roles = data.get("allowed_roles")
                mode = data.get("roles_mode", "any")
                reverse = data.get("roles_reverse", False)
                
                member_role_ids = [str(r.id) for r in member.roles]
                
                if mode == "all":
                    has_match = all(r_id in member_role_ids for r_id in allowed_roles)
                else:
                    has_match = any(r_id in member_role_ids for r_id in allowed_roles)
                    
                if reverse:
                    is_disqualified = any(r_id in member_role_ids for r_id in allowed_roles)
                    if is_disqualified:
                        return await interaction.response.send_message("You have a blacklisted role and cannot enter.", ephemeral=True)
                else:
                    if not has_match:
                        return await interaction.response.send_message("You do not possess the required roles to enter.", ephemeral=True)
            
            # Append participant (prevent duplicate entries)
            participants = embed_config.get("participants", [])
            user_id_str = str(interaction.user.id)
            if user_id_str in participants:
                return await interaction.response.send_message("You have already entered this giveaway!", ephemeral=True)
                
            participants.append(user_id_str)
            embed_config["participants"] = participants
            
            # Sync back to Supabase
            db_client.supabase.table("giveaways").update({"embed_config": embed_config}).eq("id", self.db_id).execute()
            
            # Send positive feedback to user
            await interaction.response.send_message("🎉 You have successfully entered the giveaway!", ephemeral=True)
            
            # Update embed count dynamically
            title = embed_config.get("title") or "🎉 GIVEAWAY 🎉"
            base_desc = embed_config.get("description") or f"Click the button below to enter!\n\n**Prize:** {data['prize']}\n**Winners:** {data['winners_count']}\n**Hosted by:** <@{data['host_id']}>\n**Ends in:** <t:{int(end_dt.timestamp())}:R>"
            
            # Clean up and rebuild description showing dynamic participant count
            desc_lines = base_desc.split("\n")
            filtered_lines = [line for line in desc_lines if not (line.startswith("**Entries:**") or line.startswith("**Total Entries:**") or "Entries:" in line)]
            desc = "\n".join(filtered_lines) + f"\n**Total Entries:** {len(participants)}"
            
            color_val = embed_config.get("color") or "#9B59B6"
            if isinstance(color_val, str):
                if color_val.startswith("#"):
                    color = int(color_val[1:], 16)
                else:
                    color = int(color_val, 16)
            else:
                color = color_val
                
            embed = discord.Embed(title=title, description=desc, color=color)
            if embed_config.get("thumbnail"):
                embed.set_thumbnail(url=embed_config["thumbnail"])
            if embed_config.get("image"):
                embed.set_image(url=embed_config["image"])
            if embed_config.get("footer"):
                icon_url = embed_config.get("footer_icon")
                embed.set_footer(text=embed_config["footer"], icon_url=icon_url if icon_url else None)
                
            # Edit original message with updated embed
            await interaction.message.edit(embed=embed, view=self)
            
        except Exception as e:
            print("Error in giveaway interactive callback:", e)
            try:
                await interaction.response.send_message("Failed to process entry. Please try again.", ephemeral=True)
            except:
                pass

class GiveawaysCog(commands.Cog, name="Giveaways"):
    """Giveaway system commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.active_giveaways = {}  # message_id -> asyncio.Task

    async def cog_load(self):
        # Schedule startup load task
        self.bot.loop.create_task(self._load_active_giveaways())

    async def _load_active_giveaways(self):
        await self.bot.wait_until_ready()
        try:
            res = db_client.supabase.table("giveaways").select("*").execute()
            if not res.data:
                return
                
            for data in res.data:
                db_id = data["id"]
                embed_config = data.get("embed_config") or {}
                
                # Skip already ended giveaways
                if embed_config.get("ended"):
                    continue
                    
                # Re-register views for persistence
                view = GiveawayView(db_id, self.bot)
                self.bot.add_view(view)
                
                end_time_str = data["end_time"]
                try:
                    end_dt = datetime.datetime.fromisoformat(end_time_str.replace("Z", "+00:00"))
                except Exception:
                    continue
                    
                now_dt = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
                delay = (end_dt - now_dt).total_seconds()
                
                if delay <= 0:
                    self.bot.loop.create_task(self._end_giveaway_persistent(db_id, 0))
                else:
                    if data["message_id"] == "pending":
                        self.bot.loop.create_task(self.start_dashboard_giveaway(db_id))
                    else:
                        msg_id = int(data["message_id"])
                        task = self.bot.loop.create_task(self._end_giveaway_persistent(db_id, delay))
                        self.active_giveaways[msg_id] = task
        except Exception as e:
            print("Error loading active giveaways on startup:", e)

    async def start_dashboard_giveaway(self, db_id: str):
        try:
            res = db_client.supabase.table("giveaways").select("*").eq("id", db_id).execute()
            if not res.data:
                return
            data = res.data[0]
            
            guild_id = int(data["guild_id"])
            channel_id = int(data["channel_id"])
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return
            channel = guild.get_channel(channel_id)
            if not channel:
                return
                
            embed_config = data.get("embed_config") or {}
            if "participants" not in embed_config:
                embed_config["participants"] = []
                # Sync back to Supabase
                db_client.supabase.table("giveaways").update({"embed_config": embed_config}).eq("id", db_id).execute()
                
            title = embed_config.get("title") or "🎉 GIVEAWAY 🎉"
            end_dt = datetime.datetime.fromisoformat(data["end_time"].replace("Z", "+00:00"))
            
            base_desc = embed_config.get("description") or f"Click the button below to enter!\n\n**Prize:** {data['prize']}\n**Winners:** {data['winners_count']}\n**Hosted by:** <@{data['host_id']}>\n**Ends in:** <t:{int(end_dt.timestamp())}:R>"
            
            # Add dynamic participants entries line
            desc_lines = base_desc.split("\n")
            filtered_lines = [line for line in desc_lines if not (line.startswith("**Entries:**") or line.startswith("**Total Entries:**") or "Entries:" in line)]
            desc = "\n".join(filtered_lines) + f"\n**Total Entries:** 0"
            
            color_val = embed_config.get("color") or "#9B59B6"
            if isinstance(color_val, str):
                if color_val.startswith("#"):
                    color = int(color_val[1:], 16)
                else:
                    color = int(color_val, 16)
            else:
                color = color_val
                
            embed = discord.Embed(title=title, description=desc, color=color)
            if embed_config.get("thumbnail"):
                embed.set_thumbnail(url=embed_config["thumbnail"])
            if embed_config.get("image"):
                embed.set_image(url=embed_config["image"])
            if embed_config.get("footer"):
                icon_url = embed_config.get("footer_icon")
                embed.set_footer(text=embed_config["footer"], icon_url=icon_url if icon_url else None)
                
            # Send message with interactive button view
            view = GiveawayView(db_id, self.bot)
            msg = await channel.send(embed=embed, view=view)
            self.bot.add_view(view)
            
            # Save message ID
            db_client.supabase.table("giveaways").update({"message_id": str(msg.id)}).eq("id", db_id).execute()
            
            # Setup delay ending task
            now_dt = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
            delay = (end_dt - now_dt).total_seconds()
            if delay < 0:
                delay = 0
                
            task = self.bot.loop.create_task(self._end_giveaway_persistent(db_id, delay))
            self.active_giveaways[msg.id] = task
        except Exception as e:
            print("Error starting dashboard giveaway:", e)

    async def _end_giveaway_persistent(self, db_id: str, delay: float):
        await asyncio.sleep(delay)
        try:
            res = db_client.supabase.table("giveaways").select("*").eq("id", db_id).execute()
            if not res.data:
                return
            data = res.data[0]
            embed_config = data.get("embed_config") or {}
            
            # Skip if already marked ended
            if embed_config.get("ended"):
                return
                
            guild_id = int(data["guild_id"])
            channel_id = int(data["channel_id"])
            message_id = int(data["message_id"]) if data["message_id"] != "pending" else None
            
            if not message_id:
                return
                
            self.active_giveaways.pop(message_id, None)
            
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return
            channel = guild.get_channel(channel_id)
            if not channel:
                return
                
            try:
                msg = await channel.fetch_message(message_id)
                
                # Fetch participant user objects from database
                participant_ids = embed_config.get("participants", [])
                users = []
                for p_id in participant_ids:
                    try:
                        member = guild.get_member(int(p_id))
                        if not member:
                            member = await guild.fetch_member(int(p_id))
                        if member and not member.bot:
                            users.append(member)
                    except:
                        pass
                
                # Final safeguard role restriction check
                if data.get("restrict_roles_enabled") and data.get("allowed_roles"):
                    allowed_roles = data.get("allowed_roles")
                    mode = data.get("roles_mode", "any")
                    reverse = data.get("roles_reverse", False)
                    
                    filtered_users = []
                    for member in users:
                        member_role_ids = [str(r.id) for r in member.roles]
                        if mode == "all":
                            has_match = all(r_id in member_role_ids for r_id in allowed_roles)
                        else:
                            has_match = any(r_id in member_role_ids for r_id in allowed_roles)
                            
                        if reverse:
                            is_disqualified = any(r_id in member_role_ids for r_id in allowed_roles)
                            if not is_disqualified:
                                filtered_users.append(member)
                        else:
                            if has_match:
                                filtered_users.append(member)
                    users = filtered_users
                
                # Setup disabled button view
                ended_view = discord.ui.View()
                ended_button = discord.ui.Button(
                    label="Giveaway Ended",
                    style=discord.ButtonStyle.secondary,
                    disabled=True,
                    custom_id=f"giveaway_ended:{db_id}"
                )
                ended_view.add_item(ended_button)
                
                if len(users) == 0:
                    title = embed_config.get("title") or "🎉 GIVEAWAY ENDED 🎉"
                    desc = f"**Prize:** {data['prize']}\n**Hosted by:** <@{data['host_id']}>\n**Winners:** None"
                    
                    embed = discord.Embed(title=title, description=desc, color=discord.Color.dark_gray())
                    if embed_config.get("thumbnail"):
                        embed.set_thumbnail(url=embed_config["thumbnail"])
                    if embed_config.get("image"):
                        embed.set_image(url=embed_config["image"])
                    await msg.edit(embed=embed, view=ended_view)
                    
                    await channel.send(f"Nobody entered or met the requirements for the giveaway for **{data['prize']}**!")
                else:
                    winner_count = min(data["winners_count"], len(users))
                    winners = random.sample(users, winner_count)
                    winners_mentions = ", ".join([w.mention for w in winners])
                    
                    title = embed_config.get("title") or "🎉 GIVEAWAY ENDED 🎉"
                    desc = f"**Prize:** {data['prize']}\n**Hosted by:** <@{data['host_id']}>\n**Winners:** {winners_mentions}"
                    
                    embed = discord.Embed(title=title, description=desc, color=discord.Color.dark_gray())
                    if embed_config.get("thumbnail"):
                        embed.set_thumbnail(url=embed_config["thumbnail"])
                    if embed_config.get("image"):
                        embed.set_image(url=embed_config["image"])
                    await msg.edit(embed=embed, view=ended_view)
                    
                    await channel.send(f"Congratulations {winners_mentions}! You won **{data['prize']}**!")
            except discord.NotFound:
                pass
            finally:
                # Mark as ended in DB instead of deleting row to allow rerolls
                try:
                    embed_config["ended"] = True
                    db_client.supabase.table("giveaways").update({"embed_config": embed_config}).eq("id", db_id).execute()
                except Exception as ex:
                    print(f"Error updating ended state for giveaway {db_id}: {ex}")
        except Exception as e:
            print(f"Error executing end phase of giveaway {db_id}: {e}")

    @commands.hybrid_group(name="giveaway", description="Giveaway system commands.", fallback="help")
    @commands.has_permissions(manage_events=True)
    async def giveaway_group(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @giveaway_group.command(name="start", description="Start a new giveaway.")
    @app_commands.describe(duration="Duration in seconds", winners="Number of winners", prize="The prize to give away")
    async def giveaway_start(self, ctx: commands.Context, duration: int, winners: int, *, prize: str):
        if duration <= 0:
            return await ctx.send("Duration must be greater than 0.")
        if winners <= 0:
            return await ctx.send("Number of winners must be greater than 0.")

        import uuid
        db_id = str(uuid.uuid4())
        
        # Calculate end time
        end_time = (datetime.datetime.utcnow() + datetime.timedelta(seconds=duration)).isoformat()
        
        db_payload = {
            "id": db_id,
            "guild_id": str(ctx.guild.id),
            "channel_id": str(ctx.channel.id),
            "message_id": "pending",
            "host_id": str(ctx.author.id),
            "prize": prize,
            "winners_count": winners,
            "end_time": end_time,
            "restrict_roles_enabled": False,
            "allowed_roles": [],
            "roles_mode": "any",
            "roles_reverse": False,
            "animation_style": "scrolling_wheel",
            "embed_config": {"participants": []}
        }
        
        try:
            db_client.supabase.table("giveaways").insert(db_payload).execute()
            await ctx.send("Starting giveaway...", ephemeral=True)
            await self.start_dashboard_giveaway(db_id)
        except Exception as e:
            await ctx.send(f"Failed to start giveaway: {e}")

    @giveaway_group.command(name="end", description="End a giveaway early.")
    @app_commands.describe(message_id="The ID of the giveaway message")
    async def giveaway_end(self, ctx: commands.Context, message_id: str):
        try:
            msg_id = int(message_id)
        except ValueError:
            return await ctx.send("Invalid message ID.")
            
        res = db_client.supabase.table("giveaways").select("id").eq("message_id", str(msg_id)).execute()
        if res.data:
            db_id = res.data[0]["id"]
            task = self.active_giveaways.pop(msg_id, None)
            if task:
                task.cancel()
            await self._end_giveaway_persistent(db_id, 0)
            await ctx.send("Ended the giveaway early.")
        else:
            await ctx.send("Could not find an active giveaway with that ID.")

    @giveaway_group.command(name="reroll", description="Reroll a giveaway winner.")
    @app_commands.describe(message_id="The ID of the giveaway message")
    async def giveaway_reroll(self, ctx: commands.Context, message_id: str):
        try:
            msg_id = int(message_id)
        except ValueError:
            return await ctx.send("Invalid message ID.")
            
        res = db_client.supabase.table("giveaways").select("*").eq("message_id", str(msg_id)).execute()
        if not res.data:
            return await ctx.send("Could not find a giveaway with that message ID in the database.")
            
        data = res.data[0]
        embed_config = data.get("embed_config") or {}
        participants_ids = embed_config.get("participants", [])
        
        if not participants_ids:
            return await ctx.send("Nobody entered this giveaway, so it cannot be rerolled.")
            
        guild = ctx.guild
        users = []
        for p_id in participants_ids:
            try:
                member = guild.get_member(int(p_id))
                if not member:
                    member = await guild.fetch_member(int(p_id))
                if member and not member.bot:
                    users.append(member)
            except:
                pass
                
        # Apply role restrictions
        if data.get("restrict_roles_enabled") and data.get("allowed_roles"):
            allowed_roles = data.get("allowed_roles")
            mode = data.get("roles_mode", "any")
            reverse = data.get("roles_reverse", False)
            
            filtered_users = []
            for member in users:
                member_role_ids = [str(r.id) for r in member.roles]
                if mode == "all":
                    has_match = all(r_id in member_role_ids for r_id in allowed_roles)
                else:
                    has_match = any(r_id in member_role_ids for r_id in allowed_roles)
                    
                if reverse:
                    is_disqualified = any(r_id in member_role_ids for r_id in allowed_roles)
                    if not is_disqualified:
                        filtered_users.append(member)
                else:
                    if has_match:
                        filtered_users.append(member)
            users = filtered_users
            
        if not users:
            return await ctx.send("Nobody met the requirements or is still in the server to be drawn.")
            
        winner = random.choice(users)
        await ctx.send(f"🎉 Rerolled! The new winner is {winner.mention}! Congratulations!")

async def setup(bot: commands.Bot):
    await bot.add_cog(GiveawaysCog(bot))
