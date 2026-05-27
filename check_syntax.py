import subprocess
import re

with open('templates/server.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Extract ALL inline script tags content  
scripts = re.findall(r'<script>(.*?)</script>', text, re.DOTALL)
combined = '\n'.join(scripts)

# Remove Jinja2 template syntax - replace entire expression blocks
combined = re.sub(r'\{%[^%]*%\}', '', combined, flags=re.DOTALL)
# Replace {{ expr }} with null
combined = re.sub(r'\{\{[^}]*\}\}', 'null', combined)

with open('syntax_test.js', 'w', encoding='utf-8') as f:
    f.write(combined)

result = subprocess.run(['node', '--check', 'syntax_test.js'], capture_output=True, text=True)
if result.returncode == 0:
    print('SYNTAX OK - No JavaScript errors found!')
else:
    print('SYNTAX ERROR:')
    print(result.stderr[:1000])
