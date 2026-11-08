# DFU updater to normal application reboot contract

Read-only review of local updater source and existing host tools. No USB device was opened and no control transfer, install, or firmware change was made. The source is not proof that the installed updater image has these exact bytes; `DFU-VENDOR.md` says installed-image compatibility is unqualified.

## Control request

`handheld-dfu/src/usb/control.rs` accepts vendor control requests only when `(request_type, recipient, index)` equals `(Vendor, Interface, this_interface_number)`. In the current USB descriptor construction in `usb/mod.rs`, this is the first vendor interface, interface 0. Host setup packet for reboot-to-normal is therefore bmRequestType `0x41` (host-to-device, vendor, interface), bRequest `1` (`REQ_REBOOT`), wValue `1`, wIndex `0`, and no data / wLength `0`. `wValue=2` requests reboot back into DFU; all other values are rejected. The handler ignores the OUT data slice; no additional payload argument is required.

For `wValue=1`, the handler invokes `reboot::reboot()` and returns `OutResponse::Accepted`. That function `try_send`s a `Reboot` action to a one-slot channel but discards send failure. If queued, the reboot task waits 100 ms and calls `software_reset()`. Therefore Accepted is only the USB control-stage response: it does not prove the action was queued, reset occurred, the normal application booted, or the newly written ELF is running. There is no request-status response for reboot. A full action channel could still yield Accepted without a queued reboot.

The updater USB descriptor binds WINUSB to its vendor interface 0, with a bulk IN/OUT pair. The Python client also requires that vendor interface and exact serial `802C0E7A`; it intentionally rejects the normal application's endpoint-less control interface as an updater. The reboot control request must be sent while the updater vendor interface is present, before it disappears. The current `UsbBackend.control()` can represent the transfer, but there is no call site for request 1.

## Existing host support

`dfu_vendor.py` implements GET_INFO/status and flash READ/WRITE/ERASE. Successful apply returns `VERIFIED_NO_REBOOT`; it sets `automatic_retry=false` and `post_reboot_ELF_verified=false`. `DFU-VENDOR.md` explicitly says there is no reboot implementation. The existing `lab_controller.py reboot` action speaks the separate normal-application serial lab protocol and expects its COM/PING/ELF identity checks; it cannot operate while the device is in the DFU-only USB mode. No inspected host tool implements the vendor control request 1/value 1 after apply.

## Guard before unattended continuation

Treat `VERIFIED_NO_REBOOT` only as permission to enter a distinct, one-shot reboot stage after validating the receipt and its provenance. Require the expected schema/result; exact pre-update serial/hardware identity; exact plan hash; exact new BIN SHA-256; factory readback hash equal to the plan's expected whole-factory hash; both updater and partition-table preservation flags true; `automatic_retry=false`; `post_reboot_ELF_verified=false`; and a successful terminal `readback_verified` journal event with no apply/operation error. Re-hash the plan and BIN files against those bound values before opening USB. Any missing, mismatched, duplicate, error, or ambiguous evidence must stop with no reboot.

Then issue the vendor request exactly once to the same expected serial/interface 0 with bmRequestType `0x41`, request `1`, value `1`, index `0`, zero data, under a bounded timeout. Persist the request attempt and USB response before closing the interface. Do not retry if transfer result or response is ambiguous. Start exact-serial presence monitoring before the request/close, require disappearance and re-enumeration by the deadline, then use the normal application's independent PING/identity path to verify the exact target ELF. A USB Accepted result or reappearance alone is not success. If the device remains in DFU, target identity mismatches, or the deadline expires, stop and preserve evidence; never send a second reset automatically.

The handler's unchecked `try_send` means even a successful control ACK may not cause reboot; post-request disappearance/reenumeration is a required guard. The single factory slot also means the host must retain the reviewed recovery path; source-based control semantics are not installed-updater qualification.

## Sources

Reviewed file hashes are recorded in `source-hash-pins.json`. Key files: local `usb/control.rs`, `usb/mod.rs`, `reboot.rs`; published `dfu_vendor.py`, `DFU-VENDOR.md`, `lab_controller.py`, and the fake-backend updater tests.
