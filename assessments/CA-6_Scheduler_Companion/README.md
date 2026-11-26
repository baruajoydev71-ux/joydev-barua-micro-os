---
title: Joydev Micro-OS Scheduler
emoji: ⚙️
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
license: mit
---

# Joydev Micro-OS – Round Robin Scheduler Companion

**Developed by Joydev Barua**  
**Course:** Operating Systems – Continuous Assessment 6 (CA6)  
**Project:** Joydev Micro-OS: A Rust-Based x86_64 Operating System with Dynamic Round Robin Scheduling  
**Specialization:** Scheduler Engineering  

---

## 📌 Overview

This interactive Hugging Face Space is the companion visualization dashboard for **Joydev Micro-OS**, an educational x86_64 bare-metal kernel implemented in Rust (`no_std`, `no_main`), booted with the Limine bootloader, and emulated in QEMU.

> **⚠️ NOTE:** This application is an interactive **scheduler simulator companion**. The actual production operating system runs at the bare-metal hardware/emulator level in Rust with custom interrupt service routines, timer drivers, page frame tracking, and atomic spinlocks.

---

## 🚀 Key Features Demonstrated

1. **Round Robin Execution:** Demonstrates time-slicing and cyclic task preemption across multiple controlled tasks.
2. **Dynamic Quantum Adaptation:**
   - **Burst-Aware Scaling:** Automatically shrinks time slices for interactive/I/O tasks and expands slices for compute-bound tasks.
   - **Anti-Starvation Mechanism:** Detects tasks delayed in the ready queue past the threshold and boosts their quantum.
   - **Priority Multipliers:** Applies weights for Low, Normal, High, and Realtime priority classes.
3. **Interactive Gantt Timeline:** Real-time Gantt visualizer displaying exact task execution intervals, quantum assignments, and adaptation reasons.
4. **Performance Accounting:** Live calculation of **Waiting Time**, **Turnaround Time**, **Context Switch Counts**, and **CPU Efficiency**.
5. **Trace Log Mirror:** Real-time structured event logs matching the kernel's serial COM1 diagnostic output.

---

## 💻 Local Setup & Execution

To run this simulator companion locally:

```bash
# 1. Clone repository
git clone https://github.com/joydevbarua/joydev-micro-os-scheduler.git
cd joydev-micro-os-scheduler

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the Gradio web interface
python app.py
```

Open `http://localhost:7860` in your browser.

---

## 🔬 Comparison: Bare-Metal Kernel vs. Companion Simulator

| Dimension | Joydev Micro-OS Bare-Metal Kernel | Companion Web Simulator |
|---|---|---|
| **Language** | Rust (`no_std`, `no_main`) | Python (Gradio, Pandas, Plotly) |
| **Execution Environment** | x86_64 Hardware / QEMU Emulator | Any browser / Hugging Face Spaces |
| **Boot Mechanism** | Limine Boot Protocol (ELF64) | Standard Web Server / Python runtime |
| **Timer Mechanism** | Intel 8254 PIT (Port 0x40/0x43) | Simulation loop |
| **Synchronization** | Atomic Spinlock & TicketLock | State variables |
| **Memory Management** | Custom Bump Allocator & Frame Tracker | Python Garbage Collector |
| **Purpose** | Low-level OS mechanism implementation | Educational visualization & exploration |
