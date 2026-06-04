import os

files = []
for root, dirs, filenames in os.walk('.'):
    for f in filenames:
        if f.endswith('.py'):
            files.append(os.path.join(root, f))

for filename in files:
    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        for idx, line in enumerate(f, 1):
            line_l = line.lower()
            if 'k4_defence' in line_l or 'k4defence' in line_l or 'mute_role' in line_l or 'anti_spam' in line_l:
                print(f"{filename}:{idx}: {line.strip()}")
