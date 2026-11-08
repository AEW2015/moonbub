# Overnight ESP32 and FPGA candidates — 2026-11-08

## Current state and selected controls

V48/V027 is the last physically qualified custom-codec combination: local-host twelve-frame network trial, 12 accepted/presented, 253,440 actual HUD comparisons, zero native allocation failures, 21.923482 seconds. Corrected software reboot also passed. This diagnostic elapsed time is not a unique-display FPS benchmark.

The handheld is currently in the separate software DFU node (VID1209/PIDB010, serial802C0E7A, revision0411), Windows problem28/no driver. No vendor flash erase/write has occurred. Its factory V48 remains preserved; FPGA power was shut down by graceful DFU entry. Do not report it as listening at .157 or showing V027 now. The local sender is .33; the .47 PC is not needed for the next fixtures.

A one-device Microsoft signed in-box WinUSB binding has passed read-only preflight. Application requires an elevated UAC step, pending operator response. The preflight is C:/moon/dev/evidence/dfu-inbox-bind-preflight-20261108-v005/preflight.json; older global-list plans are invalid for apply. After binding: independently probe GET_INFO, back up protected flash and layout, verify app-only bounds and explicit readback, then separately reboot and check exact ELF. Software reset is not a true battery-level power cycle. No physical rail-control actuator exists.

## FPGA V028 / STB1

[The selected release](../../fpga/experiments/cu66-v71/stb1-release-v028-20261108/manifest.json) preserves exact board sources/includes/XDC/Tcl, standalone build scripts, BIT, routed checkpoint and reports. Image SHA256 `69da8c4b6ef3e9f15aa8bdca4973624b33a505e2b1116cd06b1e33aa744d527d`; USERID/USR_ACCESS `44593740`, Rev4.1 xc7a100tcsg324-1. Not programmed.

- Routed setup +0.005ns, hold +0.020ns, native pulse +2.000ns; 56,551/56,551 nets fully routed, zero route errors and unwaived DRC errors. Small positive setup margin is retained honestly. The separate V003 placement/replication experiment was rejected: final setup−0.197ns/TNS−9.204ns at105endpoints, despite full routing and positive hold/pulse. Its reports are preserved. The [one-line CE-factoring successor](STB1-NEXT-RTL-TIMING-PLAN-20261108.md) passed source/miter and exact-source KEY/P gates but failed final setup−0.382ns (638endpoints). Its local target improved to+0.289ns with HUD metadata feedback removed. A separate incremental attempt reused95.01%cells but failed native placement before routing. Neither is selected or produced a new BIT; V028 remains fixed. The [source-traced parser plan](STB1-PARSER-NEXT-TIMING-PLAN-20261108.md) records the next bounded design work.
- Existing clocks, SDRAM PHY, pins and timing budgets are unchanged. Two inherited bundled-data completed_bad CDC paths retain their endpoint/token proof; this is not a zero-critical CDC report. No constraint was relaxed to obtain a pass.
- ABI3 (`0x00030000`, caps`0x3f`) adds descriptor-reserved 1KiB compressed ingress and a 256-word FIFO. Native byte RAM, committed prefix/CRC/generation/ticket and whole-frame SEAL checks remain authoritative. HBU1 stays separate and unchanged.
- Maximum49,152-byte packet passed actual selected QSPI/CDC/staging pin simulation, byte/CRC checks and repeated pointer wrap. Full256-word FIFO stalled/drained intact. The nominal model measured6.642ms complete packet staging at core100MHz/SPI16MHz; no SDK/radio/native-CPU or physical throughput claim follows.
- Ready snapshots are sequential, not atomic. Driver rechecks flags/generation/ticket and ignores mixed-time busy snapshots. Raw alias transactions above1,024bytes must be rejected before writes by both driver and adapter: arbitrary longer SPI can wrap the inherited12bit CSR address, so hostile raw-burst fail-closed protection is not claimed.
- Actual V52 and V55 Rust + native FFI + selected RTL/SDRAM/HBU/scanout each pass the original KEY/P pair:2accepted/presented,42,240 actual HUD comparisons and zero canonical/raster/HUD mismatches. These use direct CSR RPC,200ms modeled Prepare service and zero native virtual CPU time. They prove composition, not physical speed. The models also advance100microseconds per yield, while the target Adapter calls std::thread::yield_now without a fixed sleep. Stage values include this model quantization.
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

The [actual V55 Rust/RTL/SDRAM twelve-new-frame replay](../../fpga/experiments/cu66-v71/stb1-v55-video12-system-20261108/REPORT.md) now passes:12accepted/presented,0rejects/underruns,253,440 actual HUD writes/readbacks, zero mismatches across6,220,800canonical bytes and4,147,200composed video pixels. HX33→HU25 predictive-envelope transition passes. The initial planar-versus-tile oracle mistake is preserved, with two independent conversions cross-qualified on the old KEY/P goldens before comparison. Frozen source/packets stayed unchanged during the run. Host logical arena peaks95,053/98,304, leaving3,251bytes of logical headroom; physical target fit remains a hardware gate. Live encoding, general continuous receiver lifecycle, network/video30fps, AV coexistence and the full120second custom stream remain unqualified.

## Next physical ladder

1. Complete the one-time DFU driver qualification and protected app-only backup/update workflow. If unavailable, keep doing offline work and leave flash untouched; do not erase or force-release a native endpoint.
2. Install V54 as the first ABI3 correctness/observability control; confirm exact SDK ELF, cold/soft-reset reason, memory/stack, then volatile-program selected V028, verify DONE/USERCODE/ABI3 and old-profile refusal. Restore .33 as the RAM-only custom host.
3. Original3 then12 historical fixtures, full readback, fresh sessions and independently reconciled presentation replies. Freeze diagnostics on failure. Measure staging/QSPI transactions, HUD CPU/write/readback, decode/drain, actual unique presentation and heap/stack, without cross-machine clock subtraction.
4. If healthy, V55 with the same BIT/fixtures/conditions. Native CPU12 and runtime stack/fragmentation gates first; do not attribute combined speedup to one fragment. Keep V49/50/51/V53 ABI2 images for isolated comparisons if needed.
5. Run the new local video12 package only after the matching full-system replay passes. Then build a longer independently decoded package and explicit bounded/continuous transport profile. Do not feed the old JPEG/MSV1 payload to this decoder or call CU66 quality Q30/Q35.
6. Reach a correct longer video-only replay before independently sequenced controller/audio coexistence or30unique displayed frames/s acceptance. Exact source, configured/sent/admitted/decoded/presented rates, stage times, trace loss and recovery/STOP results must stay separate.

Keep V48/V027 and the exact JPEG/build50 archive D:/moon/backups/JPEG-V38-BUILD50-20261107.zip as recovery controls. All active work stays under C:/moon; retain selected evidence before pruning caches. No external Sunshine sender start is requested by this report.


## Additional native and memory-model gates

[The sanitizer audit](../../firmware/experiments/v55-native-sanitizer-20261108/README.md) runs the exact V55 native endpoint and existing oracle harness under local WSL GCC11.4 ASan+UBSan, at-Os and-O2. Both pass old3/new12, full/sliced READ comparisons, fault/rollback/recovery cases, arena98304 and no allocation failures; no sanitizer report. These host results do not establish Xtensa stack, physical fragmentation or exclusive task CPU time.

[The strict Xtensa compiler audit](../../firmware/experiments/v55-native-opt-audit-20261108/README.md) retains-Os. It reproduces the selected target stack frames752/160/224/48bytes. Merely changing to-O2/-O3 fails existing-Werror=maybe-uninitialized checks around allocator ownership/optional-string cleanup. Source hashes are unchanged. The cause remains unresolved; do not suppress the warning or infer either a real runtime bug or a false positive from it alone. A minimal lifetime reproducer is a later independent task, not a change to the current candidate.

The completed new-video model starts SDRAM at zero, uses accelerated20cycle powerup/750cycle refresh, direct8cycle CSR accesses,100us modeled yields and200ms modeled Prepare service. Front banks alternate0/1; bank2 is not exercised. The [selected V028 twelve-frame poison replay](../../fpga/experiments/cu66-v71/stb1-v55-video12-poison-system-20261108/REPORT.md) now also passes all12presentations and every canonical/pixel/HUD comparison, including the HX33→HU25 transition. An executed16,777,216word fill witness binds the deterministic nonzero pattern; outputs exactly match the independent references and zero-start control. One pattern is not exhaustive unknown-memory coverage. The [separate CE pair controls](../../fpga/experiments/cu66-v71/stb1-v55-cefactor-system-20261108/README.md) pass zero/nonzero models, but do not confer timing closure or twelve-new-frame execution on the CE variant.


## Final handoff

Use [morning readiness](MORNING-READINESS-20261108.md) for exact selected images/current blocker/test order. All Vivado and model jobs are finished; rejected experiments remain evidence. The original JPEG/build50 archive hash was rechecked unchanged. New work stays underC:/moon.

The [separate normal-reboot helper](../../host/lab-selftest-v1/normal-reboot-v1/README.md) is OFFLINE_ONLY:20fake-backend tests, default dry run, exact verified apply/backup/plan/journal bindings, live read-only preservation checks, durable content-keyed one-attempt claim, then only normal reboot request1/value1. It never writes flash, retries or treats ACK as reset success. Existing DFU client is unchanged. Source-contract pins are not an installed updater association. Post-DFU composite parent/CDC/vendorMI00 return and exact SDK ELF remain physical gates; updater-root WinUSB persistence is unknown. No actual helper USB call or driver installation occurred.

The agreed public Windows CU66 branch was rechecked at15ca34224a7f08fda274ec7e9e9af5e448071f9c; it still describes offline qualification. The [next Windows preparation prompt](../SUNSHINE-NEXT-CU66-PREPARATION-PROMPT-20261108.md) requests pinned offline validation and no transmission until a fresh receiver START. This does not establish absence of work on other uninspected branches.
