
import os

os.makedirs('templates', exist_ok=True)

# 1. index.html (Directly from REFERENCE.HTML but with Jinja data)
with open('templates/REFERENCE.HTML', 'r', encoding='utf-8') as f:
    ref = f.read()
    
# Extract body content
import re
body_match = re.search(r'<body>(.*?)<script>', ref, re.DOTALL)
if body_match:
    body_content = body_match.group(1)
    # Replace the wipe div completely as we removed doWipe
    body_content = re.sub(r'<div id=\"wipe\"></div>', '', body_content)
    
    # Change Contact form to Login Button
    contact_section = '''    <!-- -- 05 CONTACT -- -->
    <section id=\"s05\">
        <span class=\"contact-title-let display\" id=\"cLet\">LOGIN</span>
        <span class=\"contact-title-create display\" id=\"cCreate\">REQUIRED</span>
        
        <div style=\"margin-top: 40px; position: relative; z-index: 5;\">
            {% if user %}
                <a href=\"/dashboard\" style=\"display: inline-block; padding: 16px 40px; background: var(--teal); color: var(--navy); text-decoration: none; font-size: 14px; font-weight: bold; border-radius: 100px; letter-spacing: 0.2em; text-transform: uppercase;\">OPEN DASHBOARD</a>
            {% else %}
                <a href=\"/login\" style=\"display: inline-block; padding: 16px 40px; background: var(--teal); color: var(--navy); text-decoration: none; font-size: 14px; font-weight: bold; border-radius: 100px; letter-spacing: 0.2em; text-transform: uppercase;\">LOGIN WITH DISCORD</a>
            {% endif %}
        </div>
        
        <div class=\"footer-tag\" id=\"footerTag\">KAIZER &copy; MMXXV</div>
    </section>'''
    
    body_content = re.sub(r'<!-- -- 05 CONTACT -- -->.*?</section>', contact_section, body_content, flags=re.DOTALL)

index_html = f'''<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no\">
    <title>KAIZER K5</title>
    <link rel=\"preconnect\" href=\"https://fonts.googleapis.com\">
    <link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin>
    <link href=\"https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Space+Grotesk:wght@300;400;500&family=Playfair+Display:ital@1&display=swap\" rel=\"stylesheet\">
    <link rel=\"stylesheet\" href=\"/static/css/style.css\">
</head>
<body>
    <script>
        window.KAIZER_STATE = {{
            user: {{{{ (user if user is defined else none) | tojson }}}},
            guild_id: {{{{ (guild_id if guild_id is defined else none) | tojson }}}},
            active_page: \"index\"
        }};
    </script>
    <script src=\"/static/js/navigationbar.js\"></script>
    
    {{body_content}}
    
    <script src=\"/static/js/core.js\"></script>
</body>
</html>'''

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(index_html)


# 2. dashboard.html
dashboard_html = f'''<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no\">
    <title>KAIZER K5 - Dashboard</title>
    <link rel=\"preconnect\" href=\"https://fonts.googleapis.com\">
    <link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin>
    <link href=\"https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Space+Grotesk:wght@300;400;500&family=Playfair+Display:ital@1&display=swap\" rel=\"stylesheet\">
    <link rel=\"stylesheet\" href=\"/static/css/style.css\">
    <style>
        body {{ overflow-y: auto; background: var(--dark); padding-top: 80px; padding-bottom: 50px; }}
        .dashboard-container {{ max-width: 1000px; margin: 0 auto; padding: 20px; }}
        .header-title {{ font-size: clamp(40px, 12vw, 80px); color: #fff; line-height: 0.9; margin-bottom: 40px; }}
        .server-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }}
        .server-card {{ 
            background: rgba(255, 255, 255, 0.03); 
            border: 1px solid rgba(255, 255, 255, 0.08); 
            border-radius: 12px; 
            padding: 24px; 
            display: flex; 
            flex-direction: column; 
            align-items: center; 
            text-decoration: none; 
            color: #fff; 
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            position: relative;
            overflow: hidden;
        }}
        .server-card:hover {{ 
            transform: translateY(-5px); 
            background: rgba(78, 205, 196, 0.08); 
            border-color: rgba(78, 205, 196, 0.3); 
        }}
        .server-card::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: radial-gradient(circle at top right, rgba(201, 168, 76, 0.1), transparent 70%);
            opacity: 0;
            transition: opacity 0.3s;
        }}
        .server-card:hover::before {{ opacity: 1; }}
        .server-icon {{ width: 80px; height: 80px; border-radius: 50%; margin-bottom: 20px; border: 2px solid rgba(255, 255, 255, 0.1); }}
        .server-icon-placeholder {{ width: 80px; height: 80px; border-radius: 50%; background: #1a1a2e; display: flex; align-items: center; justify-content: center; font-size: 32px; font-weight: bold; margin-bottom: 20px; color: var(--teal); border: 2px solid rgba(255, 255, 255, 0.1); }}
        .server-name {{ font-size: 20px; font-weight: 500; text-align: center; letter-spacing: -0.02em; z-index: 2; }}
    </style>
</head>
<body>
    <script>
        window.KAIZER_STATE = {{
            user: {{{{ (user if user is defined else none) | tojson }}}},
            guild_id: {{{{ (guild_id if guild_id is defined else none) | tojson }}}},
            active_page: \"dashboard\"
        }};
    </script>
    <script src=\"/static/js/navigationbar.js\"></script>
    
    <div class=\"dashboard-container\">
        <h1 class=\"header-title display\">SELECT<br><span style=\"color: var(--teal)\">SERVER</span></h1>
        
        <div class=\"server-grid\">
            {{% if user and user.guilds %}}
                {{% for guild in user.guilds %}}
                    {{% if guild.permissions and (guild.permissions | int) & 8 == 8 %}}
                    <a href=\"/server/{{{{ guild.id }}}}\" class=\"server-card\">
                        {{% if guild.icon %}}
                            <img src=\"https://cdn.discordapp.com/icons/{{{{ guild.id }}}}/{{{{ guild.icon }}}}.png\" class=\"server-icon\">
                        {{% else %}}
                            <div class=\"server-icon-placeholder display\">{{{{ guild.name[0] }}}}</div>
                        {{% endif %}}
                        <div class=\"server-name\">{{{{ guild.name }}}}</div>
                    </a>
                    {{% endif %}}
                {{% endfor %}}
            {{% else %}}
                <div style=\"color: var(--orange); font-size: 18px; letter-spacing: 0.1em;\">NO SERVERS FOUND. PLEASE LOGIN.</div>
            {{% endif %}}
        </div>
    </div>
</body>
</html>'''

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(dashboard_html)

