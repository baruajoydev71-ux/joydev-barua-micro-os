#!/usr/bin/env python3
"""
Joydev Micro-OS - Full Interactive Bare Metal Operating System
Direct bare metal execution in Oracle VM VirtualBox (VESA VBE 640x400x32 Linear Framebuffer)
Zero web browser dependency.
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

def build_bootloader():
    a = Assembler()

    # 1. Real Mode Setup
    a.emit(b'\xFA\xFC\x31\xC0\x8E\xD8\x8E\xC0\x8E\xD0\xBC\x00\x7C')

    # 2. Read 64 sectors (32 KB) into 0x1000:0x0000 via INT 13h AH=42h
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

    # 5. Far jump to Kernel at 0x1000:0x0000
    a.emit(b'\xEA\x00\x00\x00\x10')

    sec1_code = bytearray(a.resolve())
    print(f"Bootloader code size: {len(sec1_code)} bytes (max 352)")
    assert len(sec1_code) <= 352

    # DAP at 352 (0x7D60):
    sec1_code += b'\x00' * (352 - len(sec1_code))
    dap = struct.pack('<BBHHHQ', 16, 0, 64, 0x0000, 0x1000, 21)
    sec1_code += dap

    # GDT ptr at 384 (0x7D80)
    sec1_code += b'\x00' * (384 - len(sec1_code))
    sec1_code += struct.pack('<HI', 23, 0x00007D90)
    sec1_code += b'\x00' * (400 - len(sec1_code))
    gdt = bytes([0,0,0,0,0,0,0,0, 0xFF,0xFF,0,0,0,0x92,0xCF,0, 0xFF,0xFF,0,0,0,0x9A,0,0])
    sec1_code += gdt
    sec1_code += b'\x00' * (510 - len(sec1_code))
    sec1_code += b'\x55\xAA'

    return sec1_code

def build_kernel_code():
    a = Assembler()

    # Kernel Entry Point at 0x1000:0x0000
    # Set DS = CS = 0x1000, SS = 0x0000, SP = 0x7000
    a.emit(b'\x8C\xC8\x8E\xD8\x31\xC0\x8E\xD0\xBC\x00\x70')

    # State variables at 0x1F00..0x1F20:
    # 0x1F00: active_view (word) = 0
    # 0x1F02: mouse_x (word) = 330
    # 0x1F04: mouse_y (word) = 180
    # 0x1F06: temp_x, temp_y, temp_w, temp_h
    # 0x1F10: color (dword)
    a.emit(b'\xC7\x06\x00\x1F\x00\x00') # mov word [0x1F00], 0 (active_view)
    a.emit(b'\xC7\x06\x02\x1F\x4A\x01') # mov word [0x1F02], 330 (mouse_x)
    a.emit(b'\xC7\x06\x04\x1F\xB4\x00') # mov word [0x1F04], 180 (mouse_y)

    # Render Initial Active View (View 0: Clean Desktop)
    a.emit(b'\xB8\x00\x00')             # mov ax, 0
    a.j_near(b'\xE8', 'sub_render_view')

    # Draw initial mouse cursor
    a.j_near(b'\xE8', 'sub_draw_cursor')

    # Enable interrupts so BIOS keyboard & timer IRQs work
    a.emit(b'\xFB') # STI

    # =========================================================================
    # Interactive Event Loop
    # =========================================================================
    a.label('event_loop')

    # 1. Check Keyboard via INT 16h AH=01h
    a.emit(b'\xB4\x01\xCD\x16')          # mov ah, 1; int 16h
    a.j_rel8(b'\x75', 'key_ready')        # jnz key_ready
    a.j_near(b'\xE9', 'check_ps2_mouse')   # jmp near check_ps2_mouse
    a.label('key_ready')

    # Key pressed! Read keystroke via INT 16h AH=00h
    a.emit(b'\xB4\x00\xCD\x16')          # mov ah, 0; int 16h -> AH=scan, AL=ascii

    # Arrow Keys for cursor movement:
    # Up: AH == 0x48
    a.emit(b'\x80\xFC\x48')
    a.j_rel8(b'\x75', 'not_up')
    a.j_near(b'\xE8', 'sub_erase_cursor')
    a.emit(b'\x83\x2E\x04\x1F\x0C')      # sub word [0x1F04], 12 (y -= 12)
    a.j_near(b'\xE8', 'sub_clamp_mouse')
    a.j_near(b'\xE8', 'sub_draw_cursor')
    a.j_near(b'\xE9', 'event_loop')

    a.label('not_up')
    # Down: AH == 0x50
    a.emit(b'\x80\xFC\x50')
    a.j_rel8(b'\x75', 'not_down')
    a.j_near(b'\xE8', 'sub_erase_cursor')
    a.emit(b'\x83\x06\x04\x1F\x0C')      # add word [0x1F04], 12 (y += 12)
    a.j_near(b'\xE8', 'sub_clamp_mouse')
    a.j_near(b'\xE8', 'sub_draw_cursor')
    a.j_near(b'\xE9', 'event_loop')

    a.label('not_down')
    # Left: AH == 0x4B
    a.emit(b'\x80\xFC\x4B')
    a.j_rel8(b'\x75', 'not_left')
    a.j_near(b'\xE8', 'sub_erase_cursor')
    a.emit(b'\x83\x2E\x02\x1F\x0C')      # sub word [0x1F02], 12 (x -= 12)
    a.j_near(b'\xE8', 'sub_clamp_mouse')
    a.j_near(b'\xE8', 'sub_draw_cursor')
    a.j_near(b'\xE9', 'event_loop')

    a.label('not_left')
    # Right: AH == 0x4D
    a.emit(b'\x80\xFC\x4D')
    a.j_rel8(b'\x75', 'not_right')
    a.j_near(b'\xE8', 'sub_erase_cursor')
    a.emit(b'\x83\x06\x02\x1F\x0C')      # add word [0x1F02], 12 (x += 12)
    a.j_near(b'\xE8', 'sub_clamp_mouse')
    a.j_near(b'\xE8', 'sub_draw_cursor')
    a.j_near(b'\xE9', 'event_loop')

    a.label('not_right')
    # Enter (13) or Space (32) -> Click action at (mouse_x, mouse_y)
    a.emit(b'\x3C\x0D')
    a.j_rel8(b'\x74', 'loc_click')
    a.emit(b'\x3C\x20')
    a.j_rel8(b'\x75', 'not_click')
    a.label('loc_click')
    a.j_near(b'\xE9', 'do_click')
    a.label('not_click')

    # Hotkeys:
    # 'w' or 'W' -> View 1 (Wi-Fi)
    a.emit(b'\x3C\x77\x74\x06\x3C\x57\x75\x0B') # cmp al, 'w'; jz; cmp al, 'W'; jnz
    a.emit(b'\xC7\x06\x00\x1F\x01\x00')         # mov word [0x1F00], 1
    a.j_near(b'\xE9', 'redraw_all')

    # 'h' or 'H' -> View 2 (Hardware)
    a.emit(b'\x3C\x68\x74\x06\x3C\x48\x75\x0B')
    a.emit(b'\xC7\x06\x00\x1F\x02\x00')         # mov word [0x1F00], 2
    a.j_near(b'\xE9', 'redraw_all')

    # 'm' or 'M' -> View 3 (Monitor)
    a.emit(b'\x3C\x6D\x74\x06\x3C\x4D\x75\x0B')
    a.emit(b'\xC7\x06\x00\x1F\x03\x00')         # mov word [0x1F00], 3
    a.j_near(b'\xE9', 'redraw_all')

    # 't' or 'T' -> View 4 (Terminal)
    a.emit(b'\x3C\x74\x74\x06\x3C\x54\x75\x0B')
    a.emit(b'\xC7\x06\x00\x1F\x04\x00')         # mov word [0x1F00], 4
    a.j_near(b'\xE9', 'redraw_all')

    # '1' -> View 0 (Desktop)
    a.emit(b'\x3C\x31')
    a.j_rel8(b'\x75', 'not_1')
    a.emit(b'\xC7\x06\x00\x1F\x00\x00')
    a.j_near(b'\xE9', 'redraw_all')

    a.label('not_1')
    # '2' -> View 1 (Wi-Fi)
    a.emit(b'\x3C\x32')
    a.j_rel8(b'\x75', 'not_2')
    a.emit(b'\xC7\x06\x00\x1F\x01\x00')
    a.j_near(b'\xE9', 'redraw_all')

    a.label('not_2')
    # '3' -> View 2 (Hardware)
    a.emit(b'\x3C\x33')
    a.j_rel8(b'\x75', 'not_3')
    a.emit(b'\xC7\x06\x00\x1F\x02\x00')
    a.j_near(b'\xE9', 'redraw_all')

    a.label('not_3')
    # '4' -> View 4 (Terminal)
    a.emit(b'\x3C\x34')
    a.j_rel8(b'\x75', 'not_4')
    a.emit(b'\xC7\x06\x00\x1F\x04\x00')
    a.j_near(b'\xE9', 'redraw_all')

    a.label('not_4')
    # ESC (27) or 'c' or 'C' -> View 0 (Clean Desktop)
    a.emit(b'\x3C\x1B\x74\x08\x3C\x63\x74\x04\x3C\x43\x75\x08')
    a.emit(b'\xC7\x06\x00\x1F\x00\x00')
    a.j_near(b'\xE9', 'redraw_all')

    # Other keys: ignore
    a.j_near(b'\xE9', 'check_ps2_mouse')

    # =========================================================================
    # Click Handler
    # =========================================================================
    a.label('do_click')
    # Check if close button clicked: x >= 580 and y <= 45 and active_view > 0
    a.emit(b'\x81\x3E\x02\x1F\x44\x02') # cmp word [0x1F02], 580
    a.j_rel8(b'\x72', 'check_dock_click')
    a.emit(b'\x83\x3E\x04\x1F\x2D')      # cmp word [0x1F04], 45
    a.j_rel8(b'\x77', 'check_dock_click')
    # Clicked close button!
    a.emit(b'\xC7\x06\x00\x1F\x00\x00') # active_view = 0
    a.j_near(b'\xE9', 'redraw_all')

    a.label('check_dock_click')
    # If y >= 365: Click is on Bottom Dock!
    a.emit(b'\x81\x3E\x04\x1F\x6D\x01') # cmp word [0x1F04], 365
    a.j_rel8(b'\x73', 'is_dock')
    a.j_near(b'\xE9', 'check_icon_click')
    a.label('is_dock')

    # Dock items:
    a.emit(b'\x8B\x1E\x02\x1F')          # mov bx, [0x1F02] (x)
    a.emit(b'\x81\xFB\x90\x01')          # cmp bx, 400
    a.j_rel8(b'\x72', 'dock_apps_check')

    # Workspace pills:
    a.emit(b'\x81\xFB\xF4\x01')          # cmp bx, 500
    a.j_rel8(b'\x77', 'dock_ws2')
    a.emit(b'\xC7\x06\x00\x1F\x00\x00')  # WS1 -> View 0
    a.j_near(b'\xE9', 'redraw_all')

    a.label('dock_ws2')
    a.emit(b'\x81\xFB\x26\x02')          # cmp bx, 550
    a.j_rel8(b'\x77', 'dock_ws3')
    a.emit(b'\xC7\x06\x00\x1F\x01\x00')  # WS2 -> View 1 (Wi-Fi)
    a.j_near(b'\xE9', 'redraw_all')

    a.label('dock_ws3')
    a.emit(b'\x81\xFB\x58\x02')          # cmp bx, 600
    a.j_rel8(b'\x77', 'dock_ws4')
    a.emit(b'\xC7\x06\x00\x1F\x02\x00')  # WS3 -> View 2 (Hardware)
    a.j_near(b'\xE9', 'redraw_all')

    a.label('dock_ws4')
    a.emit(b'\xC7\x06\x00\x1F\x04\x00')  # WS4 -> View 4 (Terminal)
    a.j_near(b'\xE9', 'redraw_all')

    a.label('dock_apps_check')
    # Terminal icon around x=86
    a.emit(b'\x81\xFB\x50\x00\x72\x08\x81\xFB\x6A\x00\x77\x08')
    a.emit(b'\xC7\x06\x00\x1F\x04\x00')  # View 4
    a.j_near(b'\xE9', 'redraw_all')
    # Wi-Fi icon around x=110
    a.emit(b'\x81\xFB\x6A\x00\x72\x08\x81\xFB\x84\x00\x77\x08')
    a.emit(b'\xC7\x06\x00\x1F\x01\x00')  # View 1
    a.j_near(b'\xE9', 'redraw_all')
    # Monitor icon around x=134
    a.emit(b'\x81\xFB\x84\x00\x72\x08\x81\xFB\x9E\x00\x77\x08')
    a.emit(b'\xC7\x06\x00\x1F\x03\x00')  # View 3
    a.j_near(b'\xE9', 'redraw_all')
    a.j_near(b'\xE9', 'check_ps2_mouse')

    a.label('check_icon_click')
    # Desktop icon clicks:
    # If Col 2, Wi-Fi icon: x in [180..300], y in [130..165] -> View 1 (Wi-Fi)
    a.emit(b'\x8B\x1E\x02\x1F\x8B\x0E\x04\x1F') # BX=x, CX=y
    a.emit(b'\x81\xFB\xB4\x00\x72\x15\x81\xFB\x2C\x01\x77\x0F') # x in 180..300
    a.emit(b'\x81\xF9\x82\x00\x72\x09\x81\xF9\xA5\x00\x77\x03') # y in 130..165
    a.emit(b'\xC7\x06\x00\x1F\x01\x00')  # View 1
    a.j_near(b'\xE9', 'redraw_all')

    # If Col 1, Sys Monitor: x in [14..160], y in [130..165] -> View 3 (Monitor)
    a.emit(b'\x81\xFB\x0E\x00\x72\x15\x81\xFB\xA0\x00\x77\x0F')
    a.emit(b'\x81\xF9\x82\x00\x72\x09\x81\xF9\xA5\x00\x77\x03')
    a.emit(b'\xC7\x06\x00\x1F\x03\x00')  # View 3
    a.j_near(b'\xE9', 'redraw_all')

    # If Col 1, Hardware: x in [14..160], y in [315..355] -> View 2 (Hardware)
    a.emit(b'\x81\xFB\x0E\x00\x72\x15\x81\xFB\xA0\x00\x77\x0F')
    a.emit(b'\x81\xF9\x3B\x01\x72\x09\x81\xF9\x63\x01\x77\x03')
    a.emit(b'\xC7\x06\x00\x1F\x02\x00')  # View 2
    a.j_near(b'\xE9', 'redraw_all')

    # If none matched: check PS/2 mouse
    a.j_near(b'\xE9', 'check_ps2_mouse')

    # Redraw active view & cursor
    a.label('redraw_all')
    a.emit(b'\x8B\x06\x00\x1F')          # mov ax, [0x1F00] (active_view)
    a.j_near(b'\xE8', 'sub_render_view')
    a.j_near(b'\xE8', 'sub_draw_cursor')
    a.j_near(b'\xE9', 'event_loop')

    # 2. Check PS/2 Mouse on port 0x64
    a.label('check_ps2_mouse')
    a.emit(b'\xE4\x64')                  # in al, 0x64
    a.emit(b'\xA8\x01')                  # test al, 1 (data ready)
    a.j_rel8(b'\x74', 'loop_done')
    a.emit(b'\xA8\x20')                  # test al, 0x20 (mouse byte)
    a.j_rel8(b'\x74', 'loop_done')
    # Discard / read mouse byte
    a.emit(b'\xE4\x60')                  # in al, 0x60

    a.label('loop_done')
    a.emit(b'\xF4')                      # hlt (wait for next interrupt/tick)
    a.j_near(b'\xE9', 'event_loop')

    # =========================================================================
    # Subroutine: Clamp mouse cursor coordinates [0..624, 0..384]
    # =========================================================================
    a.label('sub_clamp_mouse')
    # clamp x: min 0, max 624 (0x0270)
    a.emit(b'\x83\x3E\x02\x1F\x00\x7D\x06\xC7\x06\x02\x1F\x00\x00')
    a.emit(b'\x81\x3E\x02\x1F\x70\x02\x7E\x06\xC7\x06\x02\x1F\x70\x02')
    # clamp y: min 0, max 384 (0x0180)
    a.emit(b'\x83\x3E\x04\x1F\x00\x7D\x06\xC7\x06\x04\x1F\x00\x00')
    a.emit(b'\x81\x3E\x04\x1F\x80\x01\x7E\x06\xC7\x06\x04\x1F\x80\x01')
    a.emit(b'\xC3')                      # ret

    # =========================================================================
    # Subroutine: Draw Mouse Cursor (Saves 12x16 background, draws white arrow)
    # =========================================================================
    a.label('sub_draw_cursor')
    a.emit(b'\x60')                      # pusha

    # EDI = 0xE0000000 + (mouse_y * 2560) + (mouse_x * 4)
    a.emit(b'\x66\x0F\xB7\x06\x04\x1F')  # movzx eax, [0x1F04] (y)
    a.emit(b'\x66\x69\xC0\x00\x0A\x00\x00') # imul eax, 2560
    a.emit(b'\x66\x0F\xB7\x3E\x02\x1F')  # movzx edi, [0x1F02] (x)
    a.emit(b'\x66\xC1\xE7\x02')          # shl edi, 2
    a.emit(b'\x66\x01\xC7')              # add edi, eax
    a.emit(b'\x66\x81\xC7\x00\x00\x00\xE0') # add edi, 0xE0000000

    # Save 12x16 pixels into save_buffer at 0x7A00
    a.emit(b'\xBE\x00\x7A')              # mov si, 0x7A00
    a.emit(b'\xBD\x10\x00')              # mov bp, 16 (16 rows)

    a.label('save_row_loop')
    a.emit(b'\x66\x57')                  # push edi
    a.emit(b'\xB9\x0C\x00')              # mov cx, 12 (12 dwords)
    a.label('save_col_loop')
    a.emit(b'\x67\x66\x8B\x07')          # mov eax, es:[edi] (addr32)
    a.emit(b'\x66\x89\x04')              # mov [si], eax
    a.emit(b'\x66\x83\xC7\x04')          # add edi, 4
    a.emit(b'\x83\xC6\x04')              # add si, 4
    a.emit(b'\x49')                      # dec cx
    a.j_rel8(b'\x75', 'save_col_loop')
    a.emit(b'\x66\x5F')                  # pop edi
    a.emit(b'\x66\x81\xC7\x00\x0A\x00\x00') # add edi, 2560
    a.emit(b'\x4D')                      # dec bp
    a.j_rel8(b'\x75', 'save_row_loop')

    # Draw Cursor Sprite onto VRAM
    # EDI rewind
    a.emit(b'\x66\x0F\xB7\x06\x04\x1F')
    a.emit(b'\x66\x69\xC0\x00\x0A\x00\x00')
    a.emit(b'\x66\x0F\xB7\x3E\x02\x1F')
    a.emit(b'\x66\xC1\xE7\x02')
    a.emit(b'\x66\x01\xC7')
    a.emit(b'\x66\x81\xC7\x00\x00\x00\xE0')

    a.emit(b'\xBE\x00\x78')              # mov si, 0x7800 (cursor sprite table)
    a.emit(b'\xBD\x10\x00')              # mov bp, 16 (16 rows)

    a.label('draw_row_loop')
    a.emit(b'\x66\x57')                  # push edi
    a.emit(b'\xAD\x89\xC2')              # lodsw; mov dx, ax (fill mask)
    a.emit(b'\xAD\x89\xC3')              # lodsw; mov bx, ax (outline mask)
    a.emit(b'\xB9\x0C\x00')              # mov cx, 12 (12 pixels)

    a.label('draw_pix_loop')
    a.emit(b'\xD1\xE2')                  # shl dx, 1
    a.j_rel8(b'\x72', 'draw_white')
    a.emit(b'\xD1\xE3')                  # shl bx, 1
    a.j_rel8(b'\x72', 'draw_black')
    # transparent
    a.emit(b'\x66\x83\xC7\x04')          # add edi, 4
    a.j_rel8(b'\xEB', 'next_pix')

    a.label('draw_white')
    a.emit(b'\xD1\xE3')                  # shl bx, 1 (keep in sync)
    a.emit(b'\x67\x66\xC7\x07\xFF\xFF\xFF\x00') # addr32 mov dword es:[edi], 0x00FFFFFF
    a.emit(b'\x66\x83\xC7\x04')
    a.j_rel8(b'\xEB', 'next_pix')

    a.label('draw_black')
    a.emit(b'\x67\x66\xC7\x07\x00\x00\x00\x00') # addr32 mov dword es:[edi], 0x00000000
    a.emit(b'\x66\x83\xC7\x04')

    a.label('next_pix')
    a.emit(b'\x49')                      # dec cx
    a.j_rel8(b'\x75', 'draw_pix_loop')
    a.emit(b'\x66\x5F')                  # pop edi
    a.emit(b'\x66\x81\xC7\x00\x0A\x00\x00') # add edi, 2560
    a.emit(b'\x4D')                      # dec bp
    a.j_rel8(b'\x75', 'draw_row_loop')

    a.emit(b'\x61\xC3')                  # popa; ret

    # =========================================================================
    # Subroutine: Erase Mouse Cursor (Restores 12x16 saved background)
    # =========================================================================
    a.label('sub_erase_cursor')
    a.emit(b'\x60')                      # pusha

    # EDI = 0xE0000000 + (mouse_y * 2560) + (mouse_x * 4)
    a.emit(b'\x66\x0F\xB7\x06\x04\x1F')
    a.emit(b'\x66\x69\xC0\x00\x0A\x00\x00')
    a.emit(b'\x66\x0F\xB7\x3E\x02\x1F')
    a.emit(b'\x66\xC1\xE7\x02')
    a.emit(b'\x66\x01\xC7')
    a.emit(b'\x66\x81\xC7\x00\x00\x00\xE0')

    a.emit(b'\xBE\x00\x7A')              # mov si, 0x7A00 (save_buffer)
    a.emit(b'\xBD\x10\x00')              # mov bp, 16 rows

    a.label('erase_row_loop')
    a.emit(b'\x66\x57')                  # push edi
    a.emit(b'\x66\xB9\x0C\x00\x00\x00')  # mov ecx, 12
    a.emit(b'\x67\x66\xF3\xA5')          # addr32 rep movsd (DS:ESI -> ES:EDI)
    a.emit(b'\x66\x5F')                  # pop edi
    a.emit(b'\x66\x81\xC7\x00\x0A\x00\x00') # add edi, 2560
    a.emit(b'\x4D')                      # dec bp
    a.j_rel8(b'\x75', 'erase_row_loop')

    a.emit(b'\x61\xC3')                  # popa; ret

    # =========================================================================
    # Subroutine: Render Active View (AX = view_id: 0..4)
    # =========================================================================
    a.label('sub_render_view')
    a.emit(b'\x60')                      # pusha
    a.emit(b'\x89\xC5')                  # mov bp, ax (view_id)

    # 1. Always render View 0 (Clean Desktop)
    a.emit(b'\xBE\x00\x20')              # mov si, 0x2000 (view 0 table)
    a.j_near(b'\xE8', 'sub_render_table')

    # 2. If view_id == 0, done!
    a.emit(b'\x09\xED')                  # or bp, bp
    a.j_rel8(b'\x74', 'view_done')

    # 3. View 1 (Wi-Fi): table at 0x4000
    a.emit(b'\x83\xFD\x01\x75\x08')      # cmp bp, 1; jne
    a.emit(b'\xBE\x00\x40')              # mov si, 0x4000
    a.j_rel8(b'\xEB', 'do_render_subview')

    # View 2 (Hardware): table at 0x4800
    a.emit(b'\x83\xFD\x02\x75\x08')      # cmp bp, 2; jne
    a.emit(b'\xBE\x00\x48')              # mov si, 0x4800
    a.j_rel8(b'\xEB', 'do_render_subview')

    # View 3 (Monitor): table at 0x5000
    a.emit(b'\x83\xFD\x03\x75\x08')      # cmp bp, 3; jne
    a.emit(b'\xBE\x00\x50')              # mov si, 0x5000
    a.j_rel8(b'\xEB', 'do_render_subview')

    # View 4 (Terminal): table at 0x5800
    a.emit(b'\xBE\x00\x58')              # mov si, 0x5800

    a.label('do_render_subview')
    a.j_near(b'\xE8', 'sub_render_table')

    a.label('view_done')
    a.emit(b'\x61\xC3')                  # popa; ret

    # =========================================================================
    # Subroutine: Render Table from SI
    # [SI]: rect_count (word)
    # [SI+2]: rects (12 bytes each: x, y, w, h, color)
    # then string_count (word)
    # then strings (10 bytes each: x, y, color, text_off)
    # =========================================================================
    a.label('sub_render_table')
    a.emit(b'\x60')                      # pusha
    a.emit(b'\xAD\x89\xC1')              # lodsw; mov cx, ax (rect_count)
    a.emit(b'\xE3\x25')                  # jcxz no_rects

    a.label('tbl_rect_loop')
    a.emit(b'\x51')                      # push cx
    a.emit(b'\xAD\x89\x06\x06\x1F')      # lodsw; mov [0x1F06], ax (x)
    a.emit(b'\xAD\x89\x06\x08\x1F')      # lodsw; mov [0x1F08], ax (y)
    a.emit(b'\xAD\x89\x06\x0A\x1F')      # lodsw; mov [0x1F0A], ax (w)
    a.emit(b'\xAD\x89\x06\x0C\x1F')      # lodsw; mov [0x1F0C], ax (h)
    a.emit(b'\x66\xAD\x66\x89\x06\x10\x1F') # lodsd; mov [0x1F10], eax (color)
    a.emit(b'\x56')                      # push si
    a.j_near(b'\xE8', 'sub_fill_rect')
    a.emit(b'\x5E\x59')                  # pop si; pop cx
    a.emit(b'\x49')                      # dec cx
    a.j_rel8(b'\x75', 'tbl_rect_loop')

    a.label('no_rects')
    # Strings:
    a.emit(b'\xAD\x89\xC1')              # lodsw; mov cx, ax (string_count)
    a.emit(b'\xE3\x21')                  # jcxz no_strings

    a.label('tbl_str_loop')
    a.emit(b'\x51')                      # push cx
    a.emit(b'\xAD\x89\x06\x06\x1F')      # lodsw; mov [0x1F06], ax (x)
    a.emit(b'\xAD\x89\x06\x08\x1F')      # lodsw; mov [0x1F08], ax (y)
    a.emit(b'\x66\xAD\x66\x89\x06\x10\x1F') # lodsd; mov [0x1F10], eax (color)
    a.emit(b'\xAD\x89\xC7')              # lodsw; mov di, ax (text_offset)
    a.emit(b'\x56')                      # push si
    a.emit(b'\x89\xFE')                  # mov si, di
    a.emit(b'\x81\xC6\x00\x64')          # add si, 0x6400 (string pool base)
    a.j_near(b'\xE8', 'sub_draw_string')
    a.emit(b'\x5E\x59')                  # pop si; pop cx
    a.emit(b'\x49')                      # dec cx
    a.j_rel8(b'\x75', 'tbl_str_loop')

    a.label('no_strings')
    a.emit(b'\x61\xC3')                  # popa; ret

    # =========================================================================
    # Subroutine: Fill Rect from [0x1F06..0x1F13]
    # =========================================================================
    a.label('sub_fill_rect')
    a.emit(b'\x60')                      # pusha
    a.emit(b'\x66\x0F\xB7\x06\x08\x1F')  # movzx eax, word [0x1F08] (y)
    a.emit(b'\x66\x69\xC0\x00\x0A\x00\x00') # imul eax, 2560
    a.emit(b'\x66\x0F\xB7\x3E\x06\x1F')  # movzx edi, word [0x1F06] (x)
    a.emit(b'\x66\xC1\xE7\x02')          # shl edi, 2
    a.emit(b'\x66\x01\xC7')              # add edi, eax
    a.emit(b'\x66\x81\xC7\x00\x00\x00\xE0') # add edi, 0xE0000000
    a.emit(b'\x8B\x2E\x0C\x1F')          # mov bp, word [0x1F0C] (h)

    a.label('rect_row_loop')
    a.emit(b'\x66\x57')                  # push edi
    a.emit(b'\x66\x0F\xB7\x0E\x0A\x1F')  # movzx ecx, word [0x1F0A] (w)
    a.emit(b'\x66\xA1\x10\x1F')          # mov eax, [0x1F10] (color)
    a.emit(b'\x67\x66\xF3\xAB')          # addr32 rep stosd
    a.emit(b'\x66\x5F')                  # pop edi
    a.emit(b'\x66\x81\xC7\x00\x0A\x00\x00') # add edi, 2560
    a.emit(b'\x4D')                      # dec bp
    a.j_rel8(b'\x75', 'rect_row_loop')
    a.emit(b'\x61\xC3')                  # popa; ret

    # =========================================================================
    # Subroutine: Draw String & Draw Char
    # =========================================================================
    a.label('sub_draw_char')
    a.emit(b'\x60')                      # pusha
    a.emit(b'\x2C\x20\xB4\x00')          # sub al, 32; mov ah, 0
    a.emit(b'\xC1\xE0\x03')              # shl ax, 3
    a.emit(b'\x05\x00\x60')              # add ax, 0x6000 (font table offset)
    a.emit(b'\x89\xC6')                  # mov si, ax

    a.emit(b'\x66\x0F\xB7\x06\x08\x1F')  # movzx eax, [0x1F08] (y)
    a.emit(b'\x66\x69\xC0\x00\x0A\x00\x00')
    a.emit(b'\x66\x0F\xB7\x3E\x06\x1F')  # movzx edi, [0x1F06] (x)
    a.emit(b'\x66\xC1\xE7\x02')
    a.emit(b'\x66\x01\xC7')
    a.emit(b'\x66\x81\xC7\x00\x00\x00\xE0')

    a.emit(b'\xBD\x08\x00')              # mov bp, 8 rows

    a.label('char_row')
    a.emit(b'\x66\x57')                  # push edi
    a.emit(b'\xAC\x88\xC3')              # lodsb; mov bl, al
    a.emit(b'\xB9\x08\x00')              # mov cx, 8

    a.label('char_bit')
    a.emit(b'\xD0\xE3')                  # shl bl, 1
    a.j_rel8(b'\x73', 'bit_zero')
    a.emit(b'\x66\xA1\x10\x1F')          # mov eax, [0x1F10] (color)
    a.emit(b'\x67\x66\xAB')              # addr32 stosd
    a.j_rel8(b'\xEB', 'bit_next')

    a.label('bit_zero')
    a.emit(b'\x66\x83\xC7\x04')          # add edi, 4

    a.label('bit_next')
    a.emit(b'\x49')                      # dec cx
    a.j_rel8(b'\x75', 'char_bit')

    a.emit(b'\x66\x5F')                  # pop edi
    a.emit(b'\x66\x81\xC7\x00\x0A\x00\x00') # add edi, 2560
    a.emit(b'\x4D')                      # dec bp
    a.j_rel8(b'\x75', 'char_row')
    a.emit(b'\x61\xC3')                  # popa; ret

    a.label('sub_draw_string')
    a.emit(b'\x60')                      # pusha
    a.label('str_loop')
    a.emit(b'\xAC\x08\xC0')              # lodsb; or al, al
    a.j_rel8(b'\x74', 'str_done')
    a.emit(b'\x56')                      # push si
    a.j_near(b'\xE8', 'sub_draw_char')
    a.emit(b'\x5E')                      # pop si
    a.emit(b'\x83\x06\x06\x1F\x08')      # add word [0x1F06], 8 (x += 8)
    a.j_rel8(b'\xEB', 'str_loop')
    a.label('str_done')
    a.emit(b'\x61\xC3')                  # popa; ret

    return bytes(a.resolve())

def generate_full_payload():
    payload = bytearray(32768)

    # 1. Kernel code at offset 0x0000
    kernel_code = build_kernel_code()
    print(f"Kernel code size: {len(kernel_code)} bytes (max 0x1E00 = 7680 bytes)")
    assert len(kernel_code) <= 0x1E00
    payload[0x0000 : len(kernel_code)] = kernel_code

    # Cursor Sprite Tables at 0x7800 (16 rows: fill mask, outline mask)
    cursor_fill = [
        0x8000, 0xC000, 0xE000, 0xF000,
        0xF800, 0xFC00, 0xFE00, 0xFF00,
        0xFF80, 0xFC00, 0xD600, 0x8B00,
        0x0B00, 0x0580, 0x0580, 0x0100
    ]
    cursor_out = [
        0xC000, 0xE000, 0xF000, 0xF800,
        0xFC00, 0xFE00, 0xFF00, 0xFF80,
        0xFFC0, 0xFE00, 0xFF00, 0xDF80,
        0x9F80, 0x0FC0, 0x0FC0, 0x0380
    ]
    for y in range(16):
        struct.pack_into('<HH', payload, 0x7800 + y * 4, cursor_fill[y], cursor_out[y])

    # 2. Build Tables from test_kernel_tables
    import sys
    sys.path.append(r"C:\Users\barua\.gemini\antigravity\scratch\micro-os\scripts")
    from test_kernel_tables import build_all_tables
    views, string_bytes = build_all_tables()

    # Font Table at 0x6000
    font_bytes = generate_font_table()
    payload[0x6000 : 0x6000 + len(font_bytes)] = font_bytes

    # String Pool at 0x6400
    payload[0x6400 : 0x6400 + len(string_bytes)] = string_bytes
    print(f"String pool size: {len(string_bytes)} bytes at 0x6400 (max 0x1400 = 5120 bytes)")
    assert len(string_bytes) <= 0x1400

    # Write each view table:
    view_offsets = {0: 0x2000, 1: 0x4000, 2: 0x4800, 3: 0x5000, 4: 0x5800}
    for vid, offset in view_offsets.items():
        vdata = views[vid]
        ptr = offset
        # Rectangles
        struct.pack_into('<H', payload, ptr, len(vdata['rects']))
        ptr += 2
        for x, y, w, h, c in vdata['rects']:
            struct.pack_into('<HHHH I', payload, ptr, x, y, w, h, c)
            ptr += 12
        # Strings
        struct.pack_into('<H', payload, ptr, len(vdata['strings']))
        ptr += 2
        for x, y, c, text_off in vdata['strings']:
            struct.pack_into('<HHI H', payload, ptr, x, y, c, text_off)
            ptr += 10
        print(f"View {vid} table at 0x{offset:04X} ends at 0x{ptr:04X}")

    return payload

def build_full_iso_and_vhd():
    # 1. Bootloader
    sec1_code = build_bootloader()

    # 2. Kernel & UI Tables Payload (32 KB = 64 sectors)
    payload = generate_full_payload()

    # 3. Build El Torito ISO
    SECTOR_SIZE = 2048
    iso = bytearray(300 * SECTOR_SIZE)
    pvd = bytearray(SECTOR_SIZE)
    pvd[0] = 1; pvd[1:6] = b'CD001'; pvd[6] = 1
    pvd[40:72] = b'JOYDEV_MICRO_OS'.ljust(32)
    struct.pack_into('<I', pvd, 80, 300); struct.pack_into('>I', pvd, 84, 300)
    struct.pack_into('<H', pvd, 120, 1); struct.pack_into('>H', pvd, 122, 1)
    struct.pack_into('<H', pvd, 124, 1); struct.pack_into('>H', pvd, 126, 1)
    struct.pack_into('<H', pvd, 128, SECTOR_SIZE); struct.pack_into('>H', pvd, 130, SECTOR_SIZE)
    iso[16*SECTOR_SIZE:17*SECTOR_SIZE] = pvd

    br = bytearray(SECTOR_SIZE)
    br[0] = 0; br[1:6] = b'CD001'; br[6] = 1; br[7:39] = b'EL TORITO SPECIFICATION'.ljust(32)
    struct.pack_into('<I', br, 71, 19); iso[17*SECTOR_SIZE:18*SECTOR_SIZE] = br

    term = bytearray(SECTOR_SIZE); term[0] = 255; term[1:6] = b'CD001'; term[6] = 1
    iso[18*SECTOR_SIZE:19*SECTOR_SIZE] = term

    c = bytearray(SECTOR_SIZE); c[0]=1; c[28]=0xAA; c[29]=0x55; c[30]=0x55; c[31]=0xAA
    chk = sum(struct.unpack('<16H', c[0:32])) & 0xFFFF
    if chk != 0: struct.pack_into('<H', c, 28, (0x10000 - chk) & 0xFFFF)
    c[32]=0x88; struct.pack_into('<H', c, 38, 4); struct.pack_into('<I', c, 40, 20); iso[19*SECTOR_SIZE:20*SECTOR_SIZE] = c

    bimg = bytearray(SECTOR_SIZE)
    bimg[0:len(sec1_code)] = sec1_code
    iso[20*SECTOR_SIZE:21*SECTOR_SIZE] = bimg

    # Payload at sectors 21..36 (32 KB = 16 ISO sectors of 2048 bytes)
    iso[21*SECTOR_SIZE : 21*SECTOR_SIZE + len(payload)] = payload

    iso_path = r"C:\Users\barua\.gemini\antigravity\scratch\micro-os\virtualbox\micro-os.iso"
    with open(iso_path, 'wb') as f:
        f.write(iso)
    print(f"Production Micro-OS ISO written: {iso_path} ({len(iso)} bytes)")

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
    build_full_iso_and_vhd()
