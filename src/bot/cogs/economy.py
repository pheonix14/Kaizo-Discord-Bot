import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
import datetime
from typing import Optional
from src.db import client as db_client
from src.bot.admin_utils import admin_only

class BlackjackView(discord.ui.View):
    def __init__(self, ctx, cog, bet: int):
        super().__init__(timeout=60.0)
        self.ctx = ctx
        self.cog = cog
        self.bet = bet
        self.player_hand = [self.draw_card(), self.draw_card()]
        self.dealer_hand = [self.draw_card(), self.draw_card()]
        
    def draw_card(self):
        cards = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11]
        return random.choice(cards)
        
    def get_score(self, hand):
        score = sum(hand)
        aces = hand.count(11)
        while score > 21 and aces:
            score -= 10
            aces -= 1
        return score

    async def update_message(self, interaction: discord.Interaction, game_over=False):
        p_score = self.get_score(self.player_hand)
        d_score = self.get_score(self.dealer_hand)
        
        embed = discord.Embed(title="Blackjack", color=0xF1C40F)
        embed.add_field(name=f"Your Hand ({p_score})", value=" ".join(str(c) for c in self.player_hand), inline=False)
        
        if game_over:
            embed.add_field(name=f"Dealer's Hand ({d_score})", value=" ".join(str(c) for c in self.dealer_hand), inline=False)
            
            if p_score > 21:
                embed.description = f"Bust! You lost **{self.bet}** coins."
                embed.color = discord.Color.red()
            elif d_score > 21 or p_score > d_score:
                win = self.bet * 2
                db_client.add_economy_balance(str(self.ctx.guild.id), str(self.ctx.author.id), wallet_delta=win)
                embed.description = f"You won! Payout: **{win}** coins."
                embed.color = discord.Color.green()
            elif p_score < d_score:
                embed.description = f"Dealer wins! You lost **{self.bet}** coins."
                embed.color = discord.Color.red()
            else:
                db_client.add_economy_balance(str(self.ctx.guild.id), str(self.ctx.author.id), wallet_delta=self.bet)
                embed.description = "Push! Your bet was returned."
                embed.color = discord.Color.gold()
                
            for child in self.children:
                child.disabled = True
        else:
            embed.add_field(name="Dealer's Hand", value=f"{self.dealer_hand[0]} ?", inline=False)
            
        await interaction.response.edit_message(embed=embed, view=self)
        if game_over:
            self.stop()

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.primary)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("Not your game!", ephemeral=True)
            
        self.player_hand.append(self.draw_card())
        if self.get_score(self.player_hand) > 21:
            await self.update_message(interaction, game_over=True)
        else:
            await self.update_message(interaction)

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.secondary)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("Not your game!", ephemeral=True)
            
        while self.get_score(self.dealer_hand) < 17:
            self.dealer_hand.append(self.draw_card())
            
        await self.update_message(interaction, game_over=True)


class EconomyCog(commands.Cog, name="Economy"):
    """Economy and currency commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.command_rewards_cooldown = {}

    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context):
        if not ctx.guild or ctx.author.bot:
            return
            
        # 30% chance to drop coins
        if random.random() < 0.30:
            import time
            current_time = time.time()
            last_time = self.command_rewards_cooldown.get(ctx.author.id, 0)
            
            # 60 second cooldown per user to prevent spam farming
            if current_time - last_time > 60:
                reward = random.randint(10, 30)
                db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), wallet_delta=reward)
                self.command_rewards_cooldown[ctx.author.id] = current_time
                
                try:
                    await ctx.message.add_reaction("🪙")
                except discord.HTTPException:
                    pass

    # ── Cooldown Helpers ──────────────────────────────────────────────────────

    def check_db_cooldown(self, guild_id: str, user_id: str, field: str, duration_seconds: int) -> Optional[float]:
        """
        Checks if a user is on a database-persisted cooldown.
        Returns the remaining seconds if on cooldown, or None if available.
        """
        data = db_client.get_economy_user(guild_id, user_id)
        last_time_str = data.get(field)
        if not last_time_str:
            return None
            
        try:
            last_time = datetime.datetime.fromisoformat(last_time_str.replace("Z", "+00:00"))
        except Exception:
            return None
            
        now = datetime.datetime.now(datetime.timezone.utc)
        elapsed = (now - last_time).total_seconds()
        if elapsed < duration_seconds:
            return duration_seconds - elapsed
        return None

    def update_db_cooldown(self, guild_id: str, user_id: str, field: str):
        """Updates the database-persisted cooldown timestamp for a user."""
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        db_client.update_economy_user(guild_id, user_id, {field: now_str})

    async def send_cooldown_error(self, ctx: commands.Context, seconds: float):
        """Sends a beautiful cooldown error embed."""
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        parts = []
        if d > 0: parts.append(f"{int(d)}d")
        if h > 0: parts.append(f"{int(h)}h")
        if m > 0: parts.append(f"{int(m)}m")
        parts.append(f"{int(s)}s")
        time_str = " ".join(parts)
        
        embed = discord.Embed(
            description=f"⏱️ This command is on cooldown. Try again in **{time_str}**.", 
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed, ephemeral=True)

    # ── Basic Economy ────────────────────────────────────────────────────────

    @commands.hybrid_command(name="balance", aliases=["money"], description="Check your or another member's balance.")
    @app_commands.describe(user="The user to check")
    async def balance(self, ctx: commands.Context, user: discord.Member = None):
        user = user or ctx.author
        data = db_client.get_economy_user(str(ctx.guild.id), str(user.id))
        wallet = data.get("wallet", 0)
        bank = data.get("bank", 0)
        net_worth = wallet + bank
        
        settings = db_client.get_guild_settings(str(ctx.guild.id))
        c_icon = settings.get("economy_currency_emoji", "🪙")
        
        embed = discord.Embed(title=f"Balance - {user.display_name}", color=0xF1C40F)
        embed.add_field(name="Wallet", value=f"{c_icon} {wallet:,}", inline=True)
        embed.add_field(name="Bank", value=f"🏦 {bank:,}", inline=True)
        embed.add_field(name="Net Worth", value=f"💎 {net_worth:,}", inline=False)
        embed.set_thumbnail(url=user.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="bal", description="Check your or another member's balance (shorthand).")
    @app_commands.describe(user="The user to check")
    async def bal(self, ctx: commands.Context, user: discord.Member = None):
        await self.balance(ctx, user)

    @commands.hybrid_command(name="deposit", aliases=["dep"], description="Deposit coins into your bank.")
    @app_commands.describe(amount="Amount to deposit (or 'all')")
    async def deposit(self, ctx: commands.Context, amount: str):
        data = db_client.get_economy_user(str(ctx.guild.id), str(ctx.author.id))
        wallet = data.get("wallet", 0)
        
        if amount.lower() == "all":
            amount_to_deposit = wallet
        else:
            try:
                amount_to_deposit = int(amount)
            except ValueError:
                return await ctx.send("Please provide a valid number or 'all'.")
                
        if amount_to_deposit <= 0:
            return await ctx.send("Amount must be greater than 0.")
        if amount_to_deposit > wallet:
            return await ctx.send("You don't have that much in your wallet.")
            
        db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), -amount_to_deposit, amount_to_deposit)
        await ctx.send(f"✅ Deposited **{amount_to_deposit:,}** coins into your bank.")

    @commands.hybrid_command(name="withdraw", aliases=["with"], description="Withdraw coins from your bank.")
    @app_commands.describe(amount="Amount to withdraw (or 'all')")
    async def withdraw(self, ctx: commands.Context, amount: str):
        data = db_client.get_economy_user(str(ctx.guild.id), str(ctx.author.id))
        bank = data.get("bank", 0)
        
        if amount.lower() == "all":
            amount_to_withdraw = bank
        else:
            try:
                amount_to_withdraw = int(amount)
            except ValueError:
                return await ctx.send("Please provide a valid number or 'all'.")
                
        if amount_to_withdraw <= 0:
            return await ctx.send("Amount must be greater than 0.")
        if amount_to_withdraw > bank:
            return await ctx.send("You don't have that much in your bank.")
            
        db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), amount_to_withdraw, -amount_to_withdraw)
        await ctx.send(f"✅ Withdrew **{amount_to_withdraw:,}** coins from your bank.")

    @commands.hybrid_command(name="transfer", aliases=["pay", "send"], description="Send coins to another user.")
    @app_commands.describe(user="User to send coins to", amount="Amount to send")
    async def transfer(self, ctx: commands.Context, user: discord.Member, amount: int):
        if amount <= 0:
            return await ctx.send("Amount must be greater than 0.")
        if user == ctx.author:
            return await ctx.send("You cannot send coins to yourself.")
            
        data = db_client.get_economy_user(str(ctx.guild.id), str(ctx.author.id))
        if data.get("wallet", 0) < amount:
            return await ctx.send("You don't have enough coins in your wallet.")
            
        db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), -amount, 0)
        db_client.add_economy_balance(str(ctx.guild.id), str(user.id), amount, 0)
        await ctx.send(f"💸 You sent **{amount:,}** coins to {user.mention}.")

    @commands.hybrid_command(name="leaderboard", aliases=["lb", "rich"], description="View the server economy leaderboard.")
    async def leaderboard(self, ctx: commands.Context):
        users = db_client.get_economy_leaderboard(str(ctx.guild.id), limit=10)
        if not users:
            return await ctx.send("No economy data for this server.")
            
        desc = ""
        for i, u in enumerate(users, 1):
            total = u.get("wallet", 0) + u.get("bank", 0)
            member = ctx.guild.get_member(int(u["user_id"]))
            name = member.display_name if member else f"User {u['user_id']}"
            desc += f"**{i}.** {name} — **{total:,}** 🪙\n"
            
        embed = discord.Embed(title=f"Economy Leaderboard — {ctx.guild.name}", description=desc, color=0xF1C40F)
        await ctx.send(embed=embed)


    # ── Income & Activities ──────────────────────────────────────────────────

    @commands.hybrid_command(name="daily", description="Claim your daily coins.")
    async def daily(self, ctx: commands.Context):
        cooldown = self.check_db_cooldown(str(ctx.guild.id), str(ctx.author.id), "last_daily", 86400)
        if cooldown:
            return await self.send_cooldown_error(ctx, cooldown)
            
        settings = db_client.get_guild_settings(str(ctx.guild.id))
        c_name = settings.get("economy_currency_name", "coins")
        c_icon = settings.get("economy_currency_emoji", "🪙")
        
        try:
            reward = int(settings.get("economy_daily", 100))
        except (ValueError, TypeError):
            reward = random.randint(500, 1000)
            
        db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), reward, 0)
        self.update_db_cooldown(str(ctx.guild.id), str(ctx.author.id), "last_daily")
        
        await ctx.send(embed=discord.Embed(description=f"📅 You claimed your daily reward of **{reward:,}** {c_icon} {c_name}!", color=discord.Color.green()))

    @commands.hybrid_command(name="weekly", description="Claim your weekly coins.")
    async def weekly(self, ctx: commands.Context):
        cooldown = self.check_db_cooldown(str(ctx.guild.id), str(ctx.author.id), "last_weekly", 604800)
        if cooldown:
            return await self.send_cooldown_error(ctx, cooldown)
            
        reward = random.randint(3000, 7000)
        db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), reward, 0)
        self.update_db_cooldown(str(ctx.guild.id), str(ctx.author.id), "last_weekly")
        
        await ctx.send(embed=discord.Embed(description=f"📅 You claimed your weekly reward of **{reward:,}** coins!", color=discord.Color.green()))

    @commands.hybrid_command(name="monthly", description="Claim your monthly coins.")
    async def monthly(self, ctx: commands.Context):
        cooldown = self.check_db_cooldown(str(ctx.guild.id), str(ctx.author.id), "last_monthly", 2592000)
        if cooldown:
            return await self.send_cooldown_error(ctx, cooldown)
            
        reward = random.randint(15000, 30000)
        db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), reward, 0)
        self.update_db_cooldown(str(ctx.guild.id), str(ctx.author.id), "last_monthly")
        
        await ctx.send(embed=discord.Embed(description=f"📅 You claimed your monthly reward of **{reward:,}** coins!", color=discord.Color.green()))

    @commands.hybrid_command(name="work", description="Work a job to earn coins.")
    async def work(self, ctx: commands.Context):
        cooldown = self.check_db_cooldown(str(ctx.guild.id), str(ctx.author.id), "last_work", 3600)
        if cooldown:
            return await self.send_cooldown_error(ctx, cooldown)
            
        settings = db_client.get_guild_settings(str(ctx.guild.id))
        c_name = settings.get("economy_currency_name", "coins")
        
        try:
            min_work = int(settings.get("economy_work_min", 50))
            max_work = int(settings.get("economy_work_max", 200))
        except (ValueError, TypeError):
            min_work, max_work = 50, 200
            
        if min_work > max_work:
            min_work, max_work = max_work, min_work
            
        jobs = ["developer", "designer", "teacher", "chef", "driver", "streamer", "mechanic", "doctor", "cashier"]
        reward = random.randint(min_work, max(min_work, max_work))
        db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), reward, 0)
        self.update_db_cooldown(str(ctx.guild.id), str(ctx.author.id), "last_work")
        
        await ctx.send(embed=discord.Embed(description=f"💼 You worked as a **{random.choice(jobs)}** and earned **{reward:,}** {c_name}!", color=discord.Color.green()))

    @commands.hybrid_command(name="crime", description="Commit a crime for high rewards, but risk a fine.")
    async def crime(self, ctx: commands.Context):
        cooldown = self.check_db_cooldown(str(ctx.guild.id), str(ctx.author.id), "last_crime", 7200)
        if cooldown:
            return await self.send_cooldown_error(ctx, cooldown)
            
        self.update_db_cooldown(str(ctx.guild.id), str(ctx.author.id), "last_crime")
        if random.random() < 0.4:
            reward = random.randint(500, 1500)
            db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), reward, 0)
            await ctx.send(embed=discord.Embed(description=f"🦹 You successfully committed a crime and stole **{reward:,}** coins!", color=discord.Color.green()))
        else:
            fine = random.randint(200, 800)
            db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), -fine, 0)
            await ctx.send(embed=discord.Embed(description=f"🚓 You were caught and fined **{fine:,}** coins.", color=discord.Color.red()))

    @commands.hybrid_command(name="rob", description="Attempt to rob someone's wallet.")
    @app_commands.describe(user="The user to rob")
    async def rob(self, ctx: commands.Context, user: discord.Member):
        if user == ctx.author:
            return await ctx.send("You can't rob yourself.")
            
        cooldown = self.check_db_cooldown(str(ctx.guild.id), str(ctx.author.id), "last_rob", 3600)
        if cooldown:
            return await self.send_cooldown_error(ctx, cooldown)
            
        target_data = db_client.get_economy_user(str(ctx.guild.id), str(user.id))
        if target_data.get("wallet", 0) < 100:
            return await ctx.send(f"{user.display_name} doesn't have enough coins worth stealing (minimum 100).")
            
        self.update_db_cooldown(str(ctx.guild.id), str(ctx.author.id), "last_rob")
        if random.random() < 0.35:
            stolen = int(target_data["wallet"] * random.uniform(0.1, 0.4))
            db_client.add_economy_balance(str(ctx.guild.id), str(user.id), -stolen, 0)
            db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), stolen, 0)
            await ctx.send(embed=discord.Embed(description=f"🥷 You successfully robbed **{stolen:,}** coins from {user.mention}!", color=discord.Color.green()))
        else:
            fine = random.randint(100, 500)
            db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), -fine, 0)
            await ctx.send(embed=discord.Embed(description=f"🚓 You were caught trying to rob {user.mention} and fined **{fine:,}** coins.", color=discord.Color.red()))

    @commands.hybrid_command(name="bankrob", description="Attempt a massive bank robbery (very hard).")
    async def bankrob(self, ctx: commands.Context):
        cooldown = self.check_db_cooldown(str(ctx.guild.id), str(ctx.author.id), "last_crime", 21600)
        if cooldown:
            return await self.send_cooldown_error(ctx, cooldown)
            
        self.update_db_cooldown(str(ctx.guild.id), str(ctx.author.id), "last_crime")
        if random.random() < 0.1:
            reward = random.randint(5000, 20000)
            db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), reward, 0)
            await ctx.send(embed=discord.Embed(title="🏦 BANK HEIST SUCCESSFUL!", description=f"You bypassed the vault and stole **{reward:,}** coins!", color=discord.Color.green()))
        else:
            fine = random.randint(1000, 5000)
            db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), -fine, 0)
            await ctx.send(embed=discord.Embed(title="🚨 BUSTED!", description=f"The SWAT team caught you. You were fined **{fine:,}** coins.", color=discord.Color.red()))

    @commands.hybrid_command(name="fish", description="Go fishing.")
    async def fish(self, ctx: commands.Context):
        cooldown = self.check_db_cooldown(str(ctx.guild.id), str(ctx.author.id), "last_fish", 1800)
        if cooldown:
            return await self.send_cooldown_error(ctx, cooldown)
            
        self.update_db_cooldown(str(ctx.guild.id), str(ctx.author.id), "last_fish")
        fish_types = ["🐟", "🐠", "🐡", "🦈", "🐙", "🦀"]
        amount = random.randint(20, 150)
        db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), amount, 0)
        await ctx.send(f"🎣 You went fishing and caught a {random.choice(fish_types)}! You sold it for **{amount}** coins.")

    @commands.hybrid_command(name="hunt", description="Go hunting.")
    async def hunt(self, ctx: commands.Context):
        cooldown = self.check_db_cooldown(str(ctx.guild.id), str(ctx.author.id), "last_hunt", 1800)
        if cooldown:
            return await self.send_cooldown_error(ctx, cooldown)
            
        self.update_db_cooldown(str(ctx.guild.id), str(ctx.author.id), "last_hunt")
        animals = ["🦌", "🐗", "🐇", "🦆", "🐻"]
        amount = random.randint(30, 200)
        db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), amount, 0)
        await ctx.send(f"🏹 You went hunting and caught a {random.choice(animals)}! You sold it for **{amount}** coins.")

    @commands.hybrid_command(name="mine", description="Go mining.")
    async def mine(self, ctx: commands.Context):
        cooldown = self.check_db_cooldown(str(ctx.guild.id), str(ctx.author.id), "last_mine", 1800)
        if cooldown:
            return await self.send_cooldown_error(ctx, cooldown)
            
        self.update_db_cooldown(str(ctx.guild.id), str(ctx.author.id), "last_mine")
        ores = ["⛏️ Coal", "⛏️ Iron", "⛏️ Gold", "💎 Diamond"]
        ore = random.choice(ores)
        amount = random.randint(50, 300) if "Diamond" not in ore else random.randint(500, 1000)
        db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), amount, 0)
        await ctx.send(f"⛏️ You went mining and found **{ore}**! You sold it for **{amount}** coins.")

    @commands.hybrid_command(name="beg", description="Beg for some spare coins.")
    @commands.cooldown(1, 45, commands.BucketType.user)
    async def beg(self, ctx: commands.Context):
        if random.random() < 0.6:
            amount = random.randint(20, 100)
            db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), amount, 0)
            beggers = ["A kind stranger", "A wealthy businessman", "A generous developer", "A friendly bot"]
            await ctx.send(f"🪙 {random.choice(beggers)} gave you **{amount}** coins!")
        else:
            refusals = ["Get a job!", "I don't have any spare change.", "Shoo!", "Maybe next time."]
            await ctx.send(f"❌ {random.choice(refusals)}")

    @commands.hybrid_command(name="search", description="Search different locations for coins.")
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def search(self, ctx: commands.Context):
        locations = ["couch", "street", "mailbox", "pocket", "car", "trash can"]
        chosen = random.sample(locations, 3)
        
        class SearchButtons(discord.ui.View):
            def __init__(self, author, guild_id):
                super().__init__(timeout=20.0)
                self.author = author
                self.guild_id = guild_id
                self.selected = False
                
                for loc in chosen:
                    btn = discord.ui.Button(label=loc.title(), style=discord.ButtonStyle.secondary)
                    btn.callback = self.make_callback(loc)
                    self.add_item(btn)
                    
            def make_callback(self, loc):
                async def callback(interaction: discord.Interaction):
                    if interaction.user != self.author:
                        return await interaction.response.send_message("This is not your search session!", ephemeral=True)
                    
                    if self.selected:
                        return
                    self.selected = True
                    
                    for child in self.children:
                        child.disabled = True
                        if child.label.lower() == loc:
                            child.style = discord.ButtonStyle.success
                            
                    if random.random() < 0.7:
                        amount = random.randint(30, 200)
                        db_client.add_economy_balance(str(self.guild_id), str(self.author.id), amount, 0)
                        content = f"🔍 You searched the **{loc}** and found **{amount}** coins!"
                    else:
                        content = f"🔍 You searched the **{loc}** but found nothing."
                        
                    await interaction.response.edit_message(content=content, view=self)
                    self.stop()
                return callback
                
            async def on_timeout(self):
                for child in self.children:
                    child.disabled = True
                try:
                    await self.message.edit(content="Search timed out!", view=self)
                except:
                    pass
                    
        view = SearchButtons(ctx.author, ctx.guild.id)
        view.message = await ctx.send("Where do you want to search?", view=view)

    @commands.hybrid_command(name="highlow", aliases=["hl"], description="Guess if a secret number is higher or lower than a hint number.")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def highlow(self, ctx: commands.Context):
        hint = random.randint(15, 85)
        secret = random.randint(1, 100)
        while secret == hint:
            secret = random.randint(1, 100)
            
        embed = discord.Embed(
            title="🎯 High or Lower!",
            description=f"I am thinking of a number between 1 and 100.\n"
                        f"The hint number is **{hint}**.\n\n"
                        f"Is the secret number **Higher** or **Lower** than **{hint}**?",
            color=0xF1C40F
        )
        
        class HighLowView(discord.ui.View):
            def __init__(self, author, guild_id, hint_val, secret_val):
                super().__init__(timeout=20.0)
                self.author = author
                self.guild_id = guild_id
                self.hint = hint_val
                self.secret = secret_val
                self.answered = False
                
            @discord.ui.button(label="Higher", style=discord.ButtonStyle.success)
            async def higher(self, interaction: discord.Interaction, button: discord.ui.Button):
                await self.process_guess(interaction, "higher")
                
            @discord.ui.button(label="Lower", style=discord.ButtonStyle.danger)
            async def lower(self, interaction: discord.Interaction, button: discord.ui.Button):
                await self.process_guess(interaction, "lower")
                
            async def process_guess(self, interaction: discord.Interaction, guess: str):
                if interaction.user != self.author:
                    return await interaction.response.send_message("This is not your session!", ephemeral=True)
                if self.answered:
                    return
                self.answered = True
                
                for child in self.children:
                    child.disabled = True
                    
                is_higher = self.secret > self.hint
                won = (guess == "higher" and is_higher) or (guess == "lower" and not is_higher)
                
                if won:
                    payout = random.randint(50, 150)
                    db_client.add_economy_balance(str(self.guild_id), str(self.author.id), payout, 0)
                    embed.description = f"🎯 The secret number was **{self.secret}** (which is {'higher' if is_higher else 'lower'} than **{self.hint}**).\n\n" \
                                        f"🎉 **You guessed correctly!** You earned **{payout}** coins."
                    embed.color = discord.Color.green()
                else:
                    embed.description = f"🎯 The secret number was **{self.secret}** (which is {'higher' if is_higher else 'lower'} than **{self.hint}**).\n\n" \
                                        f"❌ **Wrong guess!** You earned 0 coins."
                    embed.color = discord.Color.red()
                    
                await interaction.response.edit_message(embed=embed, view=self)
                self.stop()
                
            async def on_timeout(self):
                for child in self.children:
                    child.disabled = True
                try:
                    embed.description = f"⏱️ Time's up! The secret number was **{self.secret}**."
                    embed.color = discord.Color.orange()
                    await self.message.edit(embed=embed, view=self)
                except:
                    pass
                    
        view = HighLowView(ctx.author, ctx.guild.id, hint, secret)
        view.message = await ctx.send(embed=embed, view=view)

    # ── Gambling ─────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="gamble", aliases=["bet"], description="50/50 chance to double your bet.")
    @app_commands.describe(bet="Amount to bet")
    async def gamble(self, ctx: commands.Context, bet: int):
        if bet < 10:
            return await ctx.send("Minimum bet is 10.")
            
        data = db_client.get_economy_user(str(ctx.guild.id), str(ctx.author.id))
        if data.get("wallet", 0) < bet:
            return await ctx.send("You don't have enough coins.")
            
        db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), -bet, 0)
        if random.random() < 0.48:
            win = bet * 2
            db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), win, 0)
            await ctx.send(embed=discord.Embed(description=f"🎰 You won! Payout: **{win:,}** coins.", color=discord.Color.green()))
        else:
            await ctx.send(embed=discord.Embed(description=f"🎰 You lost **{bet:,}** coins. Better luck next time!", color=discord.Color.red()))

    @commands.hybrid_command(name="coinflip", aliases=["cf"], description="Bet on heads or tails.")
    @app_commands.describe(choice="heads or tails", bet="Amount to bet")
    async def coinflip(self, ctx: commands.Context, choice: str, bet: int):
        choice = choice.lower()
        if choice not in ["heads", "tails", "h", "t"]:
            return await ctx.send("Choose heads or tails.")
        if bet < 10:
            return await ctx.send("Minimum bet is 10.")
            
        data = db_client.get_economy_user(str(ctx.guild.id), str(ctx.author.id))
        if data.get("wallet", 0) < bet:
            return await ctx.send("You don't have enough coins.")
            
        db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), -bet, 0)
        result = random.choice(["heads", "tails"])
        
        is_win = (choice in ["heads", "h"] and result == "heads") or (choice in ["tails", "t"] and result == "tails")
        
        if is_win:
            win = bet * 2
            db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), win, 0)
            await ctx.send(embed=discord.Embed(description=f"🪙 It landed on **{result}**! You won **{win:,}** coins.", color=discord.Color.green()))
        else:
            await ctx.send(embed=discord.Embed(description=f"🪙 It landed on **{result}**. You lost **{bet:,}** coins.", color=discord.Color.red()))

    @commands.hybrid_command(name="slots", aliases=["slot"], description="Play the slot machine.")
    @app_commands.describe(bet="Amount to bet")
    async def slots(self, ctx: commands.Context, bet: int):
        if bet < 10:
            return await ctx.send("Minimum bet is 10.")
            
        data = db_client.get_economy_user(str(ctx.guild.id), str(ctx.author.id))
        if data.get("wallet", 0) < bet:
            return await ctx.send("You don't have enough coins.")
            
        db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), -bet, 0)
        
        emojis = ["🍒", "🍇", "🍊", "🍋", "🔔", "💎", "7️⃣"]
        s1, s2, s3 = random.choice(emojis), random.choice(emojis), random.choice(emojis)
        
        embed = discord.Embed(title="🎰 Slot Machine", description=f"**[ {s1} | {s2} | {s3} ]**", color=0xF1C40F)
        
        if s1 == s2 == s3:
            win = bet * 10
            db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), win, 0)
            embed.description += f"\n\n**JACKPOT!** You won **{win:,}** coins!"
            embed.color = discord.Color.green()
        elif s1 == s2 or s2 == s3 or s1 == s3:
            win = bet * 2
            db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), win, 0)
            embed.description += f"\n\n**Nice!** You won **{win:,}** coins!"
            embed.color = discord.Color.green()
        else:
            embed.description += f"\n\n**Loss.** You lost **{bet:,}** coins."
            embed.color = discord.Color.red()
            
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="blackjack", aliases=["bj"], description="Play blackjack against the dealer.")
    @app_commands.describe(bet="Amount to bet")
    async def blackjack(self, ctx: commands.Context, bet: int):
        if bet < 10:
            return await ctx.send("Minimum bet is 10.")
            
        data = db_client.get_economy_user(str(ctx.guild.id), str(ctx.author.id))
        if data.get("wallet", 0) < bet:
            return await ctx.send("You don't have enough coins.")
            
        db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), -bet, 0)
        
        view = BlackjackView(ctx, self, bet)
        p_score = view.get_score(view.player_hand)
        d_score = view.get_score(view.dealer_hand)
        
        embed = discord.Embed(title="Blackjack", color=0xF1C40F)
        embed.add_field(name=f"Your Hand ({p_score})", value=" ".join(str(c) for c in view.player_hand), inline=False)
        embed.add_field(name="Dealer's Hand", value=f"{view.dealer_hand[0]} ?", inline=False)
        
        if p_score == 21:
            win = int(bet * 2.5)
            db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), win, 0)
            embed.add_field(name=f"Dealer's Hand ({d_score})", value=" ".join(str(c) for c in view.dealer_hand), inline=False)
            embed.description = f"**BLACKJACK!** You won **{win:,}** coins!"
            embed.color = discord.Color.green()
            await ctx.send(embed=embed)
        else:
            msg = await ctx.send(embed=embed, view=view)


    # ── Shop & Inventory ─────────────────────────────────────────────────────

    @commands.hybrid_command(name="shop", description="Browse the server shop.")
    async def shop(self, ctx: commands.Context):
        items = db_client.get_shop_items(str(ctx.guild.id))
        if not items:
            return await ctx.send("The shop is currently empty.")
            
        desc = ""
        for item in items:
            emoji = item.get('emoji') or "📦"
            desc += f"{emoji} **{item['name']}** — 🪙 {item['price']:,}\n"
            if item.get('description'):
                desc += f"*{item['description']}*\n"
            desc += "\n"
            
        embed = discord.Embed(title=f"Shop — {ctx.guild.name}", description=desc, color=0x3498DB)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="buy", description="Buy an item from the shop.")
    @app_commands.describe(item_name="Name of the item (you can specify quantity first, e.g., '5 apple')")
    async def buy(self, ctx: commands.Context, *, item_name: str):
        # Parse quantity and real item name
        parts = item_name.strip().split(maxsplit=1)
        quantity = 1
        real_item_name = item_name.strip()
        if len(parts) > 1 and parts[0].isdigit():
            quantity = int(parts[0])
            real_item_name = parts[1].strip()

        if quantity <= 0:
            return await ctx.send("Quantity must be at least 1.")
            
        item = db_client.get_shop_item(str(ctx.guild.id), real_item_name)
        if not item:
            return await ctx.send(f"Item `{real_item_name}` not found in the shop.")
            
        total_price = item['price'] * quantity
        data = db_client.get_economy_user(str(ctx.guild.id), str(ctx.author.id))
        
        if data.get("wallet", 0) < total_price:
            return await ctx.send(f"You need **{total_price:,}** coins to buy {quantity}x {item['name']}.")
            
        db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), -total_price, 0)
        db_client.add_to_inventory(str(ctx.guild.id), str(ctx.author.id), item['item_id'], quantity)
        
        emoji = item.get('emoji') or "📦"
        await ctx.send(f"✅ You bought **{quantity}x {item['name']}** {emoji} for **{total_price:,}** coins.")

    @commands.hybrid_command(name="sell", description="Sell an item from your inventory.")
    @app_commands.describe(item_name="Name of the item to sell (you can specify quantity first, e.g., '5 apple')")
    async def sell(self, ctx: commands.Context, *, item_name: str):
        # Parse quantity and real item name
        parts = item_name.strip().split(maxsplit=1)
        quantity = 1
        real_item_name = item_name.strip()
        if len(parts) > 1 and parts[0].isdigit():
            quantity = int(parts[0])
            real_item_name = parts[1].strip()

        if quantity <= 0:
            return await ctx.send("Quantity must be at least 1.")
            
        item = db_client.get_shop_item(str(ctx.guild.id), real_item_name)
        if not item:
            return await ctx.send("That item doesn't exist.")
            
        success = db_client.remove_from_inventory(str(ctx.guild.id), str(ctx.author.id), item['item_id'], quantity)
        if not success:
            return await ctx.send("You don't have enough of that item in your inventory.")
            
        sell_price = int(item['price'] * 0.5) * quantity
        db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), sell_price, 0)
        
        await ctx.send(f"✅ You sold **{quantity}x {item['name']}** for **{sell_price:,}** coins.")

    @commands.hybrid_command(name="inventory", aliases=["inv"], description="View your inventory.")
    @app_commands.describe(user="The user to check")
    async def inventory(self, ctx: commands.Context, user: discord.Member = None):
        user = user or ctx.author
        inv = db_client.get_inventory(str(ctx.guild.id), str(user.id))
        
        if not inv:
            return await ctx.send(embed=discord.Embed(description=f"**{user.display_name}** has an empty inventory.", color=0x3498DB))
            
        desc = ""
        for row in inv:
            qty = row['quantity']
            item = row['economy_shop']
            emoji = item.get('emoji') or "📦"
            desc += f"{emoji} **{item['name']}** — x{qty}\n"
            
        embed = discord.Embed(title=f"Inventory - {user.display_name}", description=desc, color=0x3498DB)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="use", description="Use an item from your inventory.")
    @app_commands.describe(item_name="Name of the item to use")
    async def use(self, ctx: commands.Context, *, item_name: str):
        item = db_client.get_shop_item(str(ctx.guild.id), item_name)
        if not item:
            return await ctx.send("That item doesn't exist.")
            
        success = db_client.remove_from_inventory(str(ctx.guild.id), str(ctx.author.id), item['item_id'], 1)
        if not success:
            return await ctx.send("You don't have that item.")
            
        await ctx.send(f"You used **{item['name']}**!")

    @commands.hybrid_command(name="trade", aliases=["gift"], description="Trade or gift an item to another user.")
    @app_commands.describe(user="The user to gift", item_name="Name of the item (you can specify quantity first, e.g., '5 apple')")
    async def trade(self, ctx: commands.Context, user: discord.Member, *, item_name: str):
        if user == ctx.author:
            return await ctx.send("Cannot gift yourself.")
            
        # Parse quantity and real item name
        parts = item_name.strip().split(maxsplit=1)
        quantity = 1
        real_item_name = item_name.strip()
        if len(parts) > 1 and parts[0].isdigit():
            quantity = int(parts[0])
            real_item_name = parts[1].strip()

        if quantity <= 0:
            return await ctx.send("Quantity must be at least 1.")
            
        item = db_client.get_shop_item(str(ctx.guild.id), real_item_name)
        if not item:
            return await ctx.send("That item doesn't exist.")
            
        success = db_client.remove_from_inventory(str(ctx.guild.id), str(ctx.author.id), item['item_id'], quantity)
        if not success:
            return await ctx.send("You don't have enough of that item.")
            
        db_client.add_to_inventory(str(ctx.guild.id), str(user.id), item['item_id'], quantity)
        await ctx.send(f"🎁 You gifted **{quantity}x {item['name']}** to {user.mention}.")

    # ── Admin Economy ────────────────────────────────────────────────────────

    @commands.hybrid_command(name="give", description="Give money to a user.")
    @admin_only()
    async def give(self, ctx: commands.Context, user: discord.Member, amount: int):
        db_client.add_economy_balance(str(ctx.guild.id), str(user.id), amount, 0)
        settings = db_client.get_guild_settings(str(ctx.guild.id))
        c_name = settings.get("economy_currency_name", "coins")
        await ctx.send(embed=discord.Embed(description=f"✅ Added **{amount:,}** {c_name} to {user.mention}'s wallet.", color=discord.Color.green()))

    @commands.hybrid_command(name="remove", description="Remove money from a user.")
    @admin_only()
    async def remove(self, ctx: commands.Context, user: discord.Member, amount: int):
        db_client.add_economy_balance(str(ctx.guild.id), str(user.id), -amount, 0)
        settings = db_client.get_guild_settings(str(ctx.guild.id))
        c_name = settings.get("economy_currency_name", "coins")
        await ctx.send(embed=discord.Embed(description=f"✅ Removed **{amount:,}** {c_name} from {user.mention}'s wallet.", color=discord.Color.green()))

    @commands.hybrid_command(name="reset", description="Reset a user's economy data completely.")
    @admin_only()
    async def reset(self, ctx: commands.Context, user: discord.Member):
        db_client.delete_economy_user(str(ctx.guild.id), str(user.id))
        await ctx.send(embed=discord.Embed(description=f"⚠️ Reset economy data for {user.mention}.", color=discord.Color.orange()))

    @commands.hybrid_command(name="additem", description="Add an item to the shop.")
    @admin_only()
    async def additem(self, ctx: commands.Context, name: str, price: int, emoji: str = None, desc: str = None):
        data = {
            "guild_id": str(ctx.guild.id),
            "name": name,
            "price": price,
            "emoji": emoji,
            "description": desc
        }
        settings = db_client.get_guild_settings(str(ctx.guild.id))
        c_name = settings.get("economy_currency_name", "coins")
        if db_client.add_shop_item(data):
            await ctx.send(f"✅ Added **{name}** to the shop for **{price}** {c_name}.")
        else:
            await ctx.send("❌ Failed to add item.")

    @commands.hybrid_command(name="removeitem", description="Remove an item from the shop.")
    @admin_only()
    async def removeitem(self, ctx: commands.Context, name: str):
        if db_client.remove_shop_item(str(ctx.guild.id), name):
            await ctx.send(f"✅ Removed **{name}** from the shop.")
        else:
            await ctx.send("❌ Failed to remove item.")

    @commands.hybrid_command(name="equip", description="Equip a role item from your inventory.")
    @app_commands.describe(item_name="Name of the role item to equip")
    async def equip(self, ctx: commands.Context, *, item_name: str):
        item = db_client.get_shop_item(str(ctx.guild.id), item_name)
        if not item:
            return await ctx.send("That item doesn't exist.")
        if item.get("type") != "role" or not item.get("role_id"):
            return await ctx.send("This item cannot be equipped as a role.")
            
        inv = db_client.get_inventory(str(ctx.guild.id), str(ctx.author.id))
        owns_item = any(row["item_id"] == item["item_id"] for row in inv)
        
        if not owns_item:
            return await ctx.send("You don't own this item.")
            
        role = ctx.guild.get_role(int(item["role_id"]))
        if not role:
            return await ctx.send("The role for this item no longer exists on the server.")
            
        if role in ctx.author.roles:
            return await ctx.send("You already have this role equipped.")
            
        try:
            await ctx.author.add_roles(role)
            await ctx.send(f"✅ Equipped **{item['name']}** and received the role {role.mention}!")
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to grant this role. Please ensure my bot role is higher than the item role.")

    @commands.hybrid_command(name="unequip", description="Unequip a role item.")
    @app_commands.describe(item_name="Name of the role item to unequip")
    async def unequip(self, ctx: commands.Context, *, item_name: str):
        item = db_client.get_shop_item(str(ctx.guild.id), item_name)
        if not item or item.get("type") != "role" or not item.get("role_id"):
            return await ctx.send("This item is not an equippable role.")
            
        role = ctx.guild.get_role(int(item["role_id"]))
        if not role:
            return await ctx.send("The role for this item no longer exists.")
            
        if role not in ctx.author.roles:
            return await ctx.send("You don't have this role equipped.")
            
        try:
            await ctx.author.remove_roles(role)
            await ctx.send(f"✅ Unequipped **{item['name']}**.")
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to remove this role.")

    # ── Error Handler ────────────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            m, s = divmod(error.retry_after, 60)
            h, m = divmod(m, 60)
            d, h = divmod(h, 24)
            time_str = f"{int(d)}d {int(h)}h {int(m)}m {int(s)}s".replace("0d ", "").replace("0h ", "").replace("0m ", "")
            await ctx.send(embed=discord.Embed(description=f"⏱️ This command is on cooldown. Try again in **{time_str}**.", color=discord.Color.orange()), ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(EconomyCog(bot))
