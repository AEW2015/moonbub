# V48 WinUSB descriptor design and integration review

November7,2026. This task created only V48`handheld/src/usb_msos.rs` and`tests/usb_msos.rs`. No existing USB callbacks, device state, firmware build or hardware were changed by this task.

## Purpose and exact scope

The installed application's vendor control interface0 has Windows problemcode28/no bound service, while CDC interfaces1/2 work. V48 can advertise the in-box WinUSB compatible ID for vendor interface0 only. This is an app descriptor change, not a driver replacement, bootloader modification or claim that the installed updater already has matching support.

The new module owns two immutable arrays:33-byte BOS with one Microsoft OS2platform capability, and178-byte OS2descriptor set. Nested set/configuration/function/feature lengths are exact. Only interface0 receives WINUSB. A UTF-16LE REG_MULTI_SZ`DeviceInterfaceGUIDs` uses`{EBA74A86-FC4C-46B7-934D-578309693C58}`, matching the inspected upstream DFU source. The property has both string terminators. CDC/storage receive no compatible-ID override. There is no allocation, mutable scratch, callback, reset, flash or driver action in this module.

## Integration API

- `USB_BCD_VERSION`:0x0210.
- `BOS_DESCRIPTOR:[u8;33]`; `OS20_DESCRIPTOR_SET:[u8;178]`.
- `VENDOR_CODE`:0xF0; `DESCRIPTOR_INDEX`:7.
- `vendor_response(raw_bmRequestType,bRequest,wValue,wIndex,wLength)` returns the fixed static OS2slice only for`0xC0/0xF0/0/7/nonzero`. All other requests returnNone and must continue through the existing dispatch path. TinyUSB truncates the fixed response to hostwLength.
- `lab_device_release(mode)` returnsSome`0x4800|mode` only for modes0/2/3. This is explicitly V48lab USB firmware revision48.00/48.02/48.03, not physical board revision. Actual GET_INFO must continue reporting real hwinfo. VID/PID/serial/interface order remain unchanged. Other external clients that interpret bcdDevice as a hardware revision are not qualified by this change.

The selected TinyUSB`src/device/usbd.c` defines`tud_descriptor_bos_cb` weakly, so the application may supply a strong callback returning`BOS_DESCRIPTOR.as_ptr()`. Selected EspTinyUSB`descriptors_control.c` owns a strong string callback; do not replace it or change its string path. DevicebcdUSB must move from0200 to0210 so Windows fetches BOS. The deliberate bcdDevice revision change avoids reusing the previous VID/PID/revision cache identity; do not use bit3OR across the old mode field because modes2/3 would produce non-BCD low nibblesA/B.

In`tud_vendor_control_xfer_cb`, intercept the exact OS2device-recipient request before the existing interface0filter. At SETUP call`tud_control_xfer` with the static178-byte pointer/length and return its boolean result. At DATA/ACK accept only this same exact read-only request, with no application control callbacks. Do not route OS2to`handle_control_complete`, and do not broaden legacy interface requests. Validate through target build and the actual callback integration separately.

## Executed tests and source evidence

Seven Rust tests compiled the actual new production module and passed in`C:/moon/builds/v48-msos01/test.log`. They independently parse BOSUUID/version/length, all nested OS2lengths/features, interface0-only binding, UTF-16property/name/GUID terminators, strict request dispatch including rejected reboot/debug/interface forms, bounded static response behavior for partial/largewLength, and validBCD lab revisions preserving only supported mode IDs.

Command: `rustc +stable --edition=2021 --test <candidate>/tests/usb_msos.rs -o C:/moon/builds/v48-msos01/usb-msos.exe`; then execute with`--test-threads=1`. This is host structural/dispatch evidence, not Windows enumeration, successful driver binding or updater qualification. Source hashes and selected TinyUSB SDK paths are in`C:/moon/builds/v48-msos01/bindings.json`.

## Primary-source basis and remaining limits

Microsoft's [composite BOS/OS2example](https://learn.microsoft.com/en-us/windows-hardware/drivers/stream/uvc-camera-implementation-guide) specifies0210+, the platform UUID, vendor-device-IN request/index7, and configuration subset0for the first configuration. The local official TinyUSB webusb_serial example uses the same OS2descriptor layout and registry property grammar. Microsoft's [automatic WinUSB description](https://learn.microsoft.com/en-us/windows-hardware/drivers/usbcon/automatic-installation-of-winusb) supports in-box WINUSB compatible-ID loading; [device registry settings](https://learn.microsoft.com/en-us/windows-hardware/drivers/usbcon/usb-device-specific-registry-settings) documents VID/PID/revision-keyed OS query caching. These establish a design path, not this machine's future enumeration result.

First qualify app CDC continuity and read-only vendor GET_INFO after V48 installation. Do not enter software DFU on the assumption that a usable driver is guaranteed: installed updater source/identity and its accessible vendor interface must be established while a physical recovery window still exists. A software updater that exposes no CDC/MSConly works unattended if its vendor protocol remains usable. Reusing the same GUID/interface pattern is helpful but does not prove installed updater behavior or cached-driver migration.

The existing V48 nonce CDC recovery commands are an independent fallback for normal app reboot. They cannot recover from an inaccessible updater or a completely hung application without an external power/button actuator. Preserve the physical UF2 path and exact V47fallback.
