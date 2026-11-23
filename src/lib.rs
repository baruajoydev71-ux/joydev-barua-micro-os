//! Educational Micro-OS Library (CA-6)
//!
//! Exposes modular kernel subsystems for unit and integration testing.

#![cfg_attr(not(feature = "std"), no_std)]

#[cfg(not(feature = "std"))]
extern crate alloc;

pub mod drivers;
pub mod kernel;
pub mod memory;
pub mod scheduler;
pub mod sync;
pub mod task;
pub mod timer;

pub use kernel::Kernel;
