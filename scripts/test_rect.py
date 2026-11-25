import struct

class Asm:
    def __init__(self):
        self.code = bytearray()
        self.labels = {}
        self.rel_jumps = []
        self.near_jumps = []
    def label(self, name):
        self.labels[name] = len(self.code)
    def emit(self, b):
        self.code.extend(b)
    def j_rel8(self, opcodes, label_name):
        self.code.extend(opcodes)
        self.rel_jumps.append((len(self.code), label_name))
        self.code.append(0)
    def j_near(self, opcodes, label_name):
        self.code.extend(opcodes)
        self.near_jumps.append((len(self.code), label_name))
        self.code.extend(b'\x00\x00')
    def resolve(self):
        for pos, label_name in self.rel_jumps:
            target = self.labels[label_name]
            disp = target - (pos + 1)
            if not -128 <= disp <= 127:
                raise ValueError(f'Short jump out of range: {disp} to {label_name}')
            self.code[pos] = struct.pack('b', disp)[0]
        for pos, label_name in self.near_jumps:
            target = self.labels[label_name]
            disp = target - (pos + 2)
            struct.pack_into('<h', self.code, pos, disp)
        return bytes(self.code)

a = Asm()
# Real mode init
a.emit(b'\xFA\xFC\x31\xC0\x8E\xD8\x8E\xC0\x8E\xD0\xBC\x00\x7C')

# Mode 0x4141 (640x400x32)
a.emit(b'\xB8\x02\x4F\xBB\x41\x41\xCD\x10')

# Unreal Mode
a.emit(b'\xFA')
a.emit(b'\x2E\x0F\x01\x16\x80\x7D') # LGDT [cs:0x7D80]
a.emit(b'\x0F\x20\xC0\x0C\x01\x0F\x22\xC0\xEB\x00')
a.emit(b'\xBB\x08\x00\x8E\xC3')    # ES = 0x08
a.emit(b'\x31\xC0\x8E\xD8')        # DS = 0
a.emit(b'\x0F\x20\xC0\x24\xFE\x0F\x22\xC0\xEB\x00')

# Helper: macro to call fill_rect(x, y, w, h, color)
# Memory layout in scratch 0x0500:
# [0x0500] = x (word)
# [0x0502] = y (word)
# [0x0504] = w (word)
# [0x0506] = h (word)
# [0x0508] = color (dword)

def call_rect(x, y, w, h, color_hex):
    # mov word [0x0500], x
    a.emit(b'\xC7\x06\x00\x05' + struct.pack('<H', x))
    # mov word [0x0502], y
    a.emit(b'\xC7\x06\x02\x05' + struct.pack('<H', y))
    # mov word [0x0504], w
    a.emit(b'\xC7\x06\x04\x05' + struct.pack('<H', w))
    # mov word [0x0506], h
    a.emit(b'\xC7\x06\x06\x05' + struct.pack('<H', h))
    # mov dword [0x0508], color
    # color format: B, G, R, 0
    b = (color_hex >> 0) & 0xFF
    g = (color_hex >> 8) & 0xFF
    r = (color_hex >> 16) & 0xFF
    a.emit(b'\x66\xC7\x06\x08\x05' + bytes([b, g, r, 0]))
    a.j_near(b'\xE8', 'sub_fill_rect')

# 1. Fill entire background with Purple Silk (0x8B1E78: R=0x8B, G=0x1E, B=0x78)
call_rect(0, 0, 640, 400, 0x8B1E78)

# 2. Top panel: dark bar 0..20, #12091F
call_rect(0, 0, 640, 20, 0x12091F)

# 3. Bottom dock: 365..400, #12091F
call_rect(0, 365, 640, 35, 0x12091F)

# 4. Dock highlight line: 365, 1px, #A21F7B
call_rect(0, 365, 640, 1, 0xA21F7B)

# 5. Central Window border: x=160, y=35, w=460, h=310, #A21F7B
call_rect(160, 35, 460, 310, 0xA21F7B)

# 6. Central Window body: x=162, y=37, w=456, h=306, #11051D
call_rect(162, 37, 456, 306, 0x11051D)

# 7. Window Titlebar: x=162, y=37, w=456, h=25, #1E0934
call_rect(162, 37, 456, 25, 0x1E0934)

# 8. Window Tab bar: x=162, y=62, w=456, h=22, #18072A
call_rect(162, 62, 456, 22, 0x18072A)

# 9. Active Tab 1 highlight: x=166, y=63, w=95, h=20, #8A1565
call_rect(166, 63, 95, 20, 0x8A1565)

# 10. Left Desktop Icons (badges):
# Col 1 (x=25)
call_rect(25, 30, 28, 28, 0x3B82F6) # Blue badge
call_rect(25, 80, 28, 28, 0x10B981) # Green badge
call_rect(25, 130, 28, 28, 0x8B5CF6) # Purple badge
call_rect(25, 180, 28, 28, 0x06B6D4) # Cyan badge
call_rect(25, 230, 28, 28, 0xF59E0B) # Amber badge
call_rect(25, 280, 28, 28, 0x64748B) # Slate badge

# Col 2 (x=85)
call_rect(85, 30, 28, 28, 0xF97316) # Orange badge
call_rect(85, 80, 28, 28, 0xEC4899) # Pink badge
call_rect(85, 130, 28, 28, 0x6366F1) # Indigo badge
call_rect(85, 180, 28, 28, 0x14B8A6) # Teal badge
call_rect(85, 230, 28, 28, 0xA855F7) # Violet badge

# 11. Dock Workspaces (x=460..630, y=372):
call_rect(470, 372, 38, 20, 0x8A1565) # Workspace 1 (active)
call_rect(512, 372, 38, 20, 0x1E0934) # Workspace 2
call_rect(554, 372, 38, 20, 0x1E0934) # Workspace 3
call_rect(596, 372, 38, 20, 0x1E0934) # Workspace 4

a.label('hang')
a.emit(b'\xF4')
a.j_rel8(b'\xEB', 'hang')

# =========================================================================
# Subroutine: fill_rect
# Reads [0x0500]=x, [0x0502]=y, [0x0504]=w, [0x0506]=h, [0x0508]=color
# EDI = 0xE0000000 + (y * 2560) + (x * 4)
# =========================================================================
a.label('sub_fill_rect')
a.emit(b'\x60') # pusha

# eax = y * 2560
a.emit(b'\x66\x0F\xB7\x06\x02\x05')          # movzx eax, word [0x0502]
a.emit(b'\x66\x69\xC0\x00\x0A\x00\x00')      # imul eax, eax, 2560
# edi = x * 4
a.emit(b'\x66\x0F\xB7\x3E\x00\x05')          # movzx edi, word [0x0500]
a.emit(b'\x66\xC1\xE7\x02')                  # shl edi, 2
a.emit(b'\x66\x01\xC7')                      # add edi, eax
a.emit(b'\x66\x81\xC7\x00\x00\x00\xE0')      # add edi, 0xE0000000

# bp = h
a.emit(b'\x8B\x2E\x06\x05')                  # mov bp, word [0x0506]

a.label('rect_row_loop')
a.emit(b'\x66\x57')                          # push edi
a.emit(b'\x66\x0F\xB7\x0E\x04\x05')          # movzx ecx, word [0x0504] (w)
a.emit(b'\x66\xA1\x08\x05')                  # mov eax, [0x0508] (color)
a.emit(b'\x67\x66\xF3\xAB')                  # addr32 rep stosd
a.emit(b'\x66\x5F')                          # pop edi
a.emit(b'\x66\x81\xC7\x00\x0A\x00\x00')      # add edi, 2560
a.emit(b'\x4D')                              # dec bp
a.j_rel8(b'\x75', 'rect_row_loop')           # jnz rect_row_loop

a.emit(b'\x61') # popa
a.emit(b'\xC3') # ret

raw = bytearray(a.resolve())
print(f"Total Assembled Code Size: {len(raw)} bytes")
assert len(raw) <= 384, f"Code too large: {len(raw)} > 384"
raw += b'\x00' * (384 - len(raw))

# GDT ptr at 384 (0x7D80)
raw += struct.pack('<HI', 23, 0x00007D90)
raw += b'\x00' * (400 - len(raw))

# GDT at 400 (0x7D90)
gdt = bytes([
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0xFF, 0xFF, 0x00, 0x00, 0x00, 0x92, 0xCF, 0x00,
    0xFF, 0xFF, 0x00, 0x00, 0x00, 0x9A, 0x00, 0x00,
])
raw += gdt
raw += b'\x00' * (510 - len(raw))
raw += b'\x55\xAA'

SECTOR_SIZE = 2048
TOTAL_SECTORS = 300
iso = bytearray(SECTOR_SIZE * TOTAL_SECTORS)

# PVD
pvd = bytearray(SECTOR_SIZE); pvd[0] = 1; pvd[1:6] = b'CD001'; pvd[6] = 1
pvd[8:40] = b'JOYDEV_TEST_GUI'.ljust(32); pvd[40:72] = b'JOYDEV_TEST_GUI'.ljust(32)
struct.pack_into('<I', pvd, 80, TOTAL_SECTORS); struct.pack_into('>I', pvd, 84, TOTAL_SECTORS)
struct.pack_into('<H', pvd, 120, 1); struct.pack_into('>H', pvd, 122, 1); struct.pack_into('<H', pvd, 124, 1); struct.pack_into('>H', pvd, 126, 1); struct.pack_into('<H', pvd, 128, SECTOR_SIZE); struct.pack_into('>H', pvd, 130, SECTOR_SIZE)
r = bytearray(34); r[0] = 34; struct.pack_into('<I', r, 2, 22); struct.pack_into('>I', r, 6, 22); struct.pack_into('<I', r, 10, 2048); struct.pack_into('>I', r, 14, 2048); r[18]=126; r[19]=11; r[20]=24; r[25]=2; struct.pack_into('<H', r, 28, 1); struct.pack_into('>H', r, 30, 1); r[32]=1
pvd[156:190] = r; iso[16*SECTOR_SIZE:17*SECTOR_SIZE] = pvd

# BRVD
b = bytearray(SECTOR_SIZE); b[0]=0; b[1:6]=b'CD001'; b[6]=1; b[7:39]=b'EL TORITO SPECIFICATION\x00'.ljust(32, b'\x00'); struct.pack_into('<I', b, 71, 19); iso[17*SECTOR_SIZE:18*SECTOR_SIZE] = b

# Boot Catalog
c = bytearray(SECTOR_SIZE); c[0]=1; c[28]=0xAA; c[29]=0x55; c[30]=0x55; c[31]=0xAA
chk = sum(struct.unpack('<16H', c[0:32])) & 0xFFFF
if chk != 0: struct.pack_into('<H', c, 28, (0x10000 - chk) & 0xFFFF)
c[32]=0x88; struct.pack_into('<H', c, 38, 4); struct.pack_into('<I', c, 40, 20); iso[19*SECTOR_SIZE:20*SECTOR_SIZE] = c

# Boot Image: 4 sectors
bimg = bytearray(SECTOR_SIZE * 4)
bimg[0:len(raw)] = raw
iso[20*SECTOR_SIZE:24*SECTOR_SIZE] = bimg

out_path = r"C:\Users\barua\.gemini\antigravity\scratch\micro-os\virtualbox\test-rect.iso"
with open(out_path, 'wb') as f:
    f.write(iso)
print(f"Test Rect ISO created: {out_path} ({len(iso)} bytes)")
