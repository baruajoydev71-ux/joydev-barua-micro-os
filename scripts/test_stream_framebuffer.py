import struct
from PIL import Image, ImageDraw, ImageFont

# 1. Create a beautiful test 640x400 image using Pillow
img = Image.new('RGB', (640, 400), (38, 11, 60))
d = ImageDraw.Draw(img)

# Folded silk gradient:
for y in range(400):
    t = y / 400.0
    r = int(50 + 150 * (t if t < 0.5 else 1.0 - t))
    g = int(12 + 40 * (t if t < 0.5 else 1.0 - t))
    b = int(70 + 80 * (t if t < 0.5 else 1.0 - t))
    d.line([(0, y), (639, y)], fill=(r, g, b))

# Top bar
d.rectangle([0, 0, 639, 22], fill=(18, 9, 31))
d.text((10, 5), "[*] Options  Desktop  Files  Documents  Music  Pictures  Video", fill=(220, 220, 240))
d.text((460, 5), "Sat 21 Nov  21:05:13   [vol] [pwr]", fill=(200, 200, 220))

# Central window
d.rectangle([155, 30, 625, 350], fill=(17, 5, 29), outline=(162, 31, 123), width=2)
d.rectangle([157, 32, 623, 58], fill=(30, 9, 52))
d.text((168, 38), "Joydev Micro-OS  |  Academic OS Engineering (CA-6)", fill=(240, 240, 255))
d.rectangle([585, 37, 599, 51], fill=(100, 100, 120))
d.rectangle([605, 37, 619, 51], fill=(220, 38, 38))

# Tabs
d.rectangle([157, 59, 623, 81], fill=(22, 7, 38))
d.rectangle([161, 61, 250, 79], fill=(138, 21, 101))
d.text((167, 65), "[1:SysMon]", fill=(255, 255, 255))
d.rectangle([255, 61, 340, 79], fill=(34, 11, 56))
d.text((261, 65), "[2:MLFQ]", fill=(180, 180, 200))
d.rectangle([345, 61, 435, 79], fill=(34, 11, 56))
d.text((351, 65), "[3:Memory]", fill=(180, 180, 200))
d.rectangle([440, 61, 540, 79], fill=(34, 11, 56))
d.text((446, 65), "[4:Wi-Fi/HW]", fill=(180, 180, 200))

# Inner content card
d.rectangle([165, 88, 615, 142], fill=(28, 11, 48), outline=(56, 189, 248), width=1)
d.text((175, 95), "Microkernel: Joydev v3.2.0-baremetal (640x400x32 Linear Framebuffer)", fill=(56, 189, 248))
d.text((175, 116), "CPU Usage: [||||||||||||||||....] 68% | PIT Timer: 100 Hz", fill=(255, 255, 255))

d.rectangle([165, 150, 615, 204], fill=(28, 11, 48), outline=(74, 222, 128), width=1)
d.text((175, 157), "Scheduler: MLFQ 3-Level (Q0:RR/4ms, Q1:RR/8ms, Q2:FCFS)", fill=(74, 222, 128))
d.text((175, 178), "Anti-Starvation: Global Aging Boost at T=25 | Priority Inversion: 0", fill=(255, 255, 255))

d.rectangle([165, 212, 615, 266], fill=(28, 11, 48), outline=(250, 204, 21), width=1)
d.text((175, 219), "Allocator: 64 KiB Hybrid (16K Bump + 48K FreeList Coalescing)", fill=(250, 204, 21))
d.text((175, 240), "Heap Free: 48,128 B | Spinlocks: AtomicBool | Zero Race Conditions", fill=(255, 255, 255))

d.rectangle([165, 274, 615, 340], fill=(28, 11, 48), outline=(192, 132, 252), width=1)
d.text((175, 281), "Wi-Fi: 802.11ac Virtual NIC (Intel 82540EM) | IP: 192.168.1.105", fill=(192, 132, 252))
d.text((175, 301), "Status: CONNECTED (SSID: Joydev-5G, 866 Mbps, Signal: -42 dBm)", fill=(52, 211, 153))
d.text((175, 321), "Hardware: SeaBIOS / VMSVGA VBE 0xE0000000 | ACPI Power Mgmt OK", fill=(200, 200, 220))

# Left Desktop Icons (Column 1 & 2)
icons_col1 = [
    ("File System", (59, 130, 246)),
    ("Home", (16, 185, 129)),
    ("Dev Studio", (139, 92, 246)),
    ("Sys Monitor", (6, 182, 212)),
    ("Storage Exp", (245, 158, 11)),
    ("Settings", (100, 116, 139)),
]
for idx, (name, col) in enumerate(icons_col1):
    y = 35 + idx * 52
    d.rectangle([20, y, 54, y + 34], fill=col)
    d.text((10, y + 36), name[:10], fill=(255, 255, 255))

icons_col2 = [
    ("Vyron Files", (249, 115, 22)),
    ("Web Browser", (239, 68, 68)),
    ("APT Packages", (99, 102, 241)),
    ("Wi-Fi Mgr", (14, 165, 233)),
    ("Snap Store", (20, 184, 166)),
    ("Microkernel", (168, 85, 247)),
]
for idx, (name, col) in enumerate(icons_col2):
    y = 35 + idx * 52
    d.rectangle([85, y, 119, y + 34], fill=col)
    d.text((75, y + 36), name[:11], fill=(255, 255, 255))

# Bottom Dock
d.rectangle([0, 365, 639, 399], fill=(18, 9, 31), outline=(162, 31, 123), width=1)
d.rectangle([15, 370, 39, 394], fill=(138, 21, 101))
d.text((22, 374), "*", fill=(255, 255, 255))
dock_apps = [(50, (59, 130, 246)), (80, (16, 185, 129)), (110, (249, 115, 22)), (140, (14, 165, 233)), (170, (139, 92, 246)), (200, (100, 116, 139))]
for x, c in dock_apps:
    d.rectangle([x, 370, x + 24, 394], fill=c)

# Workspaces
d.rectangle([455, 372, 495, 392], fill=(138, 21, 101))
d.text((460, 375), "Ws 1", fill=(255, 255, 255))
d.rectangle([500, 372, 540, 392], fill=(34, 11, 56))
d.text((505, 375), "Ws 2", fill=(180, 180, 200))
d.rectangle([545, 372, 585, 392], fill=(34, 11, 56))
d.text((550, 375), "Ws 3", fill=(180, 180, 200))
d.rectangle([590, 372, 630, 392], fill=(34, 11, 56))
d.text((595, 375), "Ws 4", fill=(180, 180, 200))

# Convert Pillow image to 32bpp BGRX raw buffer
raw_pixels = bytearray(640 * 400 * 4)
pixel_idx = 0
for y in range(400):
    for x in range(640):
        r, g, b = img.getpixel((x, y))
        raw_pixels[pixel_idx : pixel_idx + 4] = bytes([b, g, r, 0])
        pixel_idx += 4

print(f"Generated raw pixel buffer: {len(raw_pixels)} bytes")

class Asm:
    def __init__(self):
        self.code = bytearray()
        self.labels = {}
        self.rel_jumps = []
    def label(self, name):
        self.labels[name] = len(self.code)
    def emit(self, b):
        self.code.extend(b)
    def j_rel8(self, opcodes, label_name):
        self.code.extend(opcodes)
        self.rel_jumps.append((len(self.code), label_name))
        self.code.append(0)
    def resolve(self):
        for pos, label_name in self.rel_jumps:
            disp = self.labels[label_name] - (pos + 1)
            self.code[pos] = struct.pack('b', disp)[0]
        return bytes(self.code)

a = Asm()
# Real mode init, save boot drive DL in [0x0500]
a.emit(b'\xFA\xFC\x31\xC0\x8E\xD8\x8E\xC0\x8E\xD0\xBC\x00\x7C')
a.emit(b'\x88\x16\x00\x05') # mov [0x0500], dl

# Set VBE mode 640x400x32 (0x4141)
a.emit(b'\xB8\x02\x4F\xBB\x41\x41\xCD\x10')

# Enter Unreal Mode (ES has 4GB limit, DS = 0)
a.emit(b'\xFA')
a.emit(b'\x2E\x0F\x01\x16\x80\x7D') # LGDT [cs:0x7D80]
a.emit(b'\x0F\x20\xC0\x0C\x01\x0F\x22\xC0\xEB\x00')
a.emit(b'\xBB\x08\x00\x8E\xC3')    # ES = 0x08 (4GB flat)
a.emit(b'\x31\xC0\x8E\xD8')        # DS = 0
a.emit(b'\x0F\x20\xC0\x24\xFE\x0F\x22\xC0\xEB\x00')

# EDI = 0xE0000000 (framebuffer destination)
a.emit(b'\x66\xBF\x00\x00\x00\xE0')

# BP = 25 chunks
a.emit(b'\xBD\x19\x00')

a.label('chunk_loop')
# 1. Restore DL = boot drive
a.emit(b'\x8A\x16\x00\x05')

# 2. Call INT 13h AH=42h (reads 20 sectors into 0x1000:0x0000)
a.emit(b'\xB4\x42\xBE\x60\x7D\xCD\x13')

# 3. Re-engage Unreal Mode on ES (in case BIOS INT 13h reset ES)
a.emit(b'\xFA')
a.emit(b'\x2E\x0F\x01\x16\x80\x7D') # LGDT [cs:0x7D80]
a.emit(b'\x0F\x20\xC0\x0C\x01\x0F\x22\xC0\xEB\x00')
a.emit(b'\xBB\x08\x00\x8E\xC3')    # ES = 0x08 (4GB flat)
a.emit(b'\x0F\x20\xC0\x24\xFE\x0F\x22\xC0\xEB\x00')

# 4. Fast copy: 10,240 dwords from 0x1000:0x0000 to ES:EDI
a.emit(b'\x1E')                             # push ds
a.emit(b'\xB8\x00\x10\x8E\xD8')             # mov ax, 0x1000; mov ds, ax
a.emit(b'\x66\x31\xF6')                     # xor esi, esi
a.emit(b'\x66\xB9\x00\x28\x00\x00')         # mov ecx, 10240
a.emit(b'\x67\x66\xF3\xA5')                 # addr32 rep movsd (EDI automatically advances by 40,960!)
a.emit(b'\x1F')                             # pop ds

# 5. Advance LBA at [0x7D68] by 20 sectors
a.emit(b'\x83\x06\x68\x7D\x14')

# 6. Decrement BP and loop
a.emit(b'\x4D')                             # dec bp
a.j_rel8(b'\x75', 'chunk_loop')

# Done! Hang
a.label('hang')
a.emit(b'\xF4')
a.j_rel8(b'\xEB', 'hang')

sec1_code = bytearray(a.resolve())
print(f"Code size: {len(sec1_code)} bytes (max 352)")
assert len(sec1_code) <= 352

# DAP structure at 0x7D60 (offset 352):
# Buffer: 0x1000:0x0000, Count: 20 sectors, Start LBA: 21
sec1_code += b'\x00' * (352 - len(sec1_code))
dap = struct.pack('<BBHHHQ', 16, 0, 20, 0x0000, 0x1000, 21)
sec1_code += dap

# GDT ptr at 384 (0x7D80)
sec1_code += b'\x00' * (384 - len(sec1_code))
sec1_code += struct.pack('<HI', 23, 0x00007D90)
sec1_code += b'\x00' * (400 - len(sec1_code))
gdt = bytes([0,0,0,0,0,0,0,0, 0xFF,0xFF,0,0,0,0x92,0xCF,0, 0xFF,0xFF,0,0,0,0x9A,0,0])
sec1_code += gdt
sec1_code += b'\x00' * (510 - len(sec1_code))
sec1_code += b'\x55\xAA'

# ISO Construction:
SECTOR_SIZE = 2048
TOTAL_SECTORS = 600
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

# Payload (1,024,000 bytes = 500 sectors) starting at sector 21
iso[21*SECTOR_SIZE : 21*SECTOR_SIZE + len(raw_pixels)] = raw_pixels

out_path = r"C:\Users\barua\.gemini\antigravity\scratch\micro-os\virtualbox\test-stream.iso"
with open(out_path, 'wb') as f:
    f.write(iso)
print(f"Streaming Desktop ISO created successfully: {out_path} ({len(iso)} bytes)")
