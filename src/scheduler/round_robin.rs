//! Round Robin CPU Scheduler (Core Layer 5)
//!
//! Implements fixed-quantum time-slicing with FIFO ready queue rotation,
//! timer-driven preemption, and task lifecycle metrics.

use super::traits::{Scheduler, SchedulerAction, SchedulerMetrics, SwitchReason};
use crate::task::{BlockReason, TaskControlBlock, TaskKind, TaskQueue, TaskState, MAX_TASKS};

pub struct RoundRobinScheduler {
    tasks: [Option<TaskControlBlock>; MAX_TASKS],
    task_count: usize,
    ready_queue: TaskQueue,
    current_task_id: Option<u32>,
    current_slice: u32,
    quantum: u32,
    total_switches: u64,
    idle_ticks: u64,
    total_ticks: u64,
}

impl RoundRobinScheduler {
    pub fn new(quantum: u32) -> Self {
        Self {
            tasks: [(); MAX_TASKS].map(|_| None),
            task_count: 0,
            ready_queue: TaskQueue::new(),
            current_task_id: None,
            current_slice: 0,
            quantum: quantum.max(1),
            total_switches: 0,
            idle_ticks: 0,
            total_ticks: 0,
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
}

impl Scheduler for RoundRobinScheduler {
    fn name(&self) -> &'static str {
        "Round Robin (Core)"
    }

    fn add_task(&mut self, mut task: TaskControlBlock) -> Result<(), &'static str> {
        if self.task_count >= MAX_TASKS {
            return Err("Max task limit reached");
        }

        task.quantum_remaining = self.quantum;
        let id = task.id;

        let mut empty_idx = None;
        for (i, slot) in self.tasks.iter().enumerate() {
            if slot.is_none() {
                empty_idx = Some(i);
                break;
            }
        }

        if let Some(idx) = empty_idx {
            self.tasks[idx] = Some(task);
            self.task_count += 1;
            self.ready_queue.push(id)?;
            Ok(())
        } else {
            Err("No available slot in task table")
        }
    }

    fn tick(&mut self, current_tick: u64) -> SchedulerAction {
        self.total_ticks += 1;

        // 1. Update blocked tasks: unblocked tasks are staged locally
        let mut unblocked_tasks = [None; MAX_TASKS];
        let mut unblock_count = 0;
        for slot in self.tasks.iter_mut() {
            if let Some(task) = slot {
                if let TaskState::Blocked(BlockReason::IoWait(remaining)) = task.state {
                    if remaining <= 1 {
                        task.state = TaskState::Ready;
                        unblocked_tasks[unblock_count] = Some(task.id);
                        unblock_count += 1;
                    } else {
                        task.state = TaskState::Blocked(BlockReason::IoWait(remaining - 1));
                    }
                }
            }
        }
        for i in 0..unblock_count {
            if let Some(task_id) = unblocked_tasks[i] {
                let _ = self.ready_queue.push(task_id);
            }
        }

        // 2. Increment waiting time for all ready tasks in ready queue
        for slot in self.tasks.iter_mut() {
            if let Some(task) = slot {
                if task.is_ready() && Some(task.id) != self.current_task_id {
                    task.waiting_ticks += 1;
                }
            }
        }

        // 3. Handle currently running task
        if let Some(curr_id) = self.current_task_id {
            let task_idx = self.find_task_index(curr_id);
            if let Some(idx) = task_idx {
                let mut task_terminated = false;
                let mut task_quantum_expired = false;
                let mut task_io_duration = None;

                // Scoped mutable borrow of the active task
                {
                    let task = self.tasks[idx].as_mut().unwrap();

                    // First scheduled recording
                    if task.first_scheduled_tick.is_none() {
                        task.first_scheduled_tick = Some(current_tick);
                    }

                    // Decrement burst and increment accumulated execution
                    task.burst_remaining = task.burst_remaining.saturating_sub(1);
                    task.cpu_ticks_accumulated += 1;
                    self.current_slice += 1;

                    // Simulated I/O behavior
                    if let TaskKind::IoBound { io_interval, io_duration } = task.kind {
                        if task.cpu_ticks_accumulated > 0
                            && task.cpu_ticks_accumulated % (io_interval as u64) == 0
                            && task.burst_remaining > 0
                        {
                            task_io_duration = Some(io_duration);
                        }
                    }

                    if task_io_duration.is_none() {
                        if task.burst_remaining == 0 {
                            task.state = TaskState::Terminated;
                            task.completion_tick = Some(current_tick);
                            task_terminated = true;
                        } else if self.current_slice >= self.quantum {
                            task.state = TaskState::Ready;
                            task_quantum_expired = true;
                        }
                    }
                } // End of mutable borrow for active task

                // 3a. Task requested I/O block
                if let Some(io_duration) = task_io_duration {
                    return self.block_current(BlockReason::IoWait(io_duration), current_tick);
                }

                // 3b. Task completed
                if task_terminated {
                    let prev_id = curr_id;
                    self.current_task_id = None;
                    self.current_slice = 0;

                    if let Some(next_id) = self.ready_queue.pop() {
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

                // 3c. Quantum expired (Preemption)
                if task_quantum_expired {
                    let prev_id = curr_id;
                    let _ = self.ready_queue.push(curr_id);
                    self.current_task_id = None;
                    self.current_slice = 0;

                    if let Some(next_id) = self.ready_queue.pop() {
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

                return SchedulerAction::Continue(curr_id);
            }
        }

        // 4. No task currently running: select next from ready queue
        if let Some(next_id) = self.ready_queue.pop() {
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
            }
            let _ = self.ready_queue.push(curr_id);
            self.current_task_id = None;
            self.current_slice = 0;

            if let Some(next_id) = self.ready_queue.pop() {
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
        self.tick(current_tick)
    }

    fn block_current(&mut self, reason: BlockReason, _current_tick: u64) -> SchedulerAction {
        if let Some(curr_id) = self.current_task_id {
            if let Some(idx) = self.find_task_index(curr_id) {
                let task = self.tasks[idx].as_mut().unwrap();
                task.state = TaskState::Blocked(reason);
            }
            let prev_id = curr_id;
            self.current_task_id = None;
            self.current_slice = 0;

            if let Some(next_id) = self.ready_queue.pop() {
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
        SchedulerAction::Idle
    }

    fn unblock_task(&mut self, task_id: u32, _current_tick: u64) {
        let mut should_enqueue = false;
        if let Some(idx) = self.find_task_index(task_id) {
            let task = self.tasks[idx].as_mut().unwrap();
            if task.is_blocked() {
                task.state = TaskState::Ready;
                should_enqueue = true;
            }
        }
        if should_enqueue {
            let _ = self.ready_queue.push(task_id);
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

        // Jain's Fairness Index: (sum(x_i))^2 / (n * sum(x_i^2))
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
