//! Kernel Task Ready Queue Data Structure
//!
//! Implements Layer 4: Ready Queue.
//! Provides O(1) push, pop, inspection, and task lookup.

pub const MAX_TASKS: usize = 32;

#[derive(Debug)]
pub struct TaskQueue {
    items: [u32; MAX_TASKS],
    head: usize,
    tail: usize,
    count: usize,
}

impl TaskQueue {
    pub const fn new() -> Self {
        Self {
            items: [0; MAX_TASKS],
            head: 0,
            tail: 0,
            count: 0,
        }
    }

    pub fn is_empty(&self) -> bool {
        self.count == 0
    }

    pub fn is_full(&self) -> bool {
        self.count == MAX_TASKS
    }

    pub fn len(&self) -> usize {
        self.count
    }

    /// Enqueue a task ID at the tail of the queue.
    pub fn push(&mut self, task_id: u32) -> Result<(), &'static str> {
        if self.is_full() {
            return Err("Task queue is full");
        }
        self.items[self.tail] = task_id;
        self.tail = (self.tail + 1) % MAX_TASKS;
        self.count += 1;
        Ok(())
    }

    /// Dequeue a task ID from the head of the queue.
    pub fn pop(&mut self) -> Option<u32> {
        if self.is_empty() {
            return None;
        }
        let task_id = self.items[self.head];
        self.head = (self.head + 1) % MAX_TASKS;
        self.count -= 1;
        Some(task_id)
    }

    /// Inspect the task at the head of the queue without removing it.
    pub fn peek(&self) -> Option<u32> {
        if self.is_empty() {
            None
        } else {
            Some(self.items[self.head])
        }
    }

    /// Checks if a given task ID is currently queued.
    pub fn contains(&self, task_id: u32) -> bool {
        for i in 0..self.count {
            let idx = (self.head + i) % MAX_TASKS;
            if self.items[idx] == task_id {
                return true;
            }
        }
        false
    }

    /// Remove a specific task ID from the queue (e.g. on early termination or priority migration).
    pub fn remove(&mut self, task_id: u32) -> bool {
        let mut found = false;
        let mut new_items = [0u32; MAX_TASKS];
        let mut new_count = 0usize;

        for i in 0..self.count {
            let idx = (self.head + i) % MAX_TASKS;
            let current = self.items[idx];
            if current == task_id && !found {
                found = true;
            } else {
                new_items[new_count] = current;
                new_count += 1;
            }
        }

        if found {
            self.items = new_items;
            self.head = 0;
            self.tail = new_count;
            self.count = new_count;
        }

        found
    }

    /// Collect all task IDs currently in the queue for tracing/diagnostics.
    pub fn to_array(&self) -> ([u32; MAX_TASKS], usize) {
        let mut arr = [0u32; MAX_TASKS];
        for i in 0..self.count {
            let idx = (self.head + i) % MAX_TASKS;
            arr[i] = self.items[idx];
        }
        (arr, self.count)
    }
}
