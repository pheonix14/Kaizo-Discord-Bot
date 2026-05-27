import re

with open('src/bot/cogs/fun.py', 'r', encoding='utf-8') as f:
    code = f.read()

group_defs = '''
    @commands.hybrid_group(name="fun", description="Fun commands.", invoke_without_command=True)
    async def fun(self, ctx: commands.Context):
        pass

    @commands.hybrid_group(name="games", description="Minigames.", invoke_without_command=True)
    async def games(self, ctx: commands.Context):
        pass
'''
code = code.replace('def __init__(self, bot: commands.Bot):\n        self.bot = bot', 'def __init__(self, bot: commands.Bot):\n        self.bot = bot\n' + group_defs)

def repl(m):
    line = m.group(0)
    if 'rps' in line or 'tictactoe' in line or 'trivia' in line or 'wordle' in line or 'hangman' in line:
        return line.replace('@commands.hybrid_command(', '@games.command(')
    return line.replace('@commands.hybrid_command(', '@fun.command(')

code = re.sub(r'@commands\.hybrid_command\([^)]+\)', repl, code)

with open('src/bot/cogs/fun.py', 'w', encoding='utf-8') as f:
    f.write(code)

# Do the same for economy
with open('src/bot/cogs/economy.py', 'r', encoding='utf-8') as f:
    code = f.read()

group_defs = '''
    @commands.hybrid_group(name="eco", description="Economy commands.", invoke_without_command=True)
    async def eco(self, ctx: commands.Context):
        pass
'''
code = code.replace('def __init__(self, bot: commands.Bot):\n        self.bot = bot', 'def __init__(self, bot: commands.Bot):\n        self.bot = bot\n' + group_defs)

code = re.sub(r'@commands\.hybrid_command\([^)]+\)', lambda m: m.group(0).replace('@commands.hybrid_command(', '@eco.command('), code)

with open('src/bot/cogs/economy.py', 'w', encoding='utf-8') as f:
    f.write(code)

# Do the same for utility
with open('src/bot/cogs/utility.py', 'r', encoding='utf-8') as f:
    code = f.read()

group_defs = '''
    @commands.hybrid_group(name="util", description="Utility commands.", invoke_without_command=True)
    async def util(self, ctx: commands.Context):
        pass
'''
code = code.replace('self.reminders = []', 'self.reminders = []\n' + group_defs)

code = re.sub(r'@commands\.hybrid_command\([^)]+\)', lambda m: m.group(0).replace('@commands.hybrid_command(', '@util.command('), code)

with open('src/bot/cogs/utility.py', 'w', encoding='utf-8') as f:
    f.write(code)
