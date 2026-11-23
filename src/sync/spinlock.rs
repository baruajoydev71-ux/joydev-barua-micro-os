//! Spinlock Kernel Synchronization Primitive
//!
//! Implements Layer 7: Kernel Synchronization.
//! Provides mutual exclusion via atomic test-and-set with memory ordering,
//! RAII guard release on drop, and contention measurement metrics.

use core::cell::UnsafeCell;
use core::fmt;
use core::ops::{Deref, DerefMut};
use core::sync::atomic::{AtomicBool, AtomicU64, Ordering};

pub struct Spinlock<T: ?Sized> {
    locked: AtomicBool,
    acquisitions: AtomicU64,
    contentions: AtomicU64,
    spin_cycles: AtomicU64,
    data: UnsafeCell<T>,
}

unsafe impl<T: ?Sized + Send> Sync for Spinlock<T> {}
unsafe impl<T: ?Sized + Send> Send for Spinlock<T> {}

impl<T> Spinlock<T> {
    pub const fn new(value: T) -> Self {
        Self {
            locked: AtomicBool::new(false),
            acquisitions: AtomicU64::new(0),
            contentions: AtomicU64::new(0),
            spin_cycles: AtomicU64::new(0),
            data: UnsafeCell::new(value),
        }
    }

    pub fn into_inner(self) -> T {
        self.data.into_inner()
    }
}

impl<T: ?Sized> Spinlock<T> {
    /// Attempts to acquire the lock without spinning.
    /// Returns `Some(SpinlockGuard)` on success, or `None` if currently locked.
    pub fn try_lock(&self) -> Option<SpinlockGuard<'_, T>> {
        // Compare-and-swap (false -> true) with Acquire ordering
        if self
            .locked
            .compare_exchange(false, true, Ordering::Acquire, Ordering::Relaxed)
            .is_ok()
        {
            self.acquisitions.fetch_add(1, Ordering::Relaxed);
            Some(SpinlockGuard { lock: self })
        } else {
            None
        }
    }

    /// Acquires the lock, spinning until available.
    /// Instruments contention and spin cycles for performance evaluation.
    pub fn lock(&self) -> SpinlockGuard<'_, T> {
        let mut spins = 0u64;

        // Fast path: try acquiring immediately
        if self
            .locked
            .compare_exchange_weak(false, true, Ordering::Acquire, Ordering::Relaxed)
            .is_err()
        {
            // Contention occurred
            self.contentions.fetch_add(1, Ordering::Relaxed);

            // Spin-wait loop
            loop {
                spins += 1;
                // Spin using read-only check first to reduce cache coherence bus traffic
                while self.locked.load(Ordering::Relaxed) {
                    core::hint::spin_loop();
                }

                // Attempt atomic acquisition
                if self
                    .locked
                    .compare_exchange_weak(false, true, Ordering::Acquire, Ordering::Relaxed)
                    .is_ok()
                {
                    break;
                }
            }
        }

        self.spin_cycles.fetch_add(spins, Ordering::Relaxed);
        self.acquisitions.fetch_add(1, Ordering::Relaxed);

        SpinlockGuard { lock: self }
    }

    pub fn is_locked(&self) -> bool {
        self.locked.load(Ordering::Relaxed)
    }

    pub fn contention_count(&self) -> u64 {
        self.contentions.load(Ordering::Relaxed)
    }

    pub fn acquisition_count(&self) -> u64 {
        self.acquisitions.load(Ordering::Relaxed)
    }

    pub fn total_spin_cycles(&self) -> u64 {
        self.spin_cycles.load(Ordering::Relaxed)
    }

    pub fn reset_metrics(&self) {
        self.acquisitions.store(0, Ordering::Relaxed);
        self.contentions.store(0, Ordering::Relaxed);
        self.spin_cycles.store(0, Ordering::Relaxed);
    }
}

pub struct SpinlockGuard<'a, T: ?Sized> {
    lock: &'a Spinlock<T>,
}

impl<'a, T: ?Sized> Deref for SpinlockGuard<'a, T> {
    type Target = T;

    fn deref(&self) -> &Self::Target {
        // SAFETY: The guard represents exclusive ownership while locked is true.
        unsafe { &*self.lock.data.get() }
    }
}

impl<'a, T: ?Sized> DerefMut for SpinlockGuard<'a, T> {
    fn deref_mut(&mut self) -> &mut Self::Target {
        // SAFETY: The guard guarantees unique mutable access while locked is true.
        unsafe { &mut *self.lock.data.get() }
    }
}

impl<'a, T: ?Sized> Drop for SpinlockGuard<'a, T> {
    fn drop(&mut self) {
        // Release the lock with Release ordering so all memory operations
        // inside the critical section become visible before unlock.
        self.lock.locked.store(false, Ordering::Release);
    }
}

impl<T: ?Sized + fmt::Debug> fmt::Debug for Spinlock<T> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self.try_lock() {
            Some(guard) => f
                .debug_struct("Spinlock")
                .field("data", &&*guard)
                .field("acquisitions", &self.acquisition_count())
                .field("contentions", &self.contention_count())
                .finish(),
            None => f
                .debug_struct("Spinlock")
                .field("data", &"<locked>")
                .field("contentions", &self.contention_count())
                .finish(),
        }
    }
}
