# Micro-OS Technical Defence & Individual Viva Guide
## Complete Model Answers for All 20 Viva Questions (Section 32)

---

### Q1: What happens immediately after the kernel starts?
**Answer**:
Immediately after `kernel::boot()` is invoked, the kernel initializes the Hardware Abstraction Layer (HAL). It disables hardware interrupts (`INTERRUPTS_ENABLED = false`), prints the startup diagnostics banner via the serial console driver, and establishes the physical RAM boundaries (a 64 KiB page-aligned buffer). It then partitions memory into a 16 KiB Bump allocator for early boot structures and a 48 KiB Free-List allocator with coalescing for dynamic task memory. Finally, it starts the periodic system timer at 100 Hz, initializes synchronization primitives, and enables interrupts to begin task dispatching.

---

### Q2: How is a task represented?
**Answer**:
A task is represented by a `TaskControlBlock` (TCB) in `src/task/task.rs`. It encapsulates:
1. Identification: unique `id: u32` and `name: &'static str`.
2. State: `TaskState` (`Ready`, `Running`, `Blocked(Reason)`, `Terminated`).
3. Priority: numeric level (`0` for $Q_0$, `1` for $Q_1$, `2` for $Q_2$).
4. Execution context: `CpuContext` containing instruction pointer, stack pointer, and general registers.
5. Execution profile: total burst length, remaining burst, quantum allotment, and task kind (`CpuBound`, `IoBound`, `Mixed`, `Synchronized`).
6. Performance metrics: arrival tick, first execution tick (for response time), completion tick (for turnaround time), accumulated CPU ticks, and waiting ticks.

---

### Q3: How does the scheduler select the next task?
**Answer**:
- In **Round Robin** (Core), the scheduler examines the head of the FIFO ready queue (`ready_queue.pop()`). Tasks that exhaust their quantum are re-enqueued at the tail, achieving $O(1)$ fair circular rotation.
- In **MLFQ** (Specialization), the scheduler inspects queues in strict priority order: $Q_0$ first, then $Q_1$, then $Q_2$. Within any non-empty queue, tasks are selected via Round Robin using that queue's specific quantum ($Q_0=2, Q_1=4, Q_2=8$ ticks).

---

### Q4: Why did you choose Round Robin?
**Answer**:
Round Robin was selected for the core layer because it is the fundamental preemptive time-slicing mechanism in modern operating systems. It guarantees starvation freedom, provides deterministic Upper Bounds on latency for identical workloads, and visually illustrates the trade-off between quantum size, context-switch overhead, and responsiveness.

---

### Q5: What triggers a scheduling decision?
**Answer**:
A scheduling decision is triggered by four distinct OS events:
1. **Timer Interrupt**: Periodic hardware timer tick increments `current_slice`; if `current_slice >= quantum`, an involuntary preemption occurs.
2. **Task Completion**: The running task's `burst_remaining` reaches 0, transitioning it to `Terminated`.
3. **Voluntary Yield / Block**: A task requests I/O or blocks on a contended mutex, voluntarily relinquishing the CPU.
4. **Higher Priority Preemption (MLFQ)**: An I/O-bound task wakes up in $Q_0$, immediately preempting a running task in $Q_1$ or $Q_2$.

---

### Q6: What happens during a timer tick?
**Answer**:
During each periodic tick:
1. The system tick counter advances monotonically (`TIMER.step()`).
2. The scheduler decrements the sleep timer of any blocked I/O tasks; if an I/O timer expires, the task is marked `Ready` and re-enqueued.
3. Every task waiting in the ready queue has its `waiting_ticks` incremented by 1.
4. In MLFQ, the aging timer is checked; if 25 ticks have elapsed, a global priority boost is executed.
5. The running task decrements its `burst_remaining`, increments its CPU runtime, and advances its quantum slice counter.
6. The scheduler evaluates whether to continue execution, preempt, or switch tasks.

---

### Q7: How is shared kernel data protected?
**Answer**:
Shared kernel structures are protected using the `Spinlock<T>` and `Mutex<T>` synchronization abstractions implemented in `src/sync/`. The `Spinlock` uses an atomic boolean flag (`AtomicBool`) with `compare_exchange` and `Acquire` memory ordering. Access to inner data is wrapped in an `UnsafeCell<T>` and only exposed via an RAII `SpinlockGuard` that automatically unlocks with `Release` memory ordering when dropped.

---

### Q8: Why is synchronization required?
**Answer**:
In any concurrent or preemptive multitasking environment, interleaved execution across critical sections leads to race conditions, torn reads, and lost updates. For example, if Task A and Task B both increment a shared counter without synchronization, Task A may read value $N$, get preempted by the timer, Task B writes $N+1$, and Task A resumes and overwrites $N+1$ with its own $N+1$, permanently losing an update. Synchronization enforces mutual exclusion, ensuring serializability and data consistency.

---

### Q9: How does your allocator work?
**Answer**:
Micro-OS implements two complementary allocators:
1. **Bump Allocator**: Advances a linear pointer sequentially through memory. It provides $O(1)$ allocation with zero metadata overhead, ideal for boot-time static allocations.
2. **Free-List Allocator**: Manages dynamic memory using an intrusive linked list of `BlockHeader` structures. Each header records block size, allocation status (`is_free`), and a pointer to the next block. It searches for free blocks via First-Fit, splits blocks when remaining space permits, and merges (coalesces) adjacent free blocks upon deallocation.

---

### Q10: What happens when allocation fails?
**Answer**:
Allocation failures are handled defensively without kernel panic. If the requested payload plus header exceeds available memory, or if no single contiguous block satisfies the layout alignment, the allocator returns `Err(AllocError::OutOfMemory)`. Callers must explicitly check the `Result<*mut u8, AllocError>` and handle or gracefully abort the task.

---

### Q11: Where is `unsafe` used and why?
**Answer**:
`unsafe` is strictly localized to hardware abstraction and memory boundaries:
1. In `src/kernel/hal.rs`: To acquire the raw address of the static physical memory arena (`MEMORY_ARENA.bytes.as_mut_ptr()`).
2. In `src/sync/spinlock.rs`: To dereference the inner `UnsafeCell<T>` pointer within `Deref` and `DerefMut` after the atomic lock acquisition has succeeded.
3. In `src/memory/freelist.rs`: To traverse linked list headers using raw pointers and perform address arithmetic during block splitting and coalescing.

---

### Q12: What invariant does your `unsafe` code rely on?
**Answer**:
1. In `Spinlock`: The fundamental invariant is that `UnsafeCell::get()` is dereferenced if and only if the `locked` atomic flag was transitioning from `false` to `true` by the calling thread via an atomic CAS with `Acquire` ordering, ensuring exclusive mutable access.
2. In `FreeListAllocator`: The invariant is that every valid block header begins with the magic number `0xDEADBEEF`, pointer arithmetic never extends beyond `heap_start + heap_size`, and adjacent blocks are only coalesced if their computed addresses match `curr + header_size + curr.size == next`.

---

### Q13: What happens if two tasks access the same resource?
**Answer**:
- If unsynchronized, interleaved timer preemption causes corrupted states and lost updates.
- If protected by `Spinlock`, the first task acquires the lock; the second task detects `locked == true`, increments the contention metric, and spins (or yields in `Mutex`), waiting until the first task drops its guard. This guarantees 100% deterministic data integrity.

---

### Q14: How did you test the scheduler?
**Answer**:
We implemented a three-tier testing strategy:
1. Integration test suite with six formal test cases (TC1 to TC6 in `tests/`).
2. Quantitative log trace evaluation: Every scheduling decision emits structured logs (`TASK_SWITCH`, `TASK_EXEC`, `CPU_IDLE`).
3. Automated Python analysis scripts (`analyze_traces.py` and `visualize.py`) that parse log traces and calculate waiting time, turnaround time, context-switch count, and Jain's fairness index.

---

### Q15: How did you establish that the scheduler is actually working?
**Answer**:
"It runs" was not accepted as evidence. We proved correctness through:
1. **Gantt Charts**: Visual verification of quantum expiration and round-robin task rotation at exact tick intervals.
2. **Metrics Disparity**: Demonstrating that MLFQ reduced average response time by 50% ($1.75$ ticks vs $3.50$ ticks) and reduced context-switch count from 14 to 11 compared to Round Robin.
3. **Repeatability (TC6)**: Demonstrating that running identical workloads across multiple independent kernel boots produces identical bitwise tick counts and turnaround metrics.

---

### Q16: How is your Micro-OS different from Linux?
**Answer**:
1. **Scheduler**: Linux uses the Completely Fair Scheduler (CFS) based on red-black trees and virtual runtime (`vruntime`) or the EEVDF scheduler; Micro-OS uses Round Robin and an explicit 3-level MLFQ with aging.
2. **Memory**: Linux employs full virtual memory, multi-level paging (PML4/5), demand paging, and buddy-allocator + SLUB; Micro-OS operates over a flat physical arena with Bump and Free-List allocators.
3. **Privilege**: Linux enforces strict hardware Ring 0 (kernel) vs Ring 3 (user) isolation via page table protection bits and `syscall`/`sysret` instructions; Micro-OS runs tasks in kernel space with an emulated HAL.

---

### Q17: What did CA-5 teach you that helped this project?
**Answer**:
CA-5 (Linux Systems Engineering) provided practical exposure to how Linux manages process scheduling policies (`SCHED_RR`, `SCHED_FIFO`), context switches, `/proc` and `/sys` diagnostics, and POSIX synchronization primitives (futexes and mutexes). Understanding Linux process states (`R`, `S`, `D`, `Z`) directly informed our design of Micro-OS task control block states (`Ready`, `Running`, `Blocked`, `Terminated`) and performance metrics tracking.

---

### Q18: What CA-4 research question could be extended into your Micro-OS?
**Answer**:
Our CA-4 research investigated: *"Does decreasing time quantum in preemptive scheduling improve responsiveness at the expense of throughput due to context-switch overhead?"*
In Micro-OS, we directly evaluated this hypothesis in TC3 (Boundary Case: $Q=1$) and our Round Robin vs MLFQ benchmarks. The empirical evidence confirmed that small quanta increase context switches (14 in RR vs 11 in MLFQ), while MLFQ with progressive quanta ($Q_0=2, Q_1=4, Q_2=8$) achieves the optimal Pareto frontier: near-instant response for interactive jobs while batching CPU-bound tasks.

---

### Q19: What would you implement next?
**Answer**:
Next steps would include:
1. **Hardware Paging & Virtual Memory**: Implementing an x86_64 4-level page table allocator to map isolated virtual address spaces per task.
2. **User/Kernel System Calls**: Utilizing CPU software interrupts (`int 0x80` or `syscall`) to transition from unprivileged user tasks into kernel services.
3. **Storage Block Driver**: Adding a minimal VirtIO block driver and FAT16/simple inode filesystem abstraction.

---

### Q20: What is the most important limitation of your current system?
**Answer**:
The most significant limitation is the lack of **hardware-enforced memory isolation (paging / memory protection keys)** between tasks. Because all tasks currently execute within the same address space, a malfunctioning or malicious task could theoretically overwrite another task's stack or corrupt the kernel's ready queue. Introducing hardware page tables and user privilege rings is the natural next layer of systems engineering.
