//! Hardware & Emulated Periodic Timer Subsystem
//!
//! Implements Layer 6: Timer-Driven Scheduling.
//! Tracks monotonic ticks and provides preemption interrupt triggers.

use core::sync::atomic::{AtomicBool, AtomicU64, Ordering};

pub struct SystemTimer {
    ticks: AtomicU64,
    frequency_hz: u32,
    enabled: AtomicBool,
}

impl SystemTimer {
    pub const fn new(frequency_hz: u32) -> Self {
        Self {
            ticks: AtomicU64::new(0),
            frequency_hz,
            enabled: AtomicBool::new(false),
        }
    }

    pub fn start(&self) {
        self.enabled.store(true, Ordering::SeqCst);
    }

    pub fn stop(&self) {
        self.enabled.store(false, Ordering::SeqCst);
    }

    pub fn is_enabled(&self) -> bool {
        self.enabled.load(Ordering::Relaxed)
    }

    pub fn get_ticks(&self) -> u64 {
        self.ticks.load(Ordering::Relaxed)
    }

    pub fn reset(&self) {
        self.ticks.store(0, Ordering::SeqCst);
    }

    /// Advance timer by 1 tick (representing 1 interrupt / time quantum quantum unit)
    pub fn step(&self) -> u64 {
        if self.is_enabled() {
            self.ticks.fetch_add(1, Ordering::SeqCst) + 1
        } else {
            self.ticks.load(Ordering::Relaxed)
        }
    }

    /// Convert tick count to simulated milliseconds
    pub fn ticks_to_ms(&self, ticks: u64) -> u64 {
        if self.frequency_hz == 0 {
            0
        } else {
            (ticks * 1000) / (self.frequency_hz as u64)
        }
    }

    pub fn get_frequency_hz(&self) -> u32 {
        self.frequency_hz
    }
}

pub static TIMER: SystemTimer = SystemTimer::new(100); // 100 Hz = 10ms per tick
