import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio

class GiveawaysCog(commands.Cog, name="Giveaways"):
    """Giveaway system commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.active_giveaways = {}

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

        embed = discord.Embed(title="🎉 GIVEAWAY 🎉", description=f"**Prize:** {prize}\n**Winners:** {winners}\n**Hosted by:** {ctx.author.mention}\n**Ends in:** <t:{int(discord.utils.utcnow().timestamp()) + duration}:R>", color=0x9B59B6)
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("🎉")
        
        self.active_giveaways[msg.id] = {
            "channel_id": ctx.channel.id,
            "winners": winners,
            "prize": prize,
            "host": ctx.author.mention
        }
        
        # Simple non-persistent timer for demo
        self.bot.loop.create_task(self._end_giveaway(msg.id, duration))

    async def _end_giveaway(self, message_id: int, duration: int):
        await asyncio.sleep(duration)
        if message_id not in self.active_giveaways:
            return
        
        data = self.active_giveaways.pop(message_id)
        channel = self.bot.get_channel(data["channel_id"])
        if not channel:
            return
            
        try:
            msg = await channel.fetch_message(message_id)
            reaction = discord.utils.get(msg.reactions, emoji="🎉")
            users = [user async for user in reaction.users() if not user.bot]
            
            if len(users) == 0:
                await channel.send(f"Nobody entered the giveaway for **{data['prize']}**!")
            else:
                winner_count = min(data["winners"], len(users))
                winners = random.sample(users, winner_count)
                winners_mentions = ", ".join([w.mention for w in winners])
                
                embed = discord.Embed(title="🎉 GIVEAWAY ENDED 🎉", description=f"**Prize:** {data['prize']}\n**Hosted by:** {data['host']}\n**Winners:** {winners_mentions}", color=discord.Color.dark_gray())
                await msg.edit(embed=embed)
                await channel.send(f"Congratulations {winners_mentions}! You won **{data['prize']}**!")
                
        except discord.NotFound:
            pass

    @giveaway_group.command(name="end", description="End a giveaway early.")
    @app_commands.describe(message_id="The ID of the giveaway message")
    async def giveaway_end(self, ctx: commands.Context, message_id: str):
        try:
            msg_id = int(message_id)
        except ValueError:
            return await ctx.send("Invalid message ID.")
            
        if msg_id in self.active_giveaways:
            await self._end_giveaway(msg_id, 0)
            await ctx.send("Ended the giveaway early.")
        else:
            await ctx.send("Could not find an active giveaway with that ID.")

    @giveaway_group.command(name="reroll", description="Reroll a giveaway winner.")
    @app_commands.describe(message_id="The ID of the giveaway message")
    async def giveaway_reroll(self, ctx: commands.Context, message_id: str):
        try:
            msg = await ctx.channel.fetch_message(int(message_id))
        except (ValueError, discord.NotFound):
            return await ctx.send("Could not find that message in this channel.")
            
        reaction = discord.utils.get(msg.reactions, emoji="🎉")
        if not reaction:
            return await ctx.send("That message doesn't have a giveaway reaction.")
            
        users = [user async for user in reaction.users() if not user.bot]
        if not users:
            return await ctx.send("Nobody entered the giveaway.")
            
        winner = random.choice(users)
        await ctx.send(f"🎉 The new winner is {winner.mention}! Congratulations!")

async def setup(bot: commands.Bot):
    await bot.add_cog(GiveawaysCog(bot))
