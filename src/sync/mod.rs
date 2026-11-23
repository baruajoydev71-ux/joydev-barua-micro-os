pub mod mutex;
pub mod spinlock;

pub use mutex::{Mutex, MutexGuard};
pub use spinlock::{Spinlock, SpinlockGuard};

/// Demonstration helper: A shared counter to show race condition vs synchronized access
pub struct SharedCounter {
    pub value: u64,
    pub operations: u64,
}

impl SharedCounter {
    pub const fn new() -> Self {
        Self {
            value: 0,
            operations: 0,
        }
    }

    pub fn increment(&mut self, amount: u64) {
        let current = self.value;
        // Introduce artificial interleaved delay to induce race conditions if unsynchronized
        core::hint::black_box(current);
        self.value = current + amount;
        self.operations += 1;
    }
}
