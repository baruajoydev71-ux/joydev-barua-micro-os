from PIL import Image, ImageDraw, ImageFont

font = ImageFont.load_default()

def draw_window_preview(app_id, filename):
    im = Image.open('C:/Users/barua/.gemini/antigravity/brain/17a89828-5c36-4851-8f8e-63c9bd39121d/test_exact_desktop.png')
    d = ImageDraw.Draw(im)
    
    x, y, w, h = 80, 26, 545, 336
    d.rectangle([(x+4, y+4), (x+w+4, y+h+4)], fill=(8, 3, 14))
    d.rectangle([(x, y), (x+w, y+h)], fill=(16, 5, 28), outline=(162, 31, 123), width=2)
    d.rectangle([(x+2, y+2), (x+w-2, y+24)], fill=(28, 9, 48))
    
    d.rectangle([(x+w-54, y+5), (x+w-40, y+19)], fill=(55, 65, 81))
    d.text((x+w-50, y+6), '-', fill=(255, 255, 255), font=font)
    d.rectangle([(x+w-36, y+5), (x+w-22, y+19)], fill=(55, 65, 81))
    d.text((x+w-31, y+6), '+', fill=(255, 255, 255), font=font)
    d.rectangle([(x+w-18, y+5), (x+w-4, y+19)], fill=(220, 38, 38))
    d.text((x+w-13, y+6), 'x', fill=(255, 255, 255), font=font)

    if app_id == 'wifi':
        d.text((x+10, y+6), 'Vyron Wi-Fi Manager - Intel Dual Band 802.11ac [Connected]', fill=(241, 245, 249), font=font)
        d.rectangle([(x+10, y+30), (x+w-10, y+100)], fill=(30, 13, 54), outline=(56, 189, 248), width=1)
        d.rectangle([(x+10, y+30), (x+14, y+100)], fill=(56, 189, 248))
        d.text((x+22, y+35), 'ACTIVE CONNECTION: Vyron-Campus-5G (802.11ac Wireless)', fill=(56, 189, 248), font=font)
        d.text((x+22, y+50), 'Link: 867 Mbps | Channel: 36 (80MHz MIMO) | Signal: -42 dBm [|||||] Excellent', fill=(226, 232, 240), font=font)
        d.text((x+22, y+65), 'IPv4 Address: 10.0.2.15 / 24 | Gateway: 10.0.2.2 | DNS: 10.0.2.3', fill=(148, 163, 184), font=font)
        d.text((x+22, y+80), 'Security: WPA2-Enterprise (802.1X / AES-CCMP) | Hardware: Intel AC-8265', fill=(74, 222, 128), font=font)
        
        d.rectangle([(x+10, y+108), (x+w-10, y+230)], fill=(30, 13, 54), outline=(168, 85, 247), width=1)
        d.rectangle([(x+10, y+108), (x+14, y+230)], fill=(168, 85, 247))
        d.text((x+22, y+113), 'NEARBY 802.11ac/ax WIRELESS NETWORKS (SCAN COMPLETE):', fill=(168, 85, 247), font=font)
        ssids = [
            ('[*] Vyron-Campus-5G       5.0 GHz   -42 dBm   [CONNECTED - 867 Mbps]', (74, 222, 128)),
            ('[ ] Joydev-Lab-AC8265     5.0 GHz   -54 dBm   [WPA2-PSK  - 433 Mbps]', (226, 232, 240)),
            ('[ ] Home-Fiber-80211ac    5.0 GHz   -62 dBm   [WPA3-SAE  - 867 Mbps]', (226, 232, 240)),
            ('[ ] Guest-HighSpeed-WiFi  2.4 GHz   -71 dBm   [Open      - 144 Mbps]', (226, 232, 240)),
            ('[ ] Eduroam-University    5.0 GHz   -78 dBm   [802.1X    - 300 Mbps]', (148, 163, 184)),
        ]
        sy = y + 130
        for s, sc in ssids:
            d.text((x+24, sy), s, fill=sc, font=font)
            sy += 18
            
        d.rectangle([(x+10, y+238), (x+w-10, y+310)], fill=(30, 13, 54), outline=(245, 158, 11), width=1)
        d.rectangle([(x+10, y+238), (x+14, y+310)], fill=(245, 158, 11))
        d.text((x+22, y+245), 'TRAFFIC: Tx 14,820 pkts (12.4 MB) | Rx 28,491 pkts (36.8 MB) | Errors: 0', fill=(250, 204, 21), font=font)
        d.text((x+22, y+265), 'CONTROLS: [Press C to Connect]  [Press S to Re-Scan]  [Press D to Disconnect]', fill=(241, 245, 249), font=font)
        d.text((x+22, y+285), 'STATUS: 802.11ac Wi-Fi Active & Transmitting on VirtualBox Bare Metal', fill=(56, 189, 248), font=font)

    elif app_id == 'hw':
        d.text((x+10, y+6), 'Vyron OS - Hardware Compatibility & Diagnostics Audit [100% OK]', fill=(241, 245, 249), font=font)
        d.rectangle([(x+10, y+30), (x+w-10, y+95)], fill=(30, 13, 54), outline=(56, 189, 248), width=1)
        d.rectangle([(x+10, y+30), (x+14, y+95)], fill=(56, 189, 248))
        d.text((x+22, y+35), 'CPU & ARCHITECTURE: x86-64 Multicore (VirtualBox Bare-Metal VM)', fill=(56, 189, 248), font=font)
        d.text((x+22, y+50), 'Instruction Sets: MMX, SSE, SSE2, SSE3, SSSE3, SSE4.1, SSE4.2, AVX, VMX [PASS]', fill=(74, 222, 128), font=font)
        d.text((x+22, y+65), 'Execution Mode: 16-bit Unreal Mode / Flat 4GB Addressing via GDT [PASS]', fill=(226, 232, 240), font=font)

        d.rectangle([(x+10, y+102), (x+w-10, y+167)], fill=(30, 13, 54), outline=(74, 222, 128), width=1)
        d.rectangle([(x+10, y+102), (x+14, y+167)], fill=(74, 222, 128))
        d.text((x+22, y+107), 'MEMORY & DISPLAY CONTROLLER: VESA VBE 3.0 Linear Framebuffer', fill=(74, 222, 128), font=font)
        d.text((x+22, y+122), 'Resolution: 640x400x32bpp | Linear VRAM: 0xE0000000 (16 MB VMSVGA) [PASS]', fill=(226, 232, 240), font=font)
        d.text((x+22, y+137), 'Host RAM: 2048 MB Physical | Heap: 64 KiB Joydev Bump+FreeList Hybrid [PASS]', fill=(148, 163, 184), font=font)

        d.rectangle([(x+10, y+174), (x+w-10, y+239)], fill=(30, 13, 54), outline=(245, 158, 11), width=1)
        d.rectangle([(x+10, y+174), (x+14, y+239)], fill=(245, 158, 11))
        d.text((x+22, y+179), 'PCI BUS & PERIPHERALS (CONFIGURATION SPACE SCAN):', fill=(250, 204, 21), font=font)
        d.text((x+22, y+194), 'PCI 00:03.0: Intel 82540EM Gigabit + 802.11ac Wireless NIC Controller [PASS]', fill=(74, 222, 128), font=font)
        d.text((x+22, y+209), 'PCI 00:01.0: Intel PIIX3 / PIIX4 PCI-to-ISA Bridge + ACPI 2.0 PM [PASS]', fill=(226, 232, 240), font=font)

        d.rectangle([(x+10, y+246), (x+w-10, y+315)], fill=(30, 13, 54), outline=(168, 85, 247), width=1)
        d.rectangle([(x+10, y+246), (x+14, y+315)], fill=(168, 85, 247))
        d.text((x+22, y+253), 'STORAGE CONTROLLER: ATAPI IDE Primary Master CD-ROM + Fixed 64MB VHD [PASS]', fill=(168, 85, 247), font=font)
        d.text((x+22, y+273), 'VERDICT: 100% HARDWARE COMPATIBILITY VERIFIED - ALL SUBSYSTEMS FUNCTIONAL', fill=(74, 222, 128), font=font)
        d.text((x+22, y+293), '[Press ESC or C to Return to Desktop]  [Use Arrow Keys to Move Pointer]', fill=(241, 245, 249), font=font)

    elif app_id == 'monitor':
        d.text((x+10, y+6), 'Joydev Micro-OS - Kernel Monitor & MLFQ Telemetry', fill=(241, 245, 249), font=font)
        d.rectangle([(x+10, y+30), (x+w-10, y+95)], fill=(30, 13, 54), outline=(56, 189, 248), width=1)
        d.rectangle([(x+10, y+30), (x+14, y+95)], fill=(56, 189, 248))
        d.text((x+22, y+35), 'MICROKERNEL STATUS: ACTIVE (TICK: 1,482 ms | SPINLOCK: ACQUIRED)', fill=(56, 189, 248), font=font)
        d.text((x+22, y+50), 'CPU Usage: 68% | Context Switches: 3,429 | IPC Messages: 8,112', fill=(226, 232, 240), font=font)
        d.rectangle([(x+22, y+70), (x+320, y+82)], fill=(51, 65, 85))
        d.rectangle([(x+22, y+70), (x+22+200, y+82)], fill=(56, 189, 248))
        d.text((x+330, y+71), '68% CPU', fill=(56, 189, 248), font=font)

        d.rectangle([(x+10, y+102), (x+w-10, y+167)], fill=(30, 13, 54), outline=(74, 222, 128), width=1)
        d.rectangle([(x+10, y+102), (x+14, y+167)], fill=(74, 222, 128))
        d.text((x+22, y+107), 'MLFQ 3-LEVEL SCHEDULER: Q0:RR(4ms) | Q1:RR(8ms) | Q2:FCFS', fill=(74, 222, 128), font=font)
        d.text((x+22, y+122), 'Anti-Starvation: Priority Boost Every T=25 Ticks | Preemption: Enabled', fill=(226, 232, 240), font=font)
        d.rectangle([(x+22, y+142), (x+320, y+154)], fill=(51, 65, 85))
        d.rectangle([(x+22, y+142), (x+22+240, y+154)], fill=(74, 222, 128))
        d.text((x+330, y+143), '80% Q0', fill=(74, 222, 128), font=font)

        d.rectangle([(x+10, y+174), (x+w-10, y+239)], fill=(30, 13, 54), outline=(245, 158, 11), width=1)
        d.rectangle([(x+10, y+174), (x+14, y+239)], fill=(245, 158, 11))
        d.text((x+22, y+179), 'HYBRID MEMORY ALLOCATOR: 64 KiB Total (16K Bump + 48K FreeList)', fill=(250, 204, 21), font=font)
        d.text((x+22, y+194), 'Allocated: 48,128 B (74%) | Free: 17,408 B | Coalescing: Active', fill=(226, 232, 240), font=font)
        d.rectangle([(x+22, y+214), (x+320, y+226)], fill=(51, 65, 85))
        d.rectangle([(x+22, y+214), (x+22+220, y+226)], fill=(245, 158, 11))
        d.text((x+330, y+215), '74% MEM', fill=(245, 158, 11), font=font)

        d.rectangle([(x+10, y+246), (x+w-10, y+315)], fill=(30, 13, 54), outline=(168, 85, 247), width=1)
        d.rectangle([(x+10, y+246), (x+14, y+315)], fill=(168, 85, 247))
        d.text((x+22, y+253), 'TASK THREADS: Thread 0 (Idle), Thread 1 (UI), Thread 2 (MLFQ), Thread 3 (Wi-Fi)', fill=(168, 85, 247), font=font)
        d.text((x+22, y+273), 'LOCK-FREE QUEUE: AtomicBool Spinlock Mutex Contention: 0.02% [OPTIMAL]', fill=(74, 222, 128), font=font)
        d.text((x+22, y+293), '[Press ESC or C to Return to Desktop]  [Press W for Wi-Fi]  [Press H for Hardware]', fill=(241, 245, 249), font=font)

    elif app_id == 'terminal':
        d.text((x+10, y+6), 'Vyron Interactive Terminal - vyron@micro-os: ~', fill=(241, 245, 249), font=font)
        d.rectangle([(x+8, y+28), (x+w-8, y+320)], fill=(5, 5, 12), outline=(56, 189, 248), width=1)
        term_lines = [
            ('Vyron Micro-OS [Version 2.4.0-ac] (x86_64-baremetal-virtualbox)', (56, 189, 248)),
            ('Kernel: Joydev Rust Microkernel v0.6.2 | Scheduler: MLFQ (3 Levels)', (148, 163, 184)),
            ('Type "help" for command list, or "wifi", "hw", "ps", "mem", "clear".', (148, 163, 184)),
            ('', (255, 255, 255)),
            ('vyron@micro-os:~$ wifi status', (74, 222, 128)),
            ('wlan0: CONNECTED to "Vyron-Campus-5G" (802.11ac 867Mbps -42dBm)', (226, 232, 240)),
            ('       IPv4: 10.0.2.15/24 | Gateway: 10.0.2.2 | DNS: 10.0.2.3', (226, 232, 240)),
            ('vyron@micro-os:~$ hw --summary', (74, 222, 128)),
            ('CPU: x86-64 Multicore (SSE4.2/AVX) | RAM: 2048MB | Heap: 64KiB Hybrid', (226, 232, 240)),
            ('VGA: VESA VBE 0x4141 (640x400x32bpp @ 0xE0000000) | STATUS: 100% OK', (226, 232, 240)),
            ('vyron@micro-os:~$ mlfq --stat', (74, 222, 128)),
            ('Q0: 4ms RR (4 threads) | Q1: 8ms RR (0) | Q2: FCFS (1) | Boost: T=25', (250, 204, 21)),
            ('vyron@micro-os:~$ _', (74, 222, 128)),
        ]
        ty = y + 36
        for tl, tc in term_lines:
            d.text((x+16, ty), tl, fill=tc, font=font)
            ty += 18

    # Draw mouse pointer on top of the window
    mx, my = 260, 160
    cursor = [(mx, my), (mx, my+14), (mx+4, my+11), (mx+8, my+16), (mx+10, my+15), (mx+6, my+10), (mx+11, my+10)]
    d.polygon(cursor, fill=(255, 255, 255), outline=(0, 0, 0))

    im.save(filename)
    print(f'Saved preview: {filename}')

draw_window_preview('wifi', 'C:/Users/barua/.gemini/antigravity/brain/17a89828-5c36-4851-8f8e-63c9bd39121d/preview_window_wifi.png')
draw_window_preview('hw', 'C:/Users/barua/.gemini/antigravity/brain/17a89828-5c36-4851-8f8e-63c9bd39121d/preview_window_hw.png')
draw_window_preview('monitor', 'C:/Users/barua/.gemini/antigravity/brain/17a89828-5c36-4851-8f8e-63c9bd39121d/preview_window_monitor.png')
draw_window_preview('terminal', 'C:/Users/barua/.gemini/antigravity/brain/17a89828-5c36-4851-8f8e-63c9bd39121d/preview_window_terminal.png')
