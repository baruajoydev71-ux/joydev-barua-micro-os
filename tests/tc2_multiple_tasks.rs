//! TC2 – Multiple Tasks (3-5 controlled heterogeneous tasks)
//! Evaluates scheduling fairness across mixed CPU and I/O workloads.

use micro_os::scheduler::{MlfqScheduler, Scheduler};
use micro_os::task::{TaskControlBlock, TaskKind};

#[test]
fn test_tc2_heterogeneous_workload() {
    let mut mlfq = MlfqScheduler::new();

    let t1 = TaskControlBlock::new(1, "CPU-1", 6, 0, TaskKind::CpuBound, 0);
    let t2 = TaskControlBlock::new(2, "IO-1", 4, 0, TaskKind::IoBound { io_interval: 1, io_duration: 2 }, 0);
    let t3 = TaskControlBlock::new(3, "CPU-2", 8, 0, TaskKind::CpuBound, 0);
    let t4 = TaskControlBlock::new(4, "Mixed-1", 6, 0, TaskKind::Mixed, 0);

    assert!(mlfq.add_task(t1).is_ok());
    assert!(mlfq.add_task(t2).is_ok());
    assert!(mlfq.add_task(t3).is_ok());
    assert!(mlfq.add_task(t4).is_ok());

    let mut ticks = 0;
    while !mlfq.is_complete() && ticks < 200 {
        ticks += 1;
        mlfq.tick(ticks);
    }

    assert!(mlfq.is_complete(), "All 4 tasks must terminate");
    let metrics = mlfq.metrics();
    assert_eq!(metrics.tasks_completed, 4);
    assert!(metrics.cpu_utilization > 50.0);
}
