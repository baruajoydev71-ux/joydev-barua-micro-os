# CA-6 Individual Contribution Statement (Section 31)

This project was structured using modular ownership boundaries across kernel engineering, specialization, testing, and performance analysis.

---

## Subsystem Allocation Matrix

| Team Member | Subsystems Owned | Code Contributed | Experiments & Validation | Documentation & Defence |
|---|---|---|---|---|
| **Member 1** (Systems Lead) | Kernel Boot, HAL, Task Management & Core Round Robin | `src/kernel/hal.rs`, `src/kernel/diagnostics.rs`, `src/task/task.rs`, `src/task/queue.rs`, `src/scheduler/round_robin.rs` | TC1 (Minimum Config), TC3 (Boundary Quantum), Round Robin baseline benchmarks | `README.md`, `docs/architecture.md`, Boot & Scheduler Viva Defence |
| **Member 2** (Scheduler & Concurrency Lead) | Track A MLFQ Specialization, Timer & Synchronization | `src/scheduler/mlfq.rs`, `src/scheduler/traits.rs`, `src/timer/timer.rs`, `src/sync/spinlock.rs`, `src/sync/mutex.rs` | TC2 (Heterogeneous Workload), TC4 (16-Task Stress), Lock contention experiments | `docs/design.md`, MLFQ analysis, Concurrency Viva Defence |
| **Member 3** (Memory & Evaluation Lead) | Memory Management, Formal Testing Suite & Python Harness | `src/memory/bump.rs`, `src/memory/freelist.rs`, `tests/*`, `scripts/analyze_traces.py`, `scripts/visualize.py`, `scripts/generate_plots.py` | TC5 (Defensive Failure/OOM/Double-Free), TC6 (Deterministic Repeatability), Python trace parsing | `docs/testing.md`, `docs/debugging_log.md`, `results/evaluation_report.md` |

---

## Detailed Subsystem Breakdown

### Member 1: Kernel Architecture, HAL & Core Scheduler
- **Subsystem Owned**: Bootloader, Hardware Abstraction Layer, Task Control Block, and Round Robin scheduler.
- **Code Contributed**: Designed and implemented [`TaskControlBlock`](file:///C:/Users/barua/.gemini/antigravity/scratch/micro-os/src/task/task.rs) with execution metrics and state transitions; authored the $O(1)$ ring buffer [`TaskQueue`](file:///C:/Users/barua/.gemini/antigravity/scratch/micro-os/src/task/queue.rs); implemented the core [`RoundRobinScheduler`](file:///C:/Users/barua/.gemini/antigravity/scratch/micro-os/src/scheduler/round_robin.rs) with time-slice preemption.
- **Debugging Contribution**: Resolved ready-queue wrap-around indexing bug under rapid preemption.
- **Viva Focus**: Ready queue data structure, context switching, Round Robin quantum trade-offs.

### Member 2: MLFQ Specialization & Kernel Synchronization
- **Subsystem Owned**: Multi-Level Feedback Queue (Track A), Periodic Timer, and Atomic Synchronization primitives.
- **Code Contributed**: Authored [`MlfqScheduler`](file:///C:/Users/barua/.gemini/antigravity/scratch/micro-os/src/scheduler/mlfq.rs) with 3 priority levels ($Q_0, Q_1, Q_2$), dynamic priority demotion on quantum expiry, I/O-friendly retention, and periodic priority boosting (aging); implemented [`Spinlock`](file:///C:/Users/barua/.gemini/antigravity/scratch/micro-os/src/sync/spinlock.rs) using `AtomicBool` with acquire-release ordering and read-only spin optimization; implemented yield-aware [`Mutex`](file:///C:/Users/barua/.gemini/antigravity/scratch/micro-os/src/sync/mutex.rs).
- **Debugging Contribution**: Identified and eliminated starvation of CPU-bound tasks in $Q_2$ by implementing the global anti-starvation boost every 25 ticks; optimized spinlock to reduce memory bus traffic.
- **Viva Focus**: MLFQ governing rules, priority inversion, cache bus contention, `unsafe` invariants in `Spinlock`.

### Member 3: Memory Allocator, Testing & Python Analysis
- **Subsystem Owned**: Dynamic Memory Subsystem, Verification Suite (TC1–TC6), and Python Trace Analysis Layer.
- **Code Contributed**: Implemented [`BumpAllocator`](file:///C:/Users/barua/.gemini/antigravity/scratch/micro-os/src/memory/bump.rs) and [`FreeListAllocator`](file:///C:/Users/barua/.gemini/antigravity/scratch/micro-os/src/memory/freelist.rs) with block headers, First-Fit search, block splitting, and adjacent block coalescing; authored formal integration tests in `tests/`; wrote Python trace parsers and Matplotlib visualizers.
- **Debugging Contribution**: Solved external memory fragmentation bug by implementing two-pointer coalescing; intercepted double-free vulnerabilities using magic constants.
- **Viva Focus**: Free-list headers, coalescing algorithm, mathematical definition of external fragmentation, Jain's fairness index.
