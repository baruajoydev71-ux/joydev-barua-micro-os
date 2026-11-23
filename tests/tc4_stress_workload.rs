//! TC4 – Stress Case: High Task Density (16 concurrent tasks)
//! Evaluates queue saturation, anti-starvation aging, and stability under heavy workload.

use micro_os::scheduler::{MlfqScheduler, Scheduler};
use micro_os::task::{TaskControlBlock, TaskKind};

#[test]
fn test_tc4_high_density_workload() {
    let mut mlfq = MlfqScheduler::new();

    for i in 1..=16 {
        let burst = 3 + (i % 4);
        let kind = if i % 2 == 0 {
            TaskKind::CpuBound
        } else {
            TaskKind::IoBound { io_interval: 2, io_duration: 1 }
        };
        assert!(mlfq.add_task(TaskControlBlock::new(i as u32, "Stress", burst, 0, kind, 0)).is_ok());
    }

    let mut ticks = 0;
    while !mlfq.is_complete() && ticks < 1000 {
        ticks += 1;
        mlfq.tick(ticks);
    }

    assert!(mlfq.is_complete(), "All 16 stress tasks should complete without hanging");
    let metrics = mlfq.metrics();
    assert_eq!(metrics.tasks_completed, 16);
    assert!(metrics.fairness_index > 0.80, "Aging mechanism must preserve fair CPU share");
}
