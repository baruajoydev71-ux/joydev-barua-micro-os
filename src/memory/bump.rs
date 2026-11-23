//! Bump (Linear / Arena) Kernel Allocator
//!
//! Provides fast O(1) sequential allocations within a fixed memory arena.
//! Useful during early kernel bootstrap before full dynamic allocators are active.

use core::alloc::Layout;

#[derive(Debug, PartialEq, Eq)]
pub enum AllocError {
    OutOfMemory,
    InvalidLayout,
    InvalidPointer,
}

pub struct BumpAllocator {
    heap_start: usize,
    heap_end: usize,
    next: usize,
    allocations: usize,
}

impl BumpAllocator {
    /// Creates a new bump allocator over a given memory address range.
    ///
    /// # Safety
    /// The caller must ensure that the address range `[heap_start, heap_end)`
    /// is valid, unused, and accessible.
    pub const unsafe fn new(heap_start: usize, heap_end: usize) -> Self {
        Self {
            heap_start,
            heap_end,
            next: heap_start,
            allocations: 0,
        }
    }

    /// Allocates a block with the specified layout.
    pub fn allocate(&mut self, layout: Layout) -> Result<*mut u8, AllocError> {
        let align = layout.align();
        let size = layout.size();

        // Calculate aligned start address
        let alloc_start = (self.next + align - 1) & !(align - 1);
        let alloc_end = match alloc_start.checked_add(size) {
            Some(end) => end,
            None => return Err(AllocError::OutOfMemory),
        };

        if alloc_end > self.heap_end {
            Err(AllocError::OutOfMemory)
        } else {
            self.next = alloc_end;
            self.allocations += 1;
            Ok(alloc_start as *mut u8)
        }
    }

    /// Resets the allocator pointer back to the beginning of the heap.
    ///
    /// # Safety
    /// All previously allocated references must no longer be in use.
    pub unsafe fn reset(&mut self) {
        self.next = self.heap_start;
        self.allocations = 0;
    }

    pub fn used_bytes(&self) -> usize {
        self.next - self.heap_start
    }

    pub fn available_bytes(&self) -> usize {
        self.heap_end - self.next
    }

    pub fn total_bytes(&self) -> usize {
        self.heap_end - self.heap_start
    }

    pub fn allocation_count(&self) -> usize {
        self.allocations
    }
}
