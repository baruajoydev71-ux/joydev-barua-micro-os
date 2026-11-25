#!/usr/bin/env python3
"""
Test 32-bit mode 0x4141 or 0x4143 in VirtualBox
"""
import struct

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
            if not -128 <= disp <= 127:
                raise ValueError(f'Jump out of range: {disp} to {label_name}')
            self.code[pos] = struct.pack('b', disp)[0]
        return bytes(self.code)

a = Asm()
a.emit(b'\xFA\xFC\x31\xC0\x8E\xD8\x8E\xC0\x8E\xD0\xBC\x00\x7C')

# Try setting mode 0x4141 (640x480x32)
# If fails, try 0x4112 (640x480x24)
a.emit(b'\xB8\x02\x4F\xBB\x41\x41\xCD\x10')
a.emit(b'\x3D\x4F\x00')
a.j_rel8(b'\x74', 'mode_ok')

# Fallback: 0x4112
a.emit(b'\xB8\x02\x4F\xBB\x12\x41\xCD\x10')

a.label('mode_ok')
# Enter Unreal Mode
a.emit(b'\xFA')
a.emit(b'\x2E\x0F\x01\x16\x80\x7D') # LGDT [cs:0x7D80]
a.emit(b'\x0F\x20\xC0\x0C\x01\x0F\x22\xC0')
a.emit(b'\xEB\x00')
a.emit(b'\xBB\x08\x00\x8E\xC3')    # ES = 0x08
a.emit(b'\x31\xC0\x8E\xD8')        # DS = 0
a.emit(b'\x0F\x20\xC0\x24\xFE\x0F\x22\xC0')
a.emit(b'\xEB\x00')

# Fill with magenta/purple: 0x00E01B84 (R=0xE0, G=0x1B, B=0x84)
# In 32-bit: B=0x84, G=0x1B, R=0xE0 -> 0x00E01B84
a.emit(b'\x66\xBF\x00\x00\x00\xE0') # EDI = 0xE0000000
a.emit(b'\x66\xB9\x00\xB0\x04\x00') # ECX = 640 * 480 = 307,200
a.emit(b'\x66\xB8\x84\x1B\xE0\x00') # EAX = 0x00E01B84
a.emit(b'\x67\x66\xF3\xAB')         # addr32 rep stosd

a.label('hang')
a.emit(b'\xF4')
a.j_rel8(b'\xEB', 'hang')

code = bytearray(a.resolve())
code += b'\x00' * (384 - len(code))
gdt_ptr = struct.pack('<HI', 23, 0x00007D90)
code += gdt_ptr
code += b'\x00' * (400 - len(code))
gdt = bytes([
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0xFF, 0xFF, 0x00, 0x00, 0x00, 0x92, 0xCF, 0x00,
    0xFF, 0xFF, 0x00, 0x00, 0x00, 0x9A, 0x00, 0x00,
])
code += gdt
code += b'\x00' * (510 - len(code))
code += b'\x55\xAA'
mbr = bytes(code)

SECTOR_SIZE = 2048
TOTAL_SECTORS = 300
iso = bytearray(SECTOR_SIZE * TOTAL_SECTORS)

# PVD
pvd = bytearray(SECTOR_SIZE)
pvd[0] = 0x01; pvd[1:6] = b'CD001'; pvd[6] = 0x01
pvd[8:40] = b'JOYDEV_TEST_VBE                 '
pvd[40:72] = b'JOYDEV_TEST_VBE_VIRTUALBOX      '
struct.pack_into('<I', pvd, 80, TOTAL_SECTORS); struct.pack_into('>I', pvd, 84, TOTAL_SECTORS)
struct.pack_into('<H', pvd, 120, 1); struct.pack_into('>H', pvd, 122, 1)
struct.pack_into('<H', pvd, 124, 1); struct.pack_into('>H', pvd, 126, 1)
struct.pack_into('<H', pvd, 128, SECTOR_SIZE); struct.pack_into('>H', pvd, 130, SECTOR_SIZE)
root_dir = bytearray(34); root_dir[0] = 34
struct.pack_into('<I', root_dir, 2, 22); struct.pack_into('>I', root_dir, 6, 22)
struct.pack_into('<I', root_dir, 10, 2048); struct.pack_into('>I', root_dir, 14, 2048)
root_dir[18] = 126; root_dir[19] = 11; root_dir[20] = 24; root_dir[25] = 0x02
struct.pack_into('<H', root_dir, 28, 1); struct.pack_into('>H', root_dir, 30, 1)
root_dir[32] = 1
pvd[156:190] = root_dir
iso[16 * SECTOR_SIZE : 17 * SECTOR_SIZE] = pvd

# BRVD
brvd = bytearray(SECTOR_SIZE)
brvd[0] = 0x00; brvd[1:6] = b'CD001'; brvd[6] = 0x01
brvd[7:39] = b'EL TORITO SPECIFICATION\x00' + b'\x00' * 8
struct.pack_into('<I', brvd, 71, 19)
iso[17 * SECTOR_SIZE : 18 * SECTOR_SIZE] = brvd

# Boot Catalog
cat = bytearray(SECTOR_SIZE)
cat[0] = 0x01; cat[28] = 0xAA; cat[29] = 0x55; cat[30] = 0x55; cat[31] = 0xAA
cat_chk = sum(struct.unpack('<16H', cat[0:32])) & 0xFFFF
if cat_chk != 0:
    adj = (0x10000 - cat_chk) & 0xFFFF
    struct.pack_into('<H', cat, 28, adj)
cat[32] = 0x88; cat[33] = 0x00
struct.pack_into('<H', cat, 34, 0x0000); struct.pack_into('<H', cat, 38, 4)
struct.pack_into('<I', cat, 40, 20)
iso[19 * SECTOR_SIZE : 20 * SECTOR_SIZE] = cat

# Boot Image
boot_img = bytearray(SECTOR_SIZE * 4)
boot_img[0:len(mbr)] = mbr
iso[20 * SECTOR_SIZE : 24 * SECTOR_SIZE] = boot_img

out_path = r"C:\Users\barua\.gemini\antigravity\scratch\micro-os\virtualbox\test-vbe.iso"
with open(out_path, 'wb') as f:
    f.write(iso)
print(f"32-bit test ISO written: {out_path}")
