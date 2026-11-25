import struct

def test_kernel():
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

    # 2. Clear screen with Royal Blue background and White text
    mbr += b'\xB8\x00\x06'                 # mov ax, 0x0600
    mbr += b'\xB7\x1F'                     # mov bh, 0x1F
    mbr += b'\x31\xC9'                     # xor cx, cx
    mbr += b'\xBA\x4F\x18'                 # mov dx, 0x184F
    mbr += b'\xCD\x10'                     # int 0x10

    # 3. Set cursor to row 0, col 0
    mbr += b'\xB4\x02'                     # mov ah, 0x02
    mbr += b'\x30\xFF'                     # xor bh, bh
    mbr += b'\x31\xD2'                     # xor dx, dx
    mbr += b'\xCD\x10'                     # int 0x10

    # 4. Check if kernel is already in memory at 0x7E00
    mbr += b'\x81\x3E\x00\x7E\xEB\x17'     # cmp word [0x7E00], 0x17EB
    mbr += b'\x74\x22'                     # je .jump_kernel (+34 bytes)

    # 5. Read 8 sectors
    mbr += b'\x8A\x16\xFE\x7D'             # mov dl, [0x7DFE]
    mbr += b'\xB4\x02'                     # mov ah, 0x02
    mbr += b'\xB0\x08'                     # mov al, 8
    mbr += b'\x31\xC9'                     # xor cx, cx
    mbr += b'\xB1\x02'                     # mov cl, 2
    mbr += b'\x30\xF6'                     # xor dh, dh
    mbr += b'\xBB\x00\x7E'                 # mov bx, 0x7E00
    mbr += b'\xCD\x13'                     # int 0x13
    mbr += b'\x73\x0D'                     # jnc .jump_kernel (+13 bytes)

    # Fallback retry with DL=0
    mbr += b'\x30\xD2'                     # xor dl, dl
    mbr += b'\xB4\x02'                     # mov ah, 0x02
    mbr += b'\xB0\x08'                     # mov al, 8
    mbr += b'\xB1\x02'                     # mov cl, 2
    mbr += b'\xBB\x00\x7E'                 # mov bx, 0x7E00
    mbr += b'\xCD\x13'                     # int 0x13

    # .jump_kernel:
    mbr += b'\xB8\x00\x7E\xFF\xE0'         # mov ax, 0x7E00; jmp ax
    
    assert len(mbr) <= 510, f"MBR too large: {len(mbr)}"
    mbr += b'\x00' * (510 - len(mbr))
    mbr += b'\x55\xAA'

    # Kernel
    kernel = bytearray()
    kernel += b'\xEB\x15'                  # jmp short to main execution (+21 bytes to 0x7E18)
    kernel += b'\x90'                      # nop (at 0x7E02)

    # print_string at 0x7E03:
    prn = bytearray()
    prn += b'\xAC'                         # lodsb (0x7E03)
    prn += b'\x84\xC0'                     # test al, al (0x7E04)
    prn += b'\x74\x0F'                     # jz .done (+15 bytes: skips to C3) (0x7E06)
    prn += b'\xB4\x0E'                     # mov ah, 0x0E (0x7E08)
    prn += b'\x30\xFF'                     # xor bh, bh (0x7E0A)
    prn += b'\xB3\x0F'                     # mov bl, 0x0F (0x7E0C)
    prn += b'\xCD\x10'                     # int 0x10 (0x7E0E)
    prn += b'\x52'                         # push dx (0x7E10)
    prn += b'\xBA\xF8\x03'                 # mov dx, 0x3F8 (0x7E11)
    prn += b'\xEE'                         # out dx, al (0x7E14)
    prn += b'\x5A'                         # pop dx (0x7E15)
    prn += b'\xEB\xEA'                     # jmp prn (-22 bytes to 0x7E03) (0x7E16)
    prn += b'\xC3'                         # ret (0x7E18)

    print("prn len:", len(prn))
    assert len(prn) == 22, f"prn length is {len(prn)}"
    assert prn[len(prn)-1] == 0xC3, "Last byte of prn must be ret (0xC3)"
    
    kernel += prn
    print("Kernel entry after jmp:", hex(0x7E00 + len(kernel)))

test_kernel()
