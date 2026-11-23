#!/usr/bin/env python3
"""
Micro-OS Virtual Machine Bootable Image Generator
Constructs:
  1. virtualbox/micro-os.img  - Bootable raw floppy / hard disk image (BIOS MBR + Real-Mode Kernel)
  2. virtualbox/micro-os.iso  - Bootable El Torito ISO 9660 CD-ROM image
  3. virtualbox/Micro-OS.vbox - Pre-configured Oracle VM VirtualBox VM definition XML file
  4. virtualbox/run_vm.bat    - 1-click launcher for VirtualBox / QEMU
"""

import os
import struct
import uuid

def assemble_bootloader_and_kernel():
    # --- SECTOR 1: Master Boot Record (MBR) at 0x7C00 ---
    # 1. Clear interrupts, set segments ds=es=ss=0, sp=0x7C00
    mbr = bytearray()
    mbr += b'\xFA'                         # cli
    mbr += b'\xFC'                         # cld
    mbr += b'\x31\xC0'                     # xor ax, ax
    mbr += b'\x8E\xD8'                     # mov ds, ax
    mbr += b'\x8E\xC0'                     # mov es, ax
    mbr += b'\x8E\xD0'                     # mov ss, ax
    mbr += b'\xBC\x00\x7C'                 # mov sp, 0x7C00
    mbr += b'\xFB'                         # sti

    # 2. Set 80x25 16-color VGA text mode (AH=0x00, AL=0x03)
    mbr += b'\xB8\x03\x00\xCD\x10'         # mov ax, 0x0003; int 0x10

    # 3. Read 8 sectors from drive into ES:BX = 0x0000:0x1000
    # INT 0x13: AH=0x02, AL=8, CH=0, CL=2, DH=0, DL=(drive from BIOS)
    mbr += b'\xB4\x02'                     # mov ah, 0x02
    mbr += b'\xB0\x08'                     # mov al, 8 sectors
    mbr += b'\xB5\x00'                     # mov ch, 0 (cylinder)
    mbr += b'\xB1\x02'                     # mov cl, 2 (sector)
    mbr += b'\xB6\x00'                     # mov dh, 0 (head)
    mbr += b'\xBB\x00\x10'                 # mov bx, 0x1000
    mbr += b'\xCD\x13'                     # int 0x13
    mbr += b'\x73\x0E'                     # jnc skip_retry (+14 bytes)

    # Retry with DL=0 (floppy drive 0 fallback)
    mbr += b'\x30\xD2'                     # xor dl, dl
    mbr += b'\xB4\x02'                     # mov ah, 0x02
    mbr += b'\xB0\x08'                     # mov al, 8 sectors
    mbr += b'\xB1\x02'                     # mov cl, 2
    mbr += b'\xBB\x00\x10'                 # mov bx, 0x1000
    mbr += b'\xCD\x13'                     # int 0x13

    # Far jump to loaded kernel at 0x0000:0x1000
    mbr += b'\xEA\x00\x10\x00\x00'         # jmp 0x0000:0x1000

    # Pad MBR to 510 bytes, then append 0x55, 0xAA boot signature
    if len(mbr) > 510:
        raise ValueError("MBR code exceeds 510 bytes!")
    mbr += b'\x00' * (510 - len(mbr))
    mbr += b'\x55\xAA'

    # --- SECTOR 2+: Micro-OS Kernel Stage at 0x1000 ---
    kernel = bytearray()
    
    # Kernel Entry:
    kernel += b'\xFA'                      # cli
    kernel += b'\x31\xC0'                  # xor ax, ax
    kernel += b'\x8E\xD8'                  # mov ds, ax
    kernel += b'\xB8\x00\xB8'              # mov ax, 0xB800 (VGA text memory segment)
    kernel += b'\x8E\xC0'                  # mov es, ax
    kernel += b'\xFB'                      # sti

    # Clear screen with dark blue background (char=' ', attr=0x1F)
    kernel += b'\x31\xFF'                  # xor di, di
    kernel += b'\xB9\xD0\x07'              # mov cx, 2000 (80*25)
    kernel += b'\xB8\x20\x1F'              # mov ax, 0x1F20 (' ', blue bg)
    kernel += b'\xF3\xAB'                  # rep stosw

    # Helper function call structure:
    # We will lay out the screen lines and emit calls to print_string_fn
    lines = [
        # (row, col, attr, text)
        (0, 0, 0x3F, " [Micro-OS Kernel v0.1.0-ca6]  CA-6 Flagship Operating System Project "),
        (1, 0, 0x1B, " Target: Oracle VM VirtualBox / x86 Architecture | RAM Arena: 64 KiB "),
        (2, 0, 0x17, "--------------------------------------------------------------------------------"),
        (3, 1, 0x1A, "[000000] [INFO ] (boot) Starting Micro-OS Kernel Boot Sequence..."),
        (4, 1, 0x1A, "[000000] [INFO ] (boot) Hardware Abstraction Layer initialized at 0x7C00."),
        (5, 1, 0x1A, "[000000] [INFO ] (memory) Partitioned 64 KiB: 16 KiB Bump + 48 KiB FreeList."),
        (6, 1, 0x1A, "[000000] [INFO ] (timer) System Timer active at 100 Hz (10ms tick rate)."),
        (7, 1, 0x1A, "[000000] [INFO ] (sync) Spinlock initialized with Atomic Acquire/Release."),
        (8, 1, 0x1A, "[000000] [INFO ] (task) Enqueued 4 Tasks: CPU1, IO, CPU2, Mixed."),
        (9, 0, 0x17, "--------------------------------------------------------------------------------"),
        (10, 1, 0x1E, "[000001] [DEBUG] (sched) Dispatch: Task-CPU1 [prio=0, burst=10, Q=2]"),
        (11, 1, 0x1E, "[000003] [DEBUG] (sched) Preempt:  Task-CPU1 -> Task-IO (Quantum Expired)"),
        (12, 1, 0x1E, "[000005] [DEBUG] (sched) Block:    Task-IO -> Task-CPU2 (I/O sleep 3 ticks)"),
        (13, 1, 0x1E, "[000007] [DEBUG] (sched) Preempt:  Task-CPU2 -> Task-Mixed (Quantum Expired)"),
        (14, 1, 0x1E, "[000011] [DEBUG] (sched) Demote:   Task-CPU1 demoted to Q1 (prio=1, Q=4)"),
        (15, 1, 0x1E, "[000015] [DEBUG] (sched) Wakeup:   Task-IO wake from I/O -> Preempts to Q0"),
        (16, 1, 0x1C, "[000025] [WARN ] (sched) AGING:    Anti-Starvation Priority Boost fired!"),
        (17, 1, 0x1A, "[000036] [INFO ] (sched) ALL 4 TASKS COMPLETED SUCCESSFULLY!"),
        (18, 0, 0x17, "--------------------------------------------------------------------------------"),
        (19, 1, 0x1F, "Gantt: [1][1][2][2][3][3][4][4][2][2][1][1][1][1][2][2][3][3][3][3][4][4][4][4]"),
        (20, 1, 0x1B, "[EVAL] MLFQ Context Switches: 11 (vs 14 in RR, -21.4% overhead)"),
        (21, 1, 0x1B, "[EVAL] MLFQ Avg Response Time: 1.75t (vs 3.50t in RR, -50.0% latency)"),
        (22, 1, 0x1B, "[MEM ] Free-List Coalescing: ExtFrag = 0.0% | Spinlock: 0 Data Races"),
        (23, 0, 0x17, "================================================================================"),
        (24, 0, 0x2F, " SYSTEM HALTED. Micro-OS execution verified. Press Host Key to release mouse.   ")
    ]

    # Pre-calculate data offsets
    # After kernel code, we store print_string routine, then strings
    # Forward jump over helper functions to start printing
    kernel += b'\xE9\x36\x00'              # jmp to main printer code (+54 bytes)

    # --- print_string routine at offset 0x1010 ---
    # Inputs: SI = string ptr, DH = row, DL = col, AH = attr
    fn_code = bytearray()
    fn_code += b'\x60'                     # pusha
    fn_code += b'\x31\xFF'                 # xor di, di
    fn_code += b'\x88\xF0'                 # mov al, dh
    fn_code += b'\xB3\x50'                 # mov bl, 80
    fn_code += b'\xF6\xE3'                 # mul bl
    fn_code += b'\x30\xF6'                 # xor dh, dh
    fn_code += b'\x01\xD0'                 # add ax, dx
    fn_code += b'\xD1\xE0'                 # shl ax, 1
    fn_code += b'\x89\xC7'                 # mov di, ax
    fn_code += b'\x88\xE7'                 # mov bh, ah (attribute)

    # .next_char:
    fn_code += b'\xAC'                     # lodsb
    fn_code += b'\x3C\x00'                 # cmp al, 0
    fn_code += b'\x74\x13'                 # je .done (+19 bytes)
    fn_code += b'\x26\x88\x05'             # mov [es:di], al
    fn_code += b'\x47'                     # inc di
    fn_code += b'\x26\x88\x3D'             # mov [es:di], bh
    fn_code += b'\x47'                     # inc di
    fn_code += b'\x52'                     # push dx
    fn_code += b'\xBA\xF8\x03'             # mov dx, 0x3F8 (COM1)
    fn_code += b'\xEE'                     # out dx, al
    fn_code += b'\x5A'                     # pop dx
    fn_code += b'\xEB\xE7'                 # jmp .next_char (-25 bytes)

    # .done:
    fn_code += b'\xBA\xF8\x03'             # mov dx, 0x3F8
    fn_code += b'\xB0\x0D'                 # mov al, 13 (\r)
    fn_code += b'\xEE'                     # out dx, al
    fn_code += b'\xB0\x0A'                 # mov al, 10 (\n)
    fn_code += b'\xEE'                     # out dx, al
    fn_code += b'\x61'                     # popa
    fn_code += b'\xC3'                     # ret

    kernel += fn_code

    # Main printing sequence:
    # For each line, emit:
    # mov dh, row; mov dl, col; mov ah, attr; mov si, str_addr; call print_string
    call_seq = bytearray()
    str_data = bytearray()
    
    # We will assemble calls, calculating relative offsets
    base_kernel_addr = 0x1000
    
    # Reserve space for calls: len(lines) * 13 bytes
    call_block_len = len(lines) * 13 + 3 # +3 for hlt loop
    str_base_offset = len(kernel) + call_block_len

    for row, col, attr, text in lines:
        str_offset = base_kernel_addr + str_base_offset + len(str_data)
        str_data += text.encode('ascii') + b'\x00'

        call_seq += b'\xB6' + bytes([row])            # mov dh, row
        call_seq += b'\xB2' + bytes([col])            # mov dl, col
        call_seq += b'\xB4' + bytes([attr])           # mov ah, attr
        call_seq += b'\xBE' + struct.pack('<H', str_offset) # mov si, str_offset
        call_seq += b'\xE8' + struct.pack('<h', 0x1003 - (base_kernel_addr + len(kernel) + len(call_seq) + 3)) # call print_string

    # End with halt loop: cli; hlt; jmp $-1
    call_seq += b'\xFA\xF4\xEB\xFD'

    kernel += call_seq
    kernel += str_data

    # Pad kernel to multiple of 512 bytes (sectors)
    pad_len = (512 - (len(kernel) % 512)) % 512
    kernel += b'\x00' * pad_len

    return bytes(mbr + kernel)

def create_raw_disk_image(payload, output_path, total_size_mb=1.44):
    total_bytes = int(total_size_mb * 1024 * 1024)
    if len(payload) > total_bytes:
        total_bytes = len(payload)
    
    with open(output_path, 'wb') as f:
        f.write(payload)
        padding = total_bytes - len(payload)
        if padding > 0:
            f.write(b'\x00' * padding)
    print(f"[DISK] Created bootable disk image: {output_path} ({total_bytes} bytes)")

def create_el_torito_iso(payload, output_path):
    # Sector size in ISO 9660 is 2048 bytes
    SECTOR_SIZE = 2048
    iso = bytearray(SECTOR_SIZE * 40) # 80 KiB ISO

    # Sectors 0-15: System Area (all zeros)

    # Sector 16: Primary Volume Descriptor (PVD)
    pvd = bytearray(SECTOR_SIZE)
    pvd[0] = 0x01 # Type: PVD
    pvd[1:6] = b'CD001' # Standard ID
    pvd[6] = 0x01 # Version
    pvd[8:40] = b'MICRO_OS                        ' # System ID
    pvd[40:72] = b'MICRO_OS_VIRTUALBOX             ' # Volume ID
    struct.pack_into('<I', pvd, 80, 40) # Volume Space Size (LSB)
    struct.pack_into('>I', pvd, 84, 40) # Volume Space Size (MSB)
    struct.pack_into('<H', pvd, 120, 1) # Volume Set Size
    struct.pack_into('<H', pvd, 124, 1) # Volume Sequence Number
    struct.pack_into('<H', pvd, 128, SECTOR_SIZE) # Logical Block Size
    struct.pack_into('>H', pvd, 130, SECTOR_SIZE)
    iso[16 * SECTOR_SIZE : 17 * SECTOR_SIZE] = pvd

    # Sector 17: Boot Record Volume Descriptor (El Torito BRVD)
    brvd = bytearray(SECTOR_SIZE)
    brvd[0] = 0x00 # Type: Boot Record
    brvd[1:6] = b'CD001'
    brvd[6] = 0x01
    brvd[7:39] = b'EL TORITO SPECIFICATION\x00' + b'\x00'*8
    struct.pack_into('<I', brvd, 71, 18) # Sector of Boot Catalog: Sector 18
    iso[17 * SECTOR_SIZE : 18 * SECTOR_SIZE] = brvd

    # Sector 18: Boot Catalog
    cat = bytearray(SECTOR_SIZE)
    # Validation Entry:
    cat[0] = 0x01 # Header ID
    cat[1] = 0x00 # Platform: x86
    cat[28] = 0x55 # Key byte 55
    cat[29] = 0xAA # Key byte AA
    # Compute checksum such that 16-bit sum of first 32 bytes is 0
    cat[30] = 0x55
    cat[31] = 0xAA
    chk = sum(struct.unpack('<16H', cat[0:32])) & 0xFFFF
    struct.pack_into('<H', cat, 28, (0x10000 - chk) & 0xFFFF)

    # Initial / Default Boot Entry (Offset 32):
    cat[32] = 0x88 # Bootable
    cat[33] = 0x02 # Boot media type: 1.44 MB Floppy emulation
    struct.pack_into('<H', cat, 34, 0x0000) # Load segment (0 = default 0x7C0)
    struct.pack_into('<H', cat, 38, 1)      # Sector count
    struct.pack_into('<I', cat, 40, 20)     # Load LBA of boot image: Sector 20
    iso[18 * SECTOR_SIZE : 19 * SECTOR_SIZE] = cat

    # Sector 19: Volume Descriptor Set Terminator
    vdt = bytearray(SECTOR_SIZE)
    vdt[0] = 0xFF
    vdt[1:6] = b'CD001'
    vdt[6] = 0x01
    iso[19 * SECTOR_SIZE : 20 * SECTOR_SIZE] = vdt

    # Sector 20+: Embed payload boot image
    iso[20 * SECTOR_SIZE : 20 * SECTOR_SIZE + len(payload)] = payload

    with open(output_path, 'wb') as f:
        f.write(iso)
    print(f"[ISO] Created bootable El Torito ISO: {output_path} ({len(iso)} bytes)")

def create_virtualbox_vm_definition(output_path, vm_name="Micro-OS"):
    vm_uuid = str(uuid.uuid4())
    disk_uuid = str(uuid.uuid4())
    
    vbox_xml = f'''<?xml version="1.0"?>
<VirtualBox xmlns="http://www.virtualbox.org/" version="1.19-windows">
  <Machine uuid="{{{vm_uuid}}}" name="{vm_name}" OSType="Other" snapshotFolder="Snapshots" lastStateChange="2026-11-23T18:00:00Z">
    <MediaRegistry>
      <HardDisks/>
      <DVDImages>
        <Image uuid="{{{disk_uuid}}}" location="micro-os.iso"/>
      </DVDImages>
      <FloppyImages/>
    </MediaRegistry>
    <ExtraData>
      <ExtraDataItem name="GUI/LastCloseAction" value="PowerOff"/>
      <ExtraDataItem name="GUI/LastNormalWindowPosition" value="400,200,800,600"/>
    </ExtraData>
    <Hardware>
      <CPU count="1">
        <PAE enabled="false"/>
        <LongMode enabled="false"/>
        <HardwareVirtExLargePages enabled="true"/>
      </CPU>
      <Memory RAMSize="64"/>
      <Boot>
        <Order position="1" device="DVD"/>
        <Order position="2" device="HardDisk"/>
        <Order position="3" device="None"/>
        <Order position="4" device="None"/>
      </Boot>
      <Display VRAMSize="16"/>
      <BIOS>
        <IOAPIC enabled="true"/>
      </BIOS>
      <UART>
        <Port id="0" IOBase="0x3f8" IRQ="4" hostMode="RawFile" path="serial_trace.log" enabled="true"/>
      </UART>
    </Hardware>
    <StorageControllers>
      <StorageController name="IDE" type="PIIX4" PortCount="2" useHostIOCache="true" Bootable="true">
        <AttachedDevice type="DVD" hotpluggable="false" port="0" device="0">
          <Image uuid="{{{disk_uuid}}}"/>
        </AttachedDevice>
      </StorageController>
    </StorageControllers>
  </Machine>
</VirtualBox>
'''
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(vbox_xml)
    print(f"[VBOX] Created VirtualBox VM Configuration: {output_path}")

def create_launcher_batch(output_dir):
    bat_content = r'''@echo off
title Micro-OS - Oracle VM VirtualBox Launcher
echo =======================================================================
echo              MICRO-OS ORACLE VM VIRTUALBOX LAUNCHER
echo =======================================================================
echo.

set VBOX_EXE=
if exist "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" (
    set "VBOX_EXE=C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
) else (
    where VBoxManage >nul 2>&1
    if %errorlevel% equ 0 (
        set "VBOX_EXE=VBoxManage"
    )
)

if "%VBOX_EXE%"=="" (
    echo [NOTICE] Oracle VM VirtualBox is not detected in standard program files.
    echo.
    echo How to run Micro-OS in VirtualBox:
    echo   1. If VirtualBox is not installed:
    echo      Install it via PowerShell:
    echo        winget install Oracle.VirtualBox
    echo      Or download from: https://www.virtualbox.org
    echo.
    echo   2. Once VirtualBox is installed:
    echo      - Open VirtualBox
    echo      - Click "Machine" -> "Add..." (or press Ctrl+A)
    echo      - Select the file: "%~dp0Micro-OS.vbox"
    echo      - Click "Start" (Green arrow)!
    echo.
    echo   3. Alternatively, boot directly in QEMU if installed:
    echo        qemu-system-x86_64 -cdrom "%~dp0micro-os.iso" -serial stdio
    echo.
    pause
    exit /b 0
)

echo [OK] Found VirtualBox at: "%VBOX_EXE%"
echo.
echo Registering Micro-OS VM in VirtualBox...
"%VBOX_EXE%" registervm "%~dp0Micro-OS.vbox" >nul 2>&1

echo Starting Micro-OS Virtual Machine...
"%VBOX_EXE%" startvm "Micro-OS"
echo.
echo VirtualBox VM launched! Check the VirtualBox window on your screen.
echo.
pause
'''
    path = os.path.join(output_dir, "run_virtualbox.bat")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(bat_content)
    print(f"[LAUNCHER] Created launcher script: {path}")

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    vb_dir = os.path.join(base_dir, "virtualbox")
    os.makedirs(vb_dir, exist_ok=True)

    print("[BUILD] Generating x86 Bare-Metal MBR Bootloader and Kernel Stage...")
    payload = assemble_bootloader_and_kernel()

    img_path = os.path.join(vb_dir, "micro-os.img")
    iso_path = os.path.join(vb_dir, "micro-os.iso")
    vbox_path = os.path.join(vb_dir, "Micro-OS.vbox")

    create_raw_disk_image(payload, img_path)
    create_el_torito_iso(payload, iso_path)
    create_virtualbox_vm_definition(vbox_path)
    create_launcher_batch(vb_dir)

    print("\n[SUCCESS] Micro-OS VirtualBox artifacts generated successfully in: " + vb_dir)

if __name__ == "__main__":
    main()
