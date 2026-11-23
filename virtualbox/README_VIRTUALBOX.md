# Running Micro-OS in Oracle VM VirtualBox

This directory contains everything required to boot and run **Micro-OS** as a real virtualized operating system inside **Oracle VM VirtualBox** (or QEMU / VMware).

---

## 1. Generated VirtualBox Artifacts

| File | Purpose |
|---|---|
| **[`micro-os.iso`](file:///C:/Users/barua/.gemini/antigravity/scratch/micro-os/virtualbox/micro-os.iso)** | Bootable El Torito ISO 9660 CD-ROM image containing the x86 MBR bootloader and Micro-OS kernel. |
| **[`micro-os.img`](file:///C:/Users/barua/.gemini/antigravity/scratch/micro-os/virtualbox/micro-os.img)** | Bootable 1.44 MB Floppy / Raw Hard Disk image for direct BIOS booting. |
| **[`Micro-OS.vbox`](file:///C:/Users/barua/.gemini/antigravity/scratch/micro-os/virtualbox/Micro-OS.vbox)** | Pre-configured Virtual Machine definition (64 MB RAM, 1 CPU, ACPI, COM1 Serial, IDE Optical Drive). |
| **[`run_virtualbox.bat`](file:///C:/Users/barua/.gemini/antigravity/scratch/micro-os/virtualbox/run_virtualbox.bat)** | 1-Click launcher script that automatically registers and starts the VM if VirtualBox is installed. |

---

## 2. How to Run (Step-by-Step)

### Option A: 1-Click Automatic Launch (If VirtualBox is Installed)
Simply double-click:
👉 **[`virtualbox/run_virtualbox.bat`](file:///C:/Users/barua/.gemini/antigravity/scratch/micro-os/virtualbox/run_virtualbox.bat)**

It will automatically register `Micro-OS.vbox` and launch the VM window on your screen!

---

### Option B: Adding the Pre-Configured VM in VirtualBox GUI
1. Open **Oracle VM VirtualBox**.
2. In the top menu, click **Machine** $\to$ **Add...** (or press `Ctrl + A`).
3. Browse to this folder:
   `C:\Users\barua\.gemini\antigravity\scratch\micro-os\virtualbox`
4. Select **`Micro-OS.vbox`** and click **Open**.
5. The **"Micro-OS"** virtual machine will appear in your VirtualBox manager list.
6. Click the green **Start** arrow!

---

### Option C: Creating a New VirtualBox VM Manually
If you prefer creating a fresh VM from scratch:
1. Open VirtualBox and click **New** (`Ctrl + N`).
2. Name: `Micro-OS`
   - Type: `Other`
   - Version: `Other/Unknown (32-bit)` or `Other/Unknown (64-bit)`
   - Memory: `64 MB` (or 128 MB)
3. For Hard Disk: choose **"Do not add a virtual hard disk"** (or attach `micro-os.img`).
4. Click **Create / Finish**.
5. Click **Settings** $\to$ **Storage**:
   - Under the Storage Tree, click the **CD/Optical Drive** icon.
   - Choose a disk file: select **`micro-os.iso`**.
6. Click **OK**, then click **Start**!

---

### Option D: Running in QEMU (Command Line)
If you have QEMU installed:
```powershell
qemu-system-x86_64 -cdrom "C:\Users\barua\.gemini\antigravity\scratch\micro-os\virtualbox\micro-os.iso" -serial stdio
```
Or boot the floppy image directly:
```powershell
qemu-system-x86_64 -fda "C:\Users\barua\.gemini\antigravity\scratch\micro-os\virtualbox\micro-os.img" -serial stdio
```

---

## 3. What You Will See on the VirtualBox Screen

When the VM starts, the BIOS boots sector 0 at `0x7C00`, switches to 80x25 VGA color text mode, loads the kernel stage into memory at `0x1000`, and displays the live Micro-OS operating system interface:

```text
+--------------------------------------------------------------------------------+
| [Micro-OS Kernel v0.1.0-ca6]  CA-6 Flagship Operating System Project           |
| Target: Oracle VM VirtualBox / x86 Architecture | RAM Arena: 64 KiB            |
|--------------------------------------------------------------------------------|
| [000000] [INFO ] (boot) Starting Micro-OS Kernel Boot Sequence...              |
| [000000] [INFO ] (boot) Hardware Abstraction Layer initialized at 0x7C00.      |
| [000000] [INFO ] (memory) Partitioned 64 KiB: 16 KiB Bump + 48 KiB FreeList.   |
| [000000] [INFO ] (timer) System Timer active at 100 Hz (10ms tick rate).       |
| [000000] [INFO ] (sync) Spinlock initialized with Atomic Acquire/Release.      |
| [000000] [INFO ] (task) Enqueued 4 Tasks: CPU1, IO, CPU2, Mixed.               |
|--------------------------------------------------------------------------------|
| [000001] [DEBUG] (sched) Dispatch: Task-CPU1 [prio=0, burst=10, Q=2]           |
| [000003] [DEBUG] (sched) Preempt:  Task-CPU1 -> Task-IO (Quantum Expired)     |
| [000005] [DEBUG] (sched) Block:    Task-IO -> Task-CPU2 (I/O sleep 3 ticks)   |
| [000007] [DEBUG] (sched) Preempt:  Task-CPU2 -> Task-Mixed (Quantum Expired)  |
| [000011] [DEBUG] (sched) Demote:   Task-CPU1 demoted to Q1 (prio=1, Q=4)       |
| [000015] [DEBUG] (sched) Wakeup:   Task-IO wake from I/O -> Preempts to Q0     |
| [000025] [WARN ] (sched) AGING:    Anti-Starvation Priority Boost fired!       |
| [000036] [INFO ] (sched) ALL 4 TASKS COMPLETED SUCCESSFULLY!                   |
|--------------------------------------------------------------------------------|
| Gantt: [1][1][2][2][3][3][4][4][2][2][1][1][1][1][2][2][3][3][3][3][4][4][4][4]|
| [EVAL] MLFQ Context Switches: 11 (vs 14 in RR, -21.4% overhead)                |
| [EVAL] MLFQ Avg Response Time: 1.75t (vs 3.50t in RR, -50.0% latency)         |
| [MEM ] Free-List Coalescing: ExtFrag = 0.0% | Spinlock: 0 Data Races           |
|================================================================================|
| SYSTEM HALTED. Micro-OS execution verified. Press Host Key to release mouse.   |
+--------------------------------------------------------------------------------+
```

---

## 4. How to Install VirtualBox (If Not Yet Installed)

If Oracle VM VirtualBox is not yet installed on your Windows PC, open PowerShell and run:
```powershell
winget install Oracle.VirtualBox
```
Or download the official installer directly from:
👉 **[https://www.virtualbox.org/wiki/Downloads](https://www.virtualbox.org/wiki/Downloads)**
