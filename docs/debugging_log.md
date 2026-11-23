# Micro-OS Kernel Debugging Log
## Engineering Issue Resolution & Hypothesis-Driven Debugging (Section 21)

> **Debugging Methodology**: *Observe $\to$ Localize $\to$ Hypothesize $\to$ Instrument $\to$ Modify $\to$ Test $\to$ Reproduce*

---

### Incident 1: Heap Fragmentation & Stale Magic Pointers During Coalescing
- **Target**: Memory Allocator Subsystem (`src/memory/freelist.rs`)
- **Observation**: After allocating and freeing multiple 64-byte and 128-byte blocks, an allocation of 180 bytes failed with `OutOfMemory` even though total free memory was over 48 KiB.
- **Localization**: `FreeListAllocator::allocate()` traversed the free list but could not find a single contiguous block of size $\ge 180$ bytes.
- **Hypothesis**: Deallocated blocks were marked `is_free = true` but adjacent free chunks were never merged, causing high external fragmentation (over 62.5%). Furthermore, old block headers inside merged spans retained valid magic keys, leading to potential stale dereferences.
- **Instrumentation**: Added `KernelDiagnostics::emit_trace("MEM_STATUS", ...)` to output free block list addresses and sizes before and after deallocation.
- **Modification**:
  1. Implemented a two-pointer `coalesce()` routine that verifies physical contiguous adjacency:
     $$\text{address}(\text{curr}) + \text{header\_size} + \text{curr.size} == \text{address}(\text{next})$$
  2. If adjacent, merged `curr.size += header_size + next.size`, updated `curr.next = next.next`, and explicitly cleared the absorbed block's magic key: `(*next).magic = 0;`.
- **Test & Reproduction**: Re-ran allocation sequence; adjacent blocks coalesced into a single 49,128-byte block, dropping external fragmentation to 0.0%. Verified under TC5.

---

### Incident 2: Memory Bus Contention & High Spin Cycles in Spinlock
- **Target**: Kernel Synchronization (`src/sync/spinlock.rs`)
- **Observation**: Contended spinlock acquisitions exhibited excessive CPU bus cycles and high memory controller thrashing.
- **Localization**: `Spinlock::lock()` repeatedly executed `compare_exchange_weak` in a tight loop.
- **Hypothesis**: Issuing atomic Read-Modify-Write (RMW) instructions on every cycle repeatedly invalidates the CPU cache line across the cache coherence bus.
- **Instrumentation**: Added `AtomicU64` spin-cycle counters (`self.spin_cycles`) to quantify cycles spent in the contended loop.
- **Modification**: Introduced the *test-and-test-and-set* pattern:
  ```rust
  // Read-only spin (shared cache hit, zero bus traffic)
  while self.locked.load(Ordering::Relaxed) {
      core::hint::spin_loop();
  }
  // Attempt exclusive acquisition only when observed free
  if self.locked.compare_exchange_weak(false, true, Ordering::Acquire, Ordering::Relaxed).is_ok() {
      break;
  }
  ```
- **Test & Reproduction**: Spin cycles per acquisition dropped significantly, and lock contention measurement was verified via `shared_resource.contention_count()`.

---

### Incident 3: Starvation of Long CPU-Bound Tasks in MLFQ
- **Target**: Scheduler Specialization (`src/scheduler/mlfq.rs`)
- **Observation**: When testing a high-density workload with mixed CPU and I/O tasks, `Task-CPU2` (burst = 12) suffered extreme waiting latency and made zero progress while short tasks cycled in $Q_0$.
- **Localization**: `Task-CPU2` had been demoted to $Q_2$. As long as $Q_0$ or $Q_1$ contained any ready tasks (such as recurring I/O tasks), Rule 1 prevented $Q_2$ from ever being selected.
- **Hypothesis**: Without dynamic priority aging or global priority boosting, lower queues suffer unbounded starvation in the presence of continuous interactive arrivals.
- **Instrumentation**: Logged `task.waiting_ticks` on every scheduler tick; observed `Task-CPU2.waiting_ticks` increasing continuously while other tasks terminated.
- **Modification**: Implemented Rule 5 (Anti-Starvation Priority Boost):
  ```rust
  if current_tick.saturating_sub(self.last_boost_tick) >= BOOST_INTERVAL {
      self.priority_boost();
      self.last_boost_tick = current_tick;
  }
  ```
  Every 25 ticks, all active tasks in $Q_1$ and $Q_2$ are flushed back into $Q_0$ and their priority is reset.
- **Test & Reproduction**: Re-tested workload; `Task-CPU2` regained CPU access at tick 25 and completed with a balanced Jain's Fairness Index of 0.9419.

---

### Incident 4: Ready Queue Index Wrap-Around on High Task Density
- **Target**: Ready Queue Ring Buffer (`src/task/queue.rs`)
- **Observation**: Under the 16-task stress test (TC4), tasks were occasionally dropped from the ready queue, leading to premature `AllTasksCompleted`.
- **Localization**: `TaskQueue::remove()` incorrectly updated `self.tail` when filtering out tasks during priority migrations.
- **Hypothesis**: The removal filter copied retained elements to a linear buffer but failed to reset `head = 0`, causing the circular index math `(head + i) % MAX_TASKS` to misalign.
- **Instrumentation**: Added assertions checking `self.count == (self.tail - self.head + MAX_TASKS) % MAX_TASKS` after every mutation.
- **Modification**: Standardized `remove()` to reconstruct the contiguous array starting from index 0:
  ```rust
  self.items = new_items;
  self.head = 0;
  self.tail = new_count;
  self.count = new_count;
  ```
- **Test & Reproduction**: Executed TC4 with 16 concurrent tasks; all 16 tasks were successfully tracked and completed without dropping.

---

### Incident 5: Double-Free Vulnerability in Dynamic Memory
- **Target**: Free-List Allocator Defensive Security (`src/memory/freelist.rs`)
- **Observation**: In early versions, passing an already-freed pointer to `deallocate()` corrupted the free list's forward pointers, causing an infinite loop.
- **Localization**: The allocator blindly prepended the freed block to `self.head` without checking `block.is_free`.
- **Hypothesis**: An unverified deallocation creates circular loops in intrusive linked lists.
- **Instrumentation**: Added validation checks on block header metadata before processing.
- **Modification**:
  ```rust
  if (*block).is_free {
      return Err(AllocError::InvalidPointer); // Intercept double-free
  }
  (*block).is_free = true;
  ```
- **Test & Reproduction**: Tested under TC5; calling `deallocate(ptr)` a second time reliably returns `Err(AllocError::InvalidPointer)` without corrupting kernel state.
