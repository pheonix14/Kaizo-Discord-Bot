import discord
from discord.ext import commands
from discord import app_commands
import random
from src.db import client as db_client

class LevelingCog(commands.Cog, name="Leveling"):
    """Leveling system commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def calculate_level(self, xp: int) -> int:
        # Simple formula: level = (xp / 100) ^ 0.5
        return int((xp / 100.0) ** 0.5)

    def xp_for_next_level(self, level: int) -> int:
        # xp = 100 * (level ^ 2)
        return 100 * ((level + 1) ** 2)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
            
        # Add random XP for messages
        xp_gain = random.randint(5, 15)
        
        # This adds XP and returns new stats and old level directly from DB
        result = db_client.add_xp(str(message.guild.id), str(message.author.id), xp_gain)
        
        new_level = result["level"]
        old_level = result["old_level"]
        
        if new_level > old_level:
            # ECONOMY LINK: Give level * 500 coins as a reward
            reward = new_level * 500
            db_client.add_economy_balance(str(message.guild.id), str(message.author.id), wallet_delta=reward)
            
            try:
                embed = discord.Embed(
                    title="🎉 Level Up!", 
                    description=f"Congratulations {message.author.mention}, you reached level **{new_level}**!\n\nAs a reward, you received **{reward:,}** 🪙 coins!", 
                    color=discord.Color.gold()
                )
                await message.channel.send(embed=embed)
            except discord.Forbidden:
                pass

    @commands.hybrid_command(name="rank", description="Check your or someone else's level and XP.")
    @app_commands.describe(member="The member to check")
    async def rank(self, ctx: commands.Context, member: discord.Member = None):
        member = member or ctx.author
        data = db_client.get_xp(str(ctx.guild.id), str(member.id))
        xp = data.get("xp", 0)
        level = data.get("level", 0)
        next_xp = self.xp_for_next_level(level)
        
        embed = discord.Embed(title=f"{member.display_name}'s Rank", color=0x3498DB)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Level", value=str(level), inline=True)
        embed.add_field(name="XP", value=f"{xp:,} / {next_xp:,}", inline=True)
        # Progress bar
        if next_xp == 0: progress = 1.0
        else: progress = xp / next_xp
        filled = int(progress * 10)
        bar = "█" * filled + "░" * (10 - filled)
        embed.add_field(name="Progress", value=f"`{bar}` ({int(progress*100)}%)", inline=False)
        
        await ctx.send(embed=embed)

    @commands.hybrid_group(name="leveladmin", description="Admin leveling commands.")
    @commands.has_permissions(administrator=True)
    async def leveladmin(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @leveladmin.command(name="givexp", description="Give XP to a member.")
    async def givexp(self, ctx: commands.Context, member: discord.Member, amount: int):
        result = db_client.add_xp(str(ctx.guild.id), str(member.id), amount)
        new_xp = result["xp"]
        await ctx.send(embed=discord.Embed(description=f"✅ Gave **{amount}** XP to {member.mention}. They now have {new_xp} XP.", color=discord.Color.green()))

    @leveladmin.command(name="removexp", description="Remove XP from a member.")
    async def removexp(self, ctx: commands.Context, member: discord.Member, amount: int):
        current = db_client.get_xp(str(ctx.guild.id), str(member.id))
        new_xp = max(0, current.get("xp", 0) - amount)
        new_level = self.calculate_level(new_xp)
        db_client.set_xp(str(ctx.guild.id), str(member.id), new_xp, new_level)
        await ctx.send(embed=discord.Embed(description=f"✅ Removed **{amount}** XP from {member.mention}. They now have {new_xp} XP.", color=discord.Color.green()))

async def setup(bot: commands.Bot):
    await bot.add_cog(LevelingCog(bot))
