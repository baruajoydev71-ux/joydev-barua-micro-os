with open(r'C:\Users\barua\.gemini\antigravity\scratch\micro-os\scripts\build_interactive_os.py', 'r') as f:
    text = f.read()

# In kmain, right before event_loop, add STI (\xFB)
old_kmain = """    # Draw initial mouse cursor
    a.j_near(b'\\xE8', 'sub_draw_cursor')

    # =========================================================================
    # Interactive Event Loop
    # =========================================================================
    a.label('event_loop')"""

new_kmain = """    # Draw initial mouse cursor
    a.j_near(b'\\xE8', 'sub_draw_cursor')

    # Enable interrupts so BIOS keyboard & timer IRQs work
    a.emit(b'\\xFB') # STI

    # =========================================================================
    # Interactive Event Loop
    # =========================================================================
    a.label('event_loop')"""

assert old_kmain in text, 'old_kmain not found'
text = text.replace(old_kmain, new_kmain)

with open(r'C:\Users\barua\.gemini\antigravity\scratch\micro-os\scripts\build_interactive_os.py', 'w') as f:
    f.write(text)

print('Added STI to build_interactive_os.py!')
