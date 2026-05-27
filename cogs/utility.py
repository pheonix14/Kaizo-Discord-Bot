import disnake
from disnake.ext import commands
import time
import datetime

class Utility(commands.Cog):
    """
    Utility and Developer commands for KAIZER X.
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="uptime", description="Shows how long the bot has been online.")
    async def uptime(self, inter: disnake.ApplicationCommandInteraction):
        """
        Calculates and displays the bot's uptime without using emojis.
        """
        current_time = time.time()
        difference = int(round(current_time - self.bot.start_time))
        text = str(datetime.timedelta(seconds=difference))
        
        embed = disnake.Embed(
            title="SYSTEM UPTIME",
            description=f"Online for: **{text}**",
            color=0x2b2d31 # Premium dark theme color
        )
        await inter.response.send_message(embed=embed)

    @commands.slash_command(name="dev", description="Developer utilities.")
    async def dev(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @dev.sub_command(name="id", description="Shows Channel ID, User ID, and Server ID.")
    async def dev_id(self, inter: disnake.ApplicationCommandInteraction):
        """
        Shows the current Channel ID, Server ID, and the User's ID.
        """
        embed = disnake.Embed(
            title="DEVELOPER INFORMATION",
            color=0x2b2d31
        )
        embed.add_field(name="User ID", value=f"`{inter.author.id}`", inline=False)
        embed.add_field(name="Channel ID", value=f"`{inter.channel.id}`", inline=False)
        embed.add_field(name="Server ID", value=f"`{inter.guild.id if inter.guild else 'N/A'}`", inline=False)
        await inter.response.send_message(embed=embed, ephemeral=True)

    @commands.slash_command(name="serverinfo", description="Displays information about the current server.")
    async def serverinfo(self, inter: disnake.ApplicationCommandInteraction):
        """
        Displays statistics and information about the server.
        """
        if not inter.guild:
            await inter.response.send_message("This command can only be used inside a server.", ephemeral=True)
            return
            
        guild = inter.guild
        embed = disnake.Embed(
            title=f"SERVER INFO: {guild.name.upper()}",
            color=0x2b2d31
        )
        embed.add_field(name="Server ID", value=f"`{guild.id}`", inline=True)
        embed.add_field(name="Owner", value=f"{guild.owner.name if guild.owner else 'Unknown'}", inline=True)
        embed.add_field(name="Member Count", value=f"{guild.member_count}", inline=True)
        embed.add_field(name="Created On", value=f"{guild.created_at.strftime('%Y-%m-%d')}", inline=False)
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
            
        await inter.response.send_message(embed=embed)

def setup(bot):
    bot.add_cog(Utility(bot))
