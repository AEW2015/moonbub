# Independent V48 MS OS 2.0 callback integration review

ReviewedNovember7,2026. Read-only review of root's V48 integration in`device/drivers/usb/{mod.rs,descriptors.rs,control.rs}`, the immutable`usb_msos.rs` module, actual selected TinyUSB control-transfer implementation, and unchanged GET_INFO. No existing source edits or hardware actions were performed by this review.

## Decision

No blocking source defect found in the reviewed MS OS descriptor integration. This qualifies it for the target build and controlled USB enumeration test. It does not prove WinUSB binds on this PC, that CDC remains usable after enumeration, or that the installed DFU updater can be accessed without buttons.

## Symbol, identity and lifetime checks

Selected TinyUSB`src/device/usbd.c` has a weak`tud_descriptor_bos_cb` returningNULL. Root's single strong Rust no_mangle externC callback returns the immutable33-byte BOS pointer. There is no conflicting strong EspTinyUSB BOS definition in the inspected selected sources. Target linking and symbol inspection remain the actual toolchain gate.

The existing strong string-descriptor callback is unchanged. No temporary string/descriptor allocation or borrowed stack pointer is returned. BOS and OS2set arrays have static lifetime and no mutable storage. Existing VID/PID, serial source, vendor-first/CDC/MSCorsecondaryCDC interface sequence and endpoint layout remain unchanged.

DevicebcdUSB is0210. The new USBbcdDevice values4800/4802/4803 are validBCD and preserve mode IDs0/2/3. This is explicitly a lab firmware USB revision, not hardware4.0identity. GET_INFO still returns`hwinfo::get_hardware_version()` and the existing serial/firmware metadata; physical board identity was not changed. External clients interpreting bcdDevice as hardware revision are not qualified.

## Request scope and transfer safety

The added branch is before the old interface0filter because OS2requires a device-recipient request. It accepts only rawbmRequestTypeC0, requestF0, value0, index7 and nonzerolength. Other requests retain the old path; interface-recipient reboot/debug/gamepad commands are not broadened. OUT, wrong-recipient, wrong-index and zero-length requests cannot reach the immutable descriptor transfer. No OS2stage invokes application control handlers, reboot scheduling, reset or flash operations.

At SETUP root passes the static178-byte pointer and exact178length to`tud_control_xfer` and returns its boolean result. Selected TinyUSB`usbd_control.c` sets transfer length to`min(actual-length,host-wLength)` and, for IN direction, copies from the source into its EP0buffer. Its void-pointer API cast does not make this read-only branch write to the Rust static. DATA/ACK for the same matched read-only request returntrue without touching shared legacy BUFFER; unknown stages returnfalse.

The original callback assumes a valid TinyUSB request pointer and asserts vendor-type. Those pre-existing framework assumptions remain; this patch adds no new unsafe lifetime or request-pointer dereference beyond the same valid callback context. Standard/class requests are not expected to be routed to this vendor callback by TinyUSB.

## Evidence and limits

Seven tests compiled the actual pure descriptor module and passed at`C:/moon/builds/v48-msos01/test.log`. They independently parse BOS/type/UUID/version, nested configuration/function lengths, WINUSB interface0-only binding, UTF-16GUID property with double terminators, strict request matching, static slice bounds, and lab revisionBCD/mode fields. The callback integration itself was reviewed against the selected TinyUSB C implementation; it is not executed by those host tests. Root's target build and hardware qualification must remain separate.

Next physical gates: verify CDCserial802C0E7A and exact appELF after installation; inspect WindowsvendorMI00service/problemcode; run read-only GET_INFO and compare truehardware/serial; only then qualify a graceful reboot and restoredboot identity. Establish the installed updater identity and usable vendor access while physical recovery is still available before calling softwareDFU/update unattended. SameVID/PID/interface/GUID patterns do not prove driver migration into an older updater image. Preserve the physicalUF2route and exact V47fallback.

Reviewed-source hashes are recorded in`C:/moon/builds/v48-msos01/integration-bindings.json`. Any later source change requires checking this review's affected assumptions again.
