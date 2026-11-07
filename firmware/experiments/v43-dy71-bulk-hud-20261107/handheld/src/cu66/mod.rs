//! Offline CU66 integration core. No network listener, MMIO driver or advertised capability.
#![allow(dead_code)]
pub mod framing;
pub mod staging;
pub const NETWORK_CAPABILITY_ENABLED: bool = false;
#[cfg(not(test))]
pub mod hud;
#[cfg(not(test))]
pub mod usb_probe;
#[cfg(not(test))]
pub mod local;
#[cfg(not(test))]
pub mod local_usb;

pub mod lcd_observer;

pub mod network_wire;
#[cfg(not(test))]pub mod network_driver;
#[cfg(not(test))]pub mod network_io;
#[cfg(not(test))]pub mod network_usb;
