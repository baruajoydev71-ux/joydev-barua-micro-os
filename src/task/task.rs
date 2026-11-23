//! Task Representation and Control Block (TCB)
//!
//! Implements Layer 3: Task Representation.
//! Contains task states, CPU register context, execution attributes,
//! and scheduling performance metrics.

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TaskState {
    Ready,
    Running,
    Blocked(BlockReason),
    Terminated,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BlockReason {
    ResourceWait,
    IoWait(u32), // Remaining ticks until I/O completes
    LockWait(u32), // Target mutex / resource ID
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TaskKind {
    CpuBound,
    IoBound { io_interval: u32, io_duration: u32 },
    Mixed,
    Synchronized { lock_target: u32 },
}

#[derive(Debug, Clone, Copy, Default)]
pub struct CpuContext {
    pub instruction_pointer: usize,
    pub stack_pointer: usize,
    pub register_r0: u64,
    pub register_r1: u64,
    pub flags: u32,
}

#[derive(Debug, Clone)]
pub struct TaskControlBlock {
    pub id: u32,
    pub name: &'static str,
    pub state: TaskState,
    pub priority: u8, // MLFQ priority: 0 = highest, 1 = medium, 2 = lowest
    pub kind: TaskKind,

    // Execution profile
    pub burst_remaining: u32,
    pub burst_total: u32,
    pub quantum_remaining: u32,
    pub current_work_slice: u32,

    // Timing and Metrics
    pub arrival_tick: u64,
    pub first_scheduled_tick: Option<u64>,
    pub completion_tick: Option<u64>,
    pub cpu_ticks_accumulated: u64,
    pub waiting_ticks: u64,
    pub context_switches: u64,

    // CPU execution context
    pub context: CpuContext,
}

impl TaskControlBlock {
    pub fn new(
        id: u32,
        name: &'static str,
        burst_total: u32,
        priority: u8,
        kind: TaskKind,
        arrival_tick: u64,
    ) -> Self {
        Self {
            id,
            name,
            state: TaskState::Ready,
            priority,
            kind,
            burst_remaining: burst_total,
            burst_total,
            quantum_remaining: 0,
            current_work_slice: 0,
            arrival_tick,
            first_scheduled_tick: None,
            completion_tick: None,
            cpu_ticks_accumulated: 0,
            waiting_ticks: 0,
            context_switches: 0,
            context: CpuContext::default(),
        }
    }

    /// Computes task response time: ticks from arrival until first CPU execution.
    pub fn response_time(&self) -> Option<u64> {
        self.first_scheduled_tick.map(|t| t.saturating_sub(self.arrival_tick))
    }

    /// Computes task turnaround time: ticks from arrival until termination.
    pub fn turnaround_time(&self) -> Option<u64> {
        self.completion_tick.map(|t| t.saturating_sub(self.arrival_tick))
    }

    pub fn is_terminated(&self) -> bool {
        matches!(self.state, TaskState::Terminated)
    }

    pub fn is_ready(&self) -> bool {
        matches!(self.state, TaskState::Ready)
    }

    pub fn is_blocked(&self) -> bool {
        matches!(self.state, TaskState::Blocked(_))
    }
}
