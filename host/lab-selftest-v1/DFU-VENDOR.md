# App-only vendor updater client: offline candidate

`dfu_vendor.py` implements the inspected Game Bub vendor updater protocol. It has not opened or written a physical device. Importing the module is passive. There is no reboot implementation and no automatic retry. This client must not be used until root review and read-only qualification establish the installed updater behaves compatibly.

## Source contract

Inspected local source:`C:/Users/lavat/codex/gamebub/gamebub-source/firmware/handheld-dfu/src/{protocol.rs,usb/bulk.rs,usb/control.rs,usb/mod.rs,flash.rs,info.rs}`. These reference sources are not an installed updater image binding. Official [esp-storage0.9source](https://docs.espressif.com/projects/rust/esp-storage/0.9.0/esp32s3/src/esp_storage/common.rs.html) confirms4-byte words and4,096-byte sectors used by that source.

The bulk command header is32bytes: magic`0x431FD10B`, tokenu32, commandu8, args-sizeu8, reservedu16, transfer-lengthu32,16args bytes. READ`0x84` and WRITE`0x05` use mapped addresses`0x3C000000+flash_offset`; ERASE`0x03` uses an unmapped flash offset. Args are address/length,8bytes. Data packets are at most64bytes; this client groups4,096bytes per data command.

Successful READ ends with a **host OUT ZLP**. Successful WRITE/ERASE ends with a **device IN ZLP**. Device errors do not send a success ZLP. The client checks vendor-interface GET_COMMAND_STATUS`0x42` token, command ID, status and progress; it stops on mismatch/error rather than retrying. GET_INFO must report serial802C0E7A and Rev4/product1. The selected interface must be vendor0 with exactly one64-byte bulk IN/OUT pair, so the normal application's endpoint-less control interface is refused.

All mutation is restricted to factory`[0x100000,0x600000)`. READ is restricted to factory, DFU`[0x10000,0x40000)` and partition-table`[0x8000,0x9000)`. There is no efuse, arbitrary-memory, partition-write or write-protection-disable operation. Installed partition entries and their MD5 must match the unencrypted5MiB factory and192KiB DFU layout; malformed/overlapping/unsupported tables fail before mutation.

## Four separate stages

1. `probe` checks exact device/interface, installed table and a64-byte current-image prefix against an exact known BIN/hash. No flash mutation.
2. `backup` repeats the probe, reads the full5MiB factory,192KiB updater and4KiB partition table, verifies the complete known current-image prefix, and saves unique files/hashes. The observed updater bytes/hash are preservation evidence; they do not establish that local source built it.
3. `plan` is fully offline. It binds the exact backup manifest/files and new ESP32-S3 BIN/hash. The planned erasure rounds the new image length up to4,096bytes, filling the last partial sector withFF. This intentionally removes any old bytes inside that final erased sector. Bytes beyond the erased span remain unchanged. Four-byte write padding isFF. The full expected factory hash is computed from the preserved backup and these declared changes.
4. `apply --apply` revalidates every input, exact device identity and all current preservation regions against backup **before erasing**. It applies once, reads every factory byte back, compares the complete expected factory hash/new image, and rechecks updater/table preservation. It returns`VERIFIED_NO_REBOOT`; a separate owner must verify the receipt and coordinate any reboot and post-reboot ELF identity.

Only validated apply authorizes direct mutation methods. A write-ahead append-only JSONL journal is required. Mutation token/type/address/length and phase are flushed/fsynced before a command header can reach USB. Payload, completion and failure phases retain evidence; no image bytes or credentials are logged. A journal failure stops before the pending mutation. Readback or USB failure never triggers a reboot or repeat erase. The CLI preserves an operation failure event even if no final success JSON is written.

## Example commands (do not imply current device readiness)

Run from this directory. Replace all exact paths and SHA values with source-bound selected artifacts. CLI outputs must be new paths beneathC:/moon. The explicit local libusb DLL is loaded without global PATH changes; missing backend/driver stops.

```powershell
python dfu_vendor.py --libusb-dll C:/msys64/ucrt64/bin/libusb-1.0.dll probe --current-bin EXACT_CURRENT.bin --current-sha256 CURRENT_SHA --output C:/moon/dev/evidence/UNIQUE/probe.json
python dfu_vendor.py backup --current-bin EXACT_CURRENT.bin --current-sha256 CURRENT_SHA --output C:/moon/dev/evidence/UNIQUE/backup
python dfu_vendor.py plan --backup C:/moon/dev/evidence/UNIQUE/backup/backup.json --new-bin EXACT_NEW.bin --new-sha256 NEW_SHA --output C:/moon/dev/evidence/UNIQUE/plan.json
python dfu_vendor.py apply --plan C:/moon/dev/evidence/UNIQUE/plan.json --new-bin EXACT_NEW.bin --apply --output C:/moon/dev/evidence/UNIQUE/apply.json
```

The corresponding journal is`<output>.events.jsonl`. Preserve the local hardware's exclusive reservation and stopped sender; the script does not acquire authority from other tools or kill unrelated processes. One client cannot apply twice. Run the whole client under a bounded supervising process; each command/data phase has a deadline, individual USB transfers have finite timeouts, and no scheduling/overnight loop is hidden here.

## Verification and limits

23 fake-backend tests passed. They exercise real serializer/client/plan/backup code: range/overflow/identity/image checks, actual partition grammar/checksum, token mismatch, short READ, command error without success ACK, both ZLP directions, direct-mutation refusal, changed-plan/current-flash refusal, complete fake factory+preservation readback, write-I/O/readback failures, write-ahead journal ordering/fsync/failure, and data deadlines. Evidence and source hashes are at`C:/moon/builds/v48-dfu-client01`.

There is one factory slot, no A/B rollback. An interrupted update can leave the application unbootable while the preserved updater remains available. Unattended usability therefore still requires physical qualification of vendor DFU entry/readback, updater persistence/recovery, real write verification and reboot identity. These host tests do not prove that recovery, the installed updater contract, flash endurance, or a full power-cycle mechanism.
