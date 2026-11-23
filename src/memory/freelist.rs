//! Free-List Kernel Memory Allocator with Coalescing
//!
//! Implements dynamic heap management with block headers, first-fit / best-fit
//! search, block splitting, contiguous free block coalescing, and fragmentation metrics.

use core::alloc::Layout;
use core::mem;
use super::bump::AllocError;

const BLOCK_MAGIC: u32 = 0xDEADBEEF;

#[repr(C)]
pub struct BlockHeader {
    pub magic: u32,
    pub size: usize, // Size of payload (excluding header)
    pub is_free: bool,
    pub next: *mut BlockHeader,
}

pub struct FreeListAllocator {
    heap_start: usize,
    heap_size: usize,
    head: *mut BlockHeader,
    allocated_bytes: usize,
    allocation_count: usize,
    deallocation_count: usize,
}

impl FreeListAllocator {
    /// Initializes a Free-List Allocator over a designated memory buffer.
    ///
    /// # Safety
    /// The caller must ensure `[heap_start, heap_start + heap_size)` is valid
    /// physical or simulated memory with appropriate alignment.
    pub unsafe fn new(heap_start: usize, heap_size: usize) -> Result<Self, AllocError> {
        let header_size = mem::size_of::<BlockHeader>();
        if heap_size <= header_size {
            return Err(AllocError::OutOfMemory);
        }

        // Align heap start to 8 bytes
        let aligned_start = (heap_start + 7) & !7;
        let effective_size = heap_size.saturating_sub(aligned_start - heap_start);

        let initial_block = aligned_start as *mut BlockHeader;
        (*initial_block).magic = BLOCK_MAGIC;
        (*initial_block).size = effective_size - header_size;
        (*initial_block).is_free = true;
        (*initial_block).next = core::ptr::null_mut();

        Ok(Self {
            heap_start: aligned_start,
            heap_size: effective_size,
            head: initial_block,
            allocated_bytes: 0,
            allocation_count: 0,
            deallocation_count: 0,
        })
    }

    /// Allocates a memory block using First-Fit policy.
    pub fn allocate(&mut self, layout: Layout) -> Result<*mut u8, AllocError> {
        let align = layout.align().max(mem::align_of::<usize>());
        let requested_size = layout.size().max(align);
        let header_size = mem::size_of::<BlockHeader>();

        let mut curr = self.head;

        while !curr.is_null() {
            unsafe {
                let block = &mut *curr;
                if block.magic != BLOCK_MAGIC {
                    return Err(AllocError::InvalidPointer);
                }

                if block.is_free && block.size >= requested_size {
                    // Check if block can be split
                    let leftover = block.size.saturating_sub(requested_size);
                    if leftover > header_size + 16 {
                        // Split block
                        let split_addr = (curr as usize) + header_size + requested_size;
                        let split_block = split_addr as *mut BlockHeader;

                        (*split_block).magic = BLOCK_MAGIC;
                        (*split_block).size = leftover - header_size;
                        (*split_block).is_free = true;
                        (*split_block).next = block.next;

                        block.size = requested_size;
                        block.next = split_block;
                    }

                    block.is_free = false;
                    self.allocated_bytes += block.size;
                    self.allocation_count += 1;

                    let payload_ptr = (curr as usize + header_size) as *mut u8;
                    return Ok(payload_ptr);
                }

                curr = block.next;
            }
        }

        Err(AllocError::OutOfMemory)
    }

    /// Deallocates a memory block and coalesces adjacent free blocks.
    pub fn deallocate(&mut self, ptr: *mut u8) -> Result<(), AllocError> {
        if ptr.is_null() {
            return Ok(());
        }

        let header_size = mem::size_of::<BlockHeader>();
        let block_addr = (ptr as usize).saturating_sub(header_size);

        if block_addr < self.heap_start || block_addr >= self.heap_start + self.heap_size {
            return Err(AllocError::InvalidPointer);
        }

        let block = block_addr as *mut BlockHeader;

        unsafe {
            if (*block).magic != BLOCK_MAGIC {
                return Err(AllocError::InvalidPointer);
            }

            if (*block).is_free {
                // Double free detection!
                return Err(AllocError::InvalidPointer);
            }

            (*block).is_free = true;
            self.allocated_bytes = self.allocated_bytes.saturating_sub((*block).size);
            self.deallocation_count += 1;

            // Coalesce adjacent free blocks
            self.coalesce();
        }

        Ok(())
    }

    /// Merges adjacent free blocks to mitigate external fragmentation.
    pub fn coalesce(&mut self) {
        let mut curr = self.head;
        let header_size = mem::size_of::<BlockHeader>();

        while !curr.is_null() {
            unsafe {
                let next = (*curr).next;
                if !next.is_null() && (*curr).is_free && (*next).is_free {
                    let expected_next_addr = (curr as usize) + header_size + (*curr).size;
                    // Check if adjacent in memory
                    if expected_next_addr == (next as usize) {
                        (*curr).size += header_size + (*next).size;
                        (*curr).next = (*next).next;
                        // Invalidate old block magic to avoid stale pointers
                        (*next).magic = 0;
                        continue;
                    }
                }
                curr = (*curr).next;
            }
        }
    }

    /// Computes memory and fragmentation statistics.
    pub fn stats(&self) -> MemoryStats {
        let mut total_free = 0usize;
        let mut largest_free = 0usize;
        let mut free_blocks = 0usize;
        let mut allocated_blocks = 0usize;

        let mut curr = self.head;
        while !curr.is_null() {
            unsafe {
                if (*curr).is_free {
                    total_free += (*curr).size;
                    if (*curr).size > largest_free {
                        largest_free = (*curr).size;
                    }
                    free_blocks += 1;
                } else {
                    allocated_blocks += 1;
                }
                curr = (*curr).next;
            }
        }

        let ext_frag = if total_free > 0 {
            1.0 - (largest_free as f64 / total_free as f64)
        } else {
            0.0
        };

        MemoryStats {
            heap_capacity: self.heap_size,
            allocated_bytes: self.allocated_bytes,
            free_bytes: total_free,
            allocated_blocks,
            free_blocks,
            largest_free_block: largest_free,
            external_fragmentation: ext_frag,
            allocations_total: self.allocation_count,
            deallocations_total: self.deallocation_count,
        }
    }
}

#[derive(Debug, Clone, Copy)]
pub struct MemoryStats {
    pub heap_capacity: usize,
    pub allocated_bytes: usize,
    pub free_bytes: usize,
    pub allocated_blocks: usize,
    pub free_blocks: usize,
    pub largest_free_block: usize,
    pub external_fragmentation: f64,
    pub allocations_total: usize,
    pub deallocations_total: usize,
}
