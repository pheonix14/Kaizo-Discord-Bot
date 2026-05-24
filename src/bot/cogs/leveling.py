import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
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
            
        # Get guild settings
        settings = await asyncio.to_thread(db_client.get_guild_settings, str(message.guild.id))
        if not settings.get("leveling_enabled", False):
            return
            
        # Get user's current level
        user_data = await asyncio.to_thread(db_client.get_xp, str(message.guild.id), str(message.author.id))
        user_level = user_data.get("level", 0)
        
        # Enforce Level-Based Action Permissions
        level_permissions = settings.get("level_permissions", [])
        if level_permissions:
            # Parse message content types
            has_image = len(message.attachments) > 0 or any(ext in message.content.lower() for ext in ['.png', '.jpg', '.jpeg', '.webp', '.tiff', '.bmp'])
            has_gif = 'tenor.com' in message.content.lower() or 'giphy.com' in message.content.lower() or '.gif' in message.content.lower()
            
            # Find the active rule for user's level (highest rule level <= user's level)
            sorted_rules = sorted(level_permissions, key=lambda x: x.get("level", 0))
            active_rule = None
            for r in sorted_rules:
                if r.get("level", 0) <= user_level:
                    active_rule = r
                else:
                    break
            
            if active_rule:
                allow_text = active_rule.get("allow_text", True)
                allow_image = active_rule.get("allow_image", True)
                allow_gif = active_rule.get("allow_gif", True)
                
                violated = False
                restriction_reason = ""
                if has_gif and not allow_gif:
                    violated = True
                    restriction_reason = "send GIFs"
                elif has_image and not allow_image:
                    violated = True
                    restriction_reason = "send Images/Embed links"
                elif not has_gif and not has_image and not allow_text:
                    violated = True
                    restriction_reason = "send Messages"
                
                if violated:
                    try:
                        await message.delete()
                        warn_embed = discord.Embed(
                            title="🚫 Action Restricted",
                            description=f"{message.author.mention}, your level is too low to {restriction_reason} in this server. (Current Level: **{user_level}**)",
                            color=discord.Color.red()
                        )
                        warn_msg = await message.channel.send(embed=warn_embed)
                        # Delete the warning message after a few seconds
                        await asyncio.sleep(5)
                        await warn_msg.delete()
                    except discord.Forbidden:
                        pass
                    except Exception:
                        pass
                    return  # Exit, do not award XP
            
        # Add random XP for messages
        xp_gain = random.randint(5, 15)
        
        # This adds XP and returns new stats and old level directly from DB
        result = await asyncio.to_thread(db_client.add_xp, str(message.guild.id), str(message.author.id), xp_gain)
        
        new_level = result["level"]
        old_level = result["old_level"]
        
        if new_level > old_level:
            # ECONOMY LINK: Give level * 500 coins as a reward
            reward = new_level * 500
            await asyncio.to_thread(db_client.add_economy_balance, str(message.guild.id), str(message.author.id), wallet_delta=reward)
            
            role_awarded_text = ""
            level_roles = settings.get("level_roles", {})
            role_id_str = level_roles.get(str(new_level))
            if role_id_str:
                try:
                    role = message.guild.get_role(int(role_id_str))
                    if role:
                        await message.author.add_roles(role, reason=f"Level up reward for Level {new_level}")
                        role_awarded_text = f"\n\n🏆 You have been awarded the **{role.name}** role!"
                except Exception as e:
                    role_awarded_text = f"\n\n⚠️ Failed to award level role reward: Role not found or missing bot permissions."
            
            try:
                embed = discord.Embed(
                    title="🎉 Level Up!", 
                    description=f"Congratulations {message.author.mention}, you reached level **{new_level}**!\n\nAs a reward, you received **{reward:,}** 🪙 coins!{role_awarded_text}", 
                    color=discord.Color.gold()
                )
                await message.channel.send(embed=embed)
            except discord.Forbidden:
                pass

    @commands.hybrid_command(name="rank", description="Check your or someone else's level and XP.")
    @app_commands.describe(member="The member to check")
    async def rank(self, ctx: commands.Context, member: discord.Member = None):
        member = member or ctx.author
        data = await asyncio.to_thread(db_client.get_xp, str(ctx.guild.id), str(member.id))
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
        result = await asyncio.to_thread(db_client.add_xp, str(ctx.guild.id), str(member.id), amount)
        new_xp = result["xp"]
        await ctx.send(embed=discord.Embed(description=f"✅ Gave **{amount}** XP to {member.mention}. They now have {new_xp} XP.", color=discord.Color.green()))

    @leveladmin.command(name="removexp", description="Remove XP from a member.")
    async def removexp(self, ctx: commands.Context, member: discord.Member, amount: int):
        current = await asyncio.to_thread(db_client.get_xp, str(ctx.guild.id), str(member.id))
        new_xp = max(0, current.get("xp", 0) - amount)
        new_level = self.calculate_level(new_xp)
        await asyncio.to_thread(db_client.set_xp, str(ctx.guild.id), str(member.id), new_xp, new_level)
        await ctx.send(embed=discord.Embed(description=f"✅ Removed **{amount}** XP from {member.mention}. They now have {new_xp} XP.", color=discord.Color.green()))

async def setup(bot: commands.Bot):
    await bot.add_cog(LevelingCog(bot))
