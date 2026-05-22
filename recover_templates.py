
import os

os.makedirs('templates', exist_ok=True)

templates = {
'index.html': '''<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>Kaizer K5 - Discord Bot</title>
    <link rel=\"stylesheet\" href=\"/static/css/style.css\">
</head>
<body>
    <script>
        window.KAIZER_STATE = {
            user: {{ (user if user is defined else none) | tojson }},
            guild_id: {{ (guild_id if guild_id is defined else none) | tojson }},
            active_page: \"index\"
        };
    </script>
    <script src=\"/static/js/navigationbar.js\"></script>
    <main style=\"padding-top: 80px; text-align: center; color: white;\">
        <h1>Welcome to Kaizer K5</h1>
        <p>The ultimate Discord moderation and economy bot.</p>
        <a href=\"/login\" class=\"btn btn-primary\">Login with Discord</a>
    </main>
</body>
</html>'''
}

for name, content in templates.items():
    with open(os.path.join('templates', name), 'w', encoding='utf-8') as f:
        f.write(content)

