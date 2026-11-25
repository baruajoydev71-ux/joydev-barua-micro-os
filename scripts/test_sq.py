
import struct
class Asm:
    def __init__(self): self.code = bytearray(); self.labels = {}; self.rel_jumps = []
    def label(self, name): self.labels[name] = len(self.code)
    def emit(self, b): self.code.extend(b)
    def j_rel8(self, opcodes, label_name):
        self.code.extend(opcodes); self.rel_jumps.append((len(self.code), label_name)); self.code.append(0)
    def resolve(self):
        for pos, label_name in self.rel_jumps:
            disp = self.labels[label_name] - (pos + 1)
            self.code[pos] = struct.pack('b', disp)[0]
        return bytes(self.code)

a = Asm()
a.emit(b'\xFA\xFC\x31\xC0\x8E\xD8\x8E\xC0\x8E\xD0\xBC\x00\x7C')
# Set VBE mode 640x400x32 (0x4141)
a.emit(b'\xB8\x02\x4F\xBB\x41\x41\xCD\x10')
# Unreal Mode
a.emit(b'\xFA\x2E\x0F\x01\x16\x80\x7D')
a.emit(b'\x0F\x20\xC0\x0C\x01\x0F\x22\xC0\xEB\x00')
a.emit(b'\xBB\x08\x00\x8E\xC3\x31\xC0\x8E\xD8')
a.emit(b'\x0F\x20\xC0\x24\xFE\x0F\x22\xC0\xEB\x00')

# 1. Fill entire screen with Purple
a.emit(b'\x66\xBF\x00\x00\x00\xE0') # EDI = 0xE0000000
a.emit(b'\x66\xB9\x00\xB0\x04\x00') # ECX = 256,000 (or 307,200)
a.emit(b'\x66\xB8\x18\x08\x2A\x00') # EAX = Purple
a.emit(b'\x67\x66\xF3\xAB')         # addr32 rep stosd

# 2. Draw a 100x100 WHITE square at x=100, y=100
# y=100 -> offset = 100 * 2560 + 100 * 4 = 256,000 + 400 = 256,400 = 0x0003E9A0
# EDI = 0xE003E9A0
a.emit(b'\x66\xBF\xA0\xE9\x03\xE0') # EDI = 0xE003E9A0
a.emit(b'\xBD\x64\x00')                # BP = 100 (100 rows)

a.label('row_loop')
a.emit(b'\x66\x57')                    # push edi
a.emit(b'\x66\xB9\x64\x00\x00\x00') # ECX = 100 (100 pixels)
a.emit(b'\x66\xB8\xFF\xFF\xFF\x00') # EAX = White
a.emit(b'\x67\x66\xF3\xAB')         # addr32 rep stosd
a.emit(b'\x66\x5F')                    # pop edi
a.emit(b'\x66\x81\xC7\x00\x0A\x00\x00') # add edi, 2560
a.emit(b'\x4D')                        # dec bp
a.j_rel8(b'\x75', 'row_loop')

a.label('hang')
a.emit(b'\xF4')
a.j_rel8(b'\xEB', 'hang')

raw = bytearray(a.resolve())
raw += b'\x00' * (384 - len(raw))
raw += struct.pack('<HI', 23, 0x00007D90)
raw += b'\x00' * (400 - len(raw))
gdt = bytes([0,0,0,0,0,0,0,0, 0xFF,0xFF,0,0,0,0x92,0xCF,0, 0xFF,0xFF,0,0,0,0x9A,0,0])
raw += gdt
raw += b'\x00' * (510 - len(raw))
raw += b'\x55\xAA'

SECTOR_SIZE = 2048; TOTAL_SECTORS = 300
iso = bytearray(SECTOR_SIZE * TOTAL_SECTORS)
pvd = bytearray(SECTOR_SIZE); pvd[0]=1; pvd[1:6]=b'CD001'; pvd[6]=1; pvd[8:40]=b'TEST'.ljust(32); pvd[40:72]=b'TEST'.ljust(32)
struct.pack_into('<I', pvd, 80, TOTAL_SECTORS); struct.pack_into('>I', pvd, 84, TOTAL_SECTORS)
struct.pack_into('<H', pvd, 120, 1); struct.pack_into('>H', pvd, 122, 1); struct.pack_into('<H', pvd, 124, 1); struct.pack_into('>H', pvd, 126, 1); struct.pack_into('<H', pvd, 128, SECTOR_SIZE); struct.pack_into('>H', pvd, 130, SECTOR_SIZE)
r = bytearray(34); r[0]=34; struct.pack_into('<I', r, 2, 22); struct.pack_into('>I', r, 6, 22); struct.pack_into('<I', r, 10, 2048); struct.pack_into('>I', r, 14, 2048); r[18]=126; r[19]=11; r[20]=24; r[25]=2; struct.pack_into('<H', r, 28, 1); struct.pack_into('>H', r, 30, 1); r[32]=1
pvd[156:190] = r; iso[16*SECTOR_SIZE:17*SECTOR_SIZE] = pvd
b = bytearray(SECTOR_SIZE); b[0]=0; b[1:6]=b'CD001'; b[6]=1; b[7:39]=b'EL TORITO SPECIFICATION\x00'.ljust(32, b'\x00'); struct.pack_into('<I', b, 71, 19); iso[17*SECTOR_SIZE:18*SECTOR_SIZE] = b
c = bytearray(SECTOR_SIZE); c[0]=1; c[28]=0xAA; c[29]=0x55; c[30]=0x55; c[31]=0xAA
chk = sum(struct.unpack('<16H', c[0:32])) & 0xFFFF
if chk != 0: struct.pack_into('<H', c, 28, (0x10000 - chk) & 0xFFFF)
c[32]=0x88; struct.pack_into('<H', c, 38, 4); struct.pack_into('<I', c, 40, 20); iso[19*SECTOR_SIZE:20*SECTOR_SIZE] = c
bimg = bytearray(SECTOR_SIZE); bimg[0:len(raw)] = raw; iso[20*SECTOR_SIZE:21*SECTOR_SIZE] = bimg
with open(r'C:\Users\barua\.gemini\antigravity\scratch\micro-os\virtualbox\test-sq.iso', 'wb') as f: f.write(iso)
print('Test square ISO written!')
