# Next hardware tests — 2026-11-05

## Historical CPL1 board source audit — v1

The audit below describes the earlier v1 failed-route package and remains historical; the current source package and replay status are recorded separately.

Reviewed the failed-route package at `evidence/overnight-coordinated-20261105/cpl1-board-source-01/cpl1-source-failed-route.zip` and extracted a fresh review copy to `evidence/overnight-coordinated-20261105/cpl1-board-portable-review01/cpl1-source/`.

- ZIP SHA-256: `7f735d54cf65efa98f1ba26e74d7cd5f102d3dfae083c66ce7953e243f9d514b`; 226,014 bytes.
- Outer manifest SHA-256: `2c34f2412614d65a51027a4bb290a0a9647f200adbf94b1f5dca2f42afc6ea27`; it binds 80 package artifacts. The source verifier reports `SOURCE_PACKAGE_HASHES_PASS 78` (78 selected source/data bindings).
- Fresh-copy verifier: `python reproduce.py verify`; exit code 0.
- The archive contains no DCP, BIT, EDIF, mapped netlist, or shipped vendor primitive libraries. Its reproduction recipe stages the included `inputs/` and ROM data in the requested output directory, then invokes licensed Vivado 2025.2 and its installed Artix-7 device support. No source outside the extracted package is referenced by the verifier/reproduction script; vendor tooling is an explicit external build dependency.
- `key.cp23.hex` is present (17,412 byte entries); `quantizers.hex` is present (384 8-bit entries, each represented by two hex digits / 768 hex digits total). The selected RTL declares `reg[7:0] quantizers[0:383]`; observed factors fit in one byte. `licenses/GameBub-CERN-OHL-S-2.0.txt` is present.
- The reports document functional digital/native replay but not hardware operation. Routed setup is **FAIL** at WNS −1.618 ns, TNS −7795.573 ns across 13,015 endpoints. Routed hold is +0.015 ns; all 50,673 routable nets routed with zero route errors. No BIT was produced. This CPL1 fixture is blocked by setup timing and must not be programmed or used to send custom network data.

## Current CPL1 source replay — v002

- Archive: `evidence/overnight-coordinated-20261105/cpl1-board-source-02/cpl1-source-replay-v002.zip`.
- ZIP SHA-256: `5ba475b23aee08dbb2accbc40d9f2a11ae178270bab61d42fec3ae85b7041c7f`; 465,515 bytes.
- Manifest SHA-256: `c3dc08c673c080cc80334375dd662e03ff87ee15163350231beab6a2d3ccb73e`.
- The package includes standalone smoke and full Icarus replay. Fresh smoke and extracted-package full replay both passed, including the independent fixture checker; commands and results are published under `docs/measurements/cpl1-fresh-package-full-20261105/`. This is replay evidence only, not hardware-operation evidence.

## Proposed controlled legacy regression

This is a test plan only. It does not authorize an installation or start a run. Keep the device powered off until an operator later performs the approved legacy UF2 installation step. Use the legacy v31 receiver path with the existing build50 FPGA image, preserving the known working configuration.

1. After operator installation and a fresh connection, verify receiver firmware/build identity, FPGA/build50 identity, network endpoints, and fresh starting counter values. Record settings and clock times. Keep the established baseline sender pacing unchanged.
2. Run the saved Xonotic input-only AV regression from offset zero at 720×480, 20 fps, 4 Mbps, Q25. Input SHA-256: `36ef854b29293c027dd161185dc0a2e9d03ec7854ea9039800164b03956d3a83`. Keep audio and controller injection off. Do not combine this first variable with a new pacing candidate or the CPL1 fixture.
3. Allocate new frame IDs starting at 2,014,200 or above; confirm the selected range is unused before starting. Record the exact first and last IDs and never reuse IDs from an earlier run.
4. Capture the full test window with camera and host packet capture from before START through STOP and the post-STOP observation interval. Record any coverage gaps. Use the legacy v31 trace collector v2 and retain all 33 summary pages; report trace loss by kind. Capture receiver and sender identities/counters before and after, plus accepted, decoded, presented, replaced, dropped, queue, core-fault and power-save restoration results.
5. Send STOP through the normal control path. Confirm neutral input state, clean shutdown, and observed power-save restoration; preserve sender, receiver, camera and packet-capture evidence together. Reconcile missing data or trace loss as unknown before any follow-on run.

Do not claim verified 30 fps from this test. The CPL1 fixture remains a separate failed-route development candidate, and the v33 AV restore-fence candidate is not the first test variable. No custom CPL1 network payload, firmware installation, or FPGA programming is part of this plan.

