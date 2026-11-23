//! TC3 – Boundary Case: Smallest Meaningful Quantum (Q = 1 tick)
//! Verifies rapid context switching behavior and overhead tracking.

use micro_os::scheduler::{RoundRobinScheduler, Scheduler};
use micro_os::task::{TaskControlBlock, TaskKind};

#[test]
fn test_tc3_boundary_quantum_one() {
    let mut rr = RoundRobinScheduler::new(1); // 1-tick quantum
    let t1 = TaskControlBlock::new(1, "Rapid-A", 3, 0, TaskKind::CpuBound, 0);
    let t2 = TaskControlBlock::new(2, "Rapid-B", 3, 0, TaskKind::CpuBound, 0);

    rr.add_task(t1).unwrap();
    rr.add_task(t2).unwrap();

    let mut ticks = 0;
    while !rr.is_complete() && ticks < 50 {
        ticks += 1;
        rr.tick(ticks);
    }

    assert!(rr.is_complete());
    let metrics = rr.metrics();
    // With burst 3 each and quantum 1, total switches should be >= 5
    assert!(metrics.total_context_switches >= 5, "Every tick should trigger rotation");
}
