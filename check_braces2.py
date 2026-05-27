import re

with open('temp_test.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace strings
text = re.sub(r'\"(?:\\.|[^\\\"])*\"', '\"\"', text)
text = re.sub(r'\'(?:\\.|[^\\\'])*\'', '\'\'', text)
text = re.sub(r'\`(?:\\.|[^\\\`])*\`', '\`\`', text)

# Replace block comments
text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)

# Replace line comments
text = re.sub(r'//.*', '', text)

# Replace regex literals.
text = re.sub(r'/\^#\?.*?/i', 'regex', text)

stack = []
lines = text.split('\n')
for i, line in enumerate(lines):
    for j, c in enumerate(line):
        if c in '{[(':
            stack.append((c, i+1))
        elif c in '}])':
            if stack:
                last, l_line = stack.pop()
            else:
                print(f'Extra {c} at line {i+1}')

if stack:
    for c, i in stack:
        print(f'Unclosed {c} starting at line {i}')
else:
    print('All matched.')
