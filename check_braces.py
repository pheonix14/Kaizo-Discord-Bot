import sys

with open('temp_test.js', 'r', encoding='utf-8') as f:
    text = f.read()

stack = []
in_string = False
string_char = ''
in_comment_line = False
in_comment_block = False
escape = False
regex_context = False

lines = text.split('\n')
for i, line in enumerate(lines):
    j = 0
    while j < len(line):
        c = line[j]
        
        if in_comment_line:
            break
        
        if in_comment_block:
            if c == '*' and j+1 < len(line) and line[j+1] == '/':
                in_comment_block = False
                j += 1
            j += 1
            continue
            
        if in_string:
            if escape:
                escape = False
            elif c == '\\':
                escape = True
            elif c == string_char:
                in_string = False
            j += 1
            continue
            
        if c in '\"\'\`':
            in_string = True
            string_char = c
            j += 1
            continue
            
        if c == '/' and j+1 < len(line):
            if line[j+1] == '/':
                in_comment_line = True
                break
            elif line[j+1] == '*':
                in_comment_block = True
                j += 1
                j += 1
                continue
                
        if c in '{[(': 
            stack.append((c, i+1))
        elif c in '}])':
            if not stack:
                pass
            else:
                last, l_line = stack.pop()
                if (last == '{' and c != '}') or (last == '[' and c != ']') or (last == '(' and c != ')'):
                    pass
        j += 1
    in_comment_line = False

if stack:
    for c, i in stack:
        print(f'Unclosed {c} starting at line {i}')
else:
    print('All matched.')
