//! Scheduler Abstraction Traits and Lifecycle Events
//!
//! Defines the common scheduling interface for both the Core Round Robin
//! scheduler and the Specialization Track A Multi-Level Feedback Queue (MLFQ).

use crate::task::{BlockReason, TaskControlBlock};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SwitchReason {
    QuantumExpired,
    TaskYielded,
    TaskBlocked,
    TaskTerminated,
    PreemptionHigherPriority,
}

impl SwitchReason {
    pub fn as_str(&self) -> &'static str {
        match self {
            SwitchReason::QuantumExpired => "QUANTUM_EXPIRED",
            SwitchReason::TaskYielded => "VOLUNTARY_YIELD",
            SwitchReason::TaskBlocked => "TASK_BLOCKED",
            SwitchReason::TaskTerminated => "TASK_TERMINATED",
            SwitchReason::PreemptionHigherPriority => "PREEMPT_HIGHER_PRIORITY",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SchedulerAction {
    Continue(u32),
    Switch {
        previous: Option<u32>,
        next: u32,
        reason: SwitchReason,
    },
    Idle,
    AllTasksCompleted,
}

#[derive(Debug, Clone, Copy, Default)]
pub struct SchedulerMetrics {
    pub total_ticks: u64,
    pub idle_ticks: u64,
    pub total_context_switches: u64,
    pub tasks_completed: usize,
    pub avg_waiting_time: f64,
    pub avg_turnaround_time: f64,
    pub avg_response_time: f64,
    pub cpu_utilization: f64,
    pub fairness_index: f64, // Jain's Fairness Index
}

pub trait Scheduler {
    fn name(&self) -> &'static str;
    fn add_task(&mut self, task: TaskControlBlock) -> Result<(), &'static str>;
    fn tick(&mut self, current_tick: u64) -> SchedulerAction;
    fn yield_current(&mut self, current_tick: u64) -> SchedulerAction;
    fn block_current(&mut self, reason: BlockReason, current_tick: u64) -> SchedulerAction;
    fn unblock_task(&mut self, task_id: u32, current_tick: u64);
    fn current_task_id(&self) -> Option<u32>;
    fn get_task(&self, task_id: u32) -> Option<&TaskControlBlock>;
    fn get_task_mut(&mut self, task_id: u32) -> Option<&mut TaskControlBlock>;
    fn is_complete(&self) -> bool;
    fn metrics(&self) -> SchedulerMetrics;
}
