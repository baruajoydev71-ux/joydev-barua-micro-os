# Micro-OS System Architecture & Control Flow

## 1. Executive Summary

**Micro-OS** is an educational operating system kernel engineered in Rust for the CA-6 Systems Engineering flagship assessment. It provides an explicit, visible demonstration of core operating-system mechanisms: bare-metal bootstrap, structured diagnostics, task control blocks, ready queues, timer-driven preemption, mutual-exclusion synchronization, and dynamic memory allocation with block coalescing.

In addition to the 10 Core layers, this implementation incorporates **Specialization Track A: Scheduler Engineering**, featuring a full **Multi-Level Feedback Queue (MLFQ)** scheduler with dynamic priority demotion, I/O-friendly retention, and periodic anti-starvation priority boosting (aging).

---

## 2. Complete Layered Architecture

```mermaid
graph TD
    subgraph User_Demonstration ["Layer 10: Demonstration & Workloads"]
        App["Workload Generator (CPU-Bound, I/O-Bound, Synchronized)"]
    end

    subgraph Specialization_Layer ["Specialization Track A"]
        MLFQ["MLFQ Scheduler (Q0: Quantum=2, Q1: Quantum=4, Q2: Quantum=8)<br/>Dynamic Demotion & Anti-Starvation Boost"]
    end

    subgraph Core_OS_Subsystems ["Core Operating System Subsystems"]
        RR["Layer 5: Round Robin Scheduler (Fixed Quantum)"]
        ReadyQ["Layer 4: Ready Queue (Ring Buffer O(1))"]
        TCB["Layer 3: Task Management (TCB, CpuContext, States)"]
        Sync["Layer 7: Synchronization (Spinlock, Mutex, AtomicBool)"]
        Mem["Layer 8: Memory Management (Bump & Free-List Coalescing)"]
        Diag["Layer 2: Structured Console & Diagnostics Logger"]
    end

    subgraph Hardware_Layer ["Hardware & Emulation Layer"]
        Timer["Layer 6: System Timer (100 Hz Periodic Interrupts)"]
        HAL["Layer 1: Hardware Abstraction Layer (HAL) & Boot Entry"]
        RAM["Physical RAM / Memory Arena (64 KiB)"]
    end

    App --> MLFQ
    App --> RR
    MLFQ --> ReadyQ
    RR --> ReadyQ
    ReadyQ --> TCB
    TCB --> Sync
    TCB --> Mem
    Timer -->|Periodic Tick / Involuntary Preempt| MLFQ
    Timer -->|Periodic Tick / Involuntary Preempt| RR
    HAL --> RAM
    HAL --> Diag
    HAL --> Timer
```

---

## 3. Kernel Boot & Initialization Control Flow (Layer 1 & 2)

The execution flow begins with early hardware initialization and advances incrementally through memory partitioning, timer activation, and task dispatching:

```mermaid
sequenceDiagram
    autonumber
    actor Bootloader
    participant HAL as Hardware Abstraction (HAL)
    participant Console as Diagnostic Console
    participant Memory as Memory Subsystem
    participant Timer as System Timer
    participant Sched as CPU Scheduler
    participant Tasks as Task Control Block

    Bootloader->>HAL: kernel_entry()
    HAL->>Console: print_banner(), set_log_level(Debug)
    Console-->>HAL: Console active on Serial MMIO
    HAL->>Memory: Initialize 64 KiB Physical Arena
    Memory->>Memory: Partition Arena (16 KiB Bump, 48 KiB FreeList)
    HAL->>Timer: Start Periodic Timer (100 Hz, 10ms/tick)
    HAL->>Sched: Initialize Ready Queue & Schedulers
    HAL->>Tasks: Create Tasks (CPU1, IO, CPU2, Mixed)
    Tasks->>Sched: Enqueue Tasks into Q0 / Ready Queue
    HAL->>HAL: enable_interrupts()
    HAL->>Sched: Enter Multitasking Dispatch Loop
```

---

## 4. Task State Machine (Layer 3)

Tasks progress through four strict operational states: `READY`, `RUNNING`, `BLOCKED`, and `TERMINATED`:

```mermaid
stateDiagram-v2
    [*] --> READY: Task Created (TCB Initialized)
    
    READY --> RUNNING: Scheduler Dispatches Task (Context Switch)
    
    RUNNING --> READY: Quantum Expired (Involuntary Preempt)
    RUNNING --> READY: Voluntary Yield (task_yield)
    
    RUNNING --> BLOCKED: I/O Request or Contended Lock (task_block)
    BLOCKED --> READY: I/O Complete / Lock Acquired (unblock_task)
    
    RUNNING --> TERMINATED: Burst Completed (burst_remaining == 0)
    TERMINATED --> [*]: TCB Metrics Preserved for Diagnostics
```

---

## 5. Multi-Level Feedback Queue (MLFQ) Priority Flow (Track A)

The MLFQ specialization employs three priority queues with varying quanta to balance responsiveness and CPU throughput:

```mermaid
flowchart TD
    NewTask["New Task Arrival"] --> Q0["Queue 0 (Highest Priority, Quantum = 2 ticks)"]
    
    Q0 -->|Dispatched| CPU0["CPU Execution"]
    CPU0 -->|Yields for I/O before 2 ticks| Q0
    CPU0 -->|Consumes full 2 ticks without yield| Q1["Queue 1 (Medium Priority, Quantum = 4 ticks)"]
    
    Q1 -->|Dispatched| CPU1["CPU Execution"]
    CPU1 -->|Yields for I/O before 4 ticks| Q1
    CPU1 -->|Consumes full 4 ticks without yield| Q2["Queue 2 (Lowest Priority, Quantum = 8 ticks / FCFS)"]
    
    Q2 -->|Dispatched| CPU2["CPU Execution"]
    CPU2 -->|Yields for I/O| Q2
    CPU2 -->|Consumes 8 ticks| Q2
    
    Boost["Periodic Priority Boost (Every 25 ticks)"] -.->|Promote all tasks back to top| Q0
```

### MLFQ Governing Rules:
1. **Rule 1 (Priority Selection)**: If $\text{Priority}(A) < \text{Priority}(B)$, Task $A$ runs ($Q_0$ runs before $Q_1$, which runs before $Q_2$).
2. **Rule 2 (Round Robin within Queue)**: If $\text{Priority}(A) == \text{Priority}(B)$, Tasks $A$ and $B$ alternate in Round Robin using the queue's quantum.
3. **Rule 3 (Demotion on Quantum Expiry)**: If a task consumes its time allotment without relinquishing the CPU, it is demoted to the lower queue ($Q_0 \to Q_1 \to Q_2$).
4. **Rule 4 (I/O-Friendly Retention)**: If a task voluntarily yields CPU (e.g. initiating simulated I/O), it retains its priority level.
5. **Rule 5 (Priority Boost / Anti-Starvation)**: Every $S = 25$ ticks, all active tasks in the system are boosted back to $Q_0$. This prevents starvation for compute-intensive jobs and adapts if a task transitions from CPU-bound to interactive.

---

## 6. Memory Subsystem Layout (Layer 8)

The 64 KiB memory arena is partitioned into early-boot and dynamic regions:

```text
+------------------------------------+--------------------------------------------------+
|      Bump Allocator (16 KiB)       |           Free-List Allocator (48 KiB)           |
+------------------------------------+--------------------------------------------------+
| Sequential early boot structures   | Dynamic task buffers with header & coalescing    |
| (Page tables, TCB arrays, stacks)  | [Header][Payload] -> [Header][Payload] -> Free   |
+------------------------------------+--------------------------------------------------+
0x0000                               0x4000                                             0x10000
```

### Free-List Block Structure & Coalescing:
```text
+-----------------------+---------------------+-----------------------+---------------------+
| BlockHeader (24 B)    | Payload Data (N B)  | BlockHeader (24 B)    | Payload Data (M B)  |
| - magic: 0xDEADBEEF   |                     | - magic: 0xDEADBEEF   |                     |
| - size: N bytes       |                     | - size: M bytes       |                     |
| - is_free: bool       |                     | - is_free: bool       |                     |
| - next: *mut Header   |                     | - next: *mut Header   |                     |
+-----------------------+---------------------+-----------------------+---------------------+
```
When two contiguous blocks both have `is_free == true`, the allocator's `coalesce()` procedure merges them into a single larger block, resetting `size = N + size_of::<BlockHeader>() + M`, completely eliminating external fragmentation between adjacent allocations.
