//! Dormant AR03 epoch-1 laboratory gateway. No listener, live capability or backend.
#![allow(dead_code)]
pub mod frame;
pub mod packet;
pub mod wire;
/// No live negotiation/reset/rekey implementation exists. No enable setter exists.
pub const LIVE_PROFILE_ADVERTISED: bool = false;
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ActivationError {
    NegotiationAndRecoveryNotImplemented,
}
pub fn authorize_live_profile() -> Result<(), ActivationError> {
    Err(ActivationError::NegotiationAndRecoveryNotImplemented)
}

// Compile-time target layout bound; no Gateway instance is allocated by boot/runtime.
const _: () = assert!(core::mem::size_of::<packet::Gateway>() <= 2048);
