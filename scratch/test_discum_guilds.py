import discum
token = "MTUwNDQwNjE3NTg1NTI4MDE5OQ.Gyji4K.xAbomVoMGCvby9-iH3IInUvJO-rDY-qkzbueV4"
bot = discum.Client(token=token, log=False)
r = bot.getGuilds()
print(f"Status Code: {r.status_code}")
print(f"Response: {r.text[:500]}")
