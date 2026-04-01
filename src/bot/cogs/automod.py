import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from src.db import client as db_client
from src import config

class AutomodHelpView(discord.ui.View):
    def __init__(self, author_id: int):
        super().__init__(timeout=60.0)
        self.author_id = author_id
        self.current_page = 0
        
        self.pages = [
            # Page 1
            {
                "title": "[SHIELD] Kaizo - Anti-Nuke Status & Logs (Page 1/3)",
                "description": "Monitor and log anti-nuke protection alerts.",
                "fields": [
                    {"name": "• automod_status", "value": "Checks the bot protection status for the server.\n*Usage:* `.automod_status` or `/automod_status`"},
                    {"name": "• automod_logs", "value": "Gets the recent anti-nuke actions for this server.\n*Usage:* `.automod_logs` or `/automod_logs`"}
                ]
            },
            # Page 2
            {
                "title": "[SHIELD] Kaizo - Whitelist Configuration (Page 2/3)",
                "description": "Manage users immune to anti-nuke enforcement.",
                "fields": [
                    {"name": "• automod_whitelist <member> [reason]", "value": "Whitelists a user, making them immune to anti-nuke actions.\n*Usage:* `.automod_whitelist @User [reason]` or `/automod_whitelist member:@User reason:[reason]`"},
                    {"name": "• automod_unwhitelist <member>", "value": "Removes a user from the whitelist.\n*Usage:* `.automod_unwhitelist @User` or `/automod_unwhitelist member:@User`"}
                ]
            },
            # Page 3
            {
                "title": "[SHIELD] Kaizo - K4 Defense System (Page 3/3)",
                "description": "Advanced anti-spam and anti-raid parameters.",
                "fields": [
                    {"name": "• k4defence enable", "value": "Enable the K4 Defense anti-spam/anti-raid system.\n*Usage:* `.k4defence enable` or `/k4defence enable`"},
                    {"name": "• k4defence disable", "value": "Disable the K4 Defense anti-spam/anti-raid system.\n*Usage:* `.k4defence disable` or `/k4defence disable`"},
                    {"name": "• k4defence status", "value": "Check the status and logs of the K4 Defense system.\n*Usage:* `.k4defence status` or `/k4defence status`"}
                ]
            }
        ]

    def make_embed(self) -> discord.Embed:
        page_data = self.pages[self.current_page]
        embed = discord.Embed(
            title=page_data["title"],
            description=page_data["description"],
            color=0x3B82F6
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

class AutomodCog(commands.Cog, name="Automod"):
    """Security and Anti-Nuke commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="automod", description="Show AutoMod & Security configuration help.")
    async def automod_command(self, ctx: commands.Context):
        view = AutomodHelpView(ctx.author.id)
        msg = await ctx.send(embed=view.make_embed(), view=view)
        view.message = msg

    @commands.hybrid_command(name="automod_status", description="Checks the bot protection status for the server.")
    @commands.has_permissions(manage_guild=True)
    async def automod_status(self, ctx: commands.Context):
        settings = await asyncio.to_thread(db_client.get_guild_settings, ctx.guild.id, ctx.guild.name)
        status_emoji = "Active" if settings.get("is_active") else "Disabled"
        
        embed = discord.Embed(title="Kaizo Security Engine Status", color=discord.Color.blue())
        embed.add_field(name="Protection Status", value=status_emoji, inline=False)
        embed.add_field(name="Anti-Ban Threshold", value=f"{settings.get('anti_ban_limit')} bans / {settings.get('anti_ban_time_frame')}s", inline=True)
        embed.add_field(name="Anti-Kick Threshold", value=f"{settings.get('anti_kick_limit')} kicks / {settings.get('anti_kick_time_frame')}s", inline=True)
        embed.add_field(name="Anti-Channel Deletions", value=f"{settings.get('anti_channel_delete_limit')} channels / {settings.get('anti_channel_delete_time_frame')}s", inline=True)
        embed.add_field(name="Anti-Role Deletions", value=f"{settings.get('anti_role_delete_limit')} roles / {settings.get('anti_role_delete_time_frame')}s", inline=True)
        embed.add_field(name="Anti-Bot Invitation", value="Enabled" if settings.get("anti_bot_add") else "Disabled", inline=True)
        
        embed.set_footer(text="Project Kaizo • Protected by Supabase")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="automod_whitelist", description="Whitelists a user, making them immune to anti-nuke actions.")
    @app_commands.describe(member="The user to whitelist", reason="Reason for whitelist")
    @commands.has_permissions(manage_guild=True)
    async def automod_whitelist(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        if member.bot:
            return await ctx.send("Bots cannot be whitelisted.")
            
        success = await asyncio.to_thread(db_client.add_to_whitelist, guild_id=ctx.guild.id, 
            user_id=member.id, 
            reason=reason,
            executor_tag=str(ctx.author))
        if success:
            await ctx.send(embed=discord.Embed(description=f"[OK] Successfully whitelisted **{member.name}**. Reason: {reason}", color=discord.Color.green()))
        else:
            await ctx.send("Failed to whitelist user in the database.")

    @commands.hybrid_command(name="automod_unwhitelist", description="Removes a user from the whitelist.")
    @app_commands.describe(member="The user to unwhitelist")
    @commands.has_permissions(manage_guild=True)
    async def automod_unwhitelist(self, ctx: commands.Context, member: discord.Member):
        success = await asyncio.to_thread(db_client.remove_from_whitelist, guild_id=ctx.guild.id, user_id=member.id)
        if success:
            await ctx.send(embed=discord.Embed(description=f"[OK] Successfully removed **{member.name}** from the whitelist.", color=discord.Color.green()))
        else:
            await ctx.send("Failed to remove user from the whitelist.")

    @commands.hybrid_command(name="automod_logs", description="Gets the recent anti-nuke actions for this server.")
    @commands.has_permissions(manage_guild=True)
    async def automod_logs(self, ctx: commands.Context):
        logs = await asyncio.to_thread(db_client.get_protection_logs, ctx.guild.id, limit=5)
        if not logs:
            return await ctx.send("No protection events logged for this server yet.")
            
        embed = discord.Embed(title="Recent Security Incidents", color=discord.Color.orange())
        for log in logs:
            time_str = log.get("created_at", "Unknown").split(".")[0].replace("T", " ")
            details = (
                f"**Event**: {log.get('event_type')}\n"
                f"**Executor**: {log.get('executor_tag')} ({log.get('executor_id')})\n"
                f"**Action Taken**: {log.get('action_taken')}\n"
                f"**Details**: {log.get('details')}\n"
                f"**Time (UTC)**: {time_str}"
            )
            embed.add_field(name=f"Incident ID: {log.get('id')[:8]}...", value=details, inline=False)
            
        embed.set_footer(text="Project Kaizo • Real-time Logs")
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(AutomodCog(bot))
