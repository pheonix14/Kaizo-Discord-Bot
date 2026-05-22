import os
import re

cogs_dir = "src/bot/cogs"
limit = 25

for file in os.listdir(cogs_dir):
    if not file.endswith(".py"): continue
    filepath = os.path.join(cogs_dir, file)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Find all groups
    groups = re.findall(r'@commands\.hybrid_group\(name="([^"]+)"', content)
    for group in groups:
        # Count subcommands for this group
        count = len(re.findall(f'@{group}\.command', content))
        print(f"Cog {file} -> Group '{group}' has {count} subcommands.")
        if count > limit:
            print(f"  WARNING: '{group}' exceeds {limit} subcommands!")
