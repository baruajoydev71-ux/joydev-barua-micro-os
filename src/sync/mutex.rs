//! Yield-Aware Kernel Mutex Primitive
//!
//! Unlike a pure spinlock, the Kernel Mutex yields CPU execution if the lock
//! is held by another task, preventing CPU starvation and lock-holder starvation
//! on single-core educational architectures.

use core::cell::UnsafeCell;
use core::ops::{Deref, DerefMut};
use core::sync::atomic::{AtomicBool, AtomicU32, AtomicU64, Ordering};

pub struct Mutex<T: ?Sized> {
    locked: AtomicBool,
    owner_task_id: AtomicU32,
    contentions: AtomicU64,
    data: UnsafeCell<T>,
}

unsafe impl<T: ?Sized + Send> Sync for Mutex<T> {}
unsafe impl<T: ?Sized + Send> Send for Mutex<T> {}

impl<T> Mutex<T> {
    pub const fn new(value: T) -> Self {
        Self {
            locked: AtomicBool::new(false),
            owner_task_id: AtomicU32::new(u32::MAX),
            contentions: AtomicU64::new(0),
            data: UnsafeCell::new(value),
        }
    }
}

impl<T: ?Sized> Mutex<T> {
    /// Attempts to acquire the mutex for the specified task ID.
    pub fn try_lock_by(&self, task_id: u32) -> Option<MutexGuard<'_, T>> {
        if self
            .locked
            .compare_exchange(false, true, Ordering::Acquire, Ordering::Relaxed)
            .is_ok()
        {
            self.owner_task_id.store(task_id, Ordering::Relaxed);
            Some(MutexGuard { lock: self })
        } else {
            None
        }
    }

    /// Records contention when a task cannot acquire the mutex immediately.
    pub fn record_contention(&self) {
        self.contentions.fetch_add(1, Ordering::Relaxed);
    }

    pub fn is_locked(&self) -> bool {
        self.locked.load(Ordering::Relaxed)
    }

    pub fn get_owner(&self) -> Option<u32> {
        if self.is_locked() {
            let id = self.owner_task_id.load(Ordering::Relaxed);
            if id != u32::MAX {
                Some(id)
            } else {
                None
            }
        } else {
            None
        }
    }

    pub fn contention_count(&self) -> u64 {
        self.contentions.load(Ordering::Relaxed)
    }
}

pub struct MutexGuard<'a, T: ?Sized> {
    lock: &'a Mutex<T>,
}

impl<'a, T: ?Sized> Deref for MutexGuard<'a, T> {
    type Target = T;

    fn deref(&self) -> &Self::Target {
        // SAFETY: Only one task holds the lock at any time.
        unsafe { &*self.lock.data.get() }
    }
}

impl<'a, T: ?Sized> DerefMut for MutexGuard<'a, T> {
    fn deref_mut(&mut self) -> &mut Self::Target {
        // SAFETY: Exclusive mutable access guaranteed by Mutex acquisition.
        unsafe { &mut *self.lock.data.get() }
    }
}

impl<'a, T: ?Sized> Drop for MutexGuard<'a, T> {
    fn drop(&mut self) {
        self.lock.owner_task_id.store(u32::MAX, Ordering::Relaxed);
        self.lock.locked.store(false, Ordering::Release);
    }
}
