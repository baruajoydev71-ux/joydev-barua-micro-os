//! Kernel Diagnostics, Trace Instrumentation & State Reporting
//!
//! Implements Layer 2 and Layer 9: Structured diagnostic event emission
//! compatible with Python trace parsers and benchmark evaluators.

use crate::scheduler::SchedulerMetrics;

pub struct KernelDiagnostics;

impl KernelDiagnostics {
    /// Emit a structured machine-readable trace line
    pub fn emit_trace(tick: u64, event: &str, fields: &str) {
        #[cfg(feature = "std")]
        {
            println!("[TRACE:{:06}] {} {}", tick, event, fields);
        }
        #[cfg(not(feature = "std"))]
        {
            let _ = (tick, event, fields);
        }
    }

    /// Display formatted banner on kernel startup
    pub fn print_banner(cpu: &str, ram_start: usize, ram_size: usize) {
        #[cfg(feature = "std")]
        {
            println!("\x1b[1;36m");
            println!(r#"  __  __ _                     ___  ____  "#);
            println!(r#" |  \/  (_) ___ _ __ ___      / _ \/ ___| "#);
            println!(r#" | |\/| | |/ __| '__/ _ \ ___| | | \___ \ "#);
            println!(r#" | |  | | | (__| | | (_) |___| |_| |___) |"#);
            println!(r#" |_|  |_|_|\___|_|  \___/     \___/|____/ "#);
            println!("\x1b[0m");
            println!("=======================================================");
            println!(" CA-6 Educational Micro-OS Kernel (Rust)");
            println!(" Target Architecture : {}", cpu);
            println!(" Physical Memory Pool: 0x{:X} - 0x{:X} ({} KiB)", ram_start, ram_start + ram_size, ram_size / 1024);
            println!(" Kernel Version      : 0.1.0-ca6 (Round Robin + MLFQ)");
            println!(" Diagnostics Output  : Serial / Console Active");
            println!("=======================================================\n");
        }
    }

    /// Display summary performance table
    pub fn print_metrics(name: &str, metrics: &SchedulerMetrics) {
        #[cfg(feature = "std")]
        {
            println!("\n=======================================================");
            println!(" SCHEDULER PERFORMANCE EVALUATION: {}", name);
            println!("=======================================================");
            println!(" Total Simulation Ticks  : {:>8}", metrics.total_ticks);
            println!(" CPU Idle Ticks          : {:>8}", metrics.idle_ticks);
            println!(" Total Context Switches  : {:>8}", metrics.total_context_switches);
            println!(" Tasks Completed         : {:>8}", metrics.tasks_completed);
            println!(" CPU Utilization         : {:>8.2} %", metrics.cpu_utilization);
            println!(" Average Response Time   : {:>8.2} ticks", metrics.avg_response_time);
            println!(" Average Waiting Time    : {:>8.2} ticks", metrics.avg_waiting_time);
            println!(" Average Turnaround Time : {:>8.2} ticks", metrics.avg_turnaround_time);
            println!(" Jain's Fairness Index   : {:>8.4} (1.0 = optimal)", metrics.fairness_index);
            println!("=======================================================\n");
        }
    }
}
