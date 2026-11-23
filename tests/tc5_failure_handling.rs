//! TC5 – Failure Case: Memory Limits, Invalid Deallocations, and Sync Safety
//! Verifies robust defensive programming when handling invalid operations.

use core::alloc::Layout;
use micro_os::memory::{AllocError, FreeListAllocator};
use micro_os::sync::{SharedCounter, Spinlock};

#[test]
fn test_tc5_controlled_failures() {
    // 1. Allocator Out of Memory
    let mut mem_pool = [0u8; 256];
    let mut alloc = unsafe { FreeListAllocator::new(mem_pool.as_mut_ptr() as usize, 256).unwrap() };

    let oversized = Layout::from_size_align(1024, 8).unwrap();
    let res = alloc.allocate(oversized);
    assert_eq!(res, Err(AllocError::OutOfMemory), "Must fail on heap exhaustion");

    // 2. Double Free Detection
    let valid_layout = Layout::from_size_align(32, 8).unwrap();
    let ptr = alloc.allocate(valid_layout).unwrap();
    assert!(alloc.deallocate(ptr).is_ok());

    let double_free_res = alloc.deallocate(ptr);
    assert_eq!(double_free_res, Err(AllocError::InvalidPointer), "Must detect double free");

    // 3. Synchronization Safety: Mutex / Spinlock Mutual Exclusion
    let lock = Spinlock::new(SharedCounter::new());
    {
        let mut guard1 = lock.lock();
        guard1.increment(5);
        assert!(lock.try_lock().is_none(), "Lock cannot be acquired reentrantly without release");
    }
    // After dropping guard1, lock is available again
    assert!(lock.try_lock().is_some());
}
