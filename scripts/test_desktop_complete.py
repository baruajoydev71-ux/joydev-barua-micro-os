import struct
from PIL import Image, ImageFont, ImageDraw

def generate_font_table():
    font = ImageFont.load_default()
    table = bytearray()
    for ch in range(32, 127):
        im = Image.new('1', (8, 8), 0)
        d = ImageDraw.Draw(im)
        d.text((0, 0), chr(ch), font=font, fill=1)
        for y in range(8):
            b = 0
            for x in range(8):
                if im.getpixel((x, y)):
                    b |= (1 << (7 - x))
            table.append(b)
    return bytes(table)

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

# 2. Read 8 sectors (16 KB) into 0x1000:0x0000 via INT 13h AH=42h
# DAP is at 0x7D60
a.emit(b'\xB4\x42\xBE\x60\x7D\xCD\x13')

# 3. Set VBE mode 640x400x32 (0x4141)
a.emit(b'\xB8\x02\x4F\xBB\x41\x41\xCD\x10')

# 4. Enter Unreal Mode (ES = 0x08 4GB flat)
a.emit(b'\xFA')
a.emit(b'\x2E\x0F\x01\x16\x80\x7D') # LGDT [cs:0x7D80]
a.emit(b'\x0F\x20\xC0\x0C\x01\x0F\x22\xC0\xEB\x00')
a.emit(b'\xBB\x08\x00\x8E\xC3')    # ES = 0x08
a.emit(b'\x0F\x20\xC0\x24\xFE\x0F\x22\xC0\xEB\x00')

# 5. Set DS = 0x1000 to read payload
a.emit(b'\xB8\x00\x10\x8E\xD8')

# =========================================================================
# Step 1: Render All Rectangles from [0x1000:0x0002]
# =========================================================================
a.emit(b'\xBE\x02\x00')     # mov si, 0x0002
a.emit(b'\x8B\x0E\x00\x00') # mov cx, [0x0000] (rect_count)

a.label('rect_loop')
a.emit(b'\x51')             # push cx
a.emit(b'\xAD\x89\x06\x00\x05') # lodsw; mov [0x0500], ax (x)
a.emit(b'\xAD\x89\x06\x02\x05') # lodsw; mov [0x0502], ax (y)
a.emit(b'\xAD\x89\x06\x04\x05') # lodsw; mov [0x0504], ax (w)
a.emit(b'\xAD\x89\x06\x06\x05') # lodsw; mov [0x0506], ax (h)
a.emit(b'\x66\xAD\x66\x89\x06\x08\x05') # lodsd; mov [0x0508], eax (color)
a.emit(b'\x56')             # push si
a.j_near(b'\xE8', 'sub_fill_rect')
a.emit(b'\x5E')             # pop si
a.emit(b'\x59')             # pop cx
a.j_rel8(b'\xE2', 'rect_loop')

# =========================================================================
# Step 2: Render All Text Strings from [0x1000:string_table_offset]
# string_count is at [0x1000:0x07FE] (word)
# string_table starts at [0x1000:0x0800]
# Each string entry (10 bytes):
#   x (uint16)
#   y (uint16)
#   color (uint32)
#   text_offset (uint16)
# =========================================================================
a.emit(b'\xBE\x00\x08')     # mov si, 0x0800
a.emit(b'\x8B\x0E\xFE\x07') # mov cx, [0x07FE] (string_count)

a.label('str_tbl_loop')
a.emit(b'\x51')             # push cx
a.emit(b'\xAD\x89\x06\x00\x05') # lodsw; mov [0x0500], ax (x)
a.emit(b'\xAD\x89\x06\x02\x05') # lodsw; mov [0x0502], ax (y)
a.emit(b'\x66\xAD\x66\x89\x06\x08\x05') # lodsd; mov [0x0508], eax (color)
a.emit(b'\xAD\x89\xC7')     # lodsw; mov di, ax (text_offset)
a.emit(b'\x56')             # push si
a.emit(b'\x89\xFE')         # mov si, di (SI points to string characters)
a.j_near(b'\xE8', 'sub_draw_string')
a.emit(b'\x5E')             # pop si
a.emit(b'\x59')             # pop cx
a.j_rel8(b'\xE2', 'str_tbl_loop')

# Hang / wait loop
a.label('hang')
a.emit(b'\xF4')
a.j_rel8(b'\xEB', 'hang')

# =========================================================================
# Subroutine: fill_rect
# =========================================================================
a.label('sub_fill_rect')
a.emit(b'\x60') # pusha
# eax = y * 2560
a.emit(b'\x66\x0F\xB7\x06\x02\x05')
a.emit(b'\x66\x69\xC0\x00\x0A\x00\x00')
# edi = x * 4
a.emit(b'\x66\x0F\xB7\x3E\x00\x05')
a.emit(b'\x66\xC1\xE7\x02')
a.emit(b'\x66\x01\xC7')
a.emit(b'\x66\x81\xC7\x00\x00\x00\xE0')
a.emit(b'\x8B\x2E\x06\x05')                  # mov bp, word [0x0506]

a.label('rect_row_loop')
a.emit(b'\x66\x57')                          # push edi
a.emit(b'\x66\x0F\xB7\x0E\x04\x05')          # movzx ecx, word [0x0504]
a.emit(b'\x66\xA1\x08\x05')                  # mov eax, [0x0508]
a.emit(b'\x67\x66\xF3\xAB')                  # addr32 rep stosd
a.emit(b'\x66\x5F')                          # pop edi
a.emit(b'\x66\x81\xC7\x00\x0A\x00\x00')      # add edi, 2560
a.emit(b'\x4D')                              # dec bp
a.j_rel8(b'\x75', 'rect_row_loop')
a.emit(b'\x61\xC3')                          # popa; ret

# =========================================================================
# Subroutines: draw_char, draw_string
# Font table is located at 0x1000:0x1000 (offset 4096 in payload)
# =========================================================================
a.label('sub_draw_char')
a.emit(b'\x60') # pusha
# AL = char
a.emit(b'\x2C\x20\xB4\x00')      # sub al, 32; mov ah, 0
a.emit(b'\xC1\xE0\x03')          # shl ax, 3
a.emit(b'\x05\x00\x10')          # add ax, 0x1000 (font table offset)
a.emit(b'\x89\xC6')              # mov si, ax

# edi = 0xE0000000 + (y * 2560) + (x * 4)
a.emit(b'\x66\x0F\xB7\x06\x02\x05')
a.emit(b'\x66\x69\xC0\x00\x0A\x00\x00')
a.emit(b'\x66\x0F\xB7\x3E\x00\x05')
a.emit(b'\x66\xC1\xE7\x02')
a.emit(b'\x66\x01\xC7')
a.emit(b'\x66\x81\xC7\x00\x00\x00\xE0')

a.emit(b'\xBD\x08\x00')          # mov bp, 8 (8 rows)

a.label('char_row')
a.emit(b'\x66\x57')              # push edi
a.emit(b'\xAC\x88\xC3')          # lodsb; mov bl, al
a.emit(b'\xB9\x08\x00')          # mov cx, 8

a.label('char_bit')
a.emit(b'\xD0\xE3')              # shl bl, 1
a.j_rel8(b'\x73', 'bit_zero')

# Bit is 1: write pixel via addr32 stosd
a.emit(b'\x66\xA1\x08\x05')      # mov eax, [0x0508] (color)
a.emit(b'\x67\x66\xAB')          # addr32 stosd (increments EDI by 4)
a.j_rel8(b'\xEB', 'bit_next')

a.label('bit_zero')
# Bit is 0: skip pixel
a.emit(b'\x66\x83\xC7\x04')      # add edi, 4

a.label('bit_next')
a.j_rel8(b'\xE2', 'char_bit')

a.emit(b'\x66\x5F')              # pop edi
a.emit(b'\x66\x81\xC7\x00\x0A\x00\x00') # add edi, 2560
a.emit(b'\x4D')                  # dec bp
a.j_rel8(b'\x75', 'char_row')
a.emit(b'\x61\xC3')              # popa; ret

a.label('sub_draw_string')
a.emit(b'\x60')                  # pusha
a.label('str_loop')
a.emit(b'\xAC\x08\xC0')          # lodsb; or al, al
a.j_rel8(b'\x74', 'str_done')    # jz str_done
a.emit(b'\x56')                  # push si
a.j_near(b'\xE8', 'sub_draw_char')
a.emit(b'\x5E')                  # pop si
a.emit(b'\x83\x06\x00\x05\x08')  # add word [0x0500], 8
a.j_rel8(b'\xEB', 'str_loop')
a.label('str_done')
a.emit(b'\x61\xC3')              # popa; ret

sec1_code = bytearray(a.resolve())
print(f"Code size: {len(sec1_code)} bytes (max 352)")
assert len(sec1_code) <= 352

# DAP at 352 (0x7D60):
# Read 8 sectors (16 KB) into 0x1000:0x0000 from LBA 21
sec1_code += b'\x00' * (352 - len(sec1_code))
dap = struct.pack('<BBHHHQ', 16, 0, 8, 0x0000, 0x1000, 21)
sec1_code += dap

# GDT ptr at 384 (0x7D80)
sec1_code += b'\x00' * (384 - len(sec1_code))
sec1_code += struct.pack('<HI', 23, 0x00007D90)
sec1_code += b'\x00' * (400 - len(sec1_code))
gdt = bytes([0,0,0,0,0,0,0,0, 0xFF,0xFF,0,0,0,0x92,0xCF,0, 0xFF,0xFF,0,0,0,0x9A,0,0])
sec1_code += gdt
sec1_code += b'\x00' * (510 - len(sec1_code))
sec1_code += b'\x55\xAA'

# =========================================================================
# Build Rectangles Table (offset 0 .. 0x07FE)
# =========================================================================
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

# =========================================================================
# Build Strings Table (offset 0x07FE .. 0x0FFF)
# =========================================================================
strings = []
string_bytes = bytearray()

def add_str(x, y, hex_color, text):
    r = (hex_color >> 16) & 0xFF
    g = (hex_color >> 8) & 0xFF
    b = hex_color & 0xFF
    color_dword = (b) | (g << 8) | (r << 16)
    
    # Store text at offset relative to 0x1000
    # Text pool starts at 0x1300 (offset 4864)
    text_offset = 0x1300 + len(string_bytes)
    string_bytes.extend(text.encode('ascii') + b'\x00')
    strings.append((x, y, color_dword, text_offset))

# Top bar:
add_str(8, 7, 0xE2E8F0, "Options  Desktop  Files  Documents  Music  Pictures  Video")
add_str(470, 7, 0xCBD5E1, "Sat 21 Nov 21:05  [Wi-Fi:OK]")

# Window header & tabs:
add_str(170, 39, 0xF8FAFC, "Joydev Micro-OS  |  Academic OS Engineering (CA-6)")
add_str(574, 40, 0x94A3B8, "-")
add_str(592, 40, 0x94A3B8, "+")
add_str(610, 40, 0xFCA5A5, "x")

add_str(174, 65, 0xFFFFFF, "[1:SysMon]")
add_str(267, 65, 0x94A3B8, "[2:MLFQ]")
add_str(355, 65, 0x94A3B8, "[3:Memory]")
add_str(445, 65, 0x94A3B8, "[4:Wi-Fi/HW]")

# Window Card 1:
add_str(176, 92, 0x38BDF8, "Microkernel: Joydev v3.2.0 (640x400x32 Linear Framebuffer)")
add_str(176, 105, 0xFFFFFF, "CPU Usage: [||||||||||||||||....] 68% | PIT Timer: 100 Hz")
add_str(176, 122, 0x4ADE80, "Spinlocks: AtomicBool | Priority Inversion: 0 | Preemption: ON")

# Window Card 2:
add_str(176, 150, 0x4ADE80, "Scheduler: MLFQ 3-Level (Q0:RR/4ms, Q1:RR/8ms, Q2:FCFS)")
add_str(176, 163, 0xFFFFFF, "Queue Load: Q0: 80% (Tasks 1..3) | Q1: 45% (Task 4) | Q2: 10% (Task 5)")
add_str(176, 180, 0xFACC15, "Anti-Starvation: Global Aging Boost active every T=25 ticks")

# Window Card 3:
add_str(176, 208, 0xFACC15, "Allocator: 64 KiB Hybrid (16K Bump + 48K FreeList Coalescing)")
add_str(176, 221, 0xFFFFFF, "Heap Free: 48,128 B / 65,536 B (74% avail) | Coalesce: ACTIVE")
add_str(176, 238, 0x38BDF8, "Bump Pointer: 0x4000 | Coalescing FreeList Nodes: 12 active")

# Window Card 4:
add_str(176, 266, 0xC084FC, "Wi-Fi: 802.11ac Virtual NIC (Intel 82540EM) | IP: 192.168.1.105")
add_str(176, 279, 0x34D399, "Status: CONNECTED (SSID: Joydev-5G, 866 Mbps, Signal: -42 dBm)")
add_str(176, 296, 0xE2E8F0, "Hardware: SeaBIOS / VMSVGA Linear Framebuffer 0xE0000000 | VBE OK")

# Left Desktop Icons Labels:
add_str(12, 68, 0xFFFFFF, "File System")
add_str(22, 116, 0xFFFFFF, "Home")
add_str(14, 164, 0xFFFFFF, "Dev Studio")
add_str(12, 212, 0xFFFFFF, "Sys Monitor")
add_str(16, 260, 0xFFFFFF, "Storage")
add_str(16, 308, 0xFFFFFF, "Settings")

add_str(75, 68, 0xFFFFFF, "Vyron Files")
add_str(78, 116, 0xFFFFFF, "Web Browser")
add_str(76, 164, 0xFFFFFF, "APT Packages")
add_str(78, 212, 0xFFFFFF, "Wi-Fi Mgr")
add_str(76, 260, 0xFFFFFF, "Snap Store")
add_str(75, 308, 0xFFFFFF, "Microkernel")

# Bottom Dock:
add_str(22, 377, 0xFFFFFF, "*")
add_str(474, 377, 0xFFFFFF, "[1]")
add_str(518, 377, 0x94A3B8, "[2]")
add_str(562, 377, 0x94A3B8, "[3]")
add_str(606, 377, 0x94A3B8, "[4]")

# Build 16 KB Payload:
payload = bytearray(16384)

# 1. Rectangles:
struct.pack_into('<H', payload, 0, len(rectangles))
offset = 2
for r in rectangles:
    struct.pack_into('<HHHH I', payload, offset, r[0], r[1], r[2], r[3], r[4])
    offset += 12

# 2. Strings table at offset 0x07FE (2046):
struct.pack_into('<H', payload, 0x07FE, len(strings))
offset = 0x0800
for s in strings:
    struct.pack_into('<HHIH', payload, offset, s[0], s[1], s[2], s[3])
    offset += 10

# 3. Font table at offset 0x1000 (4096):
font_table = generate_font_table()
payload[0x1000 : 0x1000 + len(font_table)] = font_table

# 4. Text strings pool at offset 0x1300 (4864):
payload[0x1300 : 0x1300 + len(string_bytes)] = string_bytes

print(f"Total Rectangles: {len(rectangles)}")
print(f"Total Strings: {len(strings)}")
print(f"Total String bytes: {len(string_bytes)}")

# Build ISO
SECTOR_SIZE = 2048
TOTAL_SECTORS = 300
iso = bytearray(SECTOR_SIZE * TOTAL_SECTORS)

# PVD
pvd = bytearray(SECTOR_SIZE); pvd[0] = 1; pvd[1:6] = b'CD001'; pvd[6] = 1
pvd[8:40] = b'JOYDEV_MICRO_OS'.ljust(32); pvd[40:72] = b'JOYDEV_MICRO_OS_VIRTUALBOX'.ljust(32)
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

# Payload at sectors 21..28 (16 KB = 8 sectors)
iso[21*SECTOR_SIZE : 21*SECTOR_SIZE + len(payload)] = payload

out_path = r"C:\Users\barua\.gemini\antigravity\scratch\micro-os\virtualbox\micro-os.iso"
with open(out_path, 'wb') as f:
    f.write(iso)
print(f"Production Micro-OS ISO written: {out_path} ({len(iso)} bytes)")
