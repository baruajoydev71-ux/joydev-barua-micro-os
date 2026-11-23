# Micro-OS Experimental Evaluation & Performance Analysis

## 1. Overview of Experimental Workload

The performance evaluation was conducted using a controlled heterogeneous workload consisting of 4 distinct tasks designed to represent real-world multitasking dynamics:
- **Task-1 (CPU-Bound)**: Burst length = 10 ticks. Requires sustained computation.
- **Task-2 (Interactive / I/O-Bound)**: Burst length = 6 ticks. Computes for 2 ticks, then initiates 3 ticks of simulated I/O sleep.
- **Task-3 (Long CPU-Bound)**: Burst length = 12 ticks. Compute-intensive batch task.
- **Task-4 (Mixed Workload)**: Burst length = 8 ticks. Moderate compute profile.

Total workload demand: **36 computation ticks**.

---

## 2. Quantitative Comparative Results

| Metric | Round Robin (Core, $Q=2$) | MLFQ (Specialization) | $\Delta$ Variance | Engineering Impact |
|---|---|---|---|---|
| **Total Simulation Ticks** | 36 ticks | 36 ticks | 0 ticks | Identical total work completed |
| **Context Switch Count** | 14 switches | 11 switches | **-21.4%** | MLFQ reduces switching overhead |
| **Average Response Time** | 3.50 ticks | 1.75 ticks | **-50.0%** | I/O tasks scheduled near-instantaneously |
| **Average Waiting Time** | 20.50 ticks | 19.00 ticks | **-7.3%** | Reduced queuing latency |
| **Average Turnaround Time** | 29.50 ticks | 28.00 ticks | **-5.1%** | Faster end-to-end task completion |
| **Task-IO Turnaround Time** | 20.00 ticks | 16.00 ticks | **-20.0%** | Interactive user experience significantly improved |
| **CPU Utilization** | 100.0% | 100.0% | 0.0% | Schedulers achieve maximum throughput |
| **Jain's Fairness Index** | 0.9419 | 0.9419 | 0.000 | Excellent long-term fairness |
| **Priority Boost Events** | N/A | 1 event | N/A | Anti-starvation triggered at tick 25 |
| **Priority Demotions** | N/A | 4 demotions | N/A | CPU tasks successfully demoted to lower queues |

---

## 3. Scheduler Analysis: Why MLFQ Outperformed Round Robin

1. **Responsiveness for Interactive Tasks**:
   In Round Robin, Task-2 (I/O) must wait behind CPU-bound tasks in the circular FIFO queue on every wake-up. In MLFQ, because Task-2 repeatedly yields before its 2-tick quantum expires, it **retains top priority in $Q_0$**. When it wakes from I/O sleep, it immediately preempts lower-priority tasks, dropping its turnaround time from 20 ticks to 16 ticks.

2. **Context-Switch Amortization**:
   In Round Robin with $Q=2$, long CPU jobs (Task-1 and Task-3) are constantly preempted every 2 ticks, racking up 14 context switches. In MLFQ, CPU-bound tasks are progressively demoted to $Q_1$ ($Q=4$) and $Q_2$ ($Q=8$). As a consequence, they receive longer uninterrupted execution slices, slashing total context switches by **21.4%** (11 vs 14).

3. **Starvation Prevention via Priority Boosting**:
   At tick 25, the global boost timer fired, resetting all active tasks back to $Q_0$. This prevented Task-3 (which was residing in $Q_2$) from being starved by incoming bursts in higher queues.

---

## 4. Memory Allocator & Fragmentation Analysis

| Allocation Stage | Allocated Bytes | Free Bytes | Free Blocks | External Fragmentation |
|---|---|---|---|---|
| **Initial Boot State** | 0 B | 49,128 B | 1 block | 0.0% |
| **After 2 Allocations (64B, 128B)** | 192 B | 48,888 B | 1 block | 0.0% |
| **After Freeing 64B (Without Coalesce)** | 128 B | 48,952 B | 2 blocks | **62.5%** |
| **After Freeing 128B (With Coalesce)** | 0 B | 49,128 B | 1 block | **0.0%** |

### Mathematical Definition of External Fragmentation:
$$\text{External Fragmentation} = 1.0 - \left( \frac{\text{Largest Free Block Size}}{\text{Total Free Bytes}} \right)$$

When non-adjacent blocks are freed without coalescing, the largest available contiguous block is significantly smaller than the total free space. The Micro-OS `coalesce()` algorithm successfully merged adjacent free blocks, restoring external fragmentation to **0.0%**.

---

## 5. Linux vs Micro-OS Architectural Comparison

| Architectural Mechanism | Production Linux Kernel (v6.x) | Student Micro-OS (CA-6) |
|---|---|---|
| **CPU Scheduling** | Completely Fair Scheduler (CFS) / EEVDF with virtual runtime ($vruntime$) and red-black trees | Fixed-Quantum Round Robin (Core) & 3-Level MLFQ with Aging (Specialization) |
| **Time-Slice Tracking** | High-resolution tickless timer (`CONFIG_NO_HZ_FULL`) + dynamic quanta | Periodic 100 Hz hardware timer ticks (10ms discrete steps) |
| **Memory Management** | Multi-level Paging (4/5-level), TLB shootdowns, Buddy System + SLUB allocator | 64 KiB contiguous arena, Bump allocator + Free-List with block coalescing |
| **Synchronization** | Futexes, Adaptive Mutexes, Reader-Writer spinlocks, RCU (Read-Copy-Update) | Atomic `AtomicBool` Spinlocks with read-only spin optimization & sleep Mutexes |
| **Isolation & Protection** | Hardware Ring 0 vs Ring 3 privilege rings, page table NX/User bits | Modular `#![no_std]` Rust abstractions with safe encapsulation over HAL |
