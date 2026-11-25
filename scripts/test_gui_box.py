#!/usr/bin/env python3
"""
Test clean 32-bit procedural GUI drawing in VirtualBox VBE 640x400 32bpp
"""
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

class Assembler:
    def __init__(self):
        self.code = bytearray()
        self.labels = {}
        self.rel_jumps = []
        self.near_jumps = []
        self.abs_labels = []

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

    def imm16_label(self, opcodes, label_name):
        self.code.extend(opcodes)
        self.abs_labels.append((len(self.code), label_name))
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

        for pos, label_name in self.abs_labels:
            target = self.labels[label_name]
            abs_addr = 0x7C00 + target
            struct.pack_into('<H', self.code, pos, abs_addr)

        return bytes(self.code)

a = Assembler()

# Entry Point (0x0000:0x7C00)
a.emit(b'\xFA\xFC\x31\xC0\x8E\xD8\x8E\xC0\x8E\xD0\xBC\x00\x7C')

# Set VBE mode 640x400 32bpp (0x4141)
a.emit(b'\xB8\x02\x4F\xBB\x41\x41\xCD\x10')
a.emit(b'\x3D\x4F\x00')
a.j_rel8(b'\x74', 'vbe_ok')
a.emit(b'\xB8\x02\x4F\xBB\x12\x41\xCD\x10')

a.label('vbe_ok')
# Enter Unreal Mode
a.emit(b'\xFA')
# LGDT [cs:gdt_ptr]
a.imm16_label(b'\x2E\x0F\x01\x16', 'gdt_ptr')
# CR0 |= 1
a.emit(b'\x0F\x20\xC0\x0C\x01\x0F\x22\xC0\xEB\x00')
# ES = 0x08
a.emit(b'\xBB\x08\x00\x8E\xC3')
# DS = 0
a.emit(b'\x31\xC0\x8E\xD8')
# CR0 &= ~1
a.emit(b'\x0F\x20\xC0\x24\xFE\x0F\x22\xC0\xEB\x00')

# =========================================================================
# Draw Top Panel: fill_rect(0, 0, 640, 20, #12091F)
# =========================================================================
a.emit(b'\xC7\x06\x00\x05\x00\x00') # x = 0
a.emit(b'\xC7\x06\x02\x05\x00\x00') # y = 0
a.emit(b'\xC7\x06\x04\x05\x80\x02') # w = 640
a.emit(b'\xC7\x06\x06\x05\x14\x00') # h = 20
a.emit(b'\x66\xC7\x06\x10\x05\x1F\x09\x12\x00') # #12091F
a.j_near(b'\xE8', 'call_fill_rect')

# =========================================================================
# Draw Wallpaper: fill_rect(0, 20, 640, 345, #5A0E6B)
# =========================================================================
a.emit(b'\xC7\x06\x00\x05\x00\x00') # x = 0
a.emit(b'\xC7\x06\x02\x05\x14\x00') # y = 20
a.emit(b'\xC7\x06\x04\x05\x80\x02') # w = 640
a.emit(b'\xC7\x06\x06\x05\x59\x01') # h = 345
a.emit(b'\x66\xC7\x06\x10\x05\x6B\x0E\x5A\x00') # Purple
a.j_near(b'\xE8', 'call_fill_rect')

# =========================================================================
# Draw Bottom Dock: fill_rect(0, 365, 640, 35, #12091F)
# =========================================================================
a.emit(b'\xC7\x06\x00\x05\x00\x00')
a.emit(b'\xC7\x06\x02\x05\x6D\x01') # y = 365
a.emit(b'\xC7\x06\x04\x05\x80\x02')
a.emit(b'\xC7\x06\x06\x05\x23\x00') # h = 35
a.emit(b'\x66\xC7\x06\x10\x05\x1F\x09\x12\x00')
a.j_near(b'\xE8', 'call_fill_rect')

# =========================================================================
# Draw Floating Window:
# Outer Border: fill_rect(243, 28, 389, 329, #A21F7B)
# =========================================================================
a.emit(b'\xC7\x06\x00\x05\xF3\x00\xC7\x06\x02\x05\x1C\x00')
a.emit(b'\xC7\x06\x04\x05\x85\x01\xC7\x06\x06\x05\x49\x01')
a.emit(b'\x66\xC7\x06\x10\x05\x7B\x1F\xA2\x00') # Border
a.j_near(b'\xE8', 'call_fill_rect')

# Window Body: fill_rect(245, 30, 385, 325, #11051D)
a.emit(b'\xC7\x06\x00\x05\xF5\x00\xC7\x06\x02\x05\x1E\x00')
a.emit(b'\xC7\x06\x04\x05\x81\x01\xC7\x06\x06\x05\x45\x01')
a.emit(b'\x66\xC7\x06\x10\x05\x1D\x05\x11\x00') # Dark body
a.j_near(b'\xE8', 'call_fill_rect')

# =========================================================================
# Text Labels:
# =========================================================================
# Top bar text:
a.emit(b'\xC7\x06\x00\x05\x08\x00\xC7\x06\x02\x05\x06\x00')
a.emit(b'\x66\xC7\x06\x10\x05\xFF\xFF\xFF\x00')
a.imm16_label(b'\xBE', 'str_top')
a.j_near(b'\xE8', 'call_draw_string')

# Window title:
a.emit(b'\xC7\x06\x00\x05\xFB\x00\xC7\x06\x02\x05\x26\x00')
a.emit(b'\x66\xC7\x06\x10\x05\x00\xFF\xFF\x00') # Cyan
a.imm16_label(b'\xBE', 'str_title')
a.j_near(b'\xE8', 'call_draw_string')

# Window content lines:
a.emit(b'\xC7\x06\x00\x05\xFB\x00\xC7\x06\x02\x05\x40\x00')
a.emit(b'\x66\xC7\x06\x10\x05\x00\xFF\x00\x00') # Green
a.imm16_label(b'\xBE', 'str_line1')
a.j_near(b'\xE8', 'call_draw_string')

a.emit(b'\xC7\x06\x00\x05\xFB\x00\xC7\x06\x02\x05\x56\x00')
a.emit(b'\x66\xC7\x06\x10\x05\xFF\xFF\x00\x00') # Yellow
a.imm16_label(b'\xBE', 'str_line2')
a.j_near(b'\xE8', 'call_draw_string')

# Hang loop
a.label('hang')
a.emit(b'\xF4\xEB\xFD')

# =========================================================================
# Subroutines:
# =========================================================================
a.label('call_fill_rect')
a.emit(b'\x60')
# edi = 0xE0000000 + (y * 2560) + (x * 4)
a.emit(b'\x66\x0F\xB7\x06\x02\x05')
a.emit(b'\x66\x69\xC0\x00\x0A\x00\x00')
a.emit(b'\x66\x0F\xB7\x3E\x00\x05')
a.emit(b'\x66\xC1\xE7\x02')
a.emit(b'\x66\x01\xC7')
a.emit(b'\x66\x81\xC7\x00\x00\x00\xE0')
a.emit(b'\x8B\x2E\x06\x05') # bp = h

a.label('fr_row')
a.emit(b'\x66\x57')
a.emit(b'\x66\x0F\xB7\x0E\x04\x05') # movzx ecx, word [0x0504] (w)
a.emit(b'\x66\xA1\x10\x05')         # eax = color
a.emit(b'\x67\x66\xF3\xAB')         # addr32 rep stosd
a.emit(b'\x66\x5F')
a.emit(b'\x66\x81\xC7\x00\x0A\x00\x00') # add edi, 2560
a.emit(b'\x4D')
a.j_rel8(b'\x75', 'fr_row')
a.emit(b'\x61\xC3')

a.label('call_draw_char')
a.emit(b'\x60')
a.emit(b'\xA0\x08\x05\x2C\x20\xB4\x00\xC1\xE0\x03')
a.imm16_label(b'\x05', 'font_table')
a.emit(b'\x89\xC6')
a.emit(b'\x66\x0F\xB7\x06\x02\x05\x66\x69\xC0\x00\x0A\x00\x00')
a.emit(b'\x66\x0F\xB7\x3E\x00\x05\x66\xC1\xE7\x02\x66\x01\xC7')
a.emit(b'\x66\x81\xC7\x00\x00\x00\xE0')
a.emit(b'\xBD\x08\x00')

a.label('dc_row')
a.emit(b'\x66\x57')
a.emit(b'\xAC\x88\xC3')
a.emit(b'\xB9\x08\x00')

a.label('dc_col')
a.emit(b'\xD0\xE3')
a.j_rel8(b'\x73', 'dc_skip')
a.emit(b'\x66\xA1\x10\x05')
a.emit(b'\x67\x26\x66\x89\x07')

a.label('dc_skip')
a.emit(b'\x66\x83\xC7\x04\x49')
a.j_rel8(b'\x75', 'dc_col')
a.emit(b'\x66\x5F\x66\x81\xC7\x00\x0A\x00\x00\x4D')
a.j_rel8(b'\x75', 'dc_row')
a.emit(b'\x61\xC3')

a.label('call_draw_string')
a.emit(b'\x60')
a.label('ds_loop')
a.emit(b'\xAC\x08\xC0')
a.j_rel8(b'\x74', 'ds_done')
a.emit(b'\xA2\x08\x05\x56')
a.j_near(b'\xE8', 'call_draw_char')
a.emit(b'\x5E\x83\x06\x00\x05\x08')
a.j_near(b'\xEB', 'ds_loop')
a.label('ds_done')
a.emit(b'\x61\xC3')

# Data
a.label('str_top')
a.emit(b'[*] Options  Desktop  Files  Documents  Kernel  MLFQ  Sat 21 Nov 21:05\x00')
a.label('str_title')
a.emit(b'Joydev Microkernel System Monitor (VirtualBox)\x00')
a.label('str_line1')
a.emit(b'CPU Usage: [||||||||||||||||....] 68% | PIT 100 Hz\x00')
a.label('str_line2')
a.emit(b'Wi-Fi: Intel 82540EM (802.11ac) Connected 192.168.1.105\x00')

a.label('font_table')
font_table_bytes = generate_font_table()
a.emit(font_table_bytes)

a.label('gdt_data')
gdt_bytes = bytes([
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0xFF, 0xFF, 0x00, 0x00, 0x00, 0x92, 0xCF, 0x00,
    0xFF, 0xFF, 0x00, 0x00, 0x00, 0x9A, 0x00, 0x00,
])
a.emit(gdt_bytes)

a.label('gdt_ptr')
a.emit(struct.pack('<H', 23))
a.imm16_label(b'', 'gdt_data')
a.emit(b'\x00\x00')

full_binary = a.resolve()
print(f"Test GUI binary size: {len(full_binary)} bytes")

# Pad to 4 sectors = 2048 bytes (fits in single CD sector!)
padded = bytearray(full_binary)
if len(padded) < 2048:
    padded += b'\x00' * (2048 - len(padded))

SECTOR_SIZE = 2048
TOTAL_SECTORS = 300
iso = bytearray(SECTOR_SIZE * TOTAL_SECTORS)

# PVD
pvd = bytearray(SECTOR_SIZE)
pvd[0] = 0x01; pvd[1:6] = b'CD001'; pvd[6] = 0x01
pvd[8:40] = b'JOYDEV_TEST_GUI                 '
pvd[40:72] = b'JOYDEV_TEST_GUI_VIRTUALBOX      '
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
struct.pack_into('<H', cat, 34, 0x0000)
struct.pack_into('<H', cat, 38, 4) # 4 * 512 = 2048 bytes (1 CD sector!)
struct.pack_into('<I', cat, 40, 20)
iso[19 * SECTOR_SIZE : 20 * SECTOR_SIZE] = cat

# Boot Image
iso[20 * SECTOR_SIZE : 21 * SECTOR_SIZE] = padded

out_path = r"C:\Users\barua\.gemini\antigravity\scratch\micro-os\virtualbox\test-gui.iso"
with open(out_path, 'wb') as f:
    f.write(iso)
print(f"Test GUI ISO written: {out_path} ({len(iso)} bytes)")
