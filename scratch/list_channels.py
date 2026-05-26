import discum
token = "MTUwNDQwNjE3NTg1NTI4MDE5OQ.Gyji4K.xAbomVoMGCvby9-iH3IInUvJO-rDY-qkzbueV4"

bot = discum.Client(token=token, log=False)
print("Fetching guilds...")
r = bot.getGuilds()
if r.status_code == 200:
    guilds = r.json()
    print(f"Token has access to {len(guilds)} guild(s):")
    for g in guilds:
        g_id = g.get("id")
        g_name = g.get("name")
        print(f"\nGuild: {g_name} (ID: {g_id})")
        cr = bot.getGuildChannels(g_id)
        if cr.status_code == 200:
            channels = cr.json()
            text_channels = [c for c in channels if c.get("type") in [0, 5]]
            print(f"  Text channels:")
            for ch in text_channels:
                print(f"    - #{ch.get('name')} (ID: {ch.get('id')})")
        else:
            print(f"  Failed to fetch channels (HTTP {cr.status_code})")
else:
    print(f"Failed to fetch guilds (HTTP {r.status_code}): {r.text}")
