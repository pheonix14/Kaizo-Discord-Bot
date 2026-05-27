import re

with open('templates/server.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Check how many times admin_roles_select and mod_roles_select appear
admin_ids = [(m.start(), m.group()) for m in re.finditer(r'id="admin_roles_select"', text)]
mod_ids = [(m.start(), m.group()) for m in re.finditer(r'id="mod_roles_select"', text)]

print(f"admin_roles_select occurrences: {len(admin_ids)}")
for pos, match in admin_ids:
    line_no = text[:pos].count('\n') + 1
    print(f"  Line {line_no}")

print(f"\nmod_roles_select occurrences: {len(mod_ids)}")
for pos, match in mod_ids:
    line_no = text[:pos].count('\n') + 1
    print(f"  Line {line_no}")

# Check the guildId variable
gid_matches = re.findall(r'const guildId\s*=\s*(.+?);', text)
print(f"\nguildId definitions: {gid_matches[:3]}")

# Check populateBotSettingsRoles function
start = text.find('function populateBotSettingsRoles')
end = text.find('\n    }', start) + 6
print(f"\npopulateBotSettingsRoles (lines {text[:start].count(chr(10))+1}-{text[:end].count(chr(10))+1}):")
print(text[start:end])

# Also look for places where admin_roles_select is populated
for m in re.finditer(r'admin_roles_select', text):
    pos = m.start()
    line_no = text[:pos].count('\n') + 1
    line = text[text[:pos].rfind('\n')+1:text.find('\n', pos)]
    print(f"  Line {line_no}: {line.strip()}")
