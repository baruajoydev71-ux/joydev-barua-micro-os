import struct

# Small diagnostic test for port 0x64 / 0x60 in VirtualBox
code = bytearray()

# 1. Real mode setup
code += b'\xFA\xFC\x31\xC0\x8E\xD8\x8E\xC0\x8E\xD0\xBC\x00\x7C'
# 2. VBE mode 640x400x32
code += b'\xB8\x02\x4F\xBB\x41\x41\xCD\x10'
# 3. Unreal mode
code += b'\xFA'
code += b'\x2E\x0F\x01\x16\x80\x7D' # LGDT [cs:0x7D80]
code += b'\x0F\x20\xC0\x0C\x01\x0F\x22\xC0\xEB\x00'
code += b'\xBB\x08\x00\x8E\xC3'    # ES = 0x08
code += b'\x0F\x20\xC0\x24\xFE\x0F\x22\xC0\xEB\x00'

# 4. Fill screen with dark blue (0x00000050)
code += b'\x66\xBF\x00\x00\x00\xE0' # EDI = 0xE0000000
code += b'\x66\xB9\x00\xB0\x04\x00' # ECX = 640*400 = 256000
code += b'\x66\xB8\x50\x00\x00\x00' # EAX = blue
code += b'\x67\x66\xF3\xAB'         # rep stosd

# 5. Enable Interrupts (STI)
code += b'\xFB'

# 6. Check INT 16h AH=01h in loop:
# loop:
#   mov ah, 1
#   int 0x16
#   jnz key_hit
#   in al, 0x64
#   test al, 1
#   jnz port_hit
#   jmp loop
code += b'\xB4\x01\xCD\x16'          # mov ah, 1; int 16h
code += b'\x75\x0B'                  # jnz key_hit (+11)
code += b'\xE4\x64'                  # in al, 0x64
code += b'\xA8\x01'                  # test al, 1
code += b'\x75\x13'                  # jnz port_hit (+19)
code += b'\xEB\xF3'                  # jmp loop (-13)

# key_hit: fill green
code += b'\xB4\x00\xCD\x16'          # read key
code += b'\x66\xBF\x00\x00\x00\xE0' # EDI = 0xE0000000
code += b'\x66\xB9\x00\xB0\x04\x00'
code += b'\x66\xB8\x00\xFF\x00\x00' # EAX = green
code += b'\x67\x66\xF3\xAB'
code += b'\xF4\xEB\xFD'

# port_hit: fill red
code += b'\xE4\x60'                  # in al, 0x60
code += b'\x66\xBF\x00\x00\x00\xE0'
code += b'\x66\xB9\x00\xB0\x04\x00'
code += b'\x66\xB8\x00\x00\xFF\x00' # EAX = red
code += b'\x67\x66\xF3\xAB'
code += b'\xF4\xEB\xFD'

assert len(code) <= 352
code += b'\x00' * (384 - len(code))
code += struct.pack('<HI', 23, 0x00007D90)
code += b'\x00' * (400 - len(code))
code += bytes([0,0,0,0,0,0,0,0, 0xFF,0xFF,0,0,0,0x92,0xCF,0, 0xFF,0xFF,0,0,0,0x9A,0,0])
code += b'\x00' * (510 - len(code))
code += b'\x55\xAA'

# Build ISO
SECTOR_SIZE = 2048
iso = bytearray(100 * SECTOR_SIZE)
pvd = bytearray(SECTOR_SIZE)
pvd[0] = 1; pvd[1:6] = b'CD001'; pvd[6] = 1
pvd[40:72] = b'TEST_INPUT'.ljust(32)
struct.pack_into('<I', pvd, 80, 100); struct.pack_into('>I', pvd, 84, 100)
struct.pack_into('<H', pvd, 120, 1); struct.pack_into('>H', pvd, 122, 1)
struct.pack_into('<H', pvd, 124, 1); struct.pack_into('>H', pvd, 126, 1)
struct.pack_into('<H', pvd, 128, SECTOR_SIZE); struct.pack_into('>H', pvd, 130, SECTOR_SIZE)
iso[16*SECTOR_SIZE:17*SECTOR_SIZE] = pvd

br = bytearray(SECTOR_SIZE); br[0]=0; br[1:6]=b'CD001'; br[6]=1; br[7:39]=b'EL TORITO SPECIFICATION'.ljust(32)
struct.pack_into('<I', br, 71, 19); iso[17*SECTOR_SIZE:18*SECTOR_SIZE] = br
term = bytearray(SECTOR_SIZE); term[0]=255; term[1:6]=b'CD001'; term[6]=1
iso[18*SECTOR_SIZE:19*SECTOR_SIZE] = term
c = bytearray(SECTOR_SIZE); c[0]=1; c[28]=0xAA; c[29]=0x55; c[30]=0x55; c[31]=0xAA
chk = sum(struct.unpack('<16H', c[0:32])) & 0xFFFF
if chk != 0: struct.pack_into('<H', c, 28, (0x10000 - chk) & 0xFFFF)
c[32]=0x88; struct.pack_into('<H', c, 38, 4); struct.pack_into('<I', c, 40, 20); iso[19*SECTOR_SIZE:20*SECTOR_SIZE] = c

bimg = bytearray(SECTOR_SIZE)
bimg[0:len(code)] = code
iso[20*SECTOR_SIZE:21*SECTOR_SIZE] = bimg

with open(r'C:\Users\barua\.gemini\antigravity\scratch\micro-os\virtualbox\micro-os.iso', 'wb') as f:
    f.write(iso)
print('Diagnostic ISO written!')
