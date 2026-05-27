with open('templates/server.html', 'r', encoding='utf-8') as f:
    text = f.read()

checks = [
    ('populateBotSettingsRoles function', 'function populateBotSettingsRoles'),
    ('ensureBotSettingsRoles function', 'function ensureBotSettingsRoles'),
    ('Tab click hook for settings', "if (target === 'settings')"),
    ('ensureBotSettingsRoles call', 'ensureBotSettingsRoles()'),
    ('Debug logging in populate fn', '[Kaizer] populateBotSettingsRoles called with'),
    ('Direct roles API fallback', '/api/guild/${guildId}/roles'),
    ('admin_roles_select in HTML', 'id="admin_roles_select"'),
    ('mod_roles_select in HTML', 'id="mod_roles_select"'),
]

all_ok = True
for name, pattern in checks:
    exists = pattern in text
    status = 'OK' if exists else 'MISSING'
    if not exists:
        all_ok = False
    print(f'[{status}] {name}')

print()
if all_ok:
    print('All checks passed!')
else:
    print('Some checks FAILED - review above')
