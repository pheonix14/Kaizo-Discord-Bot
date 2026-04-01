import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from src.db import client as db_client

class LoggingHelpView(discord.ui.View):
    def __init__(self, author_id: int):
        super().__init__(timeout=60.0)
        self.author_id = author_id
        self.current_page = 0
        
        self.pages = [
            # Page 1
            {
                "title": "[DOC] Kaizo - Server Event Logs (Page 1/2)",
                "description": "Configure channels to track server occurrences dynamically.",
                "fields": [
                    {"name": "• config logs <channel>", "value": "Configure a logging channel for server events (e.g. invites, member updates, role creations).\n"
                                                                "*Usage:* `.config logs #mod-logs` or `/config logs channel:#mod-logs`"},
                    {"name": "• Logged Actions", "value": "Once a channel is assigned, Kaizo records member joins/leaves, role edits, message deletions, and server configurations."}
                ]
            },
            # Page 2
            {
                "title": "[ALERT] Kaizo - AutoMod & Modlogs (Page 2/2)",
                "description": "Incident history and security logging.",
                "fields": [
                    {"name": "• automod_logs", "value": "Fetch the 5 most recent anti-nuke / security logs.\n*Usage:* `.automod_logs` or `/automod_logs`"},
                    {"name": "• Modlog Channel", "value": "Used by the AutoMod/Security system to print warnings, permanent mutes (K4 Defence), and administrative blocks. Setup is managed via the dashboard."}
                ]
            }
        ]

    def make_embed(self) -> discord.Embed:
        page_data = self.pages[self.current_page]
        embed = discord.Embed(
            title=page_data["title"],
            description=page_data["description"],
            color=0x34495E
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


class AdminCog(commands.Cog, name="Admin"):
    """Server configuration and admin commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="logging", aliases=["logs", "log"], description="Show server logging configurations & help.")
    async def logging_command(self, ctx: commands.Context):
        view = LoggingHelpView(ctx.author.id)
        msg = await ctx.send(embed=view.make_embed(), view=view)
        view.message = msg

    @commands.hybrid_group(name="config", description="Configure server settings.", fallback="help")
    @commands.has_permissions(manage_guild=True)
    async def config_group(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @config_group.command(name="adminrole", description="Set a role that grants admin-level bot access.")
    @app_commands.describe(role="The role to set as admin role")
    async def config_adminrole(self, ctx: commands.Context, role: discord.Role):
        await asyncio.to_thread(db_client.update_guild_settings, ctx.guild.id, {"admin_role_id": str(role.id)})
        await ctx.send(embed=discord.Embed(description=f"[OK] Admin role set to {role.mention}", color=discord.Color.green()))

    @config_group.command(name="autorole", description="Add an auto-role given to new members on join.")
    @app_commands.describe(action="Add or remove", role="The role to manage")
    async def config_autorole(self, ctx: commands.Context, action: str, role: discord.Role):
        action = action.lower()
        if action not in ["add", "remove"]:
            return await ctx.send("Action must be 'add' or 'remove'.")
        
        settings = await asyncio.to_thread(db_client.get_guild_settings, ctx.guild.id)
        auto_roles = settings.get("auto_roles", [])
        
        if action == "add":
            if str(role.id) not in auto_roles:
                auto_roles.append(str(role.id))
                await asyncio.to_thread(db_client.update_guild_settings, ctx.guild.id, {"auto_roles": auto_roles})
                await ctx.send(embed=discord.Embed(description=f"[OK] Auto-role {role.mention} added.", color=discord.Color.green()))
            else:
                await ctx.send("That role is already in the auto-role list.")
        else:
            if str(role.id) in auto_roles:
                auto_roles.remove(str(role.id))
                await asyncio.to_thread(db_client.update_guild_settings, ctx.guild.id, {"auto_roles": auto_roles})
                await ctx.send(embed=discord.Embed(description=f"[OK] Auto-role {role.mention} removed.", color=discord.Color.green()))
            else:
                await ctx.send("That role is not in the auto-role list.")

    @config_group.command(name="boosterrole", description="Set a special role given to server boosters.")
    @app_commands.describe(role="The booster role")
    async def config_boosterrole(self, ctx: commands.Context, role: discord.Role):
        await asyncio.to_thread(db_client.update_guild_settings, ctx.guild.id, {"booster_role_id": str(role.id)})
        await ctx.send(embed=discord.Embed(description=f"[OK] Booster role set to {role.mention}", color=discord.Color.green()))

    @config_group.command(name="currency", description="Customize the economy currency name and emoji.")
    @app_commands.describe(name="Currency name", emoji="Currency emoji")
    async def config_currency(self, ctx: commands.Context, name: str, emoji: str):
        await asyncio.to_thread(db_client.update_guild_settings, ctx.guild.id, {"currency_name": name, "currency_emoji": emoji})
        await ctx.send(embed=discord.Embed(description=f"[OK] Currency updated to {emoji} **{name}**", color=discord.Color.green()))

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
        await asyncio.to_thread(db_client.update_guild_settings, ctx.guild.id, {"prefix": combined})
        await ctx.send(embed=discord.Embed(
            description=f"[OK] Server prefix(es) updated to: " + ", ".join(f"`{p}`" for p in prefixes),
            color=discord.Color.green()
        ))

    @commands.hybrid_command(name="prefix", description="Change or view custom prefixes for this server. Supports multiple prefixes separated by commas.")
    @commands.has_permissions(manage_guild=True)
    @app_commands.describe(new_prefixes="New prefixes separated by commas, or leave empty to view current prefixes")
    async def prefix_command(self, ctx: commands.Context, *, new_prefixes: str = None):
        if new_prefixes is None:
            settings = await asyncio.to_thread(db_client.get_guild_settings, ctx.guild.id)
            current = settings.get("prefix", "k!")
            return await ctx.send(embed=discord.Embed(
                description=f"ℹ Current prefix(es) for this server: `{current}`\n"
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
        await asyncio.to_thread(db_client.update_guild_settings, ctx.guild.id, {"prefix": combined})
        
        await ctx.send(embed=discord.Embed(
            description=f"[OK] Server prefix(es) updated to: " + ", ".join(f"`{p}`" for p in prefixes),
            color=discord.Color.green()
        ))

    @config_group.command(name="logs", description="Set the channel for logging server events.")
    @app_commands.describe(channel="The channel for logs")
    async def config_logs(self, ctx: commands.Context, channel: discord.TextChannel):
        await asyncio.to_thread(db_client.update_guild_settings, ctx.guild.id, {"log_channel_id": str(channel.id)})
        await ctx.send(embed=discord.Embed(description=f"[OK] Log channel set to {channel.mention}", color=discord.Color.green()))

    @config_group.command(name="levels", description="Toggle the leveling system.")
    @app_commands.describe(state="Enable or disable")
    async def config_levels(self, ctx: commands.Context, state: bool):
        await asyncio.to_thread(db_client.update_guild_settings, ctx.guild.id, {"leveling_enabled": state})
        await ctx.send(embed=discord.Embed(description=f"[OK] Leveling system set to **{state}**", color=discord.Color.green()))

    @config_group.command(name="welcome", description="Configure the welcome channel.")
    @app_commands.describe(channel="The channel for welcome messages")
    async def config_welcome(self, ctx: commands.Context, channel: discord.TextChannel):
        await asyncio.to_thread(db_client.update_guild_settings, ctx.guild.id, {"welcome_channel_id": str(channel.id)})
        await ctx.send(embed=discord.Embed(description=f"[OK] Welcome channel set to {channel.mention}", color=discord.Color.green()))

    @config_group.command(name="leave", description="Configure the leave channel.")
    @app_commands.describe(channel="The channel for leave messages")
    async def config_leave(self, ctx: commands.Context, channel: discord.TextChannel):
        await asyncio.to_thread(db_client.update_guild_settings, ctx.guild.id, {"leave_channel_id": str(channel.id)})
        await ctx.send(embed=discord.Embed(description=f"[OK] Leave channel set to {channel.mention}", color=discord.Color.green()))

async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))
