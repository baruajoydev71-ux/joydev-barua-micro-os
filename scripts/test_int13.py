import struct

# Test BIOS INT 13h, AH=42h on El Torito CD-ROM
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
            target = self.labels[label_name]
            disp = target - (pos + 1)
            self.code[pos] = struct.pack('b', disp)[0]
        return bytes(self.code)

a = Asm()
# Real mode init, save DL (boot drive) in [0x0500]
a.emit(b'\xFA\xFC\x31\xC0\x8E\xD8\x8E\xC0\x8E\xD0\xBC\x00\x7C')
a.emit(b'\x88\x16\x00\x05') # mov [0x0500], dl

# Read 4 sectors (2048-byte CD sectors = 1 sector) from LBA 21 into 0x0000:0x8000
# DAP at 0x7D60 (offset 352)
# mov ah, 0x42
# mov si, 0x7D60
# int 0x13
a.emit(b'\xB4\x42\xBE\x60\x7D\xCD\x13')
# jc read_failed (carry set = error)
a.j_rel8(b'\x72', 'read_failed')

# If success: check if dword [0x8000] == 0xCAFEBABE
a.emit(b'\x66\x81\x3E\x00\x80\xBE\xBA\xFE\xCA')
a.j_rel8(b'\x75', 'sig_mismatch')

# Success! Color = GREEN (0x0000FF00)
a.emit(b'\x66\xB8\x00\xFF\x00\x00')
a.j_rel8(b'\xEB', 'set_vbe')

a.label('read_failed')
# Color = RED (0x000000FF -> 0x00FF0000)
a.emit(b'\x66\xB8\x00\x00\xFF\x00')
a.j_rel8(b'\xEB', 'set_vbe')

a.label('sig_mismatch')
# Color = YELLOW (0x00FFFF00)
a.emit(b'\x66\xB8\x00\xFF\xFF\x00')

a.label('set_vbe')
# Save color in EDX
a.emit(b'\x66\x89\xC2')
# Mode 0x4141
a.emit(b'\xB8\x02\x4F\xBB\x41\x41\xCD\x10')
# Unreal Mode
a.emit(b'\xFA\x2E\x0F\x01\x16\x80\x7D')
a.emit(b'\x0F\x20\xC0\x0C\x01\x0F\x22\xC0\xEB\x00')
a.emit(b'\xBB\x08\x00\x8E\xC3\x31\xC0\x8E\xD8')
a.emit(b'\x0F\x20\xC0\x24\xFE\x0F\x22\xC0\xEB\x00')
# Fill screen with EAX
a.emit(b'\x66\x89\xD0')
a.emit(b'\x66\xBF\x00\x00\x00\xE0')
a.emit(b'\x66\xB9\x00\xB0\x04\x00')
a.emit(b'\x67\x66\xF3\xAB')

a.label('hang')
a.emit(b'\xF4')
a.j_rel8(b'\xEB', 'hang')

raw = bytearray(a.resolve())
print(f"Code size: {len(raw)} bytes")
assert len(raw) <= 352

# DAP at offset 352 (0x7D60):
# 16 bytes:
# [0] = 0x10 (size)
# [1] = 0 (reserved)
# [2..3] = 1 (number of sectors to read)
# [4..5] = 0x8000 (offset)
# [6..7] = 0x0000 (segment)
# [8..15] = 21 (LBA 21, which is the sector right after boot image at LBA 20)
raw += b'\x00' * (352 - len(raw))
dap = struct.pack('<BBHHHIQ', 16, 0, 1, 0x8000, 0x0000, 21, 0)
# Note: struct DAP: size(1), res(1), count(2), offset(2), segment(2), lba(8)
dap = struct.pack('<BBHHHQ', 16, 0, 1, 0x8000, 0x0000, 21)
raw += dap

# GDT ptr at 384 (0x7D80)
raw += b'\x00' * (384 - len(raw))
raw += struct.pack('<HI', 23, 0x00007D90)
raw += b'\x00' * (400 - len(raw))
gdt = bytes([0,0,0,0,0,0,0,0, 0xFF,0xFF,0,0,0,0x92,0xCF,0, 0xFF,0xFF,0,0,0,0x9A,0,0])
raw += gdt
raw += b'\x00' * (510 - len(raw))
raw += b'\x55\xAA'

# CD-ROM layout:
SECTOR_SIZE = 2048
TOTAL_SECTORS = 300
iso = bytearray(SECTOR_SIZE * TOTAL_SECTORS)

# PVD
pvd = bytearray(SECTOR_SIZE); pvd[0] = 1; pvd[1:6] = b'CD001'; pvd[6] = 1; pvd[8:40] = b'JOYDEV_TEST'.ljust(32); pvd[40:72] = b'JOYDEV_TEST'.ljust(32)
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
bimg[0:len(raw)] = raw
iso[20*SECTOR_SIZE:21*SECTOR_SIZE] = bimg

# Sector 21: Data payload with signature 0xCAFEBABE
payload = bytearray(SECTOR_SIZE)
struct.pack_into('<I', payload, 0, 0xCAFEBABE)
iso[21*SECTOR_SIZE:22*SECTOR_SIZE] = payload

out_path = r"C:\Users\barua\.gemini\antigravity\scratch\micro-os\virtualbox\test-int13.iso"
with open(out_path, 'wb') as f:
    f.write(iso)
print(f"Test INT13 ISO written: {out_path}")
