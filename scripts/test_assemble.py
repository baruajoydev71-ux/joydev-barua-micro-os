import struct

def assemble():
    mbr = bytearray()
    mbr += b'\xFA'                         # cli
    mbr += b'\xFC'                         # cld
    mbr += b'\x31\xC0'                     # xor ax, ax
    mbr += b'\x8E\xD8'                     # mov ds, ax
    mbr += b'\x8E\xC0'                     # mov es, ax
    mbr += b'\x8E\xD0'                     # mov ss, ax
    mbr += b'\xBC\x00\x7C'                 # mov sp, 0x7C00
    mbr += b'\x88\x16\xFE\x7D'             # mov [0x7DFE], dl

    # 1. Set 80x25 16-color VGA text mode (AH=0x00, AL=0x03)
    mbr += b'\xB8\x03\x00\xCD\x10'         # mov ax, 0x0003; int 0x10

    # 2. Check if screen buffer is already in memory at 0x7E00
    # First word at 0x7E00 is ' ' (0x20) with attr 0x70 = 0x7020
    mbr += b'\x81\x3E\x00\x7E\x20\x70'     # cmp word [0x7E00], 0x7020 (6 bytes)
    mbr += b'\x74\x1E'                     # je .display (+30 bytes)

    # 3. Read 9 sectors from DL into 0x0000:0x7E00
    mbr += b'\x8A\x16\xFE\x7D'             # mov dl, [0x7DFE] (4 bytes)
    mbr += b'\xB8\x09\x02'                 # mov ax, 0x0209 (3 bytes)
    mbr += b'\x31\xC9'                     # xor cx, cx (2)
    mbr += b'\xB1\x02'                     # mov cl, 2 (2)
    mbr += b'\x30\xF6'                     # xor dh, dh (2)
    mbr += b'\xBB\x00\x7E'                 # mov bx, 0x7E00 (3)
    mbr += b'\xCD\x13'                     # int 0x13 (2)
    mbr += b'\x73\x0C'                     # jnc .display (+12 bytes)

    # Fallback retry with DL=0 (floppy)
    mbr += b'\x30\xD2'                     # xor dl, dl (2)
    mbr += b'\xB8\x09\x02'                 # mov ax, 0x0209 (3)
    mbr += b'\xB1\x02'                     # mov cl, 2 (2)
    mbr += b'\xBB\x00\x7E'                 # mov bx, 0x7E00 (3)
    mbr += b'\xCD\x13'                     # int 0x13 (2)

    # .display:
    mbr += b'\xB8\x00\xB8'                 # mov ax, 0xB800 (3)
    mbr += b'\x8E\xC0'                     # mov es, ax (2)
    mbr += b'\x31\xFF'                     # xor di, di (2)
    mbr += b'\xBE\x00\x7E'                 # mov si, 0x7E00 (3)
    mbr += b'\xB9\xD0\x07'                 # mov cx, 2000 (0x07D0) (3)
    mbr += b'\xF3\xA5'                     # rep movsw (2)

    # Also log to COM1 serial (0x3F8)
    mbr += b'\xBE\x00\x7E'                 # mov si, 0x7E00 (3)
    mbr += b'\xBA\xF8\x03'                 # mov dx, 0x3F8 (3)
    mbr += b'\xB9\xD0\x07'                 # mov cx, 2000 (3)
    # .serial_loop:
    mbr += b'\x8A\x04'                     # mov al, [si] (2)
    mbr += b'\xEE'                         # out dx, al (1)
    mbr += b'\x83\xC6\x02'                 # add si, 2 (3)
    mbr += b'\xE2\xF8'                     # loop .serial_loop (-8 bytes) (2)

    # Halt
    mbr += b'\xFA\xF4\xEB\xFD'             # cli; hlt; jmp $-1 (4)

    assert len(mbr) <= 510, f"MBR length exceeds 510: {len(mbr)}"
    mbr += b'\x00' * (510 - len(mbr))
    mbr += b'\x55\xAA'

    print("MBR assembled successfully! Length =", len(mbr))
    return mbr

assemble()
