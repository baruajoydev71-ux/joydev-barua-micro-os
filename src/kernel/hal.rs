//! Hardware Abstraction Layer (HAL) & Boot Initialization
//!
//! Implements Layer 1: Boot and Hardware Interaction.
//! Sets up physical/simulated address spaces, interrupt controller,
//! timer frequencies, and CPU context management.

use core::sync::atomic::{AtomicBool, Ordering};

pub const SIMULATED_RAM_SIZE: usize = 64 * 1024; // 64 KiB Kernel Memory Arena

#[repr(align(4096))]
pub struct PhysicalMemoryArena {
    pub bytes: [u8; SIMULATED_RAM_SIZE],
}

impl PhysicalMemoryArena {
    pub const fn new() -> Self {
        Self {
            bytes: [0; SIMULATED_RAM_SIZE],
        }
    }
}

pub static mut MEMORY_ARENA: PhysicalMemoryArena = PhysicalMemoryArena::new();
static INTERRUPTS_ENABLED: AtomicBool = AtomicBool::new(false);

pub struct HardwareAbstraction;

impl HardwareAbstraction {
    /// Boot sequence: Initialize CPU, Memory, and Interrupt Controller
    pub fn initialize() -> (&'static str, usize) {
        // Clear interrupt flags during early boot
        INTERRUPTS_ENABLED.store(false, Ordering::SeqCst);

        // Verify simulated RAM boundaries
        let ram_ptr = unsafe { MEMORY_ARENA.bytes.as_mut_ptr() };
        let ram_addr = ram_ptr as usize;

        ("x86_64 / Educational Virtual CPU", ram_addr)
    }

    pub fn enable_interrupts() {
        INTERRUPTS_ENABLED.store(true, Ordering::SeqCst);
    }

    pub fn disable_interrupts() {
        INTERRUPTS_ENABLED.store(false, Ordering::SeqCst);
    }

    pub fn interrupts_enabled() -> bool {
        INTERRUPTS_ENABLED.load(Ordering::Relaxed)
    }

    pub fn get_memory_range() -> (usize, usize) {
        let base = unsafe { MEMORY_ARENA.bytes.as_mut_ptr() as usize };
        (base, base + SIMULATED_RAM_SIZE)
    }
}
