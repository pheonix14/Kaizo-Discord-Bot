import logger
tokens = logger.get_tokens()
print("Currently stored tokens in Supabase:")
for t in tokens:
    print(f"ID: {t.get('id')}")
    print(f"Label: {t.get('label')}")
    print(f"Token: {t.get('token')[:15]}...")
    print(f"Guild ID: {t.get('guild_id')}")
    print(f"Channel ID: {t.get('channel_id')}")
    print(f"Active: {t.get('active')}")
    print(f"Spam Active: {t.get('spam_active')}")
    print(f"OwO Active: {t.get('owo_active')}")
    print(f"OwO Channel ID: {t.get('owo_channel_id')}")
