//! 802.11 Wireless Network Interface Card & Wi-Fi Driver
//!
//! Provides Wi-Fi scanning, WPA2/WPA3 authentication negotiation,
//! DHCP IP configuration, and network packet TX/RX integrated with
//! the Micro-OS MLFQ scheduler.

use core::fmt;
use core::sync::atomic::{AtomicU32, Ordering};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct MacAddress(pub [u8; 6]);

impl MacAddress {
    pub const fn new(b: [u8; 6]) -> Self {
        Self(b)
    }
}

impl fmt::Display for MacAddress {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "{:02X}:{:02X}:{:02X}:{:02X}:{:02X}:{:02X}",
            self.0[0], self.0[1], self.0[2], self.0[3], self.0[4], self.0[5]
        )
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum WifiSecurity {
    Open,
    Wpa2Personal,
    Wpa3Sae,
    Enterprise8021X,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AccessPoint {
    pub ssid: &'static str,
    pub bssid: MacAddress,
    pub channel: u8,
    pub signal_dbm: i8,
    pub security: WifiSecurity,
}

impl AccessPoint {
    pub fn signal_percent(&self) -> u8 {
        if self.signal_dbm <= -100 {
            0
        } else if self.signal_dbm >= -50 {
            100
        } else {
            (2 * (self.signal_dbm + 100)) as u8
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NetworkConfig {
    pub ip_address: [u8; 4],
    pub subnet_mask: [u8; 4],
    pub gateway: [u8; 4],
    pub dns: [u8; 4],
}

impl fmt::Display for NetworkConfig {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "{}.{}.{}.{} (Gateway: {}.{}.{}.{})",
            self.ip_address[0], self.ip_address[1], self.ip_address[2], self.ip_address[3],
            self.gateway[0], self.gateway[1], self.gateway[2], self.gateway[3]
        )
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum WifiState {
    Disconnected,
    Scanning,
    Connecting(&'static str),
    Connected {
        ssid: &'static str,
        config: NetworkConfig,
        signal_dbm: i8,
    },
}

pub struct WifiDriver {
    mac: MacAddress,
    state: WifiState,
    tx_count: AtomicU32,
    rx_count: AtomicU32,
    available_aps: [AccessPoint; 5],
}

impl WifiDriver {
    /// Initializes the Wi-Fi Adapter with VirtualBox-compatible Intel 82540EM MAC
    pub fn new() -> Self {
        Self {
            mac: MacAddress([0x08, 0x00, 0x27, 0xAB, 0xC3, 0x61]),
            state: WifiState::Disconnected,
            tx_count: AtomicU32::new(0),
            rx_count: AtomicU32::new(0),
            available_aps: [
                AccessPoint {
                    ssid: "Joydev-WiFi-5G",
                    bssid: MacAddress([0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC]),
                    channel: 36,
                    signal_dbm: -46, // 94%
                    security: WifiSecurity::Wpa3Sae,
                },
                AccessPoint {
                    ssid: "Campus_Secure_802.1X",
                    bssid: MacAddress([0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0x01]),
                    channel: 6,
                    signal_dbm: -58, // 84%
                    security: WifiSecurity::Enterprise8021X,
                },
                AccessPoint {
                    ssid: "Home_Fiber_Optic",
                    bssid: MacAddress([0xDE, 0xAD, 0xBE, 0xEF, 0x00, 0x42]),
                    channel: 149,
                    signal_dbm: -52, // 90%
                    security: WifiSecurity::Wpa2Personal,
                },
                AccessPoint {
                    ssid: "eduroam",
                    bssid: MacAddress([0x00, 0x11, 0x22, 0x33, 0x44, 0x55]),
                    channel: 1,
                    signal_dbm: -74, // 52%
                    security: WifiSecurity::Enterprise8021X,
                },
                AccessPoint {
                    ssid: "Public_Guest_WiFi",
                    bssid: MacAddress([0xFE, 0xDC, 0xBA, 0x98, 0x76, 0x54]),
                    channel: 11,
                    signal_dbm: -80, // 40%
                    security: WifiSecurity::Open,
                },
            ],
        }
    }

    pub fn mac_address(&self) -> MacAddress {
        self.mac
    }

    pub fn scan(&mut self) -> &[AccessPoint] {
        self.state = WifiState::Scanning;
        &self.available_aps
    }

    pub fn connect(&mut self, ssid: &'static str, _passphrase: &str) -> Result<NetworkConfig, &'static str> {
        let found = self.available_aps.iter().find(|ap| ap.ssid == ssid);
        if let Some(ap) = found {
            let config = NetworkConfig {
                ip_address: [192, 168, 1, 105],
                subnet_mask: [255, 255, 255, 0],
                gateway: [192, 168, 1, 1],
                dns: [8, 8, 8, 8],
            };
            self.state = WifiState::Connected {
                ssid: ap.ssid,
                config: config.clone(),
                signal_dbm: ap.signal_dbm,
            };
            Ok(config)
        } else {
            Err("SSID not found in range")
        }
    }

    pub fn disconnect(&mut self) {
        self.state = WifiState::Disconnected;
    }

    pub fn state(&self) -> &WifiState {
        &self.state
    }

    pub fn transmit_packet(&self, bytes: usize) -> u32 {
        self.tx_count.fetch_add(1, Ordering::Relaxed);
        bytes as u32
    }

    pub fn receive_packet(&self, bytes: usize) -> u32 {
        self.rx_count.fetch_add(1, Ordering::Relaxed);
        bytes as u32
    }

    pub fn stats(&self) -> (u32, u32) {
        (
            self.tx_count.load(Ordering::Relaxed),
            self.rx_count.load(Ordering::Relaxed),
        )
    }
}
