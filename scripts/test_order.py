
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
a.emit(b'\x88\x16\x00\x05') # save DL

# FIRST: Set VBE mode 0x4141
a.emit(b'\xB8\x02\x4F\xBB\x41\x41\xCD\x10')

# SECOND: Try calling INT 13h AH=42h
# Restore DL
a.emit(b'\x8A\x16\x00\x05')
a.emit(b'\xB4\x42\xBE\x60\x7D\xCD\x13')
a.j_rel8(b'\x72', 'int13_failed')

# Success: GREEN
a.emit(b'\x66\xB8\x00\xFF\x00\x00')
a.j_rel8(b'\xEB', 'do_fill')

a.label('int13_failed')
# FAILED: RED
a.emit(b'\x66\xB8\x00\x00\xFF\x00')

a.label('do_fill')
# Unreal Mode
a.emit(b'\xFA\x2E\x0F\x01\x16\x80\x7D')
a.emit(b'\x0F\x20\xC0\x0C\x01\x0F\x22\xC0\xEB\x00')
a.emit(b'\xBB\x08\x00\x8E\xC3\x31\xC0\x8E\xD8')
a.emit(b'\x0F\x20\xC0\x24\xFE\x0F\x22\xC0\xEB\x00')
a.emit(b'\x66\xBF\x00\x00\x00\xE0\x66\xB9\x00\xB0\x04\x00\x67\x66\xF3\xAB')
a.label('h'); a.emit(b'\xF4'); a.j_rel8(b'\xEB', 'h')

raw = bytearray(a.resolve())
raw += b'\x00' * (352 - len(raw))
dap = struct.pack('<BBHHHQ', 16, 0, 20, 0x0000, 0x1000, 21)
raw += dap
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
iso[21*SECTOR_SIZE:45*SECTOR_SIZE] = b'\x00' * (24 * SECTOR_SIZE)
with open(r'C:\Users\barua\.gemini\antigravity\scratch\micro-os\virtualbox\test-order.iso', 'wb') as f: f.write(iso)
print('Test order ISO written!')
