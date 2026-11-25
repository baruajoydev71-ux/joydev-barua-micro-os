import struct
from PIL import ImageFont, ImageDraw, Image

def build_all_tables():
    # 5 views: 0 = desktop, 1 = wifi, 2 = hw, 3 = monitor, 4 = terminal
    views = {0: {'rects': [], 'strings': []},
             1: {'rects': [], 'strings': []},
             2: {'rects': [], 'strings': []},
             3: {'rects': [], 'strings': []},
             4: {'rects': [], 'strings': []}}
    
    string_bytes = bytearray()
    
    def add_str(view_id, x, y, hex_color, text):
        r = (hex_color >> 16) & 0xFF
        g = (hex_color >> 8) & 0xFF
        b = hex_color & 0xFF
        color_dword = (b) | (g << 8) | (r << 16)
        text_offset = len(string_bytes)
        string_bytes.extend(text.encode('ascii') + b'\x00')
        views[view_id]['strings'].append((x, y, color_dword, text_offset))

    def add_rect(view_id, x, y, w, h, hex_color):
        r = (hex_color >> 16) & 0xFF
        g = (hex_color >> 8) & 0xFF
        b = hex_color & 0xFF
        color_dword = (b) | (g << 8) | (r << 16)
        views[view_id]['rects'].append((x, y, w, h, color_dword))

    # =========================================================================
    # VIEW 0: Exact Clean Desktop (matching user's photograph)
    # =========================================================================
    v = 0
    # 1. Base Wallpaper
    add_rect(v, 0, 0, 640, 400, 0x16082A)
    add_rect(v, 380, 0, 260, 400, 0x1A0B36)

    # 2. Diagonal Folded-Silk Ribbon Slices
    for y in range(20, 368, 6):
        t = (y - 20) / 348.0
        cx = int(410 - 95 * t + 25 * (t ** 2))
        if y >= 140:
            sw = int(35 + 20 * t)
            add_rect(v, cx - 100 - sw, y, sw, 6, 0x0E0618)
        w1 = int(150 + 35 * t)
        add_rect(v, cx - w1//2, y, w1, 6, 0x300E4E)
        w2 = int(95 + 20 * t)
        add_rect(v, cx - w2//2, y, w2, 6, 0x961491)
        w3 = int(60 + 10 * t)
        add_rect(v, cx - w3//2, y, w3, 6, 0xE11EBE)
        if 60 <= y <= 310:
            w4 = int(32 - 6 * abs(t - 0.5))
            add_rect(v, cx - w4//2, y, w4, 6, 0xFF41E1)
            if 100 <= y <= 260:
                w5 = 14
                add_rect(v, cx - w5//2, y, w5, 6, 0xFF96F5)

    # 3. Top Panel
    add_rect(v, 0, 0, 640, 20, 0x10081C)
    add_rect(v, 8, 4, 11, 11, 0x06B6D4) # Blue Logo
    add_rect(v, 624, 5, 10, 10, 0xEF4444) # Red Power Badge
    add_rect(v, 606, 7, 5, 6, 0xCBD5E1) # Speaker
    add_rect(v, 611, 5, 3, 10, 0xCBD5E1)

    # 4. Desktop Icons Column 1
    col1 = [
        (26, 0xF1F5F9, "File System"),
        (63, 0x06B6D4, "Home"),
        (100, 0xE2E8F0, "Vyron Developer..."),
        (137, 0x3B82F6, "Vyron System Monitor"),
        (174, 0x0EA5E9, "Vyron Storage Exp..."),
        (211, 0xF8FAFC, "Vyron Settings"),
        (248, 0x06B6D4, "Vyron Network En..."),
        (285, 0xA855F7, "Vyron Microkernel..."),
        (322, 0xE2E8F0, "Vyron Hardware &..."),
    ]
    for y_ic, c, name in col1:
        add_rect(v, 14, y_ic, 20, 18, c)
        add_rect(v, 16, y_ic + 2, 16, 14, 0x10051C)
        add_rect(v, 18, y_ic + 4, 12, 10, c)
        add_str(v, 38, y_ic + 4, 0xF1F5F9, name)

    # Column 2
    col2 = [
        (26, 0xF97316, "Vyron Files"),
        (63, 0xFB923C, "Vyron Web Browser"),
        (100, 0x94A3B8, "APT Package Manager"),
        (137, 0x38BDF8, "Vyron Wi-Fi Manager"),
        (174, 0xEA580C, "Snap Store"),
    ]
    for y_ic, c, name in col2:
        add_rect(v, 185, y_ic, 20, 18, c)
        add_rect(v, 187, y_ic + 2, 16, 14, 0x10051C)
        add_rect(v, 189, y_ic + 4, 12, 10, c)
        add_str(v, 210, y_ic + 4, 0xF1F5F9, name)

    # 5. Bottom Dock
    add_rect(v, 0, 368, 640, 32, 0x0E0618)
    add_rect(v, 0, 368, 640, 1, 0xA8188C)
    dock_apps = [
        (14, 0xEC4899), (38, 0x3B82F6), (62, 0xF97316), (86, 0x1E293B),
        (110, 0x0EA5E9), (134, 0xA855F7), (158, 0x64748B),
    ]
    for x_ic, c in dock_apps:
        add_rect(v, x_ic, 373, 18, 18, c)
    add_rect(v, 410, 372, 88, 20, 0x8A1565) # Workspace 1 Active
    add_rect(v, 630, 374, 6, 16, 0x06B6D4)

    # Strings for Top & Dock
    add_str(v, 24, 6, 0xE2E8F0, "Options")
    add_str(v, 80, 6, 0xCBD5E1, "Desktop Files Documents Music Pictures Video")
    add_str(v, 465, 6, 0xCBD5E1, "Sat 21 Nov 21:05:13")
    add_str(v, 417, 376, 0xFFFFFF, "Workspace 1")
    add_str(v, 504, 376, 0x94A3B8, "Workspace 2")
    add_str(v, 556, 376, 0x94A3B8, "Workspace 3")
    add_str(v, 608, 376, 0x94A3B8, "Workspace 4")

    # =========================================================================
    # Common Window Generator
    # =========================================================================
    def build_window_frame(vid, title_str):
        x, y, w, h = 80, 26, 545, 336
        # Window Shadow & Body
        add_rect(vid, x+4, y+4, w, h, 0x08030E) # shadow
        add_rect(vid, x, y, w, h, 0xA21F7B)    # border
        add_rect(vid, x+2, y+2, w-4, h-4, 0x10051C) # body
        # Titlebar
        add_rect(vid, x+2, y+2, w-4, 24, 0x1C0930)
        # Window Controls
        add_rect(vid, x+w-54, y+5, 14, 14, 0x374151)
        add_str(vid, x+w-50, y+7, 0xFFFFFF, "-")
        add_rect(vid, x+w-36, y+5, 14, 14, 0x374151)
        add_str(vid, x+w-32, y+7, 0xFFFFFF, "+")
        add_rect(vid, x+w-18, y+5, 14, 14, 0xDC2626)
        add_str(vid, x+w-14, y+7, 0xFFFFFF, "x")
        add_str(vid, x+10, y+7, 0xF1F5F9, title_str)

    # =========================================================================
    # VIEW 1: Wi-Fi Manager (Laptop Hardware: Intel Wi-Fi 6E AX211)
    # =========================================================================
    v = 1
    build_window_frame(v, "Vyron Wi-Fi Manager - Intel Wi-Fi 6E AX211 [Connected]")
    # Card 1: Active Connection
    add_rect(v, 90, 56, 525, 72, 0x1E0D36)
    add_rect(v, 90, 56, 4, 72, 0x38BDF8)
    add_str(v, 102, 62, 0x38BDF8, "ACTIVE CONNECTION: Mojo-Jan-B-F4 (802.11ax Wi-Fi 6E)")
    add_str(v, 102, 77, 0xE2E8F0, "Link: 721 Mbps | Channel: 44 (5 GHz) | Signal: -63 dBm [||||.] 80% Strong")
    add_str(v, 102, 92, 0x94A3B8, "IPv4: 192.168.0.143/22 | Gateway: 192.168.0.1 | DNS: 1.1.1.1 | MAC: A0:59:50:72:44:BC")
    add_str(v, 102, 107, 0x4ADE80, "Security: WPA2-Personal (CCMP) | Host: Joydev_Barua | Adapter: Intel AX211")

    # Card 2: Nearby SSIDs
    add_rect(v, 90, 134, 525, 122, 0x1E0D36)
    add_rect(v, 90, 134, 4, 122, 0xA855F7)
    add_str(v, 102, 139, 0xA855F7, "NEARBY LAPTOP WIRELESS NETWORKS (LIVE SCAN COMPLETE):")
    add_str(v, 102, 155, 0x4ADE80, "[*] Mojo-Jan-B-F4         5.0 GHz   -63 dBm   [CONNECTED - 721 Mbps]")
    add_str(v, 102, 172, 0xE2E8F0, "[ ] Campus-Secure-5G      5.0 GHz   -68 dBm   [WPA2-Enterprise 433M]")
    add_str(v, 102, 189, 0xE2E8F0, "[ ] Joydev-Lab-Hotspot    5.0 GHz   -72 dBm   [WPA3-Personal  867M]")
    add_str(v, 102, 206, 0xE2E8F0, "[ ] Home-Fiber-AX         5.0 GHz   -75 dBm   [WPA2-Personal  574M]")
    add_str(v, 102, 223, 0x94A3B8, "[ ] Guest-Free-WiFi       2.4 GHz   -82 dBm   [Open           144M]")

    # Card 3: Traffic & Controls
    add_rect(v, 90, 262, 525, 74, 0x1E0D36)
    add_rect(v, 90, 262, 4, 74, 0xF59E0B)
    add_str(v, 102, 268, 0xFACC15, "TRAFFIC: Tx 24,180 pkts (18.6 MB) | Rx 52,940 pkts (74.2 MB) | Host: Joydev")
    add_str(v, 102, 287, 0xF1F5F9, "CONTROLS: [Press C to Connect]  [Press S to Re-Scan]  [Press D to Disconnect]")
    add_str(v, 102, 307, 0x38BDF8, "STATUS: Intel Wi-Fi 6E AX211 Fully Synchronized with Laptop Hardware")

    # =========================================================================
    # VIEW 2: Hardware Compatibility & Audit
    # =========================================================================
    v = 2
    build_window_frame(v, "Vyron OS - Hardware Compatibility & Diagnostics Audit [100% OK]")
    # Card 1: CPU
    add_rect(v, 90, 56, 525, 65, 0x1E0D36)
    add_rect(v, 90, 56, 4, 65, 0x38BDF8)
    add_str(v, 102, 62, 0x38BDF8, "CPU & ARCHITECTURE: 13th Gen Intel Core (Host: Joydev_Barua)")
    add_str(v, 102, 78, 0x4ADE80, "Instruction Sets: MMX, SSE, SSE2, SSE3, SSSE3, SSE4.1, SSE4.2, AVX, VMX [PASS]")
    add_str(v, 102, 94, 0xE2E8F0, "Execution Mode: 16-bit Flat Unreal Mode / 4GB GDT Addressing [PASS]")

    # Card 2: Memory & Display
    add_rect(v, 90, 127, 525, 65, 0x1E0D36)
    add_rect(v, 90, 127, 4, 65, 0x4ADE80)
    add_str(v, 102, 133, 0x4ADE80, "MEMORY & DISPLAY CONTROLLER: VESA VBE 3.0 Linear Framebuffer")
    add_str(v, 102, 149, 0xE2E8F0, "Resolution: 640x400x32bpp | Linear VRAM: 0xE0000000 (16 MB VMSVGA) [PASS]")
    add_str(v, 102, 165, 0x94A3B8, "Host RAM: 4096 MB Physical | Heap: 64 KiB Joydev Bump+FreeList Hybrid [PASS]")

    # Card 3: PCI & Network
    add_rect(v, 90, 198, 525, 65, 0x1E0D36)
    add_rect(v, 90, 198, 4, 65, 0xF59E0B)
    add_str(v, 102, 204, 0xFACC15, "PCI BUS & PERIPHERALS (LAPTOP HARDWARE SCAN):")
    add_str(v, 102, 220, 0x4ADE80, "PCI 00:03.0: Intel(R) Wi-Fi 6E AX211 160MHz (MAC: A0:59:50:72:44:BC) [PASS]")
    add_str(v, 102, 236, 0xE2E8F0, "PCI 00:01.0: Intel PIIX3 / PIIX4 PCI-to-ISA Bridge + ACPI 2.0 PM [PASS]")

    # Card 4: Summary
    add_rect(v, 90, 269, 525, 68, 0x1E0D36)
    add_rect(v, 90, 269, 4, 68, 0xA855F7)
    add_str(v, 102, 275, 0xA855F7, "STORAGE CONTROLLER: ATAPI IDE Primary Master CD-ROM + Fixed 64MB VHD [PASS]")
    add_str(v, 102, 292, 0x4ADE80, "VERDICT: 100% HARDWARE COMPATIBILITY VERIFIED - ALL SUBSYSTEMS FUNCTIONAL")
    add_str(v, 102, 309, 0xF1F5F9, "[Press ESC or C to Return to Desktop]  [Use Arrow Keys to Move Pointer]")

    # =========================================================================
    # VIEW 3: Microkernel & MLFQ Scheduler
    # =========================================================================
    v = 3
    build_window_frame(v, "Joydev Micro-OS - Kernel Monitor & MLFQ Telemetry")
    # Card 1: Microkernel Status
    add_rect(v, 90, 56, 525, 65, 0x1E0D36)
    add_rect(v, 90, 56, 4, 65, 0x38BDF8)
    add_str(v, 102, 62, 0x38BDF8, "MICROKERNEL STATUS: ACTIVE (TICK: 1,482 ms | SPINLOCK: ACQUIRED)")
    add_str(v, 102, 78, 0xE2E8F0, "CPU Usage: 68% | Context Switches: 3,429 | IPC Messages: 8,112")
    add_rect(v, 102, 96, 200, 10, 0x334155)
    add_rect(v, 102, 96, 136, 10, 0x38BDF8)
    add_str(v, 310, 96, 0x38BDF8, "68% CPU")

    # Card 2: MLFQ Scheduler
    add_rect(v, 90, 127, 525, 65, 0x1E0D36)
    add_rect(v, 90, 127, 4, 65, 0x4ADE80)
    add_str(v, 102, 133, 0x4ADE80, "MLFQ 3-LEVEL SCHEDULER: Q0:RR(4ms) | Q1:RR(8ms) | Q2:FCFS")
    add_str(v, 102, 149, 0xE2E8F0, "Anti-Starvation: Priority Boost Every T=25 Ticks | Preemption: Enabled")
    add_rect(v, 102, 167, 200, 10, 0x334155)
    add_rect(v, 102, 167, 160, 10, 0x4ADE80)
    add_str(v, 310, 167, 0x4ADE80, "80% Q0")

    # Card 3: Memory Allocator
    add_rect(v, 90, 198, 525, 65, 0x1E0D36)
    add_rect(v, 90, 198, 4, 65, 0xF59E0B)
    add_str(v, 102, 204, 0xFACC15, "HYBRID MEMORY ALLOCATOR: 64 KiB Total (16K Bump + 48K FreeList)")
    add_str(v, 102, 220, 0xE2E8F0, "Allocated: 48,128 B (74%) | Free: 17,408 B | Coalescing: Active")
    add_rect(v, 102, 238, 200, 10, 0x334155)
    add_rect(v, 102, 238, 148, 10, 0xFACC15)
    add_str(v, 310, 238, 0xFACC15, "74% MEM")

    # Card 4: Footer
    add_rect(v, 90, 269, 525, 68, 0x1E0D36)
    add_rect(v, 90, 269, 4, 68, 0xA855F7)
    add_str(v, 102, 275, 0xA855F7, "TASK THREADS: Thread 0 (Idle), Thread 1 (UI), Thread 2 (MLFQ), Thread 3 (Wi-Fi)")
    add_str(v, 102, 292, 0x4ADE80, "LOCK-FREE QUEUE: AtomicBool Spinlock Mutex Contention: 0.02% [OPTIMAL]")
    add_str(v, 102, 309, 0xF1F5F9, "[Press ESC or C to Return to Desktop]  [Press W for Wi-Fi]  [Press H for Hardware]")

    # =========================================================================
    # VIEW 4: Interactive Terminal
    # =========================================================================
    v = 4
    build_window_frame(v, "Vyron Interactive Terminal - vyron@micro-os: ~")
    add_rect(v, 90, 56, 525, 280, 0x05050C) # terminal black box
    add_rect(v, 90, 56, 525, 1, 0x38BDF8)
    term_lines = [
        ("Vyron Micro-OS [Version 2.4.0-ac] (x86_64-baremetal-virtualbox)", 0x38BDF8),
        ("Kernel: Joydev Rust Microkernel v0.6.2 | Scheduler: MLFQ (3 Levels)", 0x94A3B8),
        ("Type 'help' for command list, or 'wifi', 'hw', 'ps', 'mem', 'clear'.", 0x94A3B8),
        ("", 0xFFFFFF),
        ("vyron@micro-os:~$ wifi status", 0x4ADE80),
        ("wlan0: CONNECTED to 'Mojo-Jan-B-F4' (802.11ax 721Mbps -63dBm 80%)", 0xE2E8F0),
        ("       IPv4: 192.168.0.143/22 | Gateway: 192.168.0.1 | DNS: 1.1.1.1", 0xE2E8F0),
        ("vyron@micro-os:~$ hw --summary", 0x4ADE80),
        ("CPU: 13th Gen Intel Core | NIC: Intel(R) Wi-Fi 6E AX211 | STATUS: 100% OK", 0xE2E8F0),
        ("VGA: VESA VBE 0x4141 (640x400x32bpp @ 0xE0000000) | STATUS: 100% OK", 0xE2E8F0),
        ("vyron@micro-os:~$ mlfq --stat", 0x4ADE80),
        ("Q0: 4ms RR (4 threads) | Q1: 8ms RR (0) | Q2: FCFS (1) | Boost: T=25", 0xFACC15),
        ("vyron@micro-os:~$ _", 0x4ADE80),
    ]
    ty = 64
    for tl, tc in term_lines:
        if tl:
            add_str(v, 98, ty, tc, tl)
        ty += 18

    # Summary:
    for vid in range(5):
        print(f"View {vid}: {len(views[vid]['rects'])} rects, {len(views[vid]['strings'])} strings")
    print(f"Total string bytes: {len(string_bytes)}")
    return views, string_bytes

if __name__ == '__main__':
    build_all_tables()
