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

# Entry Point (0x0000:0x7C00)
a.emit(b'\xFA\xFC\x31\xC0\x8E\xD8\x8E\xC0\x8E\xD0\xBC\x00\x7C')

# Read 1 sector (2048 bytes) from LBA 21 into 0x0000:0x8000 via INT 13h AH=42h
# DAP at 0x7D60
a.emit(b'\xB4\x42\xBE\x60\x7D\xCD\x13')

# Set VBE mode 640x400x32 (0x4141)
a.emit(b'\xB8\x02\x4F\xBB\x41\x41\xCD\x10')

# Enter Unreal Mode
a.emit(b'\xFA')
a.emit(b'\x2E\x0F\x01\x16\x80\x7D') # LGDT [cs:0x7D80]
a.emit(b'\x0F\x20\xC0\x0C\x01\x0F\x22\xC0\xEB\x00')
a.emit(b'\xBB\x08\x00\x8E\xC3')    # ES = 0x08
a.emit(b'\x31\xC0\x8E\xD8')        # DS = 0
a.emit(b'\x0F\x20\xC0\x24\xFE\x0F\x22\xC0\xEB\x00')

# Fill background with Deep Violet (0x002A0818: B=0x18, G=0x08, R=0x2A)
a.emit(b'\x66\xBF\x00\x00\x00\xE0')
a.emit(b'\x66\xB9\x00\xB0\x04\x00')
a.emit(b'\x66\xB8\x18\x08\x2A\x00')
a.emit(b'\x67\x66\xF3\xAB')

# Draw test string "JOYDEV MICRO-OS" at x=50, y=50 in Cyan (0x00F8BD38)
a.emit(b'\xC7\x06\x00\x05\x32\x00') # x = 50
a.emit(b'\xC7\x06\x02\x05\x32\x00') # y = 50
a.emit(b'\x66\xC7\x06\x08\x05\xF8\xBD\x38\x00') # color = cyan
a.emit(b'\xBE\x00\x83') # SI = 0x8300 (offset 768 in sector 21)
a.j_near(b'\xE8', 'sub_draw_string')

# Draw second string at x=50, y=70 in Yellow (0x0015CCFA)
a.emit(b'\xC7\x06\x00\x05\x32\x00') # x = 50
a.emit(b'\xC7\x06\x02\x05\x46\x00') # y = 70
a.emit(b'\x66\xC7\x06\x08\x05\x15\xCC\xFA\x00') # color = yellow
a.emit(b'\xBE\x40\x83') # SI = 0x8340
a.j_near(b'\xE8', 'sub_draw_string')

a.label('hang')
a.emit(b'\xF4')
a.j_rel8(b'\xEB', 'hang')

# =========================================================================
# Subroutines: draw_char, draw_string
# Font table is at 0x8000
# =========================================================================
a.label('sub_draw_char')
a.emit(b'\x60') # pusha
# char in AL
a.emit(b'\x2C\x20\xB4\x00')      # sub al, 32; mov ah, 0
a.emit(b'\xC1\xE0\x03')          # shl ax, 3 (ax = ax * 8)
a.emit(b'\x05\x00\x80')          # add ax, 0x8000 (font_table address)
a.emit(b'\x89\xC6')              # mov si, ax

# edi = 0xE0000000 + (y * 2560) + (x * 4)
a.emit(b'\x66\x0F\xB7\x06\x02\x05')          # movzx eax, word [0x0502]
a.emit(b'\x66\x69\xC0\x00\x0A\x00\x00')      # imul eax, eax, 2560
a.emit(b'\x66\x0F\xB7\x3E\x00\x05')          # movzx edi, word [0x0500]
a.emit(b'\x66\xC1\xE7\x02')                  # shl edi, 2
a.emit(b'\x66\x01\xC7')                      # add edi, eax
a.emit(b'\x66\x81\xC7\x00\x00\x00\xE0')      # add edi, 0xE0000000

a.emit(b'\xBD\x08\x00')          # mov bp, 8 (8 rows)

a.label('char_row')
a.emit(b'\x66\x57')              # push edi
a.emit(b'\xAC\x88\xC3')          # lodsb; mov bl, al
a.emit(b'\xB9\x08\x00')          # mov cx, 8

a.label('char_bit')
a.emit(b'\xD0\xE3')              # shl bl, 1
a.j_rel8(b'\x73', 'bit_skip')    # jnc bit_skip
a.emit(b'\x66\xA1\x08\x05')      # mov eax, [0x0508] (color)
a.emit(b'\x67\x26\x66\x89\x07')  # es: mov [edi], eax
a.label('bit_skip')
a.emit(b'\x66\x83\xC7\x04')      # add edi, 4
a.j_rel8(b'\xE2', 'char_bit')    # loop char_bit

a.emit(b'\x66\x5F')              # pop edi
a.emit(b'\x66\x81\xC7\x00\x0A\x00\x00') # add edi, 2560
a.emit(b'\x4D')                  # dec bp
a.j_rel8(b'\x75', 'char_row')    # jnz char_row
a.emit(b'\x61\xC3')              # popa; ret

a.label('sub_draw_string')
a.emit(b'\x60')                  # pusha
a.label('str_loop')
a.emit(b'\xAC\x08\xC0')          # lodsb; test al, al
a.j_rel8(b'\x74', 'str_done')    # jz str_done
a.emit(b'\x56')                  # push si
a.j_near(b'\xE8', 'sub_draw_char')
a.emit(b'\x5E')                  # pop si
a.emit(b'\x83\x06\x00\x05\x08')  # add word [0x0500], 8
a.j_rel8(b'\xEB', 'str_loop')    # jmp str_loop
a.label('str_done')
a.emit(b'\x61\xC3')              # popa; ret

sec1_code = bytearray(a.resolve())
print(f"Code Size: {len(sec1_code)} bytes (max 352)")
assert len(sec1_code) <= 352

# DAP at 352 (0x7D60):
# Read 1 sector (2048 bytes) from LBA 21 into 0x0000:0x8000
sec1_code += b'\x00' * (352 - len(sec1_code))
dap = struct.pack('<BBHHHQ', 16, 0, 1, 0x8000, 0x0000, 21)
sec1_code += dap

# GDT ptr at 384 (0x7D80)
sec1_code += b'\x00' * (384 - len(sec1_code))
sec1_code += struct.pack('<HI', 23, 0x00007D90)
sec1_code += b'\x00' * (400 - len(sec1_code))
gdt = bytes([0,0,0,0,0,0,0,0, 0xFF,0xFF,0,0,0,0x92,0xCF,0, 0xFF,0xFF,0,0,0,0x9A,0,0])
sec1_code += gdt
sec1_code += b'\x00' * (510 - len(sec1_code))
sec1_code += b'\x55\xAA'

# Create Payload for sector 21 (2048 bytes):
# Font table at offset 0 (0x8000)
font_table = generate_font_table()
payload = bytearray(2048)
payload[0:len(font_table)] = font_table

# Strings at offset 768 (0x8300):
str1 = b'Joydev Micro-OS v3.2.0 (Bare Metal VirtualBox)\x00'
str2 = b'MLFQ Scheduler Active | 802.11ac Wi-Fi Connected\x00'
payload[768 : 768 + len(str1)] = str1
payload[768 + 64 : 768 + 64 + len(str2)] = str2

# Build ISO
SECTOR_SIZE = 2048
TOTAL_SECTORS = 300
iso = bytearray(SECTOR_SIZE * TOTAL_SECTORS)

# PVD
pvd = bytearray(SECTOR_SIZE); pvd[0] = 1; pvd[1:6] = b'CD001'; pvd[6] = 1
pvd[8:40] = b'JOYDEV_TEST_FONT'.ljust(32); pvd[40:72] = b'JOYDEV_TEST_FONT'.ljust(32)
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

# Payload at sector 21
iso[21*SECTOR_SIZE:22*SECTOR_SIZE] = payload

out_path = r"C:\Users\barua\.gemini\antigravity\scratch\micro-os\virtualbox\test-font.iso"
with open(out_path, 'wb') as f:
    f.write(iso)
print(f"Test Font ISO written: {out_path}")
