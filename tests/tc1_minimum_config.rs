//! TC1 – Minimum Configuration: Two Tasks
//! Verifies basic scheduling rotation and completion between two minimal tasks.

use micro_os::scheduler::{RoundRobinScheduler, Scheduler};
use micro_os::task::{TaskControlBlock, TaskKind};

#[test]
fn test_tc1_two_tasks_completion() {
    let mut rr = RoundRobinScheduler::new(2);
    let t1 = TaskControlBlock::new(1, "Task-A", 4, 0, TaskKind::CpuBound, 0);
    let t2 = TaskControlBlock::new(2, "Task-B", 4, 0, TaskKind::CpuBound, 0);

    assert!(rr.add_task(t1).is_ok());
    assert!(rr.add_task(t2).is_ok());

    let mut ticks = 0;
    while !rr.is_complete() && ticks < 100 {
        ticks += 1;
        rr.tick(ticks);
    }

    assert!(rr.is_complete(), "Both tasks should terminate");
    let metrics = rr.metrics();
    assert_eq!(metrics.tasks_completed, 2);
    assert!(metrics.total_context_switches >= 3, "Expected context switches between T1 and T2");
}
