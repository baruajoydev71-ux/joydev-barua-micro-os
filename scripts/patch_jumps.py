with open(r'C:\Users\barua\.gemini\antigravity\scratch\micro-os\scripts\build_interactive_os.py', 'r') as f:
    text = f.read()

old_pattern = """    # 1. Check Keyboard via INT 16h AH=01h
    a.emit(b'\\xB4\\x01\\xCD\\x16')          # mov ah, 1; int 16h
    a.j_rel8(b'\\x74', 'check_ps2_mouse') # jz check_ps2_mouse"""

new_pattern = """    # 1. Check Keyboard via INT 16h AH=01h
    a.emit(b'\\xB4\\x01\\xCD\\x16')          # mov ah, 1; int 16h
    a.j_rel8(b'\\x75', 'key_ready')        # jnz key_ready
    a.j_near(b'\\xE9', 'check_ps2_mouse')   # jmp near check_ps2_mouse
    a.label('key_ready')"""

assert old_pattern in text, 'Old pattern not found'
text = text.replace(old_pattern, new_pattern)

text = text.replace("a.j_rel8(b'\\xEB', 'redraw_all')", "a.j_near(b'\\xE9', 'redraw_all')")
text = text.replace("a.j_rel8(b'\\xEB', 'check_ps2_mouse')", "a.j_near(b'\\xE9', 'check_ps2_mouse')")

with open(r'C:\Users\barua\.gemini\antigravity\scratch\micro-os\scripts\build_interactive_os.py', 'w') as f:
    f.write(text)

print('Updated build_interactive_os.py successfully!')
