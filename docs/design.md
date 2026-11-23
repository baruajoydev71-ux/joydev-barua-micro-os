# Micro-OS Kernel Design & `unsafe` Rust Justification

## 1. Design Principles

The design of **Micro-OS** follows three fundamental systems-engineering imperatives:
1. **Mechanism Visibility**: OS mechanisms must produce measurable, structured trace logs (`TASK_SWITCH`, `QUANTUM_EXPIRED`, `SYNC_ACQUIRE`, `MEM_ALLOC`) that can be parsed and analyzed mathematically.
2. **Deterministic Reproducibility**: Given an identical task arrival sequence and quantum parameters, kernel state transitions and scheduler decisions must be 100% bitwise deterministic.
3. **Safety and Isolation**: Safe Rust abstractions enclose all raw pointer operations and low-level hardware interactions. Every `unsafe` block must state explicit safety invariants.

---

## 2. Low-Level `unsafe` Rust Audit & Justification

In accordance with Section 26 of the CA-6 Course Specification, every usage of `unsafe` in Micro-OS is constrained, audited, and encapsulated:

| File & Location | `unsafe` Operation | Why It Is Necessary | Stated Safety Invariant & Assumption |
|---|---|---|---|
| `src/kernel/hal.rs` | `unsafe { MEMORY_ARENA.bytes.as_mut_ptr() }` | Raw pointer acquisition of physical RAM buffer | Arena is static, 4096-byte page aligned, initialized at compile time, and not moved. |
| `src/sync/spinlock.rs` | `unsafe { &*self.lock.data.get() }` | Dereference of `UnsafeCell<T>` inside RAII `SpinlockGuard` | `Spinlock::lock()` atomically verifies `locked == false` via `compare_exchange` with `Acquire` ordering before constructing guard. Mutually exclusive. |
| `src/sync/mutex.rs` | `unsafe { &mut *self.lock.data.get() }` | Mutable dereference in `MutexGuard` | Acquisition verified atomically; only the single owning task holding `locked == true` accesses data. |
| `src/memory/bump.rs` | `unsafe fn new(...)` & `unsafe fn reset(...)` | Address arithmetic across physical address range | Caller guarantees memory address range `[start, end)` is valid physical RAM and no existing references outlive a reset. |
| `src/memory/freelist.rs` | `unsafe { (*curr).next }` & block header pointers | Linked list block traversal and pointer arithmetic | Headers contain `magic == 0xDEADBEEF`. Pointer arithmetic strictly bounded within `[heap_start, heap_start + heap_size)`. |
| `src/memory/freelist.rs` | Split block payload dereference | Constructing new `BlockHeader` in split space | Allocator calculates `split_addr = curr + header_size + requested_size`, ensuring split block header fits within leftover space. |

### RAII Guard Pattern for Spinlocks:
```rust
// Safe abstraction: the consumer NEVER writes unsafe code
let mut guard = spinlock.lock();
guard.increment(10);
// Lock automatically released when guard goes out of scope via Drop!
```

---

## 3. Subsystem Design Decisions & Trade-Offs

### 3.1 Dual-Target Architecture (`no_std` + Simulator HAL)
- **Problem**: Full bare-metal kernels targeting QEMU require external toolchains (`x86_64-unknown-none`, `nasm`, `qemu-system-x86_64`), preventing automated unit testing and creating environment friction.
- **Solution**: The kernel logic is written in `#![no_std]` core Rust (`core::sync::atomic`, `core::ptr`, `core::mem`). A modular Hardware Abstraction Layer (HAL) emulates hardware timer interrupts, CPU registers, and MMIO serial logging.
- **Result**: The Micro-OS runs deterministically on any platform, supports native `cargo test` integration suites, and outputs serial traces directly to files.

### 3.2 Scheduling: Round Robin (Core) vs MLFQ (Specialization)
- **Round Robin Trade-Off**:
  - *Advantage*: Absolute fairness for CPU-bound tasks of equal length; no task starves.
  - *Disadvantage*: Inefficient for heterogeneous workloads. Long CPU jobs penalize short interactive I/O jobs, resulting in poor average response time.
- **MLFQ Trade-Off**:
  - *Advantage*: High priority for I/O tasks ensures near-zero response time ($1.75$ ticks vs $3.50$ ticks). Larger quanta at lower priority queues ($Q_1=4, Q_2=8$) reduce context-switch frequency from 14 to 11 switches.
  - *Starvation Defense*: Global priority boost every 25 ticks prevents low-priority CPU tasks from starving.

### 3.3 Memory Management: Bump vs Free-List with Coalescing
- **Bump Allocator**:
  - $O(1)$ allocation overhead; zero header space consumption.
  - Cannot free individual allocations; ideal for early-boot page tables and task arrays.
- **Free-List Allocator**:
  - Allows arbitrary `allocate()` and `deallocate()`.
  - Intrusive 24-byte headers store block size, free flag, and next pointer.
  - **Coalescing**: Merges adjacent free blocks during deallocation, mitigating external fragmentation from 62.5% down to 0.0% upon deallocation sweeps.
  - **Double-Free Interception**: Magic constant `0xDEADBEEF` and `is_free` validation instantly reject corrupted or double-freed pointers.

### 3.4 Concurrency: Test-and-Set Spinlock with Read-Only Spin
- **Cache-Conscious Spinning**:
  - Naive spinlocks repeatedly issue atomic `swap` instructions, saturating the system memory bus.
  - Our `Spinlock::lock()` issues a relaxed read-only test loop `while self.locked.load(Relaxed)` before re-attempting `compare_exchange_weak` with `Acquire` ordering.
  - This avoids memory bus thrashing while preserving strict mutual exclusion.
