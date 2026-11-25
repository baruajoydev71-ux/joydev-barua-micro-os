#!/usr/bin/env python3
"""
Joydev Micro-OS - Exact Bare Metal Desktop Operating System
Matches user's reference photograph:
- Purple/magenta folded-silk wallpaper gradient
- Top panel with Options, Desktop Files Documents Music Pictures Video, clock, audio, red power
- Two columns of desktop icons with labels
- Bottom dock with 7 launcher apps and Workspaces [ Workspace 1 ] [2] [3] [4]
- Centered mouse cursor
- Bare-metal VESA VBE 640x400x32 Linear Framebuffer in Oracle VM VirtualBox
"""
import os
import shutil
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

def build_os():
    a = Assembler()

    # 1. Entry Point: real mode setup
    a.emit(b'\xFA\xFC\x31\xC0\x8E\xD8\x8E\xC0\x8E\xD0\xBC\x00\x7C')

    # 2. Read 16 sectors (8 KB) into 0x1000:0x0000 via INT 13h AH=42h
    # DAP is at 0x7D60
    a.emit(b'\xB4\x42\xBE\x60\x7D\xCD\x13')

    # 3. Set VBE mode 640x400x32 (0x4141)
    a.emit(b'\xB8\x02\x4F\xBB\x41\x41\xCD\x10')

    # 4. Enter Unreal Mode (ES = 0x08 4GB flat)
    a.emit(b'\xFA')
    a.emit(b'\x2E\x0F\x01\x16\x80\x7D') # LGDT [cs:0x7D80]
    a.emit(b'\x0F\x20\xC0\x0C\x01\x0F\x22\xC0\xEB\x00')
    a.emit(b'\xBB\x08\x00\x8E\xC3')    # ES = 0x08
    a.emit(b'\x0F\x20\xC0\x24\xFE\x0F\x22\xC0\xEB\x00')

    # 5. Set DS = 0x1000 to read payload
    a.emit(b'\xB8\x00\x10\x8E\xD8')

    # =========================================================================
    # Step 1: Render All Rectangles from [0x1000:0x0002]
    # =========================================================================
    a.emit(b'\xBE\x02\x00')     # mov si, 0x0002
    a.emit(b'\x8B\x0E\x00\x00') # mov cx, [0x0000] (rect_count)

    a.label('rect_loop')
    a.emit(b'\x51')             # push cx
    a.emit(b'\xAD\x89\x06\x00\x05') # lodsw; mov [0x0500], ax (x)
    a.emit(b'\xAD\x89\x06\x02\x05') # lodsw; mov [0x0502], ax (y)
    a.emit(b'\xAD\x89\x06\x04\x05') # lodsw; mov [0x0504], ax (w)
    a.emit(b'\xAD\x89\x06\x06\x05') # lodsw; mov [0x0506], ax (h)
    a.emit(b'\x66\xAD\x66\x89\x06\x08\x05') # lodsd; mov [0x0508], eax (color)
    a.emit(b'\x56')             # push si
    a.j_near(b'\xE8', 'sub_fill_rect')
    a.emit(b'\x5E')             # pop si
    a.emit(b'\x59')             # pop cx
    a.j_rel8(b'\xE2', 'rect_loop')

    # =========================================================================
    # Step 2: Render All Text Strings from [0x1000:0x1402]
    # =========================================================================
    a.emit(b'\xBE\x02\x14')     # mov si, 0x1402
    a.emit(b'\x8B\x0E\x00\x14') # mov cx, [0x1400] (string_count)

    a.label('str_tbl_loop')
    a.emit(b'\x51')             # push cx
    a.emit(b'\xAD\x89\x06\x00\x05') # lodsw; mov [0x0500], ax (x)
    a.emit(b'\xAD\x89\x06\x02\x05') # lodsw; mov [0x0502], ax (y)
    a.emit(b'\x66\xAD\x66\x89\x06\x08\x05') # lodsd; mov [0x0508], eax (color)
    a.emit(b'\xAD\x89\xC7')     # lodsw; mov di, ax (text_offset)
    a.emit(b'\x56')             # push si
    a.emit(b'\x89\xFE')         # mov si, di
    a.j_near(b'\xE8', 'sub_draw_string')
    a.emit(b'\x5E')             # pop si
    a.emit(b'\x59')             # pop cx
    a.j_rel8(b'\xE2', 'str_tbl_loop')

    # =========================================================================
    # Step 3: Interactive Event Loop (Keyboard polling via BIOS INT 16h)
    # =========================================================================
    a.label('interactive_loop')
    a.emit(b'\xB4\x01\xCD\x16')      # mov ah, 0x01; int 0x16 (check keystroke)
    a.j_rel8(b'\x74', 'loop_idle')   # jz loop_idle (no key pressed)
    a.emit(b'\xB4\x00\xCD\x16')      # mov ah, 0x00; int 0x16 (read key into AL)
    a.label('loop_idle')
    a.emit(b'\xF4')                  # hlt
    a.j_rel8(b'\xEB', 'interactive_loop')

    # =========================================================================
    # Subroutine: fill_rect
    # =========================================================================
    a.label('sub_fill_rect')
    a.emit(b'\x60') # pusha
    # edi = 0xE0000000 + (y * 2560) + (x * 4)
    a.emit(b'\x66\x0F\xB7\x06\x02\x05')          # movzx eax, word [0x0502]
    a.emit(b'\x66\x69\xC0\x00\x0A\x00\x00')      # imul eax, 2560
    a.emit(b'\x66\x0F\xB7\x3E\x00\x05')          # movzx edi, word [0x0500]
    a.emit(b'\x66\xC1\xE7\x02')                  # shl edi, 2
    a.emit(b'\x66\x01\xC7')                      # add edi, eax
    a.emit(b'\x66\x81\xC7\x00\x00\x00\xE0')      # add edi, 0xE0000000
    a.emit(b'\x8B\x2E\x06\x05')                  # mov bp, word [0x0506]

    a.label('rect_row_loop')
    a.emit(b'\x66\x57')                          # push edi
    a.emit(b'\x66\x0F\xB7\x0E\x04\x05')          # movzx ecx, word [0x0504]
    a.emit(b'\x66\xA1\x08\x05')                  # mov eax, [0x0508]
    a.emit(b'\x67\x66\xF3\xAB')                  # addr32 rep stosd
    a.emit(b'\x66\x5F')                          # pop edi
    a.emit(b'\x66\x81\xC7\x00\x0A\x00\x00')      # add edi, 2560
    a.emit(b'\x4D')                              # dec bp
    a.j_rel8(b'\x75', 'rect_row_loop')
    a.emit(b'\x61\xC3')                          # popa; ret

    # =========================================================================
    # Subroutines: draw_char, draw_string
    # =========================================================================
    a.label('sub_draw_char')
    a.emit(b'\x60') # pusha
    # AL = char
    a.emit(b'\x2C\x20\xB4\x00')      # sub al, 32; mov ah, 0
    a.emit(b'\xC1\xE0\x03')          # shl ax, 3
    a.emit(b'\x05\x00\x18')          # add ax, 0x1800 (font table offset)
    a.emit(b'\x89\xC6')              # mov si, ax

    # edi = 0xE0000000 + (y * 2560) + (x * 4)
    a.emit(b'\x66\x0F\xB7\x06\x02\x05')
    a.emit(b'\x66\x69\xC0\x00\x0A\x00\x00')
    a.emit(b'\x66\x0F\xB7\x3E\x00\x05')
    a.emit(b'\x66\xC1\xE7\x02')
    a.emit(b'\x66\x01\xC7')
    a.emit(b'\x66\x81\xC7\x00\x00\x00\xE0')

    a.emit(b'\xBD\x08\x00')          # mov bp, 8 (8 rows)

    a.label('char_row')
    a.emit(b'\x66\x57')              # push edi
    a.emit(b'\xAC\x88\xC3')          # lodsb; mov bl, al
    a.emit(b'\xB9\x08\x00')          # mov cx, 8

    a.label('char_bit')
    a.emit(b'\xD0\xE3')              # shl bl, 1
    a.j_rel8(b'\x73', 'bit_zero')

    # Bit is 1: write pixel via addr32 stosd
    a.emit(b'\x66\xA1\x08\x05')      # mov eax, [0x0508] (color)
    a.emit(b'\x67\x66\xAB')          # addr32 stosd
    a.j_rel8(b'\xEB', 'bit_next')

    a.label('bit_zero')
    # Bit is 0: skip pixel
    a.emit(b'\x66\x83\xC7\x04')      # add edi, 4

    a.label('bit_next')
    a.j_rel8(b'\xE2', 'char_bit')

    a.emit(b'\x66\x5F')              # pop edi
    a.emit(b'\x66\x81\xC7\x00\x0A\x00\x00') # add edi, 2560
    a.emit(b'\x4D')                  # dec bp
    a.j_rel8(b'\x75', 'char_row')
    a.emit(b'\x61\xC3')              # popa; ret

    a.label('sub_draw_string')
    a.emit(b'\x60')                  # pusha
    a.label('str_loop')
    a.emit(b'\xAC\x08\xC0')          # lodsb; or al, al
    a.j_rel8(b'\x74', 'str_done')    # jz str_done
    a.emit(b'\x56')                  # push si
    a.j_near(b'\xE8', 'sub_draw_char')
    a.emit(b'\x5E')                  # pop si
    a.emit(b'\x83\x06\x00\x05\x08')  # add word [0x0500], 8
    a.j_rel8(b'\xEB', 'str_loop')
    a.label('str_done')
    a.emit(b'\x61\xC3')              # popa; ret

    sec1_code = bytearray(a.resolve())
    print(f"Bootloader code size: {len(sec1_code)} bytes (max 352)")
    assert len(sec1_code) <= 352

    # DAP at 352 (0x7D60):
    sec1_code += b'\x00' * (352 - len(sec1_code))
    dap = struct.pack('<BBHHHQ', 16, 0, 16, 0x0000, 0x1000, 21)
    sec1_code += dap

    # GDT ptr at 384 (0x7D80)
    sec1_code += b'\x00' * (384 - len(sec1_code))
    sec1_code += struct.pack('<HI', 23, 0x00007D90)
    sec1_code += b'\x00' * (400 - len(sec1_code))
    gdt = bytes([0,0,0,0,0,0,0,0, 0xFF,0xFF,0,0,0,0x92,0xCF,0, 0xFF,0xFF,0,0,0,0x9A,0,0])
    sec1_code += gdt
    sec1_code += b'\x00' * (510 - len(sec1_code))
    sec1_code += b'\x55\xAA'

    # Build UI Elements:
    rectangles = []
    def add_rect(x, y, w, h, hex_color):
        r = (hex_color >> 16) & 0xFF
        g = (hex_color >> 8) & 0xFF
        b = hex_color & 0xFF
        color_dword = (b) | (g << 8) | (r << 16)
        rectangles.append((x, y, w, h, color_dword))

    # 1. Base Wallpaper
    add_rect(0, 0, 640, 400, 0x16082A)     # Deep dark indigo/violet base
    add_rect(380, 0, 260, 400, 0x1A0B36)   # Soft violet field on right

    # 2. Diagonal Folded-Silk Ribbon Slices (matching photo gradient closely)
    for y in range(20, 368, 6):
        t = (y - 20) / 348.0
        cx = int(410 - 95 * t + 25 * (t ** 2))

        # Left dark shadow fold
        if y >= 140:
            sw = int(35 + 20 * t)
            add_rect(cx - 100 - sw, y, sw, 6, 0x0E0618)

        # Outer dark violet fold
        w1 = int(150 + 35 * t)
        add_rect(cx - w1//2, y, w1, 6, 0x300E4E)

        # Mid vibrant magenta band
        w2 = int(95 + 20 * t)
        add_rect(cx - w2//2, y, w2, 6, 0x961491)

        # Glowing magenta core
        w3 = int(60 + 10 * t)
        add_rect(cx - w3//2, y, w3, 6, 0xE11EBE)

        # Bright center highlight
        if 60 <= y <= 310:
            w4 = int(32 - 6 * abs(t - 0.5))
            add_rect(cx - w4//2, y, w4, 6, 0xFF41E1)
            if 100 <= y <= 260:
                w5 = 14
                add_rect(cx - w5//2, y, w5, 6, 0xFF96F5)

    # 3. Top Panel
    add_rect(0, 0, 640, 20, 0x10081C)
    # Blue Logo
    add_rect(8, 4, 11, 11, 0x06B6D4)
    # Red Power Badge
    add_rect(624, 5, 10, 10, 0xEF4444)
    # Speaker volume icon
    add_rect(606, 7, 5, 6, 0xCBD5E1)
    add_rect(611, 5, 3, 10, 0xCBD5E1)

    # 4. Desktop Icons Column 1 (x=14, y=26..330)
    col1_icons = [
        (26, 0xF1F5F9),  # File System
        (63, 0x06B6D4),  # Home
        (100, 0xE2E8F0), # Vyron Developer...
        (137, 0x3B82F6), # Vyron System Monitor
        (174, 0x0EA5E9), # Vyron Storage Exp...
        (211, 0xF8FAFC), # Vyron Settings
        (248, 0x06B6D4), # Vyron Network En...
        (285, 0xA855F7), # Vyron Microkernel...
        (322, 0xE2E8F0), # Vyron Hardware &...
    ]
    for y_ic, c in col1_icons:
        add_rect(14, y_ic, 20, 18, c)
        add_rect(16, y_ic + 2, 16, 14, 0x10051C) # inner cutout icon badge
        add_rect(18, y_ic + 4, 12, 10, c)

    # Column 2 (x=185, y=26..190)
    col2_icons = [
        (26, 0xF97316),  # Vyron Files
        (63, 0xFB923C),  # Vyron Web Browser
        (100, 0x94A3B8), # APT Package Manager
        (137, 0x38BDF8), # Vyron Wi-Fi Manager
        (174, 0xEA580C), # Snap Store
    ]
    for y_ic, c in col2_icons:
        add_rect(185, y_ic, 20, 18, c)
        add_rect(187, y_ic + 2, 16, 14, 0x10051C)
        add_rect(189, y_ic + 4, 12, 10, c)

    # 5. Center Mouse Pointer (Arrow at 330, 180)
    mx, my = 330, 180
    add_rect(mx, my, 2, 12, 0xFFFFFF)
    add_rect(mx+2, my+2, 2, 9, 0xFFFFFF)
    add_rect(mx+4, my+4, 2, 7, 0xFFFFFF)
    add_rect(mx+6, my+6, 2, 6, 0xFFFFFF)
    add_rect(mx+8, my+8, 2, 4, 0xFFFFFF)
    add_rect(mx+4, my+10, 4, 5, 0xFFFFFF)
    add_rect(mx-1, my-1, 1, 14, 0x000000) # Outline
    add_rect(mx+10, my+8, 1, 3, 0x000000)

    # 6. Bottom Dock
    add_rect(0, 368, 640, 32, 0x0E0618)
    add_rect(0, 368, 640, 1, 0xA8188C)

    # Dock Apps (7 apps)
    dock_apps = [
        (14, 0xEC4899),
        (38, 0x3B82F6),
        (62, 0xF97316),
        (86, 0x1E293B),
        (110, 0x0EA5E9),
        (134, 0xA855F7),
        (158, 0x64748B),
    ]
    for x_ic, c in dock_apps:
        add_rect(x_ic, 373, 18, 18, c)

    # Workspaces
    add_rect(410, 372, 88, 20, 0x8A1565) # Active Workspace 1 Pill
    add_rect(630, 374, 6, 16, 0x06B6D4)  # Cyan end badge

    # Build Text Strings
    strings = []
    string_bytes = bytearray()
    def add_str(x, y, hex_color, text):
        r = (hex_color >> 16) & 0xFF
        g = (hex_color >> 8) & 0xFF
        b = hex_color & 0xFF
        color_dword = (b) | (g << 8) | (r << 16)
        text_offset = 0x1B00 + len(string_bytes)
        string_bytes.extend(text.encode('ascii') + b'\x00')
        strings.append((x, y, color_dword, text_offset))

    # Top bar
    add_str(24, 6, 0xE2E8F0, "Options")
    add_str(80, 6, 0xCBD5E1, "Desktop Files Documents Music Pictures Video")
    add_str(465, 6, 0xCBD5E1, "Sat 21 Nov 21:05:13")

    # Column 1 Labels
    add_str(38, 30, 0xF1F5F9, "File System")
    add_str(38, 67, 0xF1F5F9, "Home")
    add_str(38, 104, 0xF1F5F9, "Vyron Developer...")
    add_str(38, 141, 0xF1F5F9, "Vyron System Monitor")
    add_str(38, 178, 0xF1F5F9, "Vyron Storage Exp...")
    add_str(38, 215, 0xF1F5F9, "Vyron Settings")
    add_str(38, 252, 0xF1F5F9, "Vyron Network En...")
    add_str(38, 289, 0xF1F5F9, "Vyron Microkernel...")
    add_str(38, 326, 0xF1F5F9, "Vyron Hardware &...")

    # Column 2 Labels
    add_str(210, 30, 0xF1F5F9, "Vyron Files")
    add_str(210, 67, 0xF1F5F9, "Vyron Web Browser")
    add_str(210, 104, 0xF1F5F9, "APT Package Manager")
    add_str(210, 141, 0xF1F5F9, "Vyron Wi-Fi Manager")
    add_str(210, 178, 0xF1F5F9, "Snap Store")

    # Dock Workspaces
    add_str(417, 376, 0xFFFFFF, "Workspace 1")
    add_str(504, 376, 0x94A3B8, "Workspace 2")
    add_str(556, 376, 0x94A3B8, "Workspace 3")
    add_str(608, 376, 0x94A3B8, "Workspace 4")

    # Assemble Payload Buffer (16 sectors = 8192 bytes)
    payload = bytearray(8192)

    # 1. Rectangle Table at 0x0000
    struct.pack_into('<H', payload, 0x0000, len(rectangles))
    rect_ptr = 0x0002
    for x, y, w, h, c in rectangles:
        struct.pack_into('<HHHH I', payload, rect_ptr, x, y, w, h, c)
        rect_ptr += 12
    print(f"Rectangles count: {len(rectangles)}, ends at 0x{rect_ptr:04X} (max 0x1400)")
    assert rect_ptr <= 0x1400

    # 2. String Table at 0x1400
    struct.pack_into('<H', payload, 0x1400, len(strings))
    str_ptr = 0x1402
    for x, y, c, text_off in strings:
        struct.pack_into('<HHI H', payload, str_ptr, x, y, c, text_off)
        str_ptr += 10
    print(f"Strings count: {len(strings)}, ends at 0x{str_ptr:04X} (max 0x1800)")
    assert str_ptr <= 0x1800

    # 3. Font Table at 0x1800
    font_bytes = generate_font_table()
    payload[0x1800 : 0x1800 + len(font_bytes)] = font_bytes

    # 4. String Pool at 0x1B00
    payload[0x1B00 : 0x1B00 + len(string_bytes)] = string_bytes
    print(f"String pool size: {len(string_bytes)} bytes")
    assert 0x1B00 + len(string_bytes) <= 8192

    # Build El Torito ISO
    SECTOR_SIZE = 2048
    iso = bytearray(300 * SECTOR_SIZE)
    # PVD at sector 16
    pvd = bytearray(SECTOR_SIZE)
    pvd[0] = 1; pvd[1:6] = b'CD001'; pvd[6] = 1
    pvd[40:72] = b'JOYDEV_MICRO_OS'.ljust(32)
    struct.pack_into('<I', pvd, 80, 300); struct.pack_into('>I', pvd, 84, 300)
    struct.pack_into('<H', pvd, 120, 1); struct.pack_into('>H', pvd, 122, 1)
    struct.pack_into('<H', pvd, 124, 1); struct.pack_into('>H', pvd, 126, 1)
    struct.pack_into('<H', pvd, 128, SECTOR_SIZE); struct.pack_into('>H', pvd, 130, SECTOR_SIZE)
    iso[16*SECTOR_SIZE:17*SECTOR_SIZE] = pvd

    # Boot Record at sector 17
    br = bytearray(SECTOR_SIZE)
    br[0] = 0; br[1:6] = b'CD001'; br[6] = 1; br[7:39] = b'EL TORITO SPECIFICATION'.ljust(32)
    struct.pack_into('<I', br, 71, 19); iso[17*SECTOR_SIZE:18*SECTOR_SIZE] = br

    # Volume Descriptor Set Terminator at sector 18
    term = bytearray(SECTOR_SIZE); term[0] = 255; term[1:6] = b'CD001'; term[6] = 1
    iso[18*SECTOR_SIZE:19*SECTOR_SIZE] = term

    # Boot Catalog at sector 19
    c = bytearray(SECTOR_SIZE); c[0]=1; c[28]=0xAA; c[29]=0x55; c[30]=0x55; c[31]=0xAA
    chk = sum(struct.unpack('<16H', c[0:32])) & 0xFFFF
    if chk != 0: struct.pack_into('<H', c, 28, (0x10000 - chk) & 0xFFFF)
    c[32]=0x88; struct.pack_into('<H', c, 38, 4); struct.pack_into('<I', c, 40, 20); iso[19*SECTOR_SIZE:20*SECTOR_SIZE] = c

    # Boot Image at sector 20
    bimg = bytearray(SECTOR_SIZE)
    bimg[0:len(sec1_code)] = sec1_code
    iso[20*SECTOR_SIZE:21*SECTOR_SIZE] = bimg

    # Payload at sectors 21..36 (8 KB = 16 sectors of 512 bytes = 4 ISO sectors)
    iso[21*SECTOR_SIZE : 21*SECTOR_SIZE + len(payload)] = payload

    iso_path = r"C:\Users\barua\.gemini\antigravity\scratch\micro-os\virtualbox\micro-os.iso"
    with open(iso_path, 'wb') as f:
        f.write(iso)
    print(f"Production Micro-OS ISO written: {iso_path} ({len(iso)} bytes)")

    # Also deploy to desktop for user convenience
    desktop_iso = r"C:\Users\barua\OneDrive\Pictures\Desktop\micro-os-v3.iso"
    try:
        shutil.copyfile(iso_path, desktop_iso)
        print(f"Deployed ISO to desktop: {desktop_iso}")
    except Exception as e:
        print(f"Warning deploying to desktop: {e}")

    # Build Fixed VHD (64 MB)
    vhd_path = r"C:\Users\barua\.gemini\antigravity\scratch\micro-os\virtualbox\micro-os.vhd"
    total_sectors = 131072 # 64 MB
    cylinders = 130; heads = 16; spt = 63
    vhd_disk = bytearray(512 * total_sectors)
    vhd_disk[0:len(sec1_code)] = sec1_code
    vhd_disk[512 : 512 + len(payload)] = payload
    footer = bytearray(512)
    footer[0:8] = b'conectix'
    struct.pack_into('>I', footer, 8, 2)
    struct.pack_into('>I', footer, 12, 0x00010000)
    struct.pack_into('>Q', footer, 16, 0xFFFFFFFFFFFFFFFF)
    struct.pack_into('>I', footer, 24, 0x2A000000)
    footer[28:32] = b'vpc '
    struct.pack_into('>I', footer, 32, 0x00050000)
    footer[36:40] = b'wi2k'
    struct.pack_into('>Q', footer, 40, total_sectors * 512)
    struct.pack_into('>Q', footer, 48, total_sectors * 512)
    struct.pack_into('>H', footer, 56, cylinders)
    footer[58] = heads; footer[59] = spt
    struct.pack_into('>I', footer, 60, 2)
    footer[64:80] = b'\xfe\xfa\x89\xbd\x42\xf3\x4e\xf8\xaa\xdb\x03\xf6\x64\x36\xa7\x89'
    chk = (~sum(footer[:64] + footer[68:512])) & 0xFFFFFFFF
    struct.pack_into('>I', footer, 64, chk)
    with open(vhd_path, 'wb') as f:
        f.write(vhd_disk)
        f.write(footer)
    print(f"Fixed VHD written: {vhd_path} ({os.path.getsize(vhd_path)} bytes)")

if __name__ == '__main__':
    build_os()
