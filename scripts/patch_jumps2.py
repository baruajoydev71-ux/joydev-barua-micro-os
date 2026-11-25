with open(r'C:\Users\barua\.gemini\antigravity\scratch\micro-os\scripts\build_interactive_os.py', 'r') as f:
    text = f.read()

# Replace do_click jump
old_click = """    # Enter (13) or Space (32) -> Click action at (mouse_x, mouse_y)
    a.emit(b'\\x3C\\x0D')
    a.j_rel8(b'\\x74', 'do_click')
    a.emit(b'\\x3C\\x20')
    a.j_rel8(b'\\x74', 'do_click')"""

new_click = """    # Enter (13) or Space (32) -> Click action at (mouse_x, mouse_y)
    a.emit(b'\\x3C\\x0D')
    a.j_rel8(b'\\x74', 'loc_click')
    a.emit(b'\\x3C\\x20')
    a.j_rel8(b'\\x75', 'not_click')
    a.label('loc_click')
    a.j_near(b'\\xE9', 'do_click')
    a.label('not_click')"""

assert old_click in text, 'old_click not found'
text = text.replace(old_click, new_click)

# Replace all event_loop jumps with near jumps
text = text.replace("a.j_rel8(b'\\xEB', 'event_loop')", "a.j_near(b'\\xE9', 'event_loop')")

with open(r'C:\Users\barua\.gemini\antigravity\scratch\micro-os\scripts\build_interactive_os.py', 'w') as f:
    f.write(text)

print('Patch 2 applied!')
