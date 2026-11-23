# CA-6 Final Technical Report: Engineering an Educational Micro-OS in Rust

---

## 1. Title
**Design, Implementation, and Evaluation of a Modular Micro-OS Kernel in Rust with Round Robin and Multi-Level Feedback Queue Scheduling**

---

## 2. Abstract
Operating system mechanisms such as task management, CPU scheduling, synchronization, and dynamic memory allocation are typically studied conceptually or observed indirectly through production monolithic kernels like Linux. This project implements **Micro-OS**, a minimal, transparent, and reproducible educational operating system written in **Rust**. Built in an incremental 10-layer architecture, Micro-OS demonstrates core OS primitives without relying on opaque hardware or complex virtualization. In addition to the core Round Robin scheduler, this project presents **Specialization Track A: Scheduler Engineering**, implementing a complete Multi-Level Feedback Queue (MLFQ) with dynamic priority demotion, I/O-friendly retention, and periodic anti-starvation boosting (aging). Experimental evaluation of a heterogeneous 4-task workload reveals that MLFQ achieves a 50.0% reduction in average response time (1.75 ticks vs 3.50 ticks), a 21.4% reduction in context-switching overhead (11 vs 14 switches), and improves interactive I/O turnaround time by 20.0% while maintaining long-term fairness (Jain's index of 0.9419). All kernel mechanisms are validated through a six-tier formal test suite (TC1–TC6) and verified through automated Python trace parsing and visualization.

---

## 3. Problem Statement
Undergraduate systems education frequently suffers from a disconnect between high-level theoretical algorithms (e.g., Gantt charts, Peterson's algorithm, First-Fit allocation) and real-world implementations. Production kernels such as Linux contain millions of lines of optimized code, complex subsystems (CFS, RCU, SLUB, demand paging), and multi-architecture abstraction layers that obscure fundamental causal relationships:

$$\text{OS Concept} \longrightarrow \text{Design} \longrightarrow \text{Rust Abstraction} \longrightarrow \text{Hardware Interaction} \longrightarrow \text{Observable Behaviour}$$

The engineering challenge is: *Can students construct a small, modular educational kernel from first principles in a memory-safe systems language, demonstrate visible operating system mechanisms, collect quantitative evidence from execution traces, and rigorously defend design trade-offs?*

---

## 4. Objectives
1. Implement a runnable, bare-metal-compatible Micro-OS kernel in Rust.
2. Develop an incremental 10-layer architecture spanning bootstrap, structured diagnostics, task control blocks, ready queues, CPU scheduling, periodic timer preemption, kernel synchronization, and dynamic memory allocation.
3. Engineer a Multi-Level Feedback Queue (MLFQ) specialization with dynamic priority demotion, I/O retention, and anti-starvation aging.
4. Provide a dual-mode execution model: bare-metal `#![no_std]` core with a native architecture simulator HAL for cross-platform execution, testing, and deterministic reproducibility.
5. Build an automated Python trace analysis and visualization pipeline to extract queuing latency, turnaround time, CPU utilization, and Jain's Fairness Index.
6. Formally verify the system against six core test scenarios (TC1–TC6).

---

## 5. OS Concepts
Micro-OS embodies fundamental operating-system principles:
- **Multitasking & Concurrency**: Representing independent threads of execution via Task Control Blocks (TCBs), saving/restoring CPU context, and transitioning across lifecycle states (`READY`, `RUNNING`, `BLOCKED`, `TERMINATED`).
- **CPU Scheduling Policies**: Balancing throughput, turnaround time, waiting time, and responsiveness through preemptive time slicing (Round Robin) and priority-based heuristics (MLFQ).
- **Involuntary Preemption**: Enforcing fair CPU allocation using periodic hardware timer interrupts to interrupt running tasks without cooperative yielding.
- **Mutual Exclusion**: Safeguarding shared critical sections against race conditions and torn reads using atomic test-and-set spinlocks with acquire-release memory semantics.
- **Dynamic Memory Allocation**: Managing physical heaps with contiguous block tracking, block splitting, and adjacent block coalescing to counteract external fragmentation.

---

## 6. Architecture
The architecture comprises 10 distinct, loosely-coupled layers:

```text
+-------------------------------------------------------------+
| Layer 10: Integrated Micro-OS Lifecycle & Workload Runner   |
+-------------------------------------------------------------+
| Layer 9 : Specialization: Multi-Level Feedback Queue (MLFQ) |
+-------------------------------------------------------------+
| Layer 8 : Dynamic Memory Management (Bump & Free-List)      |
+-------------------------------------------------------------+
| Layer 7 : Kernel Synchronization (Spinlock, Mutex, Atomics) |
+-------------------------------------------------------------+
| Layer 6 : Periodic System Timer (100 Hz Ticks & Preemption) |
+-------------------------------------------------------------+
| Layer 5 : Round Robin Scheduler (Fixed Quantum Slicing)     |
+-------------------------------------------------------------+
| Layer 4 : Ready Queue (O(1) Ring Buffer Data Structure)     |
+-------------------------------------------------------------+
| Layer 3 : Task Representation (TCB, CpuContext, States)     |
+-------------------------------------------------------------+
| Layer 2 : Structured Serial Diagnostics & Log Formatting    |
+-------------------------------------------------------------+
| Layer 1 : Hardware Abstraction Layer (HAL) & Boot Entry     |
+-------------------------------------------------------------+
| Hardware: 64 KiB Page-Aligned Physical RAM Arena            |
+-------------------------------------------------------------+
```

Data flows unidirectionally from the timer and HAL into the ready queue and scheduler, which dispatches tasks into execution contexts protected by synchronization guards.

---

## 7. Design Decisions
1. **Dual-Target Execution (`#![no_std]` + Native Simulator HAL)**: Writing the kernel core in `#![no_std]` Rust using core primitives (`core::sync::atomic`, `core::ptr`, `core::mem`) allows deployment to bare-metal QEMU targets, while the educational HAL enables immediate execution and unit testing on standard development hosts without QEMU installation.
2. **Ring-Buffer Ready Queue**: Using a fixed-size ring buffer (`MAX_TASKS = 32`) avoids dynamic allocation in the kernel scheduling path, providing strictly bounded $O(1)$ operations and deterministic context switches.
3. **Contiguous Coalescing Allocator**: To balance implementation complexity and fragmentation control, the Free-List allocator implements First-Fit allocation with immediate two-pointer contiguous coalescing upon deallocation.
4. **Cache-Conscious Spinlock**: Rather than executing continuous atomic compare-and-swap operations, the spinlock implements a *test-and-test-and-set* loop that spins on shared, read-only cache hits, significantly reducing memory controller bus saturation.

---

## 8. Rust Implementation
Rust was chosen for its strict ownership model, compile-time borrow checker, zero-cost abstractions, and explicit handling of low-level memory via `unsafe` blocks.

### Safe Encapsulation of Low-Level Primitives
All `unsafe` operations are strictly isolated behind safe RAII abstractions:
- `SpinlockGuard<'a, T>` implements `Deref` and `DerefMut` to expose inner data only when the atomic lock is held, releasing the lock automatically upon `drop()`.
- The physical memory arena is page-aligned to 4096 bytes using `#[repr(align(4096))]`.
- Dynamic memory deallocation requires magic constant verification (`0xDEADBEEF`) and address bounds checks (`[heap_start, heap_start + heap_size)`) to intercept invalid or double-free pointer operations.

---

## 9. Scheduling Subsystem
The scheduler is formalized around a unified `Scheduler` trait (`src/scheduler/traits.rs`):

```rust
pub trait Scheduler {
    fn add_task(&mut self, task: TaskControlBlock) -> Result<(), &'static str>;
    fn tick(&mut self, current_tick: u64) -> SchedulerAction;
    fn yield_current(&mut self, current_tick: u64) -> SchedulerAction;
    fn block_current(&mut self, reason: BlockReason, current_tick: u64) -> SchedulerAction;
    fn unblock_task(&mut self, task_id: u32, current_tick: u64);
    fn metrics(&self) -> SchedulerMetrics;
}
```

### Core Layer 5: Round Robin
- Uses a single FIFO ready queue with a fixed quantum ($Q = 2$ ticks).
- Each tick decrements the active task's burst and increments its execution slice.
- When `current_slice >= quantum`, the task is preempted, appended to the tail of the ready queue, and the next task is dispatched.

---

## 10. Synchronization Subsystem
Implemented in `src/sync/spinlock.rs` and `src/sync/mutex.rs`:
- **`Spinlock<T>`**: Employs an `AtomicBool` with `Acquire` memory ordering on acquisition and `Release` memory ordering on release. It instruments contention counts and total spin cycles.
- **`Mutex<T>`**: Sleep/yield-aware lock that records the owning task ID. Contended acquisitions trigger voluntary yielding to prevent uniprocessor deadlocks.
- **Empirical Validation**: Interleaved access to a `SharedCounter` without synchronization results in lost updates and torn counts. Under `Spinlock` protection, 100% of operations are serialized without data corruption.

---

## 11. Memory Management Subsystem
Implemented in `src/memory/bump.rs` and `src/memory/freelist.rs`:
- **Physical Partitioning**: The 64 KiB arena is split into 16 KiB for the early-boot Bump allocator and 48 KiB for the dynamic Free-List heap.
- **Block Headers**:
  ```rust
  #[repr(C)]
  pub struct BlockHeader {
      pub magic: u32,       // 0xDEADBEEF
      pub size: usize,      // Payload byte count
      pub is_free: bool,    // Allocation state flag
      pub next: *mut BlockHeader,
  }
  ```
- **Coalescing Engine**: Merges contiguous adjacent free blocks, restoring external fragmentation from 62.5% to 0.0% upon deallocation.

---

## 12. Specialization Component: Multi-Level Feedback Queue (MLFQ)
Implemented in `src/scheduler/mlfq.rs`, the MLFQ specialization addresses Round Robin's inability to optimize for heterogeneous workloads:

### Five Governing Rules:
1. **Rule 1 (Strict Priority)**: If $\text{Priority}(A) < \text{Priority}(B)$, Task $A$ runs ($Q_0 > Q_1 > Q_2$).
2. **Rule 2 (Round Robin within Queue)**: If $\text{Priority}(A) == \text{Priority}(B)$, tasks run in Round Robin using the queue's specific quantum ($Q_0 = 2, Q_1 = 4, Q_2 = 8$ ticks).
3. **Rule 3 (Demotion on Quantum Expiry)**: Tasks that consume their entire quantum without blocking are penalized as compute-intensive and demoted to the next lower queue ($Q_0 \to Q_1 \to Q_2$).
4. **Rule 4 (I/O-Friendly Retention)**: Tasks that voluntarily relinquish the CPU before quantum expiration (e.g., initiating simulated I/O) preserve their priority level.
5. **Rule 5 (Priority Boost / Aging)**: Every $S = 25$ ticks, all active tasks in $Q_1$ and $Q_2$ are promoted back to $Q_0$ with reset quanta, completely eliminating starvation for long batch jobs.

---

## 13. Testing Strategy & Test Plan
Validation was structured across six formal test cases (TC1–TC6 in `tests/`):
- **TC1 (Minimum Configuration)**: 2 tasks, Round Robin, verifies basic preemption and termination.
- **TC2 (Heterogeneous Workload)**: 4 tasks (CPU, I/O, Mixed) under MLFQ, verifies coexistence of batch and interactive tasks.
- **TC3 (Boundary Case)**: Quantum = 1 tick, verifies rapid context switching without state corruption.
- **TC4 (Stress Case)**: 16 concurrent tasks under MLFQ, verifies queue saturation and anti-starvation aging.
- **TC5 (Failure Case)**: Evaluates defensive error handling: OOM layouts return `Err(OutOfMemory)`, and double-free calls return `Err(InvalidPointer)`.
- **TC6 (Repeatability)**: Validates bitwise deterministic reproducibility across independent kernel boots.

---

## 14. Experimental Results

```text
========================================================================
 EXPERIMENTAL COMPARISON: ROUND ROBIN vs. MLFQ
========================================================================
 Metric                       Round Robin (Core)    MLFQ (Specialization)
------------------------------------------------------------------------
 Total Execution Ticks                    36                    36
 Total Context Switches                   14                    11  (-21.4%)
 Average Response Time            3.50 ticks            1.75 ticks  (-50.0%)
 Average Waiting Time            20.50 ticks           19.00 ticks  (-7.3%)
 Average Turnaround Time         29.50 ticks           28.00 ticks  (-5.1%)
 Task-IO Turnaround Time         20.00 ticks           16.00 ticks  (-20.0%)
 CPU Utilization                     100.0 %               100.0 %
 Jain's Fairness Index                0.9419                0.9419
 Priority Boost Events                   N/A                     1
 Priority Demotion Events                N/A                     4
========================================================================
```

---

## 15. Performance Analysis
1. **Interactive Responsiveness**: MLFQ slashed average response time by **50.0%** (1.75 ticks vs 3.50 ticks) and Task-IO turnaround time by **20.0%** (16 vs 20 ticks). Because Task-2 yielded for I/O before exhausting its 2-tick allotment, it was retained in $Q_0$ and immediately preempted lower-priority compute tasks upon waking.
2. **Context-Switch Amortization**: Long CPU-bound tasks (Task-1 and Task-3) were quickly demoted to $Q_1$ (quantum 4) and $Q_2$ (quantum 8). Consequently, they executed in longer contiguous chunks, reducing total context switches by **21.4%** (11 vs 14 switches).
3. **Starvation Defense**: At tick 25, the global priority boost fired, preventing long-running tasks in $Q_2$ from experiencing starvation.

---

## 16. Limitations
1. **Lack of Hardware Paging**: All tasks execute within a shared physical memory arena without hardware-enforced MMU page tables or protection keys.
2. **Single-Core Execution**: The scheduler targets a uniprocessor model; multi-core scheduling (e.g., per-CPU runqueues, work stealing, and IPI-based TLB shootdowns) is not implemented.
3. **Simulated I/O**: I/O operations are simulated via timer-based sleep cycles rather than asynchronous hardware DMA/interrupt drivers.

---

## 17. Lessons Learned
- **`unsafe` Rust Discipline**: Restricting `unsafe` to hardware interfaces and validating pointer bounds with magic numbers eliminates entire classes of use-after-free and double-free vulnerabilities.
- **Preemption Overhead**: Smaller quanta improve responsiveness but impose severe context-switch penalties. Dynamic multi-level queues effectively navigate this Pareto trade-off.
- **Trace-Driven Debugging**: Emitting machine-readable serial traces from early development enables quantitative verification that cannot be matched by visual console inspection alone.

---

## 18. Future Work
1. **x86_64 Paging Implementation**: Implementing 4-level page table management (PML4, PDPT, PD, PT) to assign each task an isolated virtual address space.
2. **User-Space Transition & System Calls**: Utilizing CPU software traps (`int 0x80` / `syscall`) to support unprivileged Ring 3 execution.
3. **VirtIO Storage Driver**: Developing a block-device driver to mount a simple read-only filesystem.

---

## 19. References
1. Remzi H. Arpaci-Dusseau and Andrea C. Arpaci-Dusseau. *Operating Systems: Three Easy Pieces*. Arpaci-Dusseau Books, 2018.
2. Philipp Oppermann. *Writing an OS in Rust*. [https://os.phil-opp.com](https://os.phil-opp.com).
3. Robert Love. *Linux Kernel Development*. 3rd Edition, Addison-Wesley, 2010.
4. Steve Klabnik and Carol Nichols. *The Rust Programming Language*. No Starch Press, 2018.

---

## 20. AI Usage Disclosure
Generative AI was used for architectural brainstorming, reviewing Rust syntax idioms, scaffolding initial test assertions, and drafting Matplotlib plotting logic. In accordance with Section 25, every line of kernel logic, memory arithmetic, atomic ordering, and safety invariants was reviewed, audited, and verified by the authors. The authors take full engineering responsibility for the submitted system.
