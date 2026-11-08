# V48 read-only DFU qualification addendum

## Result

The exact DFU root `USB\VID_1209&PID_B010\802C0E7A` is bound to Microsoft's inbox WinUSB (`winusb.inf`, service `WINUSB`) and the post-bind PnP snapshot reports problem code 0. A read-only probe completed successfully and the full read-only backup passed its byte-count and SHA-256 checks. The full 3,504,688-byte V48 release file used for both runs has SHA-256 `852bfca679a72ef1cdf20e55df22c3bc9cd22d7c184cfaa4c951591df37b1217`, matching the known release; the probe's first-64-byte sample also matches. The backup BINs remain private under `C:\moon\backups\DFU-V48-READONLY-20261108-v001`; this publication addendum contains no raw `.bin` files.

The one user-approved elevation was scoped to exact-node WinUSB binding. Its helper exited 1 at the post-install exact product-description guard (`Exact updater product description required`); the transcript also records a missing `PnpDevice.Resource.psd1` while reporting the termination. The reconciliation records the command sequence and later exact-node observation showing that driver installation had taken effect. The node now reports `WinUsb Device`, friendly name `Game Bub Handheld DFU`, Microsoft provider, `winusb.inf`, service `WINUSB`, and problem code 0. No retry, flash write, reset, or automatic reboot occurred.

## Boundaries

The successful probe read device identity, the partition table, and the first 64 factory-application bytes; it did not verify the entire installed application against the 3.5 MB release image. The backup separately read and hashed the private factory, DFU, and partition regions. The current V48 release file still matches its full recorded hash. The need-reboot flag remains unknown, and the installed updater source binding is null. Return to the normal application composite, app write behavior, and reboot behavior remain unqualified.

V54 and V55 are offline app-only plans tied to this backup manifest and current device identity. Their release BIN hashes were matched to the published artifacts, but neither plan was executed.

## Evidence

- `probe/` contains execution, launcher, result metadata, read journal, supervisor script, and stdout/stderr for the read-only probe.
- `backup-evidence/` contains execution, integrity, launcher, supervisor script, logs, and `backup.json` metadata. Factory/DFU/partition data files were not copied.
- `driver-binding/` preserves the UAC supervisor transcript, preflight and before/after PnP evidence, reconciliation record, and exact post-bind node snapshot. Operational helper source/scripts and its executable are not copied; their hashes remain in the reconciliation receipt.
- `offline-plans/` contains the V54/V55 plans only.
- `curation-manifest.json` binds every copied file and records private-only backup hashes, full release BIN hashes, and source provenance.

Curation was offline and made no USB, code, or device changes.
