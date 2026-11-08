# Guarded DFU-to-normal reboot helper candidate

This is a separate host helper; dfu_vendor.py remains unchanged. Default execution is offline dry-run and does not construct a USB backend. The candidate passed 20 fake-backend tests, including actual existing DFU READ framing, no flash mutations, copied-receipt refusal and concurrent atomic claim. No USB, driver, elevation, flash, application update or physical reboot was executed. Root review is required before publication or hardware use.

Inputs are explicit full SHA-256 bindings for a VERIFIED_NO_REBOOT receipt, exact app-only plan, selected new BIN and terminal apply journal, plus the expected SDK ELF for the later independent verification. The helper re-creates the plan from the preserved backup using the pinned existing library. It requires the exact success receipt, full-factory/preservation hashes and one terminal durable readback_verified event, rejects duplicate JSON keys, duplicate/errored/ambiguous apply evidence, and checks the source-audit pins.

Only adding --send-once constructs the existing exact-serial 802C0E7A updater backend. Its pinned constructor checks VID/PID, vendor interface 0 / alternate 0 and the updater bulk pair; GET_INFO rechecks serial/Rev4 identity and idle status. The helper READs and verifies the entire new factory region, updater and partition bytes/layout, then rechecks identity, status and every preserved input hash. READ headers/ZLPs are transport operations, not flash writes. The guard rejects flash WRITE/ERASE and any DFU-mode request.

After successful live checks, an exclusive/fsynced attempt record is reserved in the fixed C:/moon/maintenance/dfu-normal-reboot-claims-v1 directory, keyed by receipt SHA, complete device identity and plan SHA. There is no CLI override. Copying an identical receipt to another path cannot bypass it; concurrent claim attempts have one winner. Claims are never removed automatically. A durable intent then precedes exactly one vendor/interface OUT request: bmRequestType 0x41, bRequest 1, wValue 1, wIndex 0, zero payload. No automatic reset, retry, lease release, flash operation or mode 2 request exists.

A zero-length control response produces SENT_UNCONFIRMED, with reset_verified=false and post_reboot_ELF_verified=false. A timeout, exception or unexpected return produces ATTEMPT_UNCONFIRMED and consumes the same claim. A full updater action queue may ACK without scheduling reset: the source uses best-effort try_send. Source hashes establish the inspected contract only; they do not prove installed updater bytes implement that source. installed_updater_source_binding remains null. Manual investigation is required after ambiguity; never delete a claim merely to retry blindly.

Detach/normal re-enumeration and exact SDK ELF verification are deliberately separate controller gates. That monitor must start before the transfer. It must verify the normal USB composite parent, CDC and MI00 interface/driver bindings appropriate to the reviewed normal application, then exact ELF through the normal identity path. Same VID/PID/serial, disappearance, control ACK or a COM port alone is insufficient. Updater-root WinUSB persistence into normal mode remains unqualified; normal parent service evidence is incomplete. This candidate does not promise fully hands-free continuation.

A dry-run invocation supplies these required arguments and a fresh output path under C:/moon:

```
python normal_reboot.py --receipt RECEIPT.json --receipt-sha256 FULL_SHA --plan PLAN.json --plan-sha256 FULL_SHA --new-bin NEW.bin --new-sha256 FULL_SHA --apply-journal APPLY.events.jsonl --apply-journal-sha256 FULL_SHA --expected-sdk-elf FULL_ELF_SHA --output C:/moon/evidence/NEW-dry-run.json
```

Only a separately reviewed/operator-authorized invocation adds --send-once. The output and append-only event journal must be preserved along with the fixed claim directory. Overall live validation is bounded to 120 seconds plus the backend's bounded individual transfer timeout; expiration prevents the reboot request. This implementation does not integrate an independent post-reboot monitor and is not live-qualified.

Tests:

```
python -m unittest discover -s C:/moon/dev/experiments/dfu-normal-reboot-20261108 -p test_normal_reboot.py -v
```

The tests use fake flash/USB behavior and isolated injected claim roots; they never create the default production claim directory or open hardware. Their source depends on the existing dfu_vendor test fake, which is separately hashed in the candidate receipt.

Preservation note: source-contract contains the three exact audited updater Rust files with origin/hash manifest and any repository-root license file. The frozen helper intentionally checks the original local source paths recorded in source-hash-pins.json. These are host files, not proof of installed device source. A clean clone must use reviewed path rebinding against this snapshot; do not assume the Game Bub repository already exists. This preservation does not change the helper, library or pins.
