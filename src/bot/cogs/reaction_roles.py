import discord
from discord.ext import commands
from discord import app_commands

class ReactionRolesCog(commands.Cog, name="Reaction Roles"):
    """Reaction role commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Maps message_id -> { emoji: role_id }
        self.rr_data = {}

    @commands.hybrid_group(name="rr", description="Reaction roles system.", fallback="help")
    @commands.has_permissions(manage_roles=True)
    async def rr_group(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @rr_group.command(name="add", description="Add a reaction role to a message.")
    @app_commands.describe(message_id="The message ID", emoji="The emoji to react with", role="The role to give")
    async def rr_add(self, ctx: commands.Context, message_id: str, emoji: str, role: discord.Role):
        try:
            msg = await ctx.channel.fetch_message(int(message_id))
        except (ValueError, discord.NotFound):
            return await ctx.send("Could not find that message in this channel.")

        if role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.send("You cannot assign a role higher or equal to your own.")
        if role >= ctx.guild.me.top_role:
            return await ctx.send("I cannot assign a role higher or equal to my own.")

        await msg.add_reaction(emoji)
        
        msg_id = msg.id
        if msg_id not in self.rr_data:
            self.rr_data[msg_id] = {}
        self.rr_data[msg_id][emoji] = role.id

        await ctx.send(embed=discord.Embed(description=f"✅ Added {role.mention} for reaction {emoji} on message.", color=discord.Color.green()))

    @rr_group.command(name="remove", description="Remove a reaction role from a message.")
    @app_commands.describe(message_id="The message ID", emoji="The emoji to remove")
    async def rr_remove(self, ctx: commands.Context, message_id: str, emoji: str):
        try:
            msg_id = int(message_id)
        except ValueError:
            return await ctx.send("Invalid message ID.")
            
        if msg_id in self.rr_data and emoji in self.rr_data[msg_id]:
            del self.rr_data[msg_id][emoji]
            await ctx.send(embed=discord.Embed(description=f"✅ Removed reaction role for {emoji}.", color=discord.Color.green()))
        else:
            await ctx.send("No reaction role found for that emoji on that message.")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return
            
        if payload.message_id in self.rr_data:
            emoji_str = str(payload.emoji)
            if emoji_str in self.rr_data[payload.message_id]:
                guild = self.bot.get_guild(payload.guild_id)
                role = guild.get_role(self.rr_data[payload.message_id][emoji_str])
                member = guild.get_member(payload.user_id)
                if role and member:
                    try:
                        await member.add_roles(role, reason="Reaction Role")
                    except discord.Forbidden:
                        pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return
            
        if payload.message_id in self.rr_data:
            emoji_str = str(payload.emoji)
            if emoji_str in self.rr_data[payload.message_id]:
                guild = self.bot.get_guild(payload.guild_id)
                role = guild.get_role(self.rr_data[payload.message_id][emoji_str])
                member = guild.get_member(payload.user_id)
                if role and member:
                    try:
                        await member.remove_roles(role, reason="Reaction Role Removal")
                    except discord.Forbidden:
                        pass

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return
            
        custom_id = interaction.data.get("custom_id", "")
        if not custom_id.startswith("selfrole:"):
            return
            
        parts = custom_id.split(":")
        if len(parts) != 3:
            return
            
        mode, role_id_str = parts[1], parts[2]
        
        await interaction.response.defer(ephemeral=True)
        
        guild = interaction.guild
        if not guild:
            return
            
        try:
            role_id = int(role_id_str)
        except ValueError:
            return await interaction.followup.send("❌ Invalid role configuration.", ephemeral=True)
            
        role = guild.get_role(role_id)
        if not role:
            return await interaction.followup.send("❌ Role not found on this server.", ephemeral=True)
            
        if role >= guild.me.top_role:
            return await interaction.followup.send(f"❌ I cannot manage the role **{role.name}** because it is positioned higher than or equal to my bot role in the server hierarchy.", ephemeral=True)
            
        member = interaction.user
        if not isinstance(member, discord.Member):
            return
            
        has_role = any(r.id == role.id for r in member.roles)
        
        try:
            if mode == "toggle":
                if has_role:
                    await member.remove_roles(role, reason="Self role removal via button click")
                    await interaction.followup.send(f"◈ Removed role **{role.name}**.", ephemeral=True)
                else:
                    await member.add_roles(role, reason="Self role addition via button click")
                    await interaction.followup.send(f"◈ Added role **{role.name}**.", ephemeral=True)
            elif mode == "add":
                if has_role:
                    await interaction.followup.send(f"◈ You already have the **{role.name}** role.", ephemeral=True)
                else:
                    await member.add_roles(role, reason="Self role addition via button click")
                    await interaction.followup.send(f"◈ Added role **{role.name}**.", ephemeral=True)
            elif mode == "remove":
                if not has_role:
                    await interaction.followup.send(f"◈ You do not have the **{role.name}** role.", ephemeral=True)
                else:
                    await member.remove_roles(role, reason="Self role removal via button click")
                    await interaction.followup.send(f"◈ Removed role **{role.name}**.", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("❌ I lack permissions to manage roles. Please verify my permissions.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error occurred: {str(e)}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(ReactionRolesCog(bot))
