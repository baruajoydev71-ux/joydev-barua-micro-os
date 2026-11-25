pub mod console;
pub mod wifi;

pub use console::{get_log_level, set_log_level, KernelConsole, LogLevel, CONSOLE};
pub use wifi::{AccessPoint, MacAddress, NetworkConfig, WifiDriver, WifiSecurity, WifiState};
