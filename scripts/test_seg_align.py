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

# 1. Entry Point: real mode setup
a.emit(b'\xFA\xFC\x31\xC0\x8E\xD8\x8E\xC0\x8E\xD0\xBC\x00\x7C')

# 2. Read 4 sectors (8192 bytes) into 0x1000:0x0000 via INT 13h AH=42h
a.emit(b'\xB4\x42\xBE\x60\x7D\xCD\x13')

# 3. Set VBE mode 640x400x32 (0x4141)
a.emit(b'\xB8\x02\x4F\xBB\x41\x41\xCD\x10')

# 4. Enter Unreal Mode (ES = 0x08 4GB flat)
a.emit(b'\xFA')
a.emit(b'\x2E\x0F\x01\x16\x80\x7D') # LGDT [cs:0x7D80]
a.emit(b'\x0F\x20\xC0\x0C\x01\x0F\x22\xC0\xEB\x00')
a.emit(b'\xBB\x08\x00\x8E\xC3')    # ES = 0x08
a.emit(b'\x0F\x20\xC0\x24\xFE\x0F\x22\xC0\xEB\x00')

# 5. Set DS = 0x1000 to read from payload buffer
a.emit(b'\xB8\x00\x10\x8E\xD8')

# [0x1000:0x0000] = rect_count
# [0x1000:0x0002] = first rect
a.emit(b'\xBE\x02\x00')     # mov si, 0x0002
a.emit(b'\x8B\x0E\x00\x00') # mov cx, [0x0000]

a.label('rect_loop')
a.emit(b'\x51')             # push cx
a.emit(b'\xAD')             # lodsw -> AX = x
a.emit(b'\x89\x06\x00\x05') # mov [0x0500], ax
a.emit(b'\xAD')             # lodsw -> AX = y
a.emit(b'\x89\x06\x02\x05') # mov [0x0502], ax
a.emit(b'\xAD')             # lodsw -> AX = w
a.emit(b'\x89\x06\x04\x05') # mov [0x0504], ax
a.emit(b'\xAD')             # lodsw -> AX = h
a.emit(b'\x89\x06\x06\x05') # mov [0x0506], ax
a.emit(b'\x66\xAD')         # lodsd -> EAX = color
a.emit(b'\x66\x89\x06\x08\x05') # mov [0x0508], eax
a.emit(b'\x56')             # push si
a.j_near(b'\xE8', 'sub_fill_rect')
a.emit(b'\x5E')             # pop si
a.emit(b'\x59')             # pop cx
a.j_rel8(b'\xE2', 'rect_loop') # loop rect_loop

a.label('hang')
a.emit(b'\xF4')
a.j_rel8(b'\xEB', 'hang')

# Subroutine: fill_rect
# Note: DS is 0x1000, so variables at 0x0500 need CS override or 0x0000!
# Wait! In segment 0x1000: [0x0500] is 0x10500!
# That is completely safe and free RAM!
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

a.emit(b'\x61\xC3') # popa; ret

sec1_code = bytearray(a.resolve())
print(f"Code size: {len(sec1_code)} bytes (max 352)")
assert len(sec1_code) <= 352

# DAP at 352 (0x7D60):
# Segment-aligned: offset=0x0000, segment=0x1000!
sec1_code += b'\x00' * (352 - len(sec1_code))
dap = struct.pack('<BBHHHQ', 16, 0, 4, 0x0000, 0x1000, 21)
sec1_code += dap

# GDT ptr at 384 (0x7D80)
sec1_code += b'\x00' * (384 - len(sec1_code))
sec1_code += struct.pack('<HI', 23, 0x00007D90)
sec1_code += b'\x00' * (400 - len(sec1_code))
gdt = bytes([0,0,0,0,0,0,0,0, 0xFF,0xFF,0,0,0,0x92,0xCF,0, 0xFF,0xFF,0,0,0,0x9A,0,0])
sec1_code += gdt
sec1_code += b'\x00' * (510 - len(sec1_code))
sec1_code += b'\x55\xAA'

# Complete Desktop Rectangles
rectangles = []
def add_rect(x, y, w, h, hex_color):
    r = (hex_color >> 16) & 0xFF
    g = (hex_color >> 8) & 0xFF
    b = hex_color & 0xFF
    color_dword = (b) | (g << 8) | (r << 16)
    rectangles.append((x, y, w, h, color_dword))

# 1. Background silk gradient:
add_rect(0, 0, 640, 400, 0x500C5C) # Deep violet base
add_rect(0, 20, 640, 60, 0x3B0845)
add_rect(0, 80, 640, 80, 0x6E0F7D)
add_rect(0, 160, 640, 100, 0xA8188C) # Vibrant magenta band
add_rect(0, 260, 640, 60, 0x6E0F7D)
add_rect(0, 320, 640, 45, 0x3B0845)

# 2. Top panel:
add_rect(0, 0, 640, 22, 0x12091F)

# 3. Bottom dock:
add_rect(0, 365, 640, 35, 0x12091F)
add_rect(0, 365, 640, 1, 0xA21F7B)

# 4. Central Window:
add_rect(155, 30, 470, 325, 0xA21F7B) # Border
add_rect(157, 32, 466, 321, 0x10051C) # Body
add_rect(157, 32, 466, 26, 0x1C0930)  # Titlebar
add_rect(157, 58, 466, 22, 0x160726)  # Tab Bar

# Window Controls ([-] [O] [X]):
add_rect(570, 38, 14, 14, 0x374151)
add_rect(588, 38, 14, 14, 0x374151)
add_rect(606, 38, 14, 14, 0xDC2626)

# Tab buttons:
add_rect(162, 59, 90, 20, 0x8A1565) # Tab 1 (Active)
add_rect(255, 59, 85, 20, 0x220B38) # Tab 2
add_rect(343, 59, 85, 20, 0x220B38) # Tab 3
add_rect(431, 59, 95, 20, 0x220B38) # Tab 4

# Window Inner Cards:
add_rect(167, 88, 446, 52, 0x1E0D36)  # Card 1: Microkernel Status
add_rect(167, 146, 446, 52, 0x1E0D36) # Card 2: MLFQ Scheduler
add_rect(167, 204, 446, 52, 0x1E0D36) # Card 3: Memory Allocator
add_rect(167, 262, 446, 52, 0x1E0D36) # Card 4: Wi-Fi & Hardware

# Card Accents:
add_rect(167, 88, 4, 52, 0x38BDF8)   # Cyan accent
add_rect(167, 146, 4, 52, 0x4ADE80)  # Green accent
add_rect(167, 204, 4, 52, 0xFACC15)  # Yellow accent
add_rect(167, 262, 4, 52, 0xC084FC)  # Purple accent

# Progress / Usage Bars:
add_rect(240, 120, 200, 10, 0x334155) # CPU bg
add_rect(240, 120, 136, 10, 0x38BDF8) # CPU fill (68%)

add_rect(240, 178, 200, 10, 0x334155) # MLFQ Q0 bg
add_rect(240, 178, 160, 10, 0x4ADE80) # MLFQ fill (80%)

add_rect(240, 236, 200, 10, 0x334155) # Allocator bg
add_rect(240, 236, 148, 10, 0xFACC15) # Allocator fill (74%)

# Left Desktop Icons:
# Col 1 (x=20)
add_rect(20, 32, 34, 34, 0x3B82F6)  # File System (blue)
add_rect(20, 80, 34, 34, 0x10B981)  # Home (green)
add_rect(20, 128, 34, 34, 0x8B5CF6) # Dev Studio (purple)
add_rect(20, 176, 34, 34, 0x06B6D4) # Sys Monitor (cyan)
add_rect(20, 224, 34, 34, 0xF59E0B) # Storage (amber)
add_rect(20, 272, 34, 34, 0x64748B) # Settings (slate)
add_rect(20, 320, 34, 34, 0xEC4899) # Hardware (pink)

# Col 2 (x=80)
add_rect(80, 32, 34, 34, 0xF97316)  # Files (orange)
add_rect(80, 80, 34, 34, 0xEF4444)  # Browser (red)
add_rect(80, 128, 34, 34, 0x6366F1) # APT Package (indigo)
add_rect(80, 176, 34, 34, 0x0EA5E9) # Wi-Fi Manager (sky)
add_rect(80, 224, 34, 34, 0x14B8A6) # Snap Store (teal)
add_rect(80, 272, 34, 34, 0xA855F7) # Microkernel (violet)

# Dock Apps (x=16..220, y=370)
add_rect(15, 370, 24, 24, 0x8A1565)  # Launcher logo
add_rect(48, 370, 24, 24, 0x3B82F6)  # Terminal
add_rect(78, 370, 24, 24, 0x10B981)  # Files
add_rect(108, 370, 24, 24, 0xF97316) # Browser
add_rect(138, 370, 24, 24, 0x0EA5E9) # Wi-Fi
add_rect(168, 370, 24, 24, 0x8B5CF6) # Monitor
add_rect(198, 370, 24, 24, 0x64748B) # Settings

# Dock Workspaces (x=460..630, y=372):
add_rect(460, 372, 40, 20, 0x8A1565) # Workspace 1 (Active)
add_rect(504, 372, 40, 20, 0x220B38) # Workspace 2
add_rect(548, 372, 40, 20, 0x220B38) # Workspace 3
add_rect(592, 372, 40, 20, 0x220B38) # Workspace 4

print(f"Total Rectangles: {len(rectangles)}")

# Pack Payload for Sector 21 (8192 bytes = 4 sectors):
payload = bytearray(8192)
struct.pack_into('<H', payload, 0, len(rectangles))
offset = 2
for r in rectangles:
    struct.pack_into('<HHHH I', payload, offset, r[0], r[1], r[2], r[3], r[4])
    offset += 12

print(f"Payload packed size: {offset} bytes (max 8192)")

# Build ISO
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

# Boot Image at sector 20
bimg = bytearray(SECTOR_SIZE)
bimg[0:len(sec1_code)] = sec1_code
iso[20*SECTOR_SIZE:21*SECTOR_SIZE] = bimg

# Payload at sectors 21..24
iso[21*SECTOR_SIZE:25*SECTOR_SIZE] = payload

out_path = r"C:\Users\barua\.gemini\antigravity\scratch\micro-os\virtualbox\test-seg.iso"
with open(out_path, 'wb') as f:
    f.write(iso)
print(f"Test Seg ISO written: {out_path} ({len(iso)} bytes)")
