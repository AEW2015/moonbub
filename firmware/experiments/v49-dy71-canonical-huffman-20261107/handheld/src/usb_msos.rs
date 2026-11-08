//! Immutable Microsoft OS 2.0 descriptors for vendor interface 0 only.
//! No USB/SDK callbacks or side effects live here; integration remains explicit.
pub const VENDOR_CODE: u8 = 0xf0;
pub const DESCRIPTOR_INDEX: u16 = 7;
pub const USB_BCD_VERSION: u16 = 0x0210;
pub const CONTROL_INTERFACE: u8 = 0;
pub const DEVICE_INTERFACE_GUID: &str = "{EBA74A86-FC4C-46B7-934D-578309693C58}";

/// V48's lab USB firmware revision, deliberately distinct from hardware identity.
/// GET_INFO must still report actual hwinfo. Preserve existing 0/2/3 mode IDs.
pub const fn lab_device_release(mode: u16) -> Option<u16> {
    match mode { 0 | 2 | 3 => Some(0x4800 | mode), _ => None }
}

const fn u16_at(b: &mut [u8], at: usize, value: u16) {
    b[at] = value as u8;
    b[at + 1] = (value >> 8) as u8;
}
const fn utf16_ascii_at(b: &mut [u8], at: usize, value: &[u8]) {
    let mut i = 0;
    while i < value.len() {
        b[at + i * 2] = value[i];
        b[at + i * 2 + 1] = 0;
        i += 1;
    }
}
const fn make_os20() -> [u8; 178] {
    let mut b = [0u8; 178];
    // Set header; Windows 8.1 (0x06030000); no alternate enumeration.
    u16_at(&mut b, 0, 10);
    b[6] = 3;
    b[7] = 6;
    u16_at(&mut b, 8, 178);
    // Configuration subset: index zero is configuration value 1.
    u16_at(&mut b, 10, 8);
    u16_at(&mut b, 12, 1);
    u16_at(&mut b, 16, 168);
    // Function subset: only the already-existing vendor interface 0.
    u16_at(&mut b, 18, 8);
    u16_at(&mut b, 20, 2);
    b[22] = CONTROL_INTERFACE;
    u16_at(&mut b, 24, 160);
    // Compatible ID feature: WINUSB, no sub-compatible ID.
    u16_at(&mut b, 26, 20);
    u16_at(&mut b, 28, 3);
    let id = b"WINUSB";
    let mut i = 0;
    while i < id.len() { b[30 + i] = id[i]; i += 1; }
    // REG_MULTI_SZ DeviceInterfaceGUIDs, UTF-16LE name and double-NUL data.
    u16_at(&mut b, 46, 132);
    u16_at(&mut b, 48, 4);
    u16_at(&mut b, 50, 7);
    u16_at(&mut b, 52, 42);
    utf16_ascii_at(&mut b, 54, b"DeviceInterfaceGUIDs\0");
    u16_at(&mut b, 96, 80);
    utf16_ascii_at(&mut b, 98, b"{EBA74A86-FC4C-46B7-934D-578309693C58}\0\0");
    b
}

pub static OS20_DESCRIPTOR_SET: [u8; 178] = make_os20();
pub static BOS_DESCRIPTOR: [u8; 33] = [
    5, 15, 33, 0, 1, // BOS header: 33 bytes, one platform capability.
    28, 16, 5, 0,
    0xdf, 0x60, 0xdd, 0xd8, 0x89, 0x45, 0xc7, 0x4c,
    0x9c, 0xd2, 0x65, 0x9d, 0x9e, 0x64, 0x8a, 0x9f,
    0, 0, 3, 6, // Windows 8.1.
    178, 0, VENDOR_CODE, 0,
];

/// Match only the reserved, read-only device-recipient OS 2.0 request.
/// TinyUSB must truncate the returned fixed slice to the host's wLength.
/// None must leave existing vendor interface requests on their existing path.
pub fn vendor_response(
    request_type: u8, request: u8, value: u16, index: u16, length: u16,
) -> Option<&'static [u8]> {
    if request_type == 0xc0 && request == VENDOR_CODE && value == 0
        && index == DESCRIPTOR_INDEX && length != 0 {
        Some(&OS20_DESCRIPTOR_SET)
    } else {
        None
    }
}
