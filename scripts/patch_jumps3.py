with open(r'C:\Users\barua\.gemini\antigravity\scratch\micro-os\scripts\build_interactive_os.py', 'r') as f:
    text = f.read()

old_pat = """    # If y >= 365: Click is on Bottom Dock!
    a.emit(b'\\x81\\x3E\\x04\\x1F\\x6D\\x01') # cmp word [0x1F04], 365
    a.j_rel8(b'\\x72', 'check_icon_click')"""

new_pat = """    # If y >= 365: Click is on Bottom Dock!
    a.emit(b'\\x81\\x3E\\x04\\x1F\\x6D\\x01') # cmp word [0x1F04], 365
    a.j_rel8(b'\\x73', 'is_dock')
    a.j_near(b'\\xE9', 'check_icon_click')
    a.label('is_dock')"""

assert old_pat in text, 'old_pat not found'
text = text.replace(old_pat, new_pat)

with open(r'C:\Users\barua\.gemini\antigravity\scratch\micro-os\scripts\build_interactive_os.py', 'w') as f:
    f.write(text)

print('Patch 3 applied!')
