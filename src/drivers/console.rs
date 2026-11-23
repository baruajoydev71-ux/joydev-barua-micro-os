//! Console and Kernel Serial Diagnostics Driver
//!
//! Provides structured logging mechanisms for Layer 2 diagnostics.
//! Supports INFO, WARN, ERROR, DEBUG, and TRACE severity levels
//! with monotonic hardware tick timestamps.

use core::fmt::{self, Write};
use core::sync::atomic::{AtomicUsize, Ordering};

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum LogLevel {
    Trace = 0,
    Debug = 1,
    Info = 2,
    Warn = 3,
    Error = 4,
}

impl LogLevel {
    pub fn as_str(&self) -> &'static str {
        match self {
            LogLevel::Trace => "TRACE",
            LogLevel::Debug => "DEBUG",
            LogLevel::Info => "INFO ",
            LogLevel::Warn => "WARN ",
            LogLevel::Error => "ERROR",
        }
    }

    pub fn color_code(&self) -> &'static str {
        match self {
            LogLevel::Trace => "\x1b[90m", // Gray
            LogLevel::Debug => "\x1b[36m", // Cyan
            LogLevel::Info => "\x1b[32m",  // Green
            LogLevel::Warn => "\x1b[33m",  // Yellow
            LogLevel::Error => "\x1b[31m", // Red
        }
    }
}

static CURRENT_LOG_LEVEL: AtomicUsize = AtomicUsize::new(LogLevel::Debug as usize);

pub fn set_log_level(level: LogLevel) {
    CURRENT_LOG_LEVEL.store(level as usize, Ordering::Relaxed);
}

pub fn get_log_level() -> LogLevel {
    match CURRENT_LOG_LEVEL.load(Ordering::Relaxed) {
        0 => LogLevel::Trace,
        1 => LogLevel::Debug,
        2 => LogLevel::Info,
        3 => LogLevel::Warn,
        _ => LogLevel::Error,
    }
}

pub struct KernelConsole;

impl KernelConsole {
    pub const fn new() -> Self {
        Self
    }

    pub fn log(
        &self,
        level: LogLevel,
        tick: u64,
        subsystem: &str,
        args: fmt::Arguments,
    ) {
        if level < get_log_level() {
            return;
        }

        let reset = "\x1b[0m";
        let color = level.color_code();
        let level_str = level.as_str();

        // Format: [<ticks:06>] [LEVEL] (subsystem) message
        #[cfg(feature = "std")]
        {
            println!(
                "{}[{:06}] [{}] ({}) {}{}",
                color, tick, level_str, subsystem, args, reset
            );
        }

        #[cfg(not(feature = "std"))]
        {
            // In pure baremetal, write directly to serial MMIO port 0x3F8
            let _ = (color, tick, level_str, subsystem, args, reset);
        }
    }
}

pub static CONSOLE: KernelConsole = KernelConsole::new();

#[macro_export]
macro_rules! klog {
    ($level:expr, $tick:expr, $subsys:expr, $($arg:tt)*) => {
        $crate::drivers::console::CONSOLE.log(
            $level,
            $tick,
            $subsys,
            format_args!($($arg)*)
        )
    };
}

#[macro_export]
macro_rules! kinfo {
    ($tick:expr, $subsys:expr, $($arg:tt)*) => {
        $crate::klog!($crate::drivers::console::LogLevel::Info, $tick, $subsys, $($arg)*)
    };
}

#[macro_export]
macro_rules! kwarn {
    ($tick:expr, $subsys:expr, $($arg:tt)*) => {
        $crate::klog!($crate::drivers::console::LogLevel::Warn, $tick, $subsys, $($arg)*)
    };
}

#[macro_export]
macro_rules! kerror {
    ($tick:expr, $subsys:expr, $($arg:tt)*) => {
        $crate::klog!($crate::drivers::console::LogLevel::Error, $tick, $subsys, $($arg)*)
    };
}

#[macro_export]
macro_rules! kdebug {
    ($tick:expr, $subsys:expr, $($arg:tt)*) => {
        $crate::klog!($crate::drivers::console::LogLevel::Debug, $tick, $subsys, $($arg)*)
    };
}

#[macro_export]
macro_rules! ktrace {
    ($tick:expr, $subsys:expr, $($arg:tt)*) => {
        $crate::klog!($crate::drivers::console::LogLevel::Trace, $tick, $subsys, $($arg)*)
    };
}
