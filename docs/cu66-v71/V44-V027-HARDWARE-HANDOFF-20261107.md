# V44 / V027 bounded-three hardware test

November 7, 2026, America/Denver. This is the next controlled correctness and stage-timing trial. It is **not the two-minute Mass Effect replay or a 20/30 fps acceptance test**. The original exact KEY0/P1 pair is followed by a distinct retained Mass Effect-family P2/ref1, exercising bank reuse 0 -> 1 -> 0.

## Exact candidate

- ESP32 source: `firmware/experiments/v44-dy71-three-frame-20261107`.
- Selected release: `release-bounded3-v001`; use no intermediate target01/02 ELF.
- ELF SHA-256: `f92e3df64a104657957e0d9c86e7a1b79d4f07e2febb5f6fb40a6dd11da76110`.
- UF2 SHA-256: `e2f5a90143015cefeea367158f957638de4eeac4bdc3838eb49077a70952c903`.
- BIN SHA-256: `c8ecb5e2b84527cabb627baa0b8f3245437fee5e437129c477ca6eb6742128f3`.
- Unchanged V027 BIT: `C:/moon/dev/dy71-v027-20261107-v001/image01/moonbub-v027-lab.bit`; SHA-256 `9922aa617c21a03e8a31f932d45e22d905e91d4e263ef593692898d363d07dee`. Require DONE1/USERCODE `4459373f`, DY71 ABI2/caps31 and HBU1. No FPGA rebuild is needed for this native-software change; the existing selected BIT's routed timing/source qualification remains the FPGA control.
- Network: explicit `dy71-bounded3-v2` on UDP5535, DYN1/DYA1 byte4=2. Version1 is rejected before staging. No negotiation is implied.
- Host package: [bounded-three uploader, exact packets, manifest and golden vectors](../../host/dy71-bounded3-v2/README.md).

## Completed build/package evidence

Target03 compiled with esp193/ESP-IDF5.4.3, offline locked release/rev4. Handheld/native inputs were unchanged during build. Static shared SRAM is **130,948 bytes**, below the retained 163,840-byte build guard. Effective SDK configuration checks passed. Production updater parser accepted **13,290 UF2 blocks**, checking Rev4 identity, application-only addresses and exact BIN round trip. Build logs/manifests are under `C:/moon/builds/v44-target-run03`; packaging/checks are under the selected release's `verification` folder.

The native arena is again the original **98,304-byte cap**. The initial 114,688-byte free-heap /24,576-byte largest-block checks and per-allocation **8,192-byte physical reserve remain unchanged**. A corrected immutable-reference borrow for HS plain prediction avoids unnecessary copies; owned motion prediction and output buffers remain separate. The historical-baseline allocator/wire-lifetime model now passes all three frames at peak92,379 bytes versus103,484 before the fix. This model is not a physical heap/fragmentation proof.

## Functional evidence and boundaries

- Final actual-native/driver/wire suites:46 tests passed. All63,360 HUD words are written and actually read back; failures/lost acknowledgment tests do not invent a third presentation.
- Five bounded log-export tests passed. Maximum formatted record is241 bytes including an80-byte prefix allowance; oversized single Debug output was removed. Failure output explicitly says partial stage arrays are not retained.
- Published Python uploader pure tests and Python/Rust golden-vector interoperability passed, including CRC-correct version1 rejection.
- Final-source actual localhost uploader -> V44 socket receiver/driver/native service passed all three matching status2 replies and63,360 word comparisons under the98,304-byte cap. FPGA MMIO is modeled in this test; it does not establish RF delivery.
- Actual final native semantic regression decoded457 retained frames and compared9,651,840 HUD words plus malformed-input rejection controls. Its broad-corpus logical cap is1MiB to isolate semantics; only the exact three-frame cohort is qualified against the target arena budget.
- Final exact-selected V027 decoder/control/rows system replay **passed** with the corrected native source and98,304-byte cap:3accepted/3presented, zero rejects/underruns,63,360 actual HUD readbacks, all canonical bytes and1,036,800 composed pixels/borders equal. The earlier larger-arena/pre-fix run is preserved as a separate control, not final-source evidence. The functional model omits physical SPI/CDC/PLL and real ESP32 CPU scheduling; no throughput claim follows from its virtual timestamps.

Local detailed evidence is indexed under `C:/moon/maintenance/streaming-verification-20261107` and `C:/moon/maintenance/v44-localhost`. The readiness receipt records the final executed gates and hashes. Physical playback remains untested for V44 until this trial is completed.

## Physical window and Windows preparation

1. Keep all host senders, JPEG, AV/audio and controller injection stopped. Reserve the handheld/JTAG adapter for this trial. Reinsert the microSD after the backup; leave USB and JTAG connected. Current device state/IP is not inferred from historical results.
2. Once offline gates are recorded as passed, enter GAME BUB update mode for the selected app-only UF2. The current Windows control-interface driver requires the physical power/Volume-minus step. Preserve partitions, settings, SD files and exact V43/build50 rollback artifacts.
3. Check post-reboot exact V44 ELF identity. With a fresh native owner and adequate programming memory, load only the selected unchanged V027 volatile image, verify DONE/USERCODE/ABI/HBU and clean counters. Do not change FPGA images underneath a retained native endpoint.
4. Windows prepares the separate bounded3-v2 package. After boot/reset is confirmed, start one uploader invocation in its600-second initial-wait mode and report actual source/session; receiver owner then verifies IP/filter, heap/largest/stack and arms the explicit V44 lab worker. Do not substitute the old pair uploader or send a video loop. Prepare command, not an unattended START:

   `python bounded3_sender.py --profile dy71-bounded3-v2 --receiver 192.168.0.157 --bind 192.168.0.47 --initial-wait-seconds 600 --log fresh-v44-bounded3.jsonl`

   The addresses are historical intended values, subject to fresh receiver/host confirmation. Wait for actual matching status2 replies for KEY0, P1 and P2. No whole-run retry; any failure or unknown outcome stops the sender.
5. Capture USB records and the display through completion. Collect the new request/snapshot/extraction/native/write/readback/drain/commit/presentation timings, QSPI counts, free/largest/minimum heap, native peak and stack high-water. Do not subtract host and receiver clocks. A missing stage on error remains unknown.

## Physical acceptance and recovery

Require independent3accepted/3presented, zero rejection/LCD underrun,63,360 actual HUD words verified, matching host status2 identities and expected natural scene/color. Inspect measured heap/stack/reserve rather than treating the static SRAM guard as runtime proof. Any guard refusal is a safe failure to investigate, not permission to lower the reserve.

Success intentionally holds the final endpoint/lease. Mutated errors retain/quarantine as before. No STOP/session restart protocol for continuous playback is implemented. Keep the sender stopped afterward; use the qualified paired reset/reconfiguration workflow for another test, never force-release live ownership.

After this bounded three-frame hardware gate, choose the next service-cost fix from the measured phase breakdown, extend bounded lifecycle/KEY recovery, and integrate a real Windows CU66 encoder before returning to the requested120-second clip. JPEG Q30/Q35 labels are not CU66 quality settings.
