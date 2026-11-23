# Micro-OS Formal Test Plan & Validation Evidence (TC1 – TC6)

## 1. Testing Philosophy & Progression

In accordance with Section 15 & 16 of the CA-6 Course Specification, validation follows a three-level verification hierarchy:
1. **Level 1 (Unit Testing)**: Isolated component validation (ReadyQueue circular push/pop, Allocator layout alignment, Spinlock atomic acquire).
2. **Level 2 (Mechanism Testing)**: Timer-driven preemption, context switching frequency, coalescing sweep.
3. **Level 3 (Integration Testing)**: Full lifecycle execution: Boot $\to$ Initialization $\to$ Multitasking $\to$ Synchronization $\to$ Memory Reclamation $\to$ Metrics Export.

---

## 2. Test Case Specifications (TC1 – TC6)

### TC1 – Minimum Configuration (Two Tasks)
- **Objective**: Verify fundamental cooperative and preemptive scheduling rotation between the minimum possible task set.
- **Workload**: Two CPU-bound tasks (`Task-A`: burst=4, `Task-B`: burst=4) under Round Robin with Quantum = 2 ticks.
- **Expected Behavior**:
  - `Task-A` executes ticks 1–2 $\to$ Quantum expires $\to$ Preempted.
  - `Task-B` executes ticks 3–4 $\to$ Quantum expires $\to$ Preempted.
  - `Task-A` executes ticks 5–6 $\to$ Terminates.
  - `Task-B` executes ticks 7–8 $\to$ Terminates.
- **Verification Assertions**:
  ```rust
  assert!(rr.is_complete());
  assert_eq!(metrics.tasks_completed, 2);
  assert!(metrics.total_context_switches >= 3);
  ```

---

### TC2 – Multiple Tasks (Heterogeneous Workload)
- **Objective**: Evaluate scheduling stability and fairness across 4 distinct tasks combining compute-intensive, I/O-intensive, and mixed profiles.
- **Workload**:
  - `Task-1` (CPU-Bound, burst=6)
  - `Task-2` (I/O-Bound, burst=4, sleeps every 1 tick for 2 ticks)
  - `Task-3` (CPU-Bound, burst=8)
  - `Task-4` (Mixed, burst=6)
- **Expected Behavior**: All 4 tasks terminate correctly; I/O task preserves top priority; CPU utilization exceeds 50%.
- **Verification Assertions**:
  ```rust
  assert!(mlfq.is_complete());
  assert_eq!(metrics.tasks_completed, 4);
  assert!(metrics.cpu_utilization > 50.0);
  ```

---

### TC3 – Boundary Case (Smallest Meaningful Quantum: Q = 1 tick)
- **Objective**: Stress-test the timer interrupt and context-switch mechanism with rapid alternating preemption.
- **Workload**: Two tasks (`T1`: burst=3, `T2`: burst=3) with Quantum = 1 tick.
- **Expected Behavior**: Preemption occurs on every single tick ($T1 \to T2 \to T1 \to T2 \to T1 \to T2$), yielding at least 5 context switches without corruption.
- **Verification Assertions**:
  ```rust
  assert!(rr.is_complete());
  assert!(metrics.total_context_switches >= 5);
  ```

---

### TC4 – Stress Case (High Task Density: 16 Concurrent Tasks)
- **Objective**: Test ready queue capacity limits and ensure the anti-starvation aging mechanism prevents CPU monopolization under heavy loads.
- **Workload**: 16 concurrent tasks with variable burst lengths (3 to 6 ticks) in MLFQ.
- **Expected Behavior**: No deadlocks or dropped tasks; all 16 tasks reach `TERMINATED` state; Jain's fairness index exceeds 0.80 due to periodic priority boosting.
- **Verification Assertions**:
  ```rust
  assert!(mlfq.is_complete());
  assert_eq!(metrics.tasks_completed, 16);
  assert!(metrics.fairness_index > 0.80);
  ```

---

### TC5 – Failure Case (Defensive Error Handling)
- **Objective**: Confirm the kernel defensively rejects invalid operations without panicking or corrupting memory.
- **Scenarios Evaluated**:
  1. **Heap Exhaustion (OOM)**: Requesting 1024 bytes from a 256-byte pool returns `Err(AllocError::OutOfMemory)`.
  2. **Double Free Detection**: Calling `deallocate()` twice on the same pointer returns `Err(AllocError::InvalidPointer)`.
  3. **Spinlock Mutual Exclusion**: Verifying `try_lock()` returns `None` while the lock is already held.
- **Verification Assertions**:
  ```rust
  assert_eq!(alloc.allocate(huge_layout), Err(AllocError::OutOfMemory));
  assert_eq!(alloc.deallocate(ptr), Err(AllocError::InvalidPointer));
  assert!(spinlock.try_lock().is_none());
  ```

---

### TC6 – Repeatability (Bitwise Determinism Test)
- **Objective**: Execute identical workloads across multiple independent kernel instantiations and verify 100% bitwise reproducibility.
- **Workload**: 3 tasks running under MLFQ across Run 1, Run 2, and Run 3.
- **Verification Assertions**:
  ```rust
  assert_eq!(run1.total_ticks, run2.total_ticks);
  assert_eq!(run2.total_ticks, run3.total_ticks);
  assert_eq!(run1.total_context_switches, run2.total_context_switches);
  assert!((run1.avg_waiting_time - run2.avg_waiting_time).abs() < 1e-9);
  ```

---

## 3. Reproduction Command Reference

### Running the Formal Verification Suite:
```bash
cargo run -- --test-all
```
*Expected Output: `All 6 test cases passed successfully!`*

### Running Unit & Integration Tests via Cargo:
```bash
cargo test
```
*Executes all unit tests in `src/` and integration tests in `tests/`.*
