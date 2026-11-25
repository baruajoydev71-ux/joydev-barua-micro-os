with open(r'C:\Users\barua\.gemini\antigravity\scratch\micro-os\scripts\build_clean_interactive_os.py', 'r') as f:
    text = f.read()

# Replace any j_near with 0x7x opcodes back to j_rel8:
# Specifically:
# a.j_near(b'\x74', ...) -> a.j_rel8(b'\x74', ...)
# a.j_near(b'\x75', ...) -> a.j_rel8(b'\x75', ...)
# a.j_near(b'\x72', ...) -> a.j_rel8(b'\x72', ...)
# a.j_near(b'\x73', ...) -> a.j_rel8(b'\x73', ...)
# a.j_near(b'\x77', ...) -> a.j_rel8(b'\x77', ...)
import re

for op in [r"\\x74", r"\\x75", r"\\x72", r"\\x73", r"\\x77"]:
    pattern = rf"a\.j_near\(b'{op}',"
    replacement = f"a.j_rel8(b'{op}',"
    text = re.sub(pattern, replacement, text)

# Also check lines 140 and 147:
# line 140: test al, 1; jz event_loop
# Since event_loop is backward 6 bytes, j_rel8(b'\x74', 'event_loop') works!
# line 147: test al, 0x80; jnz event_loop
# event_loop is backward 13 bytes, j_rel8(b'\x75', 'event_loop') works!

with open(r'C:\Users\barua\.gemini\antigravity\scratch\micro-os\scripts\build_clean_interactive_os.py', 'w') as f:
    f.write(text)

print('Jump opcodes repaired successfully!')
