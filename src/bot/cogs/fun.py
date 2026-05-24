import discord
from discord.ext import commands
from discord import app_commands
import random
import aiohttp
import asyncio
import pyfiglet
import html
import urllib.parse
from typing import Optional

# ── Helper Views for Games ─────────────────────────────────────────────────

class TicTacToeButton(discord.ui.Button['TicTacToe']):
    def __init__(self, x: int, y: int):
        super().__init__(style=discord.ButtonStyle.secondary, label='\u200b', row=y)
        self.x = x
        self.y = y

    async def callback(self, interaction: discord.Interaction):
        view: TicTacToe = self.view
        state = view.board[self.y][self.x]
        if state in (view.X, view.O):
            return

        if interaction.user == view.player1 and view.current_player == view.X:
            self.style = discord.ButtonStyle.danger
            self.label = 'X'
            self.disabled = True
            view.board[self.y][self.x] = view.X
            view.current_player = view.O
            content = f"It is now {view.player2.mention}'s turn."
        elif interaction.user == view.player2 and view.current_player == view.O:
            self.style = discord.ButtonStyle.success
            self.label = 'O'
            self.disabled = True
            view.board[self.y][self.x] = view.O
            view.current_player = view.X
            content = f"It is now {view.player1.mention}'s turn."
        else:
            return await interaction.response.send_message("It's not your turn!", ephemeral=True)

        winner = view.check_board_winner()
        if winner is not None:
            if winner == view.X:
                content = f"{view.player1.mention} won!"
            elif winner == view.O:
                content = f"{view.player2.mention} won!"
            else:
                content = "It's a tie!"
            
            for child in view.children:
                child.disabled = True
            view.stop()

        await interaction.response.edit_message(content=content, view=view)


class TicTacToe(discord.ui.View):
    children: list[TicTacToeButton]
    X = -1
    O = 1
    Tie = 2

    def __init__(self, player1: discord.Member, player2: discord.Member):
        super().__init__()
        self.current_player = self.X
        self.board = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]
        self.player1 = player1
        self.player2 = player2

        for y in range(3):
            for x in range(3):
                self.add_item(TicTacToeButton(x, y))

    def check_board_winner(self):
        for across in self.board:
            value = sum(across)
            if value == 3: return self.O
            elif value == -3: return self.X

        for line in range(3):
            value = self.board[0][line] + self.board[1][line] + self.board[2][line]
            if value == 3: return self.O
            elif value == -3: return self.X

        diag = self.board[0][0] + self.board[1][1] + self.board[2][2]
        if diag == 3: return self.O
        elif diag == -3: return self.X

        diag = self.board[0][2] + self.board[1][1] + self.board[2][0]
        if diag == 3: return self.O
        elif diag == -3: return self.X

        if all(i != 0 for row in self.board for i in row):
            return self.Tie

        return None


class RPSView(discord.ui.View):
    def __init__(self, ctx, user_choice):
        super().__init__(timeout=0)
        self.ctx = ctx
        self.user_choice = user_choice
        self.bot_choice = random.choice(["rock", "paper", "scissors"])
        
    def get_result(self):
        u, b = self.user_choice, self.bot_choice
        if u == b: return "It's a tie!"
        if (u=="rock" and b=="scissors") or (u=="paper" and b=="rock") or (u=="scissors" and b=="paper"):
            return "You won!"
        return "I won!"


class TriviaView(discord.ui.View):
    def __init__(self, ctx, question_data):
        super().__init__(timeout=20.0)
        self.ctx = ctx
        self.correct_answer = html.unescape(question_data['correct_answer'])
        self.answers = [self.correct_answer] + [html.unescape(a) for a in question_data['incorrect_answers']]
        random.shuffle(self.answers)
        
        for i, ans in enumerate(self.answers):
            btn = discord.ui.Button(label=ans[:80], custom_id=str(i), style=discord.ButtonStyle.primary)
            btn.callback = self.make_callback(ans)
            self.add_item(btn)
            
    def make_callback(self, answer):
        async def callback(interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                return await interaction.response.send_message("Not your trivia!", ephemeral=True)
                
            for child in self.children:
                child.disabled = True
                if child.label == self.correct_answer:
                    child.style = discord.ButtonStyle.success
                elif child.label == answer and answer != self.correct_answer:
                    child.style = discord.ButtonStyle.danger
                    
            if answer == self.correct_answer:
                content = "Correct!"
            else:
                content = f"Wrong! The correct answer was **{self.correct_answer}**."
                
            await interaction.response.edit_message(content=content, view=self)
            self.stop()
        return callback

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
            if child.label == self.correct_answer:
                child.style = discord.ButtonStyle.success
        try:
            await self.message.edit(content="Time's up!", view=self)
        except Exception:
            pass


class FunCog(commands.Cog, name="Fun"):
    """Entertainment, games, and fun commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Hardcoded lists for RNG
        self.eight_ball = ["It is certain.", "It is decidedly so.", "Without a doubt.", "Yes definitely.",
                           "You may rely on it.", "As I see it, yes.", "Most likely.", "Outlook good.", "Yes.",
                           "Signs point to yes.", "Reply hazy, try again.", "Ask again later.",
                           "Better not tell you now.", "Cannot predict now.", "Concentrate and ask again.",
                           "Don't count on it.", "My reply is no.", "My sources say no.",
                           "Outlook not so good.", "Very doubtful."]
                           
        self.compliments = ["You are awesome!", "You have a great sense of humor.", "You light up the room.",
                            "You are incredibly thoughtful.", "Your creative potential seems limitless.",
                            "You are a gift to those around you.", "You are better than a unicorn.",
                            "You bring out the best in other people.", "You are really something special."]
                            
        self.roasts = ["You're like a cloud. When you disappear, it's a beautiful day.",
                       "I'd agree with you but then we'd both be wrong.",
                       "You bring everyone so much joy... when you leave the room.",
                       "I love what you've done with your hair. How do you get it to come out of the nostrils like that?",
                       "You're the reason the gene pool needs a lifeguard."]
                       
        self.dares = ["Send a voice message of you singing a pop song.", "Text your crush right now.",
                      "Do 20 pushups.", "Change your Discord nickname to something embarrassing for an hour.",
                      "Speak in an accent for the next 10 minutes.", "Let the person who dared you write a status for you."]
                      
        self.truths = ["What's the most embarrassing thing you've done?", "Who is your secret crush?",
                       "What's a secret you've never told anyone?", "When was the last time you lied?",
                       "What's the worst trouble you got into as a kid?"]
                       
        self.would_you_rathers = ["Would you rather be able to fly or be invisible?",
                                  "Would you rather always have to say everything on your mind or never speak again?",
                                  "Would you rather have unlimited free food or free travel?",
                                  "Would you rather live in the past or the future?",
                                  "Would you rather find true love or win the lottery?"]

    @commands.hybrid_group(name="fun", description="Fun commands.", fallback="help")
    async def fun(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @commands.hybrid_group(name="games", description="Minigames.", fallback="help")
    async def games(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    # ── Basic RNG ────────────────────────────────────────────────────────────

    @fun.command(name="8ball", aliases=["8b"], description="Ask the magic 8-ball a question.")
    @app_commands.describe(question="The question to ask")
    async def eightball(self, ctx: commands.Context, *, question: str):
        answer = random.choice(self.eight_ball)
        embed = discord.Embed(title="🎱 Magic 8-Ball", color=0x3498DB)
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Answer", value=answer, inline=False)
        await ctx.send(embed=embed)

    @fun.command(name="compliment", description="Send a compliment to a member.")
    async def compliment(self, ctx: commands.Context, user: discord.Member):
        if user == ctx.author:
            return await ctx.send(f"{ctx.author.mention}, you're awesome for trying to compliment yourself!")
        await ctx.send(f"💖 {user.mention}, {random.choice(self.compliments)}")

    @fun.command(name="roast", description="Send a harmless roast to a member.")
    async def roast(self, ctx: commands.Context, user: discord.Member):
        if user == self.bot.user:
            return await ctx.send("I'm immune to your roasts.")
        await ctx.send(f"🔥 {user.mention}, {random.choice(self.roasts)}")

    @fun.command(name="dare", description="Get a random dare challenge.")
    async def dare(self, ctx: commands.Context):
        await ctx.send(embed=discord.Embed(title="🔥 Dare", description=random.choice(self.dares), color=0xE74C3C))

    @fun.command(name="truth", description="Get a random truth question.")
    async def truth(self, ctx: commands.Context):
        await ctx.send(embed=discord.Embed(title="💡 Truth", description=random.choice(self.truths), color=0x3498DB))

    @fun.command(name="wouldyourather", aliases=["wyr"], description="Get a Would You Rather scenario.")
    async def wouldyourather(self, ctx: commands.Context):
        await ctx.send(embed=discord.Embed(title="🤔 Would You Rather...", description=random.choice(self.would_you_rathers), color=0x9B59B6))

    @fun.command(name="rate", description="Rate something out of 10.")
    async def rate(self, ctx: commands.Context, *, thing: str):
        rating = random.randint(0, 100)
        await ctx.send(f"I rate **{thing}** a solid **{rating}/100**.")

    @fun.command(name="ship", description="Calculate ship compatibility between two users.")
    async def ship(self, ctx: commands.Context, user1: discord.Member, user2: discord.Member):
        percent = random.randint(0, 100)
        bar = "█" * (percent // 10) + "░" * (10 - (percent // 10))
        embed = discord.Embed(title="❤️ Compatibility", description=f"**{user1.display_name}** x **{user2.display_name}**\n\n{bar} **{percent}%**", color=0xE91E63)
        await ctx.send(embed=embed)

    @fun.command(name="dice", aliases=["roll"], description="Roll one or more dice.")
    @app_commands.describe(sides="Number of sides", count="Number of dice")
    async def dice(self, ctx: commands.Context, sides: int = 6, count: int = 1):
        if count < 1 or count > 50:
            return await ctx.send("Count must be between 1 and 50.")
        if sides < 2 or sides > 1000:
            return await ctx.send("Sides must be between 2 and 1000.")
            
        rolls = [random.randint(1, sides) for _ in range(count)]
        total = sum(rolls)
        rolls_str = ", ".join(str(r) for r in rolls)
        if len(rolls_str) > 1000:
            rolls_str = rolls_str[:1000] + "..."
            
        embed = discord.Embed(title="🎲 Dice Roll", color=0x3498DB)
        embed.add_field(name="Rolls", value=rolls_str, inline=False)
        embed.add_field(name="Total", value=str(total), inline=False)
        await ctx.send(embed=embed)

    # ── Text Manipulators ────────────────────────────────────────────────────

    @fun.command(name="ascii", description="Convert text into ASCII art.")
    async def ascii_text(self, ctx: commands.Context, *, text: str):
        if len(text) > 20:
            return await ctx.send("Text too long. Max 20 characters.")
        result = pyfiglet.figlet_format(text)
        if len(result) > 1900:
            return await ctx.send("Resulting ASCII art is too large for Discord.")
        await ctx.send(f"```\n{result}\n```")

    @fun.command(name="emojify", description="Convert text to regional indicator emojis.")
    async def emojify(self, ctx: commands.Context, *, text: str):
        mapping = {
            'a': '🇦', 'b': '🇧', 'c': '🇨', 'd': '🇩', 'e': '🇪', 'f': '🇫', 'g': '🇬', 'h': '🇭',
            'i': '🇮', 'j': '🇯', 'k': '🇰', 'l': '🇱', 'm': '🇲', 'n': '🇳', 'o': '🇴', 'p': '🇵',
            'q': '🇶', 'r': '🇷', 's': '🇸', 't': '🇹', 'u': '🇺', 'v': '🇻', 'w': '🇼', 'x': '🇽',
            'y': '🇾', 'z': '🇿', '0': '0️⃣', '1': '1️⃣', '2': '2️⃣', '3': '3️⃣', '4': '4️⃣',
            '5': '5️⃣', '6': '6️⃣', '7': '7️⃣', '8': '8️⃣', '9': '9️⃣', '!': '❗', '?': '❓'
        }
        res = ""
        for char in text.lower():
            if char in mapping:
                res += mapping[char] + " "
            elif char == " ":
                res += "   "
            else:
                res += char
                
        if len(res) > 2000:
            return await ctx.send("Result is too long!")
        await ctx.send(res)

    @fun.command(name="mock", description="MoCk AnY tExT lIkE tHiS.")
    async def mock(self, ctx: commands.Context, *, text: str):
        res = "".join(random.choice([c.upper(), c.lower()]) for c in text)
        await ctx.send(res)

    @fun.command(name="reverse", description="Reverse input text.")
    async def reverse(self, ctx: commands.Context, *, text: str):
        await ctx.send(text[::-1])


    # ── APIs ─────────────────────────────────────────────────────────────────

    @fun.command(name="joke", description="Get a random joke.")
    async def joke(self, ctx: commands.Context, category: str = "Any"):
        url = f"https://v2.jokeapi.dev/joke/{category}?blacklistFlags=nsfw,religious,political,racist,sexist,explicit"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as r:
                    data = await r.json()
                    if data.get('error'):
                        return await ctx.send("Could not find a joke.")
                    
                    if data['type'] == 'single':
                        await ctx.send(data['joke'])
                    else:
                        await ctx.send(f"{data['setup']}\n\n||{data['delivery']}||")
        except Exception:
            await ctx.send("Error fetching joke.")

    @fun.command(name="fact", description="Get a random fact.")
    async def fact(self, ctx: commands.Context):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://uselessfacts.jsph.pl/api/v2/facts/random") as r:
                    data = await r.json()
                    await ctx.send(f"🧠 **Fact:** {data['text']}")
        except Exception:
            await ctx.send("Error fetching fact.")

    @fun.command(name="quote", description="Get a random quote.")
    async def quote(self, ctx: commands.Context):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://zenquotes.io/api/random") as r:
                    if r.status != 200:
                        return await ctx.send("Could not fetch quote.")
                    data = await r.json()
                    if isinstance(data, list) and len(data) > 0:
                        quote_text = data[0].get("q")
                        author = data[0].get("a", "Unknown")
                        embed = discord.Embed(description=f'"{quote_text}"', color=0x3498DB)
                        embed.set_footer(text=f"— {author}")
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send("Could not parse quote data.")
        except Exception:
            await ctx.send("Error fetching quote.")

    @fun.command(name="meme", description="Get a random meme from Reddit.")
    async def meme(self, ctx: commands.Context, subreddit: str = None):
        url = f"https://meme-api.com/gimme/{subreddit}" if subreddit else "https://meme-api.com/gimme"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as r:
                    if r.status != 200:
                        return await ctx.send("Could not fetch meme.")
                    data = await r.json()
                    if data.get('nsfw') and not ctx.channel.is_nsfw():
                        return await ctx.send("This meme is NSFW. Go to an NSFW channel.")
                        
                    embed = discord.Embed(title=data.get('title'), url=data.get('postLink'), color=0x3498DB)
                    embed.set_image(url=data.get('url'))
                    embed.set_footer(text=f"r/{data.get('subreddit')}")
                    await ctx.send(embed=embed)
        except Exception:
            await ctx.send("Error fetching meme.")

    # ── Interactive Games ────────────────────────────────────────────────────

    @games.command(name="rps", description="Play Rock Paper Scissors.")
    @app_commands.choices(choice=[
        app_commands.Choice(name="Rock", value="rock"),
        app_commands.Choice(name="Paper", value="paper"),
        app_commands.Choice(name="Scissors", value="scissors"),
    ])
    async def rps(self, ctx: commands.Context, choice: str):
        choice = choice.lower()
        if choice not in ["rock", "paper", "scissors"]:
            return await ctx.send("Please choose rock, paper, or scissors.")
            
        bot_choice = random.choice(["rock", "paper", "scissors"])
        emojis = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
        
        result = "It's a tie!"
        if (choice=="rock" and bot_choice=="scissors") or (choice=="paper" and bot_choice=="rock") or (choice=="scissors" and bot_choice=="paper"):
            result = "You won!"
        elif (bot_choice=="rock" and choice=="scissors") or (bot_choice=="paper" and choice=="rock") or (bot_choice=="scissors" and choice=="paper"):
            result = "I won!"
            
        embed = discord.Embed(title="Rock Paper Scissors", color=0x3498DB)
        embed.add_field(name="You", value=f"{emojis[choice]} {choice.title()}", inline=True)
        embed.add_field(name="Bot", value=f"{emojis[bot_choice]} {bot_choice.title()}", inline=True)
        embed.add_field(name="Result", value=result, inline=False)
        await ctx.send(embed=embed)

    @games.command(name="tictactoe", aliases=["ttt"], description="Play TicTacToe with another user.")
    async def tictactoe(self, ctx: commands.Context, user: discord.Member):
        if user.bot or user == ctx.author:
            return await ctx.send("You must challenge another real user.")
            
        await ctx.send(f"Tic Tac Toe: {ctx.author.mention} vs {user.mention}\n{ctx.author.mention} goes first (X)!", view=TicTacToe(ctx.author, user))

    @games.command(name="trivia", description="Answer a trivia question.")
    async def trivia(self, ctx: commands.Context):
        url = "https://opentdb.com/api.php?amount=1&type=multiple"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as r:
                    data = await r.json()
                    question_data = data['results'][0]
                    question = html.unescape(question_data['question'])
                    category = html.unescape(question_data['category'])
                    diff = question_data['difficulty'].title()
                    
                    embed = discord.Embed(title="Trivia", description=question, color=0x3498DB)
                    embed.set_footer(text=f"Category: {category} | Difficulty: {diff}")
                    
                    view = TriviaView(ctx, question_data)
                    view.message = await ctx.send(embed=embed, view=view)
        except Exception:
            await ctx.send("Failed to fetch trivia question.")

    @games.command(name="wordle", description="Play Wordle in Discord.")
    async def wordle(self, ctx: commands.Context):
        words = ["APPLE", "BRAIN", "CRASH", "DRIVE", "EAGLE", "FROST", "GHOST", "HOUSE", "INDEX", "JUMPS", "KNIFE", "LEMON", "MAGIC", "NIGHT", "OCEAN", "PIZZA", "QUEEN", "RIVER", "SNAKE", "TRAIN", "UNDER", "VOICE", "WATER", "YOUTH", "ZEBRA"]
        secret = random.choice(words)
        guesses = []
        max_guesses = 6
        
        await ctx.send("🟩🟨⬛ **Discord Wordle** ⬛🟨🟩\nI have chosen a 5-letter word. Type your guess in chat!")
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and len(m.content) == 5 and m.content.isalpha()
            
        while len(guesses) < max_guesses:
            try:
                msg = await self.bot.wait_for('message', timeout=60.0, check=check)
            except asyncio.TimeoutError:
                return await ctx.send(f"Time's up! The word was **{secret}**.")
                
            guess = msg.content.upper()
            result = ""
            secret_list = list(secret)
            
            # Exact matches (Green)
            for i in range(5):
                if guess[i] == secret[i]:
                    result += "🟩"
                    secret_list[i] = None
                else:
                    result += "X"
                    
            # Partial matches (Yellow) and Misses (Black)
            final_result = ""
            for i in range(5):
                if result[i] == "🟩":
                    final_result += "🟩"
                elif guess[i] in secret_list:
                    final_result += "🟨"
                    secret_list[secret_list.index(guess[i])] = None
                else:
                    final_result += "⬛"
                    
            guesses.append(f"`{guess}` {final_result}")
            
            board = "\n".join(guesses)
            if guess == secret:
                return await ctx.send(f"{board}\n\n🎉 **You got it!** The word was **{secret}**.")
            elif len(guesses) == max_guesses:
                return await ctx.send(f"{board}\n\n💀 **Game Over!** The word was **{secret}**.")
            else:
                await ctx.send(f"{board}\n*You have {max_guesses - len(guesses)} guesses left.*")

    @games.command(name="hangman", description="Play Hangman in Discord.")
    async def hangman(self, ctx: commands.Context):
        words = ["PYTHON", "DISCORD", "COMPUTER", "KEYBOARD", "MOUSE", "SERVER", "INTERNET", "DEVELOPER", "SOFTWARE"]
        secret = random.choice(words)
        guessed = set()
        lives = 6
        
        stages = [
            "```\n  +---+\n  |   |\n      |\n      |\n      |\n      |\n=========```",
            "```\n  +---+\n  |   |\n  O   |\n      |\n      |\n      |\n=========```",
            "```\n  +---+\n  |   |\n  O   |\n  |   |\n      |\n      |\n=========```",
            "```\n  +---+\n  |   |\n  O   |\n /|   |\n      |\n      |\n=========```",
            "```\n  +---+\n  |   |\n  O   |\n /|\\  |\n      |\n      |\n=========```",
            "```\n  +---+\n  |   |\n  O   |\n /|\\  |\n /    |\n      |\n=========```",
            "```\n  +---+\n  |   |\n  O   |\n /|\\  |\n / \\  |\n      |\n=========```"
        ]
        
        def get_display():
            disp = " ".join([c if c in guessed else "_" for c in secret])
            return disp
            
        await ctx.send(f"🎮 **Hangman**\nType a single letter in chat to guess!\n{stages[0]}\nWord: `{get_display()}`")
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and len(m.content) == 1 and m.content.isalpha()
            
        while lives > 0:
            try:
                msg = await self.bot.wait_for('message', timeout=60.0, check=check)
            except asyncio.TimeoutError:
                return await ctx.send(f"Time's up! The word was **{secret}**.")
                
            guess = msg.content.upper()
            if guess in guessed:
                await ctx.send("You already guessed that letter!")
                continue
                
            guessed.add(guess)
            
            if guess not in secret:
                lives -= 1
                
            disp = get_display()
            if "_" not in disp:
                return await ctx.send(f"{stages[6-lives]}\nWord: `{disp}`\n🎉 **You won!**")
                
            if lives == 0:
                return await ctx.send(f"{stages[6]}\n💀 **Game Over!** The word was **{secret}**.")
                
            await ctx.send(f"{stages[6-lives]}\nWord: `{disp}`\nGuessed: {', '.join(sorted(guessed))}")

    async def cog_load(self):
        # Dynamically register top-level prefix commands for all subcommands of the 'fun' group
        # Using standard commands.command to avoid exceeding Discord's 100 slash command limit
        for cmd in list(self.fun.commands):
            top_cmd = commands.command(
                name=cmd.name,
                description=cmd.description,
                help=cmd.help
            )(cmd.callback)
            top_cmd.cog = self
            top_cmd.checks = cmd.checks.copy()
            self.bot.add_command(top_cmd)

async def setup(bot: commands.Bot):
    await bot.add_cog(FunCog(bot))
