import discord
from discord.ext import commands
from discord import app_commands
from src.db import client as db_client

class AdminCog(commands.Cog, name="Admin"):
    """Server configuration and admin commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_group(name="config", description="Configure server settings.", fallback="help")
    @commands.has_permissions(manage_guild=True)
    async def config_group(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @config_group.command(name="adminrole", description="Set a role that grants admin-level bot access.")
    @app_commands.describe(role="The role to set as admin role")
    async def config_adminrole(self, ctx: commands.Context, role: discord.Role):
        db_client.update_guild_settings(ctx.guild.id, {"admin_role_id": str(role.id)})
        await ctx.send(embed=discord.Embed(description=f"✅ Admin role set to {role.mention}", color=discord.Color.green()))

    @config_group.command(name="autorole", description="Add an auto-role given to new members on join.")
    @app_commands.describe(action="Add or remove", role="The role to manage")
    async def config_autorole(self, ctx: commands.Context, action: str, role: discord.Role):
        action = action.lower()
        if action not in ["add", "remove"]:
            return await ctx.send("Action must be 'add' or 'remove'.")
        
        settings = db_client.get_guild_settings(ctx.guild.id)
        auto_roles = settings.get("auto_roles", [])
        
        if action == "add":
            if str(role.id) not in auto_roles:
                auto_roles.append(str(role.id))
                db_client.update_guild_settings(ctx.guild.id, {"auto_roles": auto_roles})
                await ctx.send(embed=discord.Embed(description=f"✅ Auto-role {role.mention} added.", color=discord.Color.green()))
            else:
                await ctx.send("That role is already in the auto-role list.")
        else:
            if str(role.id) in auto_roles:
                auto_roles.remove(str(role.id))
                db_client.update_guild_settings(ctx.guild.id, {"auto_roles": auto_roles})
                await ctx.send(embed=discord.Embed(description=f"✅ Auto-role {role.mention} removed.", color=discord.Color.green()))
            else:
                await ctx.send("That role is not in the auto-role list.")

    @config_group.command(name="boosterrole", description="Set a special role given to server boosters.")
    @app_commands.describe(role="The booster role")
    async def config_boosterrole(self, ctx: commands.Context, role: discord.Role):
        db_client.update_guild_settings(ctx.guild.id, {"booster_role_id": str(role.id)})
        await ctx.send(embed=discord.Embed(description=f"✅ Booster role set to {role.mention}", color=discord.Color.green()))

    @config_group.command(name="currency", description="Customize the economy currency name and emoji.")
    @app_commands.describe(name="Currency name", emoji="Currency emoji")
    async def config_currency(self, ctx: commands.Context, name: str, emoji: str):
        db_client.update_guild_settings(ctx.guild.id, {"currency_name": name, "currency_emoji": emoji})
        await ctx.send(embed=discord.Embed(description=f"✅ Currency updated to {emoji} **{name}**", color=discord.Color.green()))

    @config_group.command(name="prefix", description="Set one or more custom prefixes for the server (comma-separated).")
    @app_commands.describe(new_prefix="New prefix(es) separated by commas")
    async def config_prefix(self, ctx: commands.Context, new_prefix: str):
        prefixes = [p.strip() for p in new_prefix.split(",") if p.strip()]
        if not prefixes:
            return await ctx.send("Please provide at least one valid prefix.")
        for p in prefixes:
            if len(p) > 10:
                return await ctx.send("Each prefix must be 10 characters or less.")
        combined = ", ".join(prefixes)
        db_client.update_guild_settings(ctx.guild.id, {"prefix": combined})
        await ctx.send(embed=discord.Embed(
            description=f"✅ Server prefix(es) updated to: " + ", ".join(f"`{p}`" for p in prefixes),
            color=discord.Color.green()
        ))

    @commands.hybrid_command(name="prefix", description="Change or view custom prefixes for this server. Supports multiple prefixes separated by commas.")
    @commands.has_permissions(manage_guild=True)
    @app_commands.describe(new_prefixes="New prefixes separated by commas, or leave empty to view current prefixes")
    async def prefix_command(self, ctx: commands.Context, *, new_prefixes: str = None):
        if new_prefixes is None:
            settings = db_client.get_guild_settings(ctx.guild.id)
            current = settings.get("prefix", "k!")
            return await ctx.send(embed=discord.Embed(
                description=f"ℹ️ Current prefix(es) for this server: `{current}`\n"
                            f"You can change them by running `{ctx.prefix}prefix <prefix1, prefix2, ...>`",
                color=discord.Color.blue()
            ))
            
        # Parse new prefixes
        prefixes = [p.strip() for p in new_prefixes.split(",") if p.strip()]
        if not prefixes:
            return await ctx.send("Please provide at least one valid prefix.")
            
        for p in prefixes:
            if len(p) > 10:
                return await ctx.send("Each prefix must be 10 characters or less.")
                
        combined = ", ".join(prefixes)
        db_client.update_guild_settings(ctx.guild.id, {"prefix": combined})
        
        await ctx.send(embed=discord.Embed(
            description=f"✅ Server prefix(es) updated to: " + ", ".join(f"`{p}`" for p in prefixes),
            color=discord.Color.green()
        ))

    @config_group.command(name="logs", description="Set the channel for logging server events.")
    @app_commands.describe(channel="The channel for logs")
    async def config_logs(self, ctx: commands.Context, channel: discord.TextChannel):
        db_client.update_guild_settings(ctx.guild.id, {"log_channel_id": str(channel.id)})
        await ctx.send(embed=discord.Embed(description=f"✅ Log channel set to {channel.mention}", color=discord.Color.green()))

    @config_group.command(name="levels", description="Toggle the leveling system.")
    @app_commands.describe(state="Enable or disable")
    async def config_levels(self, ctx: commands.Context, state: bool):
        db_client.update_guild_settings(ctx.guild.id, {"leveling_enabled": state})
        await ctx.send(embed=discord.Embed(description=f"✅ Leveling system set to **{state}**", color=discord.Color.green()))

    @config_group.command(name="welcome", description="Configure the welcome channel.")
    @app_commands.describe(channel="The channel for welcome messages")
    async def config_welcome(self, ctx: commands.Context, channel: discord.TextChannel):
        db_client.update_guild_settings(ctx.guild.id, {"welcome_channel_id": str(channel.id)})
        await ctx.send(embed=discord.Embed(description=f"✅ Welcome channel set to {channel.mention}", color=discord.Color.green()))

    @config_group.command(name="leave", description="Configure the leave channel.")
    @app_commands.describe(channel="The channel for leave messages")
    async def config_leave(self, ctx: commands.Context, channel: discord.TextChannel):
        db_client.update_guild_settings(ctx.guild.id, {"leave_channel_id": str(channel.id)})
        await ctx.send(embed=discord.Embed(description=f"✅ Leave channel set to {channel.mention}", color=discord.Color.green()))

async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))
