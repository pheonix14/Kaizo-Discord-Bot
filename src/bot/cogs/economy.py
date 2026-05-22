import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
from typing import Optional
from src.db import client as db_client

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
                    # Optionally send a small message:
                    # await ctx.send(f"🪙 You found **{reward}** coins while using that command!", delete_after=5.0)
                except discord.HTTPException:
                    pass

    async def cog_check(self, ctx: commands.Context):
        # We can implement a global /config economy check here if desired.
        # For now we allow them to run.
        return True

    # ── Basic Economy ────────────────────────────────────────────────────────

    @commands.hybrid_command(name="balance", aliases=["bal", "money"], description="Check your or another member's balance.")
    @app_commands.describe(user="The user to check")
    async def balance(self, ctx: commands.Context, user: discord.Member = None):
        user = user or ctx.author
        data = db_client.get_economy_user(str(ctx.guild.id), str(user.id))
        wallet = data.get("wallet", 0)
        bank = data.get("bank", 0)
        net_worth = wallet + bank
        
        embed = discord.Embed(title=f"Balance - {user.display_name}", color=0xF1C40F)
        embed.add_field(name="Wallet", value=f"🪙 {wallet:,}", inline=True)
        embed.add_field(name="Bank", value=f"🏦 {bank:,}", inline=True)
        embed.add_field(name="Net Worth", value=f"💎 {net_worth:,}", inline=False)
        embed.set_thumbnail(url=user.display_avatar.url)
        await ctx.send(embed=embed)

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

    @commands.hybrid_command(name="transfer", aliases=["pay", "give"], description="Send coins to another user.")
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
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def daily(self, ctx: commands.Context):
        reward = random.randint(500, 1000)
        db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), reward, 0)
        await ctx.send(embed=discord.Embed(description=f"📅 You claimed your daily reward of **{reward:,}** coins!", color=discord.Color.green()))

    @commands.hybrid_command(name="weekly", description="Claim your weekly coins.")
    @commands.cooldown(1, 604800, commands.BucketType.user)
    async def weekly(self, ctx: commands.Context):
        reward = random.randint(3000, 7000)
        db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), reward, 0)
        await ctx.send(embed=discord.Embed(description=f"📅 You claimed your weekly reward of **{reward:,}** coins!", color=discord.Color.green()))

    @commands.hybrid_command(name="monthly", description="Claim your monthly coins.")
    @commands.cooldown(1, 2592000, commands.BucketType.user)
    async def monthly(self, ctx: commands.Context):
        reward = random.randint(15000, 30000)
        db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), reward, 0)
        await ctx.send(embed=discord.Embed(description=f"📅 You claimed your monthly reward of **{reward:,}** coins!", color=discord.Color.green()))

    @commands.hybrid_command(name="work", description="Work a job to earn coins.")
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def work(self, ctx: commands.Context):
        jobs = ["developer", "designer", "teacher", "chef", "driver", "streamer", "mechanic", "doctor", "cashier"]
        reward = random.randint(100, 400)
        db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), reward, 0)
        await ctx.send(embed=discord.Embed(description=f"💼 You worked as a **{random.choice(jobs)}** and earned **{reward:,}** coins!", color=discord.Color.green()))

    @commands.hybrid_command(name="crime", description="Commit a crime for high rewards, but risk a fine.")
    @commands.cooldown(1, 7200, commands.BucketType.user)
    async def crime(self, ctx: commands.Context):
        if random.random() < 0.4:
            reward = random.randint(500, 1500)
            db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), reward, 0)
            await ctx.send(embed=discord.Embed(description=f"🦹 You successfully committed a crime and stole **{reward:,}** coins!", color=discord.Color.green()))
        else:
            fine = random.randint(200, 800)
            db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), -fine, 0)
            await ctx.send(embed=discord.Embed(description=f"🚓 You were caught and fined **{fine:,}** coins.", color=discord.Color.red()))

    @commands.hybrid_command(name="rob", description="Attempt to rob someone's wallet.")
    @commands.cooldown(1, 3600, commands.BucketType.user)
    @app_commands.describe(user="The user to rob")
    async def rob(self, ctx: commands.Context, user: discord.Member):
        if user == ctx.author:
            return await ctx.send("You can't rob yourself.")
            
        target_data = db_client.get_economy_user(str(ctx.guild.id), str(user.id))
        if target_data.get("wallet", 0) < 100:
            return await ctx.send(f"{user.display_name} doesn't have enough coins worth stealing (minimum 100).")
            
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
    @commands.cooldown(1, 21600, commands.BucketType.user)
    async def bankrob(self, ctx: commands.Context):
        if random.random() < 0.1: # 10% chance
            reward = random.randint(5000, 20000)
            db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), reward, 0)
            await ctx.send(embed=discord.Embed(title="🏦 BANK HEIST SUCCESSFUL!", description=f"You bypassed the vault and stole **{reward:,}** coins!", color=discord.Color.green()))
        else:
            fine = random.randint(1000, 5000)
            db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), -fine, 0)
            await ctx.send(embed=discord.Embed(title="🚨 BUSTED!", description=f"The SWAT team caught you. You were fined **{fine:,}** coins.", color=discord.Color.red()))

    @commands.hybrid_command(name="fish", description="Go fishing.")
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def fish(self, ctx: commands.Context):
        fish_types = ["🐟", "🐠", "🐡", "🦈", "🐙", "🦀"]
        amount = random.randint(20, 150)
        db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), amount, 0)
        await ctx.send(f"🎣 You went fishing and caught a {random.choice(fish_types)}! You sold it for **{amount}** coins.")

    @commands.hybrid_command(name="hunt", description="Go hunting.")
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def hunt(self, ctx: commands.Context):
        animals = ["🦌", "🐗", "🐇", "🦆", "🐻"]
        amount = random.randint(30, 200)
        db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), amount, 0)
        await ctx.send(f"🏹 You went hunting and caught a {random.choice(animals)}! You sold it for **{amount}** coins.")

    @commands.hybrid_command(name="mine", description="Go mining.")
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def mine(self, ctx: commands.Context):
        ores = ["⛏️ Coal", "⛏️ Iron", "⛏️ Gold", "💎 Diamond"]
        ore = random.choice(ores)
        amount = random.randint(50, 300) if "Diamond" not in ore else random.randint(500, 1000)
        db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), amount, 0)
        await ctx.send(f"⛏️ You went mining and found **{ore}**! You sold it for **{amount}** coins.")

    # ── Gambling ─────────────────────────────────────────────────────────────

    @commands.hybrid_command(name="gamble", description="50/50 chance to double your bet.")
    @app_commands.describe(bet="Amount to bet")
    async def gamble(self, ctx: commands.Context, bet: int):
        if bet < 10:
            return await ctx.send("Minimum bet is 10.")
            
        data = db_client.get_economy_user(str(ctx.guild.id), str(ctx.author.id))
        if data.get("wallet", 0) < bet:
            return await ctx.send("You don't have enough coins.")
            
        db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), -bet, 0)
        if random.random() < 0.48: # 48% win rate (slight house edge)
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

    @commands.hybrid_command(name="slots", description="Play the slot machine.")
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
            
        # Deduct bet upfront
        db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), -bet, 0)
        
        view = BlackjackView(ctx, self, bet)
        
        p_score = view.get_score(view.player_hand)
        d_score = view.get_score(view.dealer_hand)
        
        embed = discord.Embed(title="Blackjack", color=0xF1C40F)
        embed.add_field(name=f"Your Hand ({p_score})", value=" ".join(str(c) for c in view.player_hand), inline=False)
        embed.add_field(name="Dealer's Hand", value=f"{view.dealer_hand[0]} ?", inline=False)
        
        if p_score == 21:
            win = int(bet * 2.5) # Blackjack pays 3:2 + original bet
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
    @app_commands.describe(item_name="Name of the item", quantity="Amount to buy")
    async def buy(self, ctx: commands.Context, item_name: str, quantity: int = 1):
        if quantity <= 0:
            return await ctx.send("Quantity must be at least 1.")
            
        item = db_client.get_shop_item(str(ctx.guild.id), item_name)
        if not item:
            return await ctx.send(f"Item `{item_name}` not found in the shop.")
            
        total_price = item['price'] * quantity
        data = db_client.get_economy_user(str(ctx.guild.id), str(ctx.author.id))
        
        if data.get("wallet", 0) < total_price:
            return await ctx.send(f"You need **{total_price:,}** coins to buy {quantity}x {item['name']}.")
            
        db_client.add_economy_balance(str(ctx.guild.id), str(ctx.author.id), -total_price, 0)
        db_client.add_to_inventory(str(ctx.guild.id), str(ctx.author.id), item['item_id'], quantity)
        
        emoji = item.get('emoji') or "📦"
        await ctx.send(f"✅ You bought **{quantity}x {item['name']}** {emoji} for **{total_price:,}** coins.")

    @commands.hybrid_command(name="sell", description="Sell an item from your inventory.")
    @app_commands.describe(item_name="Name of the item", quantity="Amount to sell")
    async def sell(self, ctx: commands.Context, item_name: str, quantity: int = 1):
        if quantity <= 0:
            return await ctx.send("Quantity must be at least 1.")
            
        item = db_client.get_shop_item(str(ctx.guild.id), item_name)
        if not item:
            return await ctx.send("That item doesn't exist.")
            
        success = db_client.remove_from_inventory(str(ctx.guild.id), str(ctx.author.id), item['item_id'], quantity)
        if not success:
            return await ctx.send("You don't have enough of that item in your inventory.")
            
        sell_price = int(item['price'] * 0.5) * quantity # Sell for 50%
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
    async def use(self, ctx: commands.Context, *, item_name: str):
        item = db_client.get_shop_item(str(ctx.guild.id), item_name)
        if not item:
            return await ctx.send("That item doesn't exist.")
            
        success = db_client.remove_from_inventory(str(ctx.guild.id), str(ctx.author.id), item['item_id'], 1)
        if not success:
            return await ctx.send("You don't have that item.")
            
        # Implementation for specific item effects would go here.
        await ctx.send(f"You used **{item['name']}**!")

    @commands.hybrid_command(name="trade", aliases=["gift"], description="Trade or gift an item to another user.")
    async def trade(self, ctx: commands.Context, user: discord.Member, item_name: str, quantity: int = 1):
        if user == ctx.author:
            return await ctx.send("Cannot gift yourself.")
            
        item = db_client.get_shop_item(str(ctx.guild.id), item_name)
        if not item:
            return await ctx.send("That item doesn't exist.")
            
        success = db_client.remove_from_inventory(str(ctx.guild.id), str(ctx.author.id), item['item_id'], quantity)
        if not success:
            return await ctx.send("You don't have enough of that item.")
            
        db_client.add_to_inventory(str(ctx.guild.id), str(user.id), item['item_id'], quantity)
        await ctx.send(f"🎁 You gifted **{quantity}x {item['name']}** to {user.mention}.")

    # ── Admin Economy ────────────────────────────────────────────────────────

    @commands.hybrid_command(name="give", description="Give money to a user.")
    @commands.has_permissions(administrator=True)
    async def give(self, ctx: commands.Context, user: discord.Member, amount: int):
        db_client.add_economy_balance(str(ctx.guild.id), str(user.id), amount, 0)
        await ctx.send(embed=discord.Embed(description=f"✅ Added **{amount:,}** coins to {user.mention}'s wallet.", color=discord.Color.green()))

    @commands.hybrid_command(name="remove", description="Remove money from a user.")
    @commands.has_permissions(administrator=True)
    async def remove(self, ctx: commands.Context, user: discord.Member, amount: int):
        db_client.add_economy_balance(str(ctx.guild.id), str(user.id), -amount, 0)
        await ctx.send(embed=discord.Embed(description=f"✅ Removed **{amount:,}** coins from {user.mention}'s wallet.", color=discord.Color.green()))

    @commands.hybrid_command(name="reset", description="Reset a user's economy data completely.")
    @commands.has_permissions(administrator=True)
    async def reset(self, ctx: commands.Context, user: discord.Member):
        db_client.delete_economy_user(str(ctx.guild.id), str(user.id))
        await ctx.send(embed=discord.Embed(description=f"⚠️ Reset economy data for {user.mention}.", color=discord.Color.orange()))

    @commands.hybrid_command(name="additem", description="Add an item to the shop.")
    @commands.has_permissions(administrator=True)
    async def additem(self, ctx: commands.Context, name: str, price: int, emoji: str = None, desc: str = None):
        data = {
            "guild_id": str(ctx.guild.id),
            "name": name,
            "price": price,
            "emoji": emoji,
            "description": desc
        }
        if db_client.add_shop_item(data):
            await ctx.send(f"✅ Added **{name}** to the shop for **{price}** coins.")
        else:
            await ctx.send("❌ Failed to add item.")

    @commands.hybrid_command(name="removeitem", description="Remove an item from the shop.")
    @commands.has_permissions(administrator=True)
    async def removeitem(self, ctx: commands.Context, name: str):
        if db_client.remove_shop_item(str(ctx.guild.id), name):
            await ctx.send(f"✅ Removed **{name}** from the shop.")
        else:
            await ctx.send("❌ Failed to remove item.")


    @commands.hybrid_command(name="equip", description="Equip a role item from your inventory.")
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
            # Calculate readable time
            m, s = divmod(error.retry_after, 60)
            h, m = divmod(m, 60)
            d, h = divmod(h, 24)
            time_str = f"{int(d)}d {int(h)}h {int(m)}m {int(s)}s".replace("0d ", "").replace("0h ", "").replace("0m ", "")
            await ctx.send(embed=discord.Embed(description=f"⏱️ This command is on cooldown. Try again in **{time_str}**.", color=discord.Color.orange()), ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(EconomyCog(bot))
