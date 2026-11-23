//! TC6 – Repeatability: Deterministic OS Execution Verification
//! Executes identical workloads across separate kernel runs and verifies identical state.

use micro_os::scheduler::{MlfqScheduler, Scheduler};
use micro_os::task::{TaskControlBlock, TaskKind};

fn execute_run() -> (u64, u64, f64) {
    let mut mlfq = MlfqScheduler::new();

    let t1 = TaskControlBlock::new(1, "A", 10, 0, TaskKind::CpuBound, 0);
    let t2 = TaskControlBlock::new(2, "B", 6, 0, TaskKind::IoBound { io_interval: 2, io_duration: 2 }, 0);
    let t3 = TaskControlBlock::new(3, "C", 8, 0, TaskKind::Mixed, 0);

    mlfq.add_task(t1).unwrap();
    mlfq.add_task(t2).unwrap();
    mlfq.add_task(t3).unwrap();

    let mut tick = 0;
    while !mlfq.is_complete() && tick < 300 {
        tick += 1;
        mlfq.tick(tick);
    }

    let m = mlfq.metrics();
    (m.total_ticks, m.total_context_switches, m.avg_waiting_time)
}

#[test]
fn test_tc6_deterministic_reproducibility() {
    let run1 = execute_run();
    let run2 = execute_run();
    let run3 = execute_run();

    assert_eq!(run1.0, run2.0, "Total ticks must match across runs");
    assert_eq!(run2.0, run3.0);

    assert_eq!(run1.1, run2.1, "Total switches must be bitwise identical");
    assert_eq!(run2.1, run3.1);

    assert!((run1.2 - run2.2).abs() < 1e-9, "Average waiting time must be deterministic");
}
