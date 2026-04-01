import discord
from discord.ext import commands
from discord import app_commands
import datetime

class ModerationHelpView(discord.ui.View):
    def __init__(self, author_id: int):
        super().__init__(timeout=60.0)
        self.author_id = author_id
        self.current_page = 0
        
        self.pages = [
            # Page 1
            {
                "title": "[SHIELD] Kaizo - Member Discipline (Page 1/4)",
                "description": "Administrative member moderation commands. Requires appropriate moderator permissions.",
                "fields": [
                    {"name": "• kick <member> [reason]", "value": "Kick a member from the server.\n*Permissions Required:* `Kick Members` or Admin role.\n*Usage:* `.kick @User spamming` or `/kick member:@User reason:spamming`"},
                    {"name": "• ban <member> [reason]", "value": "Ban a member from the server.\n*Permissions Required:* `Ban Members` or Admin role.\n*Usage:* `.ban @User raid` or `/ban member:@User reason:raid`"},
                    {"name": "• unban <user_id> [reason]", "value": "Unban a user from the server by their ID.\n*Permissions Required:* `Ban Members` or Admin role.\n*Usage:* `.unban 1234567890 appeal` or `/unban user_id:1234567890 reason:appeal`"}
                ]
            },
            # Page 2
            {
                "title": "[TIME] Kaizo - Timeouts & Mutes (Page 2/4)",
                "description": "Temporary member restriction commands.",
                "fields": [
                    {"name": "• timeout <member> <minutes> [reason]", "value": "Timeout/Mute a member temporarily.\n*Permissions Required:* `Moderate Members` or Admin/Mod role.\n*Usage:* `.timeout @User 10 toxic` or `/timeout member:@User minutes:10 reason:toxic`"},
                    {"name": "• untimeout <member> [reason]", "value": "Remove a timeout from a member.\n*Permissions Required:* `Moderate Members` or Admin/Mod role.\n*Usage:* `.untimeout @User` or `/untimeout member:@User`"}
                ]
            },
            # Page 3
            {
                "title": "[CHAT] Kaizo - Channel Protection (Page 3/4)",
                "description": "Manage channels, slowmode, and message purging.",
                "fields": [
                    {"name": "• purge <amount>", "value": "Delete multiple messages in the channel (max 100).\n*Permissions Required:* `Manage Messages` or Admin/Mod role.\n*Usage:* `.purge 50` or `/purge amount:50`"},
                    {"name": "• lock", "value": "Lock the current channel to prevent members from sending messages.\n*Permissions Required:* `Manage Channels` or Admin role.\n*Usage:* `.lock` or `/lock`"},
                    {"name": "• unlock", "value": "Unlock the current channel.\n*Permissions Required:* `Manage Channels` or Admin role.\n*Usage:* `.unlock` or `/unlock`"},
                    {"name": "• slowmode <seconds>", "value": "Set a slowmode delay for the current channel.\n*Permissions Required:* `Manage Channels` or Admin role.\n*Usage:* `.slowmode 5` or `/slowmode seconds:5`"}
                ]
            },
            # Page 4
            {
                "title": "[LOCKED] Kaizo - Security & AutoMod (Page 4/4)",
                "description": "Server protection and anti-nuke tools.",
                "fields": [
                    {"name": "• automod_status", "value": "Checks the bot protection settings/status for the server.\n*Permissions Required:* `Manage Server` or Admin role.\n*Usage:* `.automod_status` or `/automod_status`"},
                    {"name": "• automod_whitelist <member> [reason]", "value": "Whitelist a user, making them immune to anti-nuke protections.\n*Permissions Required:* `Manage Server` or Admin role.\n*Usage:* `.automod_whitelist @User trusted` or `/automod_whitelist member:@User`"},
                    {"name": "• automod_unwhitelist <member>", "value": "Remove a user from the anti-nuke whitelist.\n*Permissions Required:* `Manage Server` or Admin role.\n*Usage:* `.automod_unwhitelist @User` or `/automod_unwhitelist member:@User`"},
                    {"name": "• automod_logs", "value": "Fetch the 5 most recent anti-nuke/security incidents.\n*Permissions Required:* `Manage Server` or Admin role.\n*Usage:* `.automod_logs` or `/automod_logs`"},
                    {"name": "• k4defence <enable/disable/status>", "value": "Manage advanced anti-spam & anti-raid system.\n*Permissions Required:* `Administrator`.\n*Usage:* `.k4defence status` or `/k4defence status`"}
                ]
            }
        ]

    def make_embed(self) -> discord.Embed:
        page_data = self.pages[self.current_page]
        embed = discord.Embed(
            title=page_data["title"],
            description=page_data["description"],
            color=0xE74C3C
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
        # Disable all buttons on timeout
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


class ModerationCog(commands.Cog, name="Moderation"):
    """Commands for server moderators."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_group(name="mod", aliases=["moderation"], description="Moderation commands.", fallback="help")
    async def mod(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            view = ModerationHelpView(ctx.author.id)
            msg = await ctx.send(embed=view.make_embed(), view=view)
            view.message = msg

    @commands.hybrid_command(name="kick", description="Kick a member from the server.")
    @commands.has_permissions(kick_members=True)
    @app_commands.describe(member="The member to kick", reason="The reason for kicking")
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.send("You cannot kick someone with a higher or equal role than you.")
        try:
            await member.kick(reason=reason)
            await ctx.send(embed=discord.Embed(description=f"[OK] Kicked **{member}**. Reason: {reason}", color=discord.Color.orange()))
        except discord.Forbidden:
            await ctx.send("I do not have permission to kick that member.")

    @commands.hybrid_command(name="ban", description="Ban a member from the server.")
    @commands.has_permissions(ban_members=True)
    @app_commands.describe(member="The member to ban", reason="The reason for banning")
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.send("You cannot ban someone with a higher or equal role than you.")
        try:
            await member.ban(reason=reason)
            await ctx.send(embed=discord.Embed(description=f"[OK] Banned **{member}**. Reason: {reason}", color=discord.Color.red()))
        except discord.Forbidden:
            await ctx.send("I do not have permission to ban that member.")

    @commands.hybrid_command(name="unban", description="Unban a user by their ID.")
    @commands.has_permissions(ban_members=True)
    @app_commands.describe(user_id="The ID of the user to unban", reason="The reason for unbanning")
    async def unban(self, ctx: commands.Context, user_id: str, *, reason: str = "No reason provided"):
        try:
            user = await self.bot.fetch_user(int(user_id))
            await ctx.guild.unban(user, reason=reason)
            await ctx.send(embed=discord.Embed(description=f"[OK] Unbanned **{user}**. Reason: {reason}", color=discord.Color.green()))
        except ValueError:
            await ctx.send("Please provide a valid user ID.")
        except discord.NotFound:
            await ctx.send("That user is not banned.")
        except discord.Forbidden:
            await ctx.send("I do not have permission to unban users.")

    @commands.hybrid_command(name="timeout", description="Timeout a member.")
    @commands.has_permissions(moderate_members=True)
    @app_commands.describe(member="The member to timeout", minutes="Duration in minutes", reason="The reason")
    async def timeout(self, ctx: commands.Context, member: discord.Member, minutes: int, *, reason: str = "No reason provided"):
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.send("You cannot timeout someone with a higher or equal role than you.")
        duration = datetime.timedelta(minutes=minutes)
        try:
            await member.timeout(duration, reason=reason)
            await ctx.send(embed=discord.Embed(description=f"[OK] Timed out **{member}** for {minutes}m. Reason: {reason}", color=discord.Color.orange()))
        except discord.Forbidden:
            await ctx.send("I do not have permission to timeout that member.")

    @commands.hybrid_command(name="untimeout", description="Remove a timeout from a member.")
    @commands.has_permissions(moderate_members=True)
    @app_commands.describe(member="The member to remove timeout from", reason="The reason")
    async def untimeout(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason provided"):
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.send("You cannot manage this user.")
        try:
            await member.timeout(None, reason=reason)
            await ctx.send(embed=discord.Embed(description=f"[OK] Removed timeout from **{member}**. Reason: {reason}", color=discord.Color.green()))
        except discord.Forbidden:
            await ctx.send("I do not have permission to remove timeout from that member.")

    @commands.hybrid_command(name="purge", description="Delete multiple messages in a channel.")
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(amount="Number of messages to delete")
    async def purge(self, ctx: commands.Context, amount: int):
        if amount <= 0 or amount > 100:
            return await ctx.send("Please specify an amount between 1 and 100.")
        deleted = await ctx.channel.purge(limit=amount + 1)  # +1 to include the command message
        await ctx.send(embed=discord.Embed(description=f"[OK] Deleted {len(deleted)-1} messages.", color=discord.Color.green()), delete_after=5)

    @commands.hybrid_command(name="lock", description="Lock the current channel.")
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx: commands.Context):
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(embed=discord.Embed(description="[LOCKED] Channel locked.", color=discord.Color.red()))

    @commands.hybrid_command(name="unlock", description="Unlock the current channel.")
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx: commands.Context):
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = None
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(embed=discord.Embed(description="[UNLOCKED] Channel unlocked.", color=discord.Color.green()))

    @commands.hybrid_command(name="slowmode", description="Set the slowmode delay for the channel.")
    @commands.has_permissions(manage_channels=True)
    @app_commands.describe(seconds="Delay in seconds")
    async def slowmode(self, ctx: commands.Context, seconds: int):
        if seconds < 0 or seconds > 21600:
            return await ctx.send("Slowmode must be between 0 and 21600 seconds.")
        await ctx.channel.edit(slowmode_delay=seconds)
        await ctx.send(embed=discord.Embed(description=f"[OK] Slowmode set to {seconds} seconds.", color=discord.Color.blue()))

async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationCog(bot))
