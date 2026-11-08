# V45: ESP32 ingress cache and longer bounded host sequence

November 7, 2026, America/Denver. This work is primarily **ESP32 firmware and host tooling**. The selected FPGA remains the exact qualified V027 image; no RTL/clock/pin/SDRAM change or new BIT is required for this candidate. Current physical V44/V027 final endpoint remains held and untouched.

## Changes implemented

- ESP32 caches only the checked HU range while forwarding the incoming packet into FPGA storage, reusing the same bounded HC70 input allocation rather than adding a full-frame buffer. Whole-packet/staging integrity and the live FPGA HUD request identity/range/tag must pass before native use. Cached mode eliminates scalar command21 HU fetches; explicit scalar control remains available. Full HUD write/readback/drain/commit/presentation checks remain.
- Finite sequence API accepts1..12,000 frames but stores only the most recent three stage records, keyed by actual ordinal/frame/generation. Memory and report storage do not grow with run length. The exposed first hardware selectors are cached3 (`~`), cached12 (`@`) and scalar3 (`^`), with fresh owner/boot for each trial.
- Retained diagnostics export one indexed record per40ms through the existing USB task. BEGIN/END, epoch/attempt/count and payload checksum detect incomplete output; `$` requests read-only re-export. No new worker or unbounded logging queue. Failure snapshots preserve last observed identity/phase and transport progress; detailed partial per-stage arrays remain explicitly unavailable.
- Native owned motion prediction is reconstructed in place per independent RGB channel. Immutable plain prediction stays borrowed. This removes transient duplicate pixel storage while preserving output and transaction authority. First12 previously hit the98,304-byte arena ceiling at frame4; final native first12 passes at the original ceiling and unchanged8,192-byte reserve in the conservative114,688-baseline model (peak92,544, modeled minimum19,747). Physical SRAM/fragmentation/stack still need measurement.
- Host package [dy71-sequence-v3](../../host/dy71-sequence-v3/README.md) sends an explicitly selected3- or12-frame prefix, one frame in flight and actual presentation before continuation. Version3 includes finite count at header offset46, echoed and matched in all replies. Count/version mismatch is rejected before transport header admission/staging START. V44/v2 remains untouched.

The12 packets are distinct historical Mass Effect-family frames with fresh canonical/HUD/display oracles. They are **not** the requested120-second source or a12fps test. JPEG Q settings do not apply to CU66.

## Verification gates

Actual driver/native/wire suites passed59 tests; retained/paced telemetry suite passed11; host uploader8 and cross-language wire11 passed. Actuallocalhost cached12 passed12matching presentation replies,253,440HUD word comparisons, zero command21 calls and complete indexed/checksummed telemetry. FPGA MMIO and target health are modeled in localhost tests; those results establish software interaction, not RF delivery or physical throughput.

Target build/run02 passed with frozen handheld/native inputs. Exact selected ELF is `0c263a944775f5523cc7eb316bdacfb44da02c193f444fc5136644b90318f643`; UF2 is `ead4b81da7fe2e697d094acfba2b7d514df7e8500ddfd373742ccf9f24595a12` under `firmware/experiments/v45-dy71-ingress-cache-20261107/release-ingress-cache-v001`. Static shared SRAM131,572bytes passed the unchanged163,840 guard and effective SDK checks. The production updater parser accepted13,367 app-only UF2 blocks and exact BIN round trip. Initial run01 failed a Rust job-channel type inference check; explicit `Job` typing fixed it, and that failed build is preserved separately.

The exact-selected V027 cached5 full-system replay passed:5accepted/5presented, zero rejects/underruns,105,600 actual HUD comparisons, all canonical banks and1,728,000 composed pixels/borders equal, and independently observed command21count0. It exercises the new motion-coded frame4 and bank reuse. A failed initial attempt loaded an older DLL through the copied environment; it is preserved separately, and the final replay pins the actual loaded DLL path/hash. The final source gate covers compiled imports; unrelated worker-source drift is recorded separately and checked by the complete target build. CPU/QSPI timings are modeled; no FPS claim is permitted. The selected offline candidate is ready for cached3 followed by conditional cached12 physical trials; it has not been installed.

Local receipts: `C:/moon/maintenance/v45-sequence`, `v45-telemetry`, `v45-localhost`, `v45-native-inplace` and `v45-system-cached5`; target records under `C:/moon/builds/v45-target-run02`. Source/cache outputs remain under `C:/moon`, using the shared warm custom cache `t/c44`; exact V44 release images remain preserved separately and are not replaced by target-cache contents.

## Latest physical result

[Cached3 passed end to end](V45-V027-CACHED3-RESULT-20261107.md):3presented/0rejects/underruns,63,360 actual HUD comparisons, complete telemetry and read-only re-export validated. Native minimum free15,664 and network-worker stack low-water4,780bytes were captured. Windows confirmed all3matching presentation replies/count3. Next is the fresh-boot cached12 trial; no extra firmware update is needed.

## Next physical ladder

1. After all offline gates pass, install only the selected V45 app-only package in a coordinated update window. A physical power cycle/update-mode step also clears V44's held lease. Reload unchanged V027 and verify exact ELF/DONE/USERCODE/ABI, fresh owner, IP/filter and heap/stack. Keep all senders stopped until coordinated readiness.
2. Run cached3 with the exact original KEY/P/P packets and explicit v3 count3. Compare with V44's scalar3 observations. Zero command21 is a checked structural result; ingress-cache span includes receive/staging time and must not be labeled copy CPU cost or directly compared with old post-admission scalar extraction duration.
3. Verify complete telemetry export, including network worker stack/minimum heap and target arena peak. If output is incomplete, request retained re-export using `$`; do not rerun the video to recover diagnostics. Any ownership, memory or correctness failure stops escalation.
4. With a fresh qualified boot/owner, run cached12 and compare all12 presentations, reference/bank reuse, actual HUD checks and complete report. Stop on unknown/rejected outcome; no automatic retry, session restart or KEY-recovery claim.
5. Extend lifecycle/recovery and actual Windows encoding, then test a short moving-video interval and finally the120-second clip. The current slow stop-and-wait/full-readback diagnostic is not a30fps streaming release.

## Separate FPGA/UI follow-up: Power menu overlay

The ESP32 Power key handler still invokes `power-menu.show()` in `handheld/res/ui/main.slint`. The selected V027 top leaves the normal QSPI overlay data/bounds outputs unconnected (`overlay_xctrl`, `overlay_yctrl`, `ov_wr`, `ov_addr`, `ov_data` in the frozen reset-bufg-v027 top). Its direct DY71 scanout therefore does not display the ordinary ESP32 popup over the custom image. This explains the missing visible overlay on that image; actual physical-button event delivery was not separately measured by this source inspection.

Restoring it requires a qualified FPGA overlay/composition path with the existing pixel/bounds format, memory/scanout budgeting and frame-boundary/CDC checks, plus a safe pause/exit or power action that respects the retained native owner. This is separate from V45 ingress caching. Do not alter V027 or force-release its active lease during the current comparison. V45 does not claim Power-overlay support while the custom image is active.

## Windows work required for the original two-minute clip

Prepare source SHA `fb01977e41e649bfb9fd53d1ee0e6db436127fb86e4b3b7ec303158e0568aff5`, offset0/no loop, and the approved720x480 canvas with720x405 content at(0,37). The original file is not established on this local machine. The Windows owner should report current encoder branch/commit/capability and build an output-only adapter around the supported causal CU66 research path if no live encoder exists. Enforce exact accepted arithmetic/profile/zero-base-motion constraints and HUD semantics; preserve accepted reconstruction/reference identity, packet/HU limits and an explicit oversize policy. Validate all output against the software oracle before transmitting.

Neither new retained fixtures nor an offline decoder constitute a real-video encoder. No two-minute START or automatic hardware trial is issued by this plan.
