# Test jump calculation
mbr = bytearray()
mbr += b'\x81\x3E\x00\x7E\xEB\x17' # 6 bytes: cmp word [0x7E00], 0x17EB

# We want je to jump to .jump_kernel
# Let's measure bytes between end of je instruction and .jump_kernel
between = bytearray()
between += b'\x8A\x16\xFE\x7D' # mov dl, [0x7DFE] (4 bytes)
between += b'\xB4\x02'         # mov ah, 0x02 (2)
between += b'\xB0\x08'         # mov al, 8 (2)
between += b'\x31\xC9'         # xor cx, cx (2)
between += b'\xB1\x02'         # mov cl, 2 (2)
between += b'\x30\xF6'         # xor dh, dh (2)
between += b'\xBB\x00\x7E'     # mov bx, 0x7E00 (3)
between += b'\xCD\x13'         # int 0x13 (2)

# from jnc to .jump_kernel:
between_fallback = bytearray()
between_fallback += b'\x30\xD2'     # xor dl, dl (2)
between_fallback += b'\xB4\x02'     # mov ah, 0x02 (2)
between_fallback += b'\xB0\x08'     # mov al, 8 (2)
between_fallback += b'\xB1\x02'     # mov cl, 2 (2)
between_fallback += b'\xBB\x00\x7E' # mov bx, 0x7E00 (3)
between_fallback += b'\xCD\x13'     # int 0x13 (2)

jnc_len = 2
jnc_offset = len(between_fallback) # jump over fallback
print("jnc offset:", jnc_offset)

total_skip = len(between) + jnc_len + len(between_fallback)
print("je total skip:", total_skip)
