# DFU to application USB driver return audit

## Evidence reviewed

The selected DFU observation is the noncomposite root instance `USB\VID_1209&PID_B010\802C0E7A`, hardware ID `USB\VID_1209&PID_B010&REV_0411`, description `Game Bub Handheld DFU`, problem code 28, and no service. V48 evidence says the normal application retains VID/PID/serial, advertises a composite USB layout with lab `bcdDevice=0x4800`, has a vendor interface 0, and retained CDC operation after V48 was installed. The DFU result records that V48's application vendor MI00 had previously used WinUSB, explicitly distinct from the noncomposite DFU node.

The preserved records do not include an exact post-V48 Windows PnP snapshot of the composite parent and all MI children. In particular, they do not directly record the parent `Service=usbccgp` or every child instance/service. Operational evidence did confirm vendor interface 0 WinUSB with problem code 0, read-only GET_INFO for serial `802C0E7A` / Rev 4.1, and continued CDC operation. Treat the PnP service detail as expected topology, not as independently preserved observation.

The current DFU node shares the same VID/PID/serial identity as the normal application. The root instance path is recorded without `&MI_00`; the normal application's vendor function is a child path with an MI suffix. The preflight wrapper is strictly scoped to root instance `USB\VID_1209&PID_B010\802C0E7A` and requires `REV_0411` plus problem code 28. It explicitly rejects MI child IDs. It writes a device-associated `DeviceInterfaceGUIDs` value and calls `DiInstallDevice` with the selected in-box WinUSB driver for that exact current node.

## Persistence risk

**Windows re-selection behavior is unknown from this evidence.** Because DFU and normal app share VID/PID/serial and thus the same root instance identity, a driver association or root device property set while the updater is enumerated could plausibly remain associated when the same root returns with the composite descriptors. The application then needs the composite parent stack and separate function children. We cannot claim that Windows will automatically discard/reselect the parent driver or that the per-device interface GUID will be harmless after descriptors change. No installation has occurred; current preflight is read-only and UAC/apply remains pending.

## Required post-reboot gate

After any separately approved binding/update/reboot, do not claim unattended recovery until a fresh read-only PnP capture verifies all of these against the exact serial:

1. The root parent has the application descriptor/revision (`bcdDevice=0x4800` for V48), enumerates as a composite device, has `usbccgp` (or the verified Microsoft USB composite parent stack) and problem code 0. Confirm the updater-only WinUSB binding is not controlling the composite parent.
2. The expected interface children exist. Vendor MI00 is accessible through WinUSB with problem code 0. CDC child/COM interface is present, its correct serial identity is preserved, and an actual nonce PING completes. Record all child instance IDs, services, problem codes, driver INF/provider, and COM number.
3. The running application independently proves exact selected ELF identity using the normal host controller's PING/ELF check. GET_INFO over the vendor interface must report the exact serial and hardware revision; it does not replace exact ELF verification.
4. Preserve the fresh PnP snapshot, raw controller/GET_INFO responses, timestamps, selected ELF hash, and binding/installation result. If the composite parent fails to load, CDC disappears, vendor MI00 is missing, or ELF mismatches, stop and retain evidence. Do not force another binding or reset automatically.

Until these checks pass after the actual driver/app transition, hands-off update/reboot is not qualified. This review is read-only: no helper invocation, registry/driver operation, UAC action, hardware access, or USB transfer was performed.

## Bound inputs

See `source-hash-pins.json` for SHA-256 bindings of the V48 observations, selected V005 preflight, current helper/wrapper, and V48 USB/reboot documentation.
