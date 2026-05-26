import discum
token = "MTUwNDQwNjE3NTg1NTI4MDE5OQ.Gyji4K.xAbomVoMGCvby9-iH3IInUvJO-rDY-qkzbueV4"
channel_id = "1305417409249054761"

bot = discum.Client(token=token, log=True)
try:
    r = bot.getMessages(channel_id, num=50)
    print("Response status code:", getattr(r, 'status_code', None))
    print("Response text:", getattr(r, 'text', 'No text'))
except Exception as e:
    print("Exception occurred:", e)
