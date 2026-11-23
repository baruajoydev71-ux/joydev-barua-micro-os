# Micro-OS Live Demonstration & Viva Defence Walkthrough Script

This guide provides a step-by-step, 5-minute demonstration script for presenting **Micro-OS** during the CA-7 Viva and Technical Defence.

---

## 5-Minute Demonstration Plan

| Time | Phase | Command / Action | Key Mechanism to Highlight |
|---|---|---|---|
| **0:00 – 1:00** | **Boot & Memory Init** | `cargo run -- --rr` | Physical RAM partitioning (16 KiB Bump, 48 KiB FreeList), monotonic timer activation (100 Hz), structured diagnostics. |
| **1:00 – 2:00** | **Memory Subsystem** | Walkthrough console output | Dynamic 64B & 128B allocations, pointer alignment, block deallocation, and **block coalescing** (reducing external fragmentation to 0.0%). |
| **2:00 – 2:45** | **Synchronization** | Walkthrough console output | Atomic `Spinlock` critical section protection on `SharedCounter`, zero data corruption, contention tracking. |
| **2:45 – 3:45** | **Comparative Schedulers** | `cargo run -- --compare` | Side-by-side execution: Round Robin ($Q=2$) vs. MLFQ ($Q_0=2, Q_1=4, Q_2=8$). Explain dynamic demotion of CPU tasks and anti-starvation boost at tick 25. |
| **3:45 – 4:30** | **Python Visualizer** | `python scripts/visualize.py` | Display ASCII Gantt chart; demonstrate how interactive I/O tasks achieve near-instant response time in MLFQ. |
| **4:30 – 5:00** | **Verification Suite** | `cargo run -- --test-all` | Run TC1 to TC6; prove 100% bitwise repeatability and defensive OOM/double-free rejection. |

---

## Live Demonstration Commands

### Step 1: Execute Kernel Boot & Comparative Workload
Open terminal in `micro-os/`:
```bash
cargo run -- --compare
```
**Talking Points**:
> *"Here we see Layer 1 booting the Micro-OS kernel, establishing a 64 KiB memory arena, and setting up our 100 Hz timer. We then run an identical 4-task workload through both Round Robin and MLFQ. Notice the side-by-side comparison: MLFQ cuts average response time in half (from 3.50 to 1.75 ticks) and reduces context switches by 21.4% (from 14 down to 11). Furthermore, at tick 25, our anti-starvation aging boost fired, restoring all tasks to Queue 0."*

---

### Step 2: Show Python Log Trace Analysis & Visual Gantt Chart
```bash
python scripts/analyze_traces.py
python scripts/visualize.py
```
**Talking Points**:
> *"Following Section 19 of the specification, the Rust kernel emits structured serial logs which our Python pipeline parses. The Gantt chart clearly displays how Task-2, an interactive I/O task, stays in Queue 0 and receives immediate CPU access whenever it wakes, dropping its turnaround time from 20 ticks down to 16 ticks."*

---

### Step 3: Run the 6 Formal Verification Tests
```bash
cargo run -- --test-all
```
**Talking Points**:
> *"All 6 formal test cases pass cleanly: TC1 confirms two-task rotation; TC2 validates heterogeneous workloads; TC3 stress-tests boundary quantum preemption at Q=1; TC4 scales to 16 concurrent tasks without starvation; TC5 proves our allocator defensively rejects OOM and catches double-frees; and TC6 verifies bitwise deterministic repeatability across multiple kernel boots."*
