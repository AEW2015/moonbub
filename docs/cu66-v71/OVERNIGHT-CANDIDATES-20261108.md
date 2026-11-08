# Overnight ESP32 and FPGA candidates — 2026-11-08

## Current state and selected controls

V48/V027 is the last physically qualified custom-codec combination: local-host twelve-frame network trial, 12 accepted/presented, 253,440 actual HUD comparisons, zero native allocation failures, 21.923482 seconds. Corrected software reboot also passed. This diagnostic elapsed time is not a unique-display FPS benchmark.

The handheld is currently in the separate software DFU node (VID1209/PIDB010, serial802C0E7A, revision0411), Windows problem28/no driver. No vendor flash erase/write has occurred. Its factory V48 remains preserved; FPGA power was shut down by graceful DFU entry. Do not report it as listening at .157 or showing V027 now. The local sender is .33; the .47 PC is not needed for the next fixtures.

A one-device Microsoft signed in-box WinUSB binding has passed read-only preflight. Application requires an elevated UAC step, pending operator response. The preflight is C:/moon/dev/evidence/dfu-inbox-bind-preflight-20261108-v005/preflight.json; older global-list plans are invalid for apply. After binding: independently probe GET_INFO, back up protected flash and layout, verify app-only bounds and explicit readback, then separately reboot and check exact ELF. Software reset is not a true battery-level power cycle. No physical rail-control actuator exists.

## FPGA V028 / STB1

[The selected release](../../fpga/experiments/cu66-v71/stb1-release-v028-20261108/manifest.json) preserves exact board sources/includes/XDC/Tcl, standalone build scripts, BIT, routed checkpoint and reports. Image SHA256 `69da8c4b6ef3e9f15aa8bdca4973624b33a505e2b1116cd06b1e33aa744d527d`; USERID/USR_ACCESS `44593740`, Rev4.1 xc7a100tcsg324-1. Not programmed.

- Routed setup +0.005ns, hold +0.020ns, native pulse +2.000ns; 56,551/56,551 nets fully routed, zero route errors and unwaived DRC errors. Small positive setup margin is retained honestly. A separate placement/replication experiment is not selected unless its final complete gates improve on this image.
- Existing clocks, SDRAM PHY, pins and timing budgets are unchanged. Two inherited bundled-data completed_bad CDC paths retain their endpoint/token proof; this is not a zero-critical CDC report. No constraint was relaxed to obtain a pass.
- ABI3 (`0x00030000`, caps`0x3f`) adds descriptor-reserved 1KiB compressed ingress and a 256-word FIFO. Native byte RAM, committed prefix/CRC/generation/ticket and whole-frame SEAL checks remain authoritative. HBU1 stays separate and unchanged.
- Maximum49,152-byte packet passed actual selected QSPI/CDC/staging pin simulation, byte/CRC checks and repeated pointer wrap. Full256-word FIFO stalled/drained intact. The nominal model measured6.642ms complete packet staging at core100MHz/SPI16MHz; no SDK/radio/native-CPU or physical throughput claim follows.
- Ready snapshots are sequential, not atomic. Driver rechecks flags/generation/ticket and ignores mixed-time busy snapshots. Raw alias transactions above1,024bytes must be rejected before writes by both driver and adapter: arbitrary longer SPI can wrap the inherited12bit CSR address, so hostile raw-burst fail-closed protection is not claimed.
- Actual V52 and V55 Rust + native FFI + selected RTL/SDRAM/HBU/scanout each pass the original KEY/P pair:2accepted/presented,42,240 actual HUD comparisons and zero canonical/raster/HUD mismatches. These use direct CSR RPC,200ms modeled Prepare service and zero native virtual CPU time. They prove composition, not physical speed.
- RTL and exact-source OOC primitive FIFO tests pass10cases,8full256 events and13,329 actual RAM bytes/CRC. Selected routed/OOC RAMB18 mapping agrees. Full optimized routed-cell replay and SDF are not qualified; primitive startup sensitivity failures and the corrected post-init stimulus are preserved.

## ESP32 choices — all new candidates NOT INSTALLED

| Candidate | FPGA ABI | Purpose | Selected ELF / UF2 SHA prefixes |
|---|---|---|---|
| V48 | V027 ABI2 | Physical control, serial recovery and local-host selection | 93a389ad / a10cd156 |
| V49 | V027 ABI2 | Canonical Huffman, fewer allocations | 64a7243f / a6b2d30b |
| V50 | V027 ABI2 | Copy only requested native READ slice | 8dc3788f / 748036c9 |
| V51v002 | V027 ABI2 | Keep reserve checks, remove unused largest-block heap walks | 991d0896 / 4dbfd500 |
| V52 | V028 ABI3 | Isolated STB1 ingress control, exact V48 native code | 285bc495 / 06f56805 |
| V53 | V027 ABI2 | One five-u32 HBU status transaction; native code unchanged | 02315863 / 9701ad4c |
| V54 | V028 ABI3 | V52 plus bounded failure-only STB diagnostics | c7506ed0 / 1f3bd4ce |
| V55 | V028 ABI3 | V54 plus separately qualified V49/50/51/53 improvements | ef005e82 / 5278b95b |

Exact images/source/evidence are under firmware/experiments. Every new target builds, packages and passes host/native controls. Original arena98,304, physical reserve8,192, worker16,384, shared static SRAM132,076 and stack canaries remain. Effective target config has no PSRAM. Preserve exact target ELF for log decoding; inherited Git metadata is not the SDK ELF identity.

V55's Huffman/channel stack frames increase by576bytes over the original native path; observed target worker/run-mode prologues are5,328/4,000bytes (V54worker5,344; V48worker5,200). These are partial static frames, not summed full-callchain bounds or a runtime stack proof. Measure real worker low-water/canaries before advancing. No guard reduction or stack enlargement was used to force a build/pass.

V54 reads13STB CSRs only after failure. Its four STBF1 records bind identity/progress and validity masks with CRCs;20ms is a pre-call sampling budget, not a hard deadline for a blocking SDK transaction. Records are non-atomic post-failure samples and best-effort delivery. Missing fields remain unknown; they do not establish FIFO emptiness or failure onset time.

## New-source package and remaining throughput work

[The offline encoder bridge](../../experiments/cu66-source-bridge-20261108/REPORT.md) now creates12 distinct CU66 packets from local motion-test.mp4,720×405 at(0,37) in720×480, KEY0→P1…P11. Exact native-v69 and frozen Python receiver agree on canonical/HUD/display hashes; original98,304arena peaks95,053bytes. Source duration covered is0.367seconds, not a120second movie. The original Mass Effect SHAfb01977… was not located locally. No new packet has been sent to hardware.

A finite12-new-frame actual V55 Rust/RTL/SDRAM replay is running separately. Preserve its final result and source bindings when complete; launching it is not a pass. Live encoding, general continuous receiver lifecycle, network/video30fps, AV coexistence and the full120second custom stream remain unqualified.

## Next physical ladder

1. Complete the one-time DFU driver qualification and protected app-only backup/update workflow. If unavailable, keep doing offline work and leave flash untouched; do not erase or force-release a native endpoint.
2. Install V54 as the first ABI3 correctness/observability control; confirm exact SDK ELF, cold/soft-reset reason, memory/stack, then volatile-program selected V028, verify DONE/USERCODE/ABI3 and old-profile refusal. Restore .33 as the RAM-only custom host.
3. Original3 then12 historical fixtures, full readback, fresh sessions and independently reconciled presentation replies. Freeze diagnostics on failure. Measure staging/QSPI transactions, HUD CPU/write/readback, decode/drain, actual unique presentation and heap/stack, without cross-machine clock subtraction.
4. If healthy, V55 with the same BIT/fixtures/conditions. Native CPU12 and runtime stack/fragmentation gates first; do not attribute combined speedup to one fragment. Keep V49/50/51/V53 ABI2 images for isolated comparisons if needed.
5. Run the new local video12 package only after the matching full-system replay passes. Then build a longer independently decoded package and explicit bounded/continuous transport profile. Do not feed the old JPEG/MSV1 payload to this decoder or call CU66 quality Q30/Q35.
6. Reach a correct longer video-only replay before independently sequenced controller/audio coexistence or30unique displayed frames/s acceptance. Exact source, configured/sent/admitted/decoded/presented rates, stage times, trace loss and recovery/STOP results must stay separate.

Keep V48/V027 and the exact JPEG/build50 archive D:/moon/backups/JPEG-V38-BUILD50-20261107.zip as recovery controls. All active work stays under C:/moon; retain selected evidence before pruning caches. No external Sunshine sender start is requested by this report.
