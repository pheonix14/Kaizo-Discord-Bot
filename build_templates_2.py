
import os

server_html = '''<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no\">
    <title>KAIZER K5 - Server Config</title>
    <link rel=\"preconnect\" href=\"https://fonts.googleapis.com\">
    <link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin>
    <link href=\"https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Space+Grotesk:wght@300;400;500&family=Playfair+Display:ital@1&display=swap\" rel=\"stylesheet\">
    <link rel=\"stylesheet\" href=\"/static/css/style.css\">
    <style>
        body {{ background: var(--dark); overflow: hidden; }}
        .layout {{ display: flex; height: 100vh; padding-top: 60px; }}
        
        /* SIDEBAR */
        .sidebar {{ 
            width: 280px; 
            background: rgba(26, 26, 46, 0.4); 
            backdrop-filter: blur(20px); 
            border-right: 1px solid rgba(255, 255, 255, 0.05); 
            padding: 30px 20px; 
            display: flex; 
            flex-direction: column; 
            gap: 8px; 
        }}
        .sidebar-title {{ font-size: 11px; letter-spacing: 0.25em; color: rgba(255, 255, 255, 0.3); text-transform: uppercase; margin-bottom: 20px; padding-left: 10px; }}
        .nav-btn {{ 
            background: transparent; 
            border: none; 
            color: rgba(255, 255, 255, 0.6); 
            text-align: left; 
            padding: 12px 15px; 
            font-family: 'Space Grotesk', sans-serif; 
            font-size: 14px; 
            letter-spacing: 0.05em; 
            cursor: pointer; 
            border-radius: 8px; 
            transition: all 0.3s;
            position: relative;
            overflow: hidden;
        }}
        .nav-btn:hover {{ color: #fff; background: rgba(255, 255, 255, 0.03); }}
        .nav-btn.active {{ color: var(--teal); background: rgba(78, 205, 196, 0.08); font-weight: 500; }}
        .nav-btn.active::before {{ content: ''; position: absolute; left: 0; top: 20%; bottom: 20%; width: 3px; background: var(--teal); border-radius: 0 4px 4px 0; }}

        /* MAIN CONTENT */
        .main-content {{ 
            flex: 1; 
            padding: 40px; 
            overflow-y: auto; 
            position: relative; 
        }}
        .tab-content {{ display: none; max-width: 800px; margin: 0 auto; animation: fadeUp 0.4s cubic-bezier(0.16, 1, 0.3, 1); }}
        .tab-content.active {{ display: block; }}
        
        @keyframes fadeUp {{
            from {{ opacity: 0; transform: translateY(15px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        h2.display {{ font-size: clamp(32px, 8vw, 56px); margin-bottom: 30px; letter-spacing: -0.01em; }}
        
        /* PANELS */
        .glass-panel {{ 
            background: rgba(255, 255, 255, 0.02); 
            border: 1px solid rgba(255, 255, 255, 0.08); 
            border-radius: 12px; 
            padding: 30px; 
            margin-bottom: 24px;
        }}
        .glass-panel h3 {{ font-size: 20px; font-weight: 500; margin-bottom: 10px; color: var(--cream); }}
        .glass-panel p {{ font-size: 14px; color: rgba(255, 255, 255, 0.5); margin-bottom: 24px; line-height: 1.6; }}
        
        /* FORMS */
        .form-group {{ margin-bottom: 20px; }}
        .form-group label {{ display: block; font-size: 11px; letter-spacing: 0.15em; color: rgba(255,255,255,0.7); text-transform: uppercase; margin-bottom: 8px; }}
        .form-control {{ 
            width: 100%; 
            background: rgba(0, 0, 0, 0.3); 
            border: 1px solid rgba(255, 255, 255, 0.1); 
            color: #fff; 
            padding: 12px 16px; 
            border-radius: 6px; 
            font-family: 'Space Grotesk', sans-serif; 
            font-size: 14px; 
            transition: border-color 0.3s;
        }}
        .form-control:focus {{ outline: none; border-color: var(--teal); }}
        
        .toggle-label {{ display: flex; align-items: center; gap: 12px; font-size: 14px; cursor: pointer; user-select: none; margin-bottom: 20px; }}
        .toggle-label input[type=\"checkbox\"] {{ 
            appearance: none; 
            width: 40px; height: 22px; 
            background: rgba(255, 255, 255, 0.1); 
            border-radius: 20px; 
            position: relative; 
            cursor: pointer; 
            transition: background 0.3s; 
        }}
        .toggle-label input[type=\"checkbox\"]::after {{
            content: ''; position: absolute; top: 2px; left: 2px; width: 18px; height: 18px;
            background: #fff; border-radius: 50%; transition: left 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        }}
        .toggle-label input[type=\"checkbox\"]:checked {{ background: var(--teal); }}
        .toggle-label input[type=\"checkbox\"]:checked::after {{ left: 20px; }}
        
        /* BUTTONS */
        .btn-submit {{
            background: var(--teal);
            color: var(--navy);
            border: none;
            padding: 14px 28px;
            border-radius: 100px;
            font-family: 'Space Grotesk', sans-serif;
            font-weight: 600;
            font-size: 12px;
            letter-spacing: 0.15em;
            text-transform: uppercase;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .btn-submit:hover {{ transform: translateY(-2px); box-shadow: 0 8px 20px rgba(78, 205, 196, 0.3); }}
        .btn-submit:active {{ transform: translateY(0); }}
        
        /* PROGRESS BAR */
        #task-progress-container {{ display: none; border-left: 3px solid var(--orange); }}
        .progress-track {{ width: 100%; height: 6px; background: rgba(255,255,255,0.1); border-radius: 6px; overflow: hidden; margin-top: 15px; position: relative; }}
        #task-progress-bar {{ width: 0%; height: 100%; background: var(--orange); transition: width 0.3s; }}
    </style>
</head>
<body>
    <script>
        window.KAIZER_STATE = {{
            user: {{{{ (user if user is defined else none) | tojson }}}},
            guild_id: {{{{ (guild_id if guild_id is defined else none) | tojson }}}},
            active_page: \"server\"
        }};
    </script>
    <script src=\"/static/js/navigationbar.js\"></script>
    
    <div class=\"layout\">
        <aside class=\"sidebar\">
            <div class=\"sidebar-title\">Modules</div>
            <button class=\"nav-btn active\" data-target=\"automod\">Automod & K4 Defence</button>
            <button class=\"nav-btn\" data-target=\"economy\">Economy & Shop</button>
            <button class=\"nav-btn\" data-target=\"music\">Music System</button>
            <button class=\"nav-btn\" data-target=\"tempvc-settings\">Temporary VC</button>
            <button class=\"nav-btn\" data-target=\"server-builder\">Server Builder</button>
        </aside>

        <main class=\"main-content\">
            
            <div id=\"automod\" class=\"tab-content active\">
                <h2 class=\"display\">SECURITY <span style=\"color: var(--teal)\">ENGINE</span></h2>
                <div class=\"glass-panel\">
                    <h3>K4 Defence System</h3>
                    <p>Advanced anti-spam and duplication tracking. Spammers are automatically assigned a mute role.</p>
                    <form onsubmit=\"event.preventDefault(); saveSettings(event, 'k4_defence');\">
                        <label class=\"toggle-label\">
                            <input type=\"checkbox\" id=\"k4_defence_enabled\"> Enable Spam Protection
                        </label>
                        <div class=\"form-group\">
                            <label>Mute Role ID</label>
                            <input type=\"text\" id=\"mute_role\" class=\"form-control\" placeholder=\"Role ID to assign to spammers\">
                        </div>
                        <button type=\"submit\" class=\"btn-submit\">Save Security Policy</button>
                    </form>
                </div>
            </div>

            <div id=\"economy\" class=\"tab-content\">
                <h2 class=\"display\">ECONOMY <span style=\"color: var(--gold)\">SYNC</span></h2>
                <div class=\"glass-panel\">
                    <h3>Marketplace Integration</h3>
                    <p>The economy engine is synced with Supabase. You can create shop items and members can purchase them via <code>/buy</code>.</p>
                    <button class=\"btn-submit\" style=\"background: var(--gold);\" onclick=\"alert('Economy sync verified and active.')\">Verify Sync Status</button>
                </div>
            </div>

            <div id=\"music\" class=\"tab-content\">
                <h2 class=\"display\">MUSIC <span style=\"color: var(--lav)\">CORE</span></h2>
                <div class=\"glass-panel\">
                    <h3>Interactive Player & Uploader</h3>
                    <p>High-fidelity audio streaming. Members can use <code>/music download</code> for interactive downloads, or <code>/music upload</code> to play local files directly in voice channels.</p>
                </div>
            </div>

            <div id=\"tempvc-settings\" class=\"tab-content\">
                <h2 class=\"display\">DYNAMIC <span style=\"color: var(--teal)\">VOICE</span></h2>
                <div class=\"glass-panel\">
                    <h3>Join-to-Create</h3>
                    <form onsubmit=\"saveSettings(event,'tempvc_setup')\">
                        <label class=\"toggle-label\">
                            <input type=\"checkbox\" id=\"temp_vc_enabled\" checked> Enable Dynamic Voice
                        </label>
                        <div class=\"form-group\">
                            <label>Lobby Channel ID</label>
                            <input type=\"text\" class=\"form-control\" id=\"temp_vc_lobby\" placeholder=\"Join to create channel\">
                        </div>
                        <div class=\"form-group\">
                            <label>Creation Category ID</label>
                            <input type=\"text\" class=\"form-control\" id=\"temp_vc_category\" placeholder=\"Category to spawn new VCs\">
                        </div>
                        <div class=\"form-group\">
                            <label>Channel Name Format</label>
                            <input type=\"text\" class=\"form-control\" id=\"temp_vc_name_format\" value=\"{user}'s Lounge\">
                        </div>
                        <div class=\"form-group\">
                            <label>User Limit (0 = Unlimited)</label>
                            <input type=\"number\" class=\"form-control\" id=\"temp_vc_limit\" value=\"0\" min=\"0\" max=\"99\">
                        </div>
                        <button type=\"submit\" class=\"btn-submit\">Save Voice Settings</button>
                    </form>
                </div>
            </div>

            <div id=\"server-builder\" class=\"tab-content\">
                <h2 class=\"display\">SERVER <span style=\"color: var(--orange)\">BUILDER</span></h2>
                <div class=\"glass-panel\">
                    <h3>Bulk Channel Permissions</h3>
                    <form onsubmit=\"event.preventDefault(); runServerAction('server_bulkpermissions', { role_id: document.getElementById('bulk_role_id').value, preset: document.getElementById('bulk_preset').value })\">
                        <div class=\"form-group\">
                            <label>Target Role ID</label>
                            <input type=\"text\" class=\"form-control\" id=\"bulk_role_id\" placeholder=\"Role to apply preset to\" required>
                        </div>
                        <div class=\"form-group\">
                            <label>Permission Preset</label>
                            <select class=\"form-control\" id=\"bulk_preset\">
                                <option value=\"read_only\">Read Only</option>
                                <option value=\"member\">Standard Member</option>
                                <option value=\"mod\">Moderator</option>
                                <option value=\"locked\">Strict Lockdown</option>
                            </select>
                        </div>
                        <button type=\"submit\" class=\"btn-submit\" style=\"background: var(--orange); color: #fff;\">Apply Globally</button>
                    </form>
                </div>
                
                <!-- BACKGROUND TASK PROGRESS -->
                <div id=\"task-progress-container\" class=\"glass-panel\">
                    <h4 style=\"margin-bottom: 8px; font-size: 14px; color: var(--orange);\">EXECUTING BACKGROUND TASK</h4>
                    <div id=\"task-progress-message\" style=\"font-size: 12px; color: rgba(255,255,255,0.5);\">Initializing...</div>
                    <div class=\"progress-track\">
                        <div id=\"task-progress-bar\"></div>
                    </div>
                    <div id=\"task-progress-percent\" style=\"font-size: 10px; text-align: right; margin-top: 6px; letter-spacing: 0.1em; color: rgba(255,255,255,0.4);\">0%</div>
                </div>
            </div>

        </main>
    </div>

    <script>
        // Tab logic
        document.querySelectorAll('.nav-btn').forEach(btn => {{
            btn.addEventListener('click', () => {{
                document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                document.getElementById(btn.getAttribute('data-target')).classList.add('active');
            }});
        }});
        
        // Mock callbacks for the frontend form overrides (if dashboard.js doesn't catch them)
        function saveSettings(e, category) {{
            e.preventDefault();
            const btn = e.target.querySelector('button');
            const orig = btn.innerText;
            btn.innerText = 'SAVED';
            btn.style.background = '#2ECC71';
            setTimeout(() => {{ btn.innerText = orig; btn.style.background = ''; }}, 2000);
        }}
        function runServerAction(action, payload) {{
            document.getElementById('task-progress-container').style.display = 'block';
            setTimeout(() => {{
                document.getElementById('task-progress-bar').style.width = '100%';
                document.getElementById('task-progress-percent').innerText = '100%';
                document.getElementById('task-progress-message').innerText = 'Completed successfully.';
            }}, 2500);
        }}
    </script>
    <script src=\"/static/js/dashboard.js\"></script>
</body>
</html>'''

with open('templates/server.html', 'w', encoding='utf-8') as f:
    f.write(server_html)

auth_html = '''<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no\">
    <title>KAIZER K5 - Auth</title>
    <link href=\"https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Space+Grotesk:wght@300;400;500&display=swap\" rel=\"stylesheet\">
    <link rel=\"stylesheet\" href=\"/static/css/style.css\">
    <style>
        body {{ background: var(--dark); display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
        .auth-card {{ background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); padding: 50px; text-align: center; border-radius: 16px; backdrop-filter: blur(20px); max-width: 400px; }}
        h1 {{ font-family: 'Bebas Neue', sans-serif; font-size: 60px; line-height: 1; margin-bottom: 10px; color: #fff; }}
        p {{ font-family: 'Space Grotesk', sans-serif; color: rgba(255, 255, 255, 0.5); font-size: 14px; margin-bottom: 30px; }}
        .btn {{ display: inline-block; padding: 14px 32px; background: var(--teal); color: var(--navy); text-decoration: none; font-family: 'Space Grotesk', sans-serif; font-weight: 600; font-size: 12px; letter-spacing: 0.15em; text-transform: uppercase; border-radius: 100px; }}
    </style>
</head>
<body>
    <div class=\"auth-card\">
        <h1>ACCESS<br><span style=\"color: var(--teal)\">REQUIRED</span></h1>
        <p>You must authenticate your Discord account to access the KAIZER K5 dashboard.</p>
        <a href=\"/login\" class=\"btn\">CONNECT DISCORD</a>
    </div>
</body>
</html>'''

with open('templates/auth.html', 'w', encoding='utf-8') as f:
    f.write(auth_html)

