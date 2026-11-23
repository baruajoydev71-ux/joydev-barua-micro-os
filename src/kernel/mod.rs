pub mod diagnostics;
pub mod hal;

pub use diagnostics::KernelDiagnostics;
pub use hal::{HardwareAbstraction, SIMULATED_RAM_SIZE};

use crate::drivers::console::{LogLevel, CONSOLE};
use crate::memory::{BumpAllocator, FreeListAllocator};
use crate::scheduler::{MlfqScheduler, RoundRobinScheduler, Scheduler, SchedulerAction};
use crate::sync::{SharedCounter, Spinlock};
use crate::task::{BlockReason, TaskControlBlock, TaskKind};
use crate::timer::TIMER;
use core::alloc::Layout;

pub struct Kernel {
    pub bump_allocator: BumpAllocator,
    pub freelist_allocator: FreeListAllocator,
    pub shared_resource: Spinlock<SharedCounter>,
}

impl Kernel {
    /// Layer 1: Kernel Boot and Initialization
    pub fn boot() -> Self {
        let (cpu, ram_start) = HardwareAbstraction::initialize();
        let ram_size = SIMULATED_RAM_SIZE;

        KernelDiagnostics::print_banner(cpu, ram_start, ram_size);

        crate::kinfo!(0, "boot", "Starting Kernel Boot Sequence...");
        crate::kinfo!(0, "boot", "Hardware Abstraction Layer initialized.");

        // Allocate memory partition: First 16 KiB for Bump allocator, remaining 48 KiB for FreeList
        let bump_size = 16 * 1024;
        let bump_start = ram_start;
        let freelist_start = ram_start + bump_size;
        let freelist_size = ram_size - bump_size;

        crate::kinfo!(
            0,
            "memory",
            "Initializing Bump Allocator at 0x{:X} ({} KiB)...",
            bump_start,
            bump_size / 1024
        );
        let bump = unsafe { BumpAllocator::new(bump_start, bump_start + bump_size) };

        crate::kinfo!(
            0,
            "memory",
            "Initializing Free-List Allocator at 0x{:X} ({} KiB)...",
            freelist_start,
            freelist_size / 1024
        );
        let freelist = unsafe {
            FreeListAllocator::new(freelist_start, freelist_size)
                .expect("Failed to initialize FreeListAllocator")
        };

        crate::kinfo!(0, "timer", "Starting Periodic System Timer at 100 Hz...");
        TIMER.start();

        crate::kinfo!(0, "sync", "Initializing Kernel Synchronization primitives...");
        let shared = Spinlock::new(SharedCounter::new());

        crate::kinfo!(0, "boot", "Kernel Initialization Complete. Enabling Interrupts.");
        HardwareAbstraction::enable_interrupts();

        Self {
            bump_allocator: bump,
            freelist_allocator: freelist,
            shared_resource: shared,
        }
    }

    /// Layer 10: Integrated Micro-OS Demonstration
    pub fn run_demonstration(&mut self, use_mlfq: bool) {
        crate::kinfo!(
            TIMER.get_ticks(),
            "kernel",
            "Launching Integrated Micro-OS Demonstration (Track: {})...",
            if use_mlfq { "MLFQ Specialization" } else { "Round Robin Core" }
        );

        // 1. Demonstrate Memory Subsystem Allocations
        crate::kinfo!(TIMER.get_ticks(), "memory", "Testing Dynamic Memory Allocation (Free-List)...");
        let layout_64 = Layout::from_size_align(64, 8).unwrap();
        let layout_128 = Layout::from_size_align(128, 8).unwrap();

        let ptr1 = self.freelist_allocator.allocate(layout_64).expect("Alloc 1 failed");
        KernelDiagnostics::emit_trace(
            TIMER.get_ticks(),
            "MEM_ALLOC",
            &format!("size=64 ptr=0x{:X}", ptr1 as usize),
        );

        let ptr2 = self.freelist_allocator.allocate(layout_128).expect("Alloc 2 failed");
        KernelDiagnostics::emit_trace(
            TIMER.get_ticks(),
            "MEM_ALLOC",
            &format!("size=128 ptr=0x{:X}", ptr2 as usize),
        );

        // Deallocate ptr1 and check coalescing
        self.freelist_allocator.deallocate(ptr1).expect("Dealloc ptr1 failed");
        KernelDiagnostics::emit_trace(
            TIMER.get_ticks(),
            "MEM_DEALLOC",
            &format!("ptr=0x{:X}", ptr1 as usize),
        );

        let mem_stats = self.freelist_allocator.stats();
        crate::kinfo!(
            TIMER.get_ticks(),
            "memory",
            "Heap Status: Allocated={} B, Free={} B, FreeBlocks={}, ExtFrag={:.2}%",
            mem_stats.allocated_bytes,
            mem_stats.free_bytes,
            mem_stats.free_blocks,
            mem_stats.external_fragmentation * 100.0
        );

        // 2. Demonstrate Synchronization (Spinlock Critical Section)
        crate::kinfo!(TIMER.get_ticks(), "sync", "Testing Kernel Spinlock Critical Section...");
        {
            let mut guard = self.shared_resource.lock();
            guard.increment(10);
            KernelDiagnostics::emit_trace(
                TIMER.get_ticks(),
                "SYNC_ACQUIRE",
                &format!("val={} contentions={}", guard.value, self.shared_resource.contention_count()),
            );
        }
        KernelDiagnostics::emit_trace(TIMER.get_ticks(), "SYNC_RELEASE", "lock released");

        // 3. Create Tasks and Run Scheduler
        crate::kinfo!(TIMER.get_ticks(), "task", "Populating Ready Queue with Multitasking Workload...");

        let mut scheduler: Box<dyn Scheduler> = if use_mlfq {
            Box::new(MlfqScheduler::new())
        } else {
            Box::new(RoundRobinScheduler::new(2)) // Quantum = 2 ticks
        };

        // Task 1: CPU-bound computation
        let t1 = TaskControlBlock::new(1, "Task-CPU1", 6, 0, TaskKind::CpuBound, TIMER.get_ticks());
        // Task 2: Interactive / I/O-bound (bursts of 2, then I/O wait)
        let t2 = TaskControlBlock::new(
            2,
            "Task-IO",
            5,
            0,
            TaskKind::IoBound { io_interval: 2, io_duration: 3 },
            TIMER.get_ticks(),
        );
        // Task 3: CPU-bound computation
        let t3 = TaskControlBlock::new(3, "Task-CPU2", 8, 0, TaskKind::CpuBound, TIMER.get_ticks());
        // Task 4: Synchronized task (performs work on shared resource)
        let t4 = TaskControlBlock::new(
            4,
            "Task-Sync",
            4,
            0,
            TaskKind::Synchronized { lock_target: 1 },
            TIMER.get_ticks(),
        );

        scheduler.add_task(t1).unwrap();
        scheduler.add_task(t2).unwrap();
        scheduler.add_task(t3).unwrap();
        scheduler.add_task(t4).unwrap();

        crate::kinfo!(
            TIMER.get_ticks(),
            "scheduler",
            "Executing Multitasking Loop using {}...",
            scheduler.name()
        );

        // Execution loop driven by periodic timer ticks
        while !scheduler.is_complete() {
            let tick = TIMER.step();
            let action = scheduler.tick(tick);

            match action {
                SchedulerAction::Switch { previous, next, reason } => {
                    let prev_str = match previous {
                        Some(p) => format!("Task-{}", p),
                        None => "None".to_string(),
                    };
                    let next_task = scheduler.get_task(next).unwrap();

                    crate::kdebug!(
                        tick,
                        "sched",
                        "Context Switch: {} -> {} (reason: {}, prio: {})",
                        prev_str,
                        next_task.name,
                        reason.as_str(),
                        next_task.priority
                    );

                    KernelDiagnostics::emit_trace(
                        tick,
                        "TASK_SWITCH",
                        &format!(
                            "prev={:?} next={} prio={} reason={}",
                            previous, next, next_task.priority, reason.as_str()
                        ),
                    );
                }
                SchedulerAction::Continue(id) => {
                    let task = scheduler.get_task(id).unwrap();
                    crate::ktrace!(
                        tick,
                        "cpu",
                        "Running {} (remaining: {}, prio: {})",
                        task.name,
                        task.burst_remaining,
                        task.priority
                    );
                }
                SchedulerAction::Idle => {
                    crate::ktrace!(tick, "cpu", "CPU Idle (waiting on I/O or tasks)");
                    KernelDiagnostics::emit_trace(tick, "CPU_IDLE", "state=waiting");
                }
                SchedulerAction::AllTasksCompleted => {
                    crate::kinfo!(tick, "scheduler", "All tasks in ready queue completed!");
                    break;
                }
            }
        }

        // Deallocate remaining memory
        let _ = self.freelist_allocator.deallocate(ptr2);

        // Print final metrics report
        let metrics = scheduler.metrics();
        KernelDiagnostics::print_metrics(scheduler.name(), &metrics);
    }
}
