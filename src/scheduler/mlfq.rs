//! Multi-Level Feedback Queue (MLFQ) Scheduler (Track A Specialization)
//!
//! Implements a 3-level feedback queue with dynamic priority demotion,
//! I/O-friendly priority retention, and global priority boost (aging) to prevent starvation.

use super::traits::{Scheduler, SchedulerAction, SchedulerMetrics, SwitchReason};
use crate::task::{BlockReason, TaskControlBlock, TaskKind, TaskQueue, TaskState, MAX_TASKS};

pub const NUM_QUEUES: usize = 3;
pub const QUEUE_QUANTA: [u32; NUM_QUEUES] = [2, 4, 8];
pub const BOOST_INTERVAL: u64 = 25; // Global priority boost every 25 ticks to prevent starvation

pub struct MlfqScheduler {
    tasks: [Option<TaskControlBlock>; MAX_TASKS],
    task_count: usize,
    queues: [TaskQueue; NUM_QUEUES],
    current_task_id: Option<u32>,
    current_slice: u32,
    total_switches: u64,
    idle_ticks: u64,
    total_ticks: u64,
    last_boost_tick: u64,
    boost_count: u64,
    demotion_count: u64,
}

impl MlfqScheduler {
    pub fn new() -> Self {
        Self {
            tasks: [(); MAX_TASKS].map(|_| None),
            task_count: 0,
            queues: [TaskQueue::new(), TaskQueue::new(), TaskQueue::new()],
            current_task_id: None,
            current_slice: 0,
            total_switches: 0,
            idle_ticks: 0,
            total_ticks: 0,
            last_boost_tick: 0,
            boost_count: 0,
            demotion_count: 0,
        }
    }

    fn find_task_index(&self, task_id: u32) -> Option<usize> {
        self.tasks.iter().position(|slot| {
            if let Some(t) = slot {
                t.id == task_id
            } else {
                false
            }
        })
    }

    /// Selects the highest priority ready task from Q0, Q1, then Q2.
    fn pop_highest_priority_task(&mut self) -> Option<(u32, usize)> {
        for prio in 0..NUM_QUEUES {
            if let Some(task_id) = self.queues[prio].pop() {
                return Some((task_id, prio));
            }
        }
        None
    }

    /// Global Priority Boost (Rule 5): Promotes all non-terminated tasks back to Q0.
    pub fn priority_boost(&mut self) {
        self.boost_count += 1;

        // Drain Q1 and Q2 into Q0
        for prio in 1..NUM_QUEUES {
            while let Some(task_id) = self.queues[prio].pop() {
                let _ = self.queues[0].push(task_id);
            }
        }

        // Reset priority of all active tasks to 0
        for slot in self.tasks.iter_mut() {
            if let Some(task) = slot {
                if !task.is_terminated() {
                    task.priority = 0;
                    task.quantum_remaining = QUEUE_QUANTA[0];
                }
            }
        }
    }

    pub fn boost_count(&self) -> u64 {
        self.boost_count
    }

    pub fn demotion_count(&self) -> u64 {
        self.demotion_count
    }
}

impl Scheduler for MlfqScheduler {
    fn name(&self) -> &'static str {
        "Multi-Level Feedback Queue (Specialization)"
    }

    fn add_task(&mut self, mut task: TaskControlBlock) -> Result<(), &'static str> {
        if self.task_count >= MAX_TASKS {
            return Err("Max task limit reached");
        }

        let prio = (task.priority as usize).min(NUM_QUEUES - 1);
        task.priority = prio as u8;
        task.quantum_remaining = QUEUE_QUANTA[prio];
        let id = task.id;

        for slot in self.tasks.iter_mut() {
            if slot.is_none() {
                *slot = Some(task);
                self.task_count += 1;
                self.queues[prio].push(id)?;
                return Ok(());
            }
        }

        Err("No available slot in task table")
    }

    fn tick(&mut self, current_tick: u64) -> SchedulerAction {
        self.total_ticks += 1;

        // 1. Periodic Anti-Starvation Boost (Aging)
        if current_tick.saturating_sub(self.last_boost_tick) >= BOOST_INTERVAL {
            self.priority_boost();
            self.last_boost_tick = current_tick;
        }

        // 2. Update blocked tasks
        for slot in self.tasks.iter_mut() {
            if let Some(task) = slot {
                if let TaskState::Blocked(BlockReason::IoWait(remaining)) = task.state {
                    if remaining <= 1 {
                        task.state = TaskState::Ready;
                        let prio = (task.priority as usize).min(NUM_QUEUES - 1);
                        let _ = self.queues[prio].push(task.id);
                    } else {
                        task.state = TaskState::Blocked(BlockReason::IoWait(remaining - 1));
                    }
                }
            }
        }

        // 3. Accumulate waiting time for all ready tasks
        for slot in self.tasks.iter_mut() {
            if let Some(task) = slot {
                if task.is_ready() && Some(task.id) != self.current_task_id {
                    task.waiting_ticks += 1;
                }
            }
        }

        // 4. Handle currently running task
        if let Some(curr_id) = self.current_task_id {
            if let Some(idx) = self.find_task_index(curr_id) {
                let task = self.tasks[idx].as_mut().unwrap();

                if task.first_scheduled_tick.is_none() {
                    task.first_scheduled_tick = Some(current_tick);
                }

                task.burst_remaining = task.burst_remaining.saturating_sub(1);
                task.cpu_ticks_accumulated += 1;
                self.current_slice += 1;

                // Simulated I/O behavior: I/O tasks voluntarily yield before exhausting quantum
                if let TaskKind::IoBound { io_interval, io_duration } = task.kind {
                    if task.cpu_ticks_accumulated > 0 && task.cpu_ticks_accumulated % (io_interval as u64) == 0 && task.burst_remaining > 0 {
                        // Task keeps its current priority (Rule 4: I/O friendly)
                        return self.block_current(BlockReason::IoWait(io_duration), current_tick);
                    }
                }

                // Check completion
                if task.burst_remaining == 0 {
                    task.state = TaskState::Terminated;
                    task.completion_tick = Some(current_tick);
                    let prev_id = curr_id;
                    self.current_task_id = None;
                    self.current_slice = 0;

                    if let Some((next_id, _)) = self.pop_highest_priority_task() {
                        if let Some(next_idx) = self.find_task_index(next_id) {
                            let next_task = self.tasks[next_idx].as_mut().unwrap();
                            next_task.state = TaskState::Running;
                            next_task.context_switches += 1;
                            self.current_task_id = Some(next_id);
                            self.total_switches += 1;

                            return SchedulerAction::Switch {
                                previous: Some(prev_id),
                                next: next_id,
                                reason: SwitchReason::TaskTerminated,
                            };
                        }
                    }

                    if self.is_complete() {
                        return SchedulerAction::AllTasksCompleted;
                    } else {
                        return SchedulerAction::Idle;
                    }
                }

                let curr_prio = (task.priority as usize).min(NUM_QUEUES - 1);
                let quantum = QUEUE_QUANTA[curr_prio];

                // Check quantum expiration -> Demote to lower priority queue (Rule 3)
                if self.current_slice >= quantum {
                    let prev_id = curr_id;
                    task.state = TaskState::Ready;

                    // Demote priority if not already at lowest queue
                    if curr_prio < NUM_QUEUES - 1 {
                        task.priority = (curr_prio + 1) as u8;
                        self.demotion_count += 1;
                    }

                    let new_prio = task.priority as usize;
                    let _ = self.queues[new_prio].push(curr_id);
                    self.current_task_id = None;
                    self.current_slice = 0;

                    if let Some((next_id, _)) = self.pop_highest_priority_task() {
                        if let Some(next_idx) = self.find_task_index(next_id) {
                            let next_task = self.tasks[next_idx].as_mut().unwrap();
                            next_task.state = TaskState::Running;
                            next_task.context_switches += 1;
                            self.current_task_id = Some(next_id);
                            self.total_switches += 1;

                            return SchedulerAction::Switch {
                                previous: Some(prev_id),
                                next: next_id,
                                reason: SwitchReason::QuantumExpired,
                            };
                        }
                    }
                }

                // Check if a higher-priority task became ready (Preemption)
                for prio in 0..curr_prio {
                    if !self.queues[prio].is_empty() {
                        let prev_id = curr_id;
                        task.state = TaskState::Ready;
                        let _ = self.queues[curr_prio].push(curr_id);
                        self.current_task_id = None;
                        self.current_slice = 0;

                        let (next_id, _) = self.pop_highest_priority_task().unwrap();
                        let next_idx = self.find_task_index(next_id).unwrap();
                        let next_task = self.tasks[next_idx].as_mut().unwrap();
                        next_task.state = TaskState::Running;
                        next_task.context_switches += 1;
                        self.current_task_id = Some(next_id);
                        self.total_switches += 1;

                        return SchedulerAction::Switch {
                            previous: Some(prev_id),
                            next: next_id,
                            reason: SwitchReason::PreemptionHigherPriority,
                        };
                    }
                }

                return SchedulerAction::Continue(curr_id);
            }
        }

        // No task currently running: pop from highest priority queue
        if let Some((next_id, _)) = self.pop_highest_priority_task() {
            if let Some(next_idx) = self.find_task_index(next_id) {
                let next_task = self.tasks[next_idx].as_mut().unwrap();
                next_task.state = TaskState::Running;
                next_task.context_switches += 1;
                if next_task.first_scheduled_tick.is_none() {
                    next_task.first_scheduled_tick = Some(current_tick);
                }
                self.current_task_id = Some(next_id);
                self.current_slice = 0;
                self.total_switches += 1;

                return SchedulerAction::Switch {
                    previous: None,
                    next: next_id,
                    reason: SwitchReason::PreemptionHigherPriority,
                };
            }
        }

        if self.is_complete() {
            SchedulerAction::AllTasksCompleted
        } else {
            self.idle_ticks += 1;
            SchedulerAction::Idle
        }
    }

    fn yield_current(&mut self, current_tick: u64) -> SchedulerAction {
        if let Some(curr_id) = self.current_task_id {
            if let Some(idx) = self.find_task_index(curr_id) {
                let task = self.tasks[idx].as_mut().unwrap();
                task.state = TaskState::Ready;
                let prio = (task.priority as usize).min(NUM_QUEUES - 1);
                let _ = self.queues[prio].push(curr_id);
                self.current_task_id = None;
                self.current_slice = 0;

                if let Some((next_id, _)) = self.pop_highest_priority_task() {
                    if let Some(next_idx) = self.find_task_index(next_id) {
                        let next_task = self.tasks[next_idx].as_mut().unwrap();
                        next_task.state = TaskState::Running;
                        next_task.context_switches += 1;
                        self.current_task_id = Some(next_id);
                        self.total_switches += 1;

                        return SchedulerAction::Switch {
                            previous: Some(curr_id),
                            next: next_id,
                            reason: SwitchReason::TaskYielded,
                        };
                    }
                }
            }
        }
        self.tick(current_tick)
    }

    fn block_current(&mut self, reason: BlockReason, _current_tick: u64) -> SchedulerAction {
        if let Some(curr_id) = self.current_task_id {
            if let Some(idx) = self.find_task_index(curr_id) {
                let task = self.tasks[idx].as_mut().unwrap();
                task.state = TaskState::Blocked(reason);
                let prev_id = curr_id;
                self.current_task_id = None;
                self.current_slice = 0;

                if let Some((next_id, _)) = self.pop_highest_priority_task() {
                    if let Some(next_idx) = self.find_task_index(next_id) {
                        let next_task = self.tasks[next_idx].as_mut().unwrap();
                        next_task.state = TaskState::Running;
                        next_task.context_switches += 1;
                        self.current_task_id = Some(next_id);
                        self.total_switches += 1;

                        return SchedulerAction::Switch {
                            previous: Some(prev_id),
                            next: next_id,
                            reason: SwitchReason::TaskBlocked,
                        };
                    }
                }

                return SchedulerAction::Idle;
            }
        }
        SchedulerAction::Idle
    }

    fn unblock_task(&mut self, task_id: u32, _current_tick: u64) {
        if let Some(idx) = self.find_task_index(task_id) {
            let task = self.tasks[idx].as_mut().unwrap();
            if task.is_blocked() {
                task.state = TaskState::Ready;
                let prio = (task.priority as usize).min(NUM_QUEUES - 1);
                let _ = self.queues[prio].push(task_id);
            }
        }
    }

    fn current_task_id(&self) -> Option<u32> {
        self.current_task_id
    }

    fn get_task(&self, task_id: u32) -> Option<&TaskControlBlock> {
        self.find_task_index(task_id).and_then(|idx| self.tasks[idx].as_ref())
    }

    fn get_task_mut(&mut self, task_id: u32) -> Option<&mut TaskControlBlock> {
        if let Some(idx) = self.find_task_index(task_id) {
            self.tasks[idx].as_mut()
        } else {
            None
        }
    }

    fn is_complete(&self) -> bool {
        if self.task_count == 0 {
            return true;
        }
        self.tasks.iter().filter_map(|s| s.as_ref()).all(|t| t.is_terminated())
    }

    fn metrics(&self) -> SchedulerMetrics {
        let mut total_waiting = 0u64;
        let mut total_turnaround = 0u64;
        let mut total_response = 0u64;
        let mut completed_count = 0usize;
        let mut active_count = 0usize;

        let mut sum_cpu = 0.0f64;
        let mut sum_sq_cpu = 0.0f64;

        for slot in self.tasks.iter().filter_map(|s| s.as_ref()) {
            active_count += 1;
            total_waiting += slot.waiting_ticks;

            let cpu = slot.cpu_ticks_accumulated as f64;
            sum_cpu += cpu;
            sum_sq_cpu += cpu * cpu;

            if let Some(rt) = slot.response_time() {
                total_response += rt;
            }
            if let Some(tt) = slot.turnaround_time() {
                total_turnaround += tt;
                completed_count += 1;
            }
        }

        let avg_waiting = if active_count > 0 {
            total_waiting as f64 / active_count as f64
        } else {
            0.0
        };

        let avg_turnaround = if completed_count > 0 {
            total_turnaround as f64 / completed_count as f64
        } else {
            0.0
        };

        let avg_response = if active_count > 0 {
            total_response as f64 / active_count as f64
        } else {
            0.0
        };

        let cpu_util = if self.total_ticks > 0 {
            (self.total_ticks.saturating_sub(self.idle_ticks) as f64 / self.total_ticks as f64) * 100.0
        } else {
            0.0
        };

        let fairness = if active_count > 0 && sum_sq_cpu > 0.0 {
            (sum_cpu * sum_cpu) / (active_count as f64 * sum_sq_cpu)
        } else {
            1.0
        };

        SchedulerMetrics {
            total_ticks: self.total_ticks,
            idle_ticks: self.idle_ticks,
            total_context_switches: self.total_switches,
            tasks_completed: completed_count,
            avg_waiting_time: avg_waiting,
            avg_turnaround_time: avg_turnaround,
            avg_response_time: avg_response,
            cpu_utilization: cpu_util,
            fairness_index: fairness,
        }
    }
}
