# MoonBub morning handoff — 2026-11-05

The overnight work produced independently packaged ESP32 candidates, an optimized CP23 decoder component, and an actual routed CPL1 board diagnosis. **The custom FPGA still fails setup timing; no BIT was generated and 30 unique physically displayed frames/s remains unverified.** Installed v30/build50, overlap and the 32-slot queue were unchanged. No hardware stream, flashing, JTAG operation, SD change or Windows pacing change occurred overnight.

## Ready and blocked paths

| Path | Result | Next gate |
|---|---|---|
| Existing JPEG/AV hardware | Last measured baseline remains v30/build50 | Fresh identity/network checks after power-up; proposed v31-only regression |
| v31 ESP32 trace-lock reduction | Target build, source export and host checks passed | Physical regression, matched trace-v2 collector; uninstalled |
| v32 local CPL1 observer | Read-only snapshot command, target build and offline checker passed | Requires a separately qualified CPL1 image; uninstalled |
| v33 AV restore-failure fence | Target build and focused production-fragment/session tests passed | Separate controlled AV failure/recovery regression; uninstalled |
| CP23 address-strength component | Functional equivalence passed; 10 fewer DSPs | Global unplaced setup still fails at −2.277 ns; not adopted into board |
| CPL1 actual board | Full digital/native/QSPI replay passed; all nets routed | Routed setup **−1.618 ns**, 13,015 failing endpoints; no BIT |
| Custom network streaming | No carriage/port assigned | Agree versioned bounds, credits, recovery and readiness before implementation |

The selected first custom fixture remains restricted **CP23/HC22/HD22**, independent KEY frames and the implemented mode-0/HR01 INDEX_RUNS2 subset. CP25 is not selected. CPL1 is a fixed local ROM diagnostic with CAPS=0; it is not MSV1 video or a custom network service.

## ESP32 deliverables

Use the individual handoffs and source manifests; do not combine candidates silently:

- [v31 trace-lock reduction](V31-RECEIVER-CANDIDATE-HANDOFF-20261105.md): removes phase-maxima scans from the hot trace mutex. UF2 SHA-256 `380bf1c894744cc38e3b7988c8d1aaa4c10faefd499cca937eb27548a639024b`. Static shared SRAM 130,436 bytes. It does **not** implement the proposed identity journal or establish a whole-task stack bound.
- [v32 CPL1 observer](V32-CPL1-OBSERVER-HANDOFF-20261105.md): fresh-cookie, generation-checked 40-word snapshots, ten cached pages, bounded polling and strict image/profile checks. UF2 `13c27ca9a919dd7d40b7ff7aa4d55e5d97e00ad79e596d5aeee732966e9c3d4d`. No decoder start/reset/upload command.
- [v33 AV restore fence](V33-AV-RESTORE-FENCE-HANDOFF-20261105.md): retains a failed power-save restoration as a sticky recovery failure instead of allowing a later empty guard to report successful release. UF2 `a3a7cb727cf2ce4074e576f4f312e4fc8bb504757d82161cb7626a03959815f2`. Static shared SRAM 130,812 bytes, unchanged from v32. This is tested failure handling, not evidence that power saving caused earlier losses.

The portable exports include exact sources, licenses, build helpers and selected artifacts. They need external ESP Rust/ESP-IDF toolchains and caches, not an assumed second GameBub repository. Relocated builds were verified for v31/v32; v33 has its original target build and a fresh exported host replay, not a second relocated target-build claim.

## FPGA findings and next implementation

The actual routed board uses source freeze `58be226c18264735705f38c4e4f606c2d6d69e7e3003e5ad1b8a4019cf2d3bcc`, routed DCP `04a54e2316064bdf5e08bc129f40cf53064a2a4e23f72740cbdc2a16dc4dbd24`. It has 27,274 LUTs, 24,558 FFs, 108 RAMB36 + 4 RAMB18 and 47 DSPs. All 50,673 routable nets routed, hold +0.015 ns, setup −1.618 ns/TNS −7795.573 ns. Positive hold and complete routing do not clear setup failure.

The measured worst families are gather request-address arithmetic, HUD RAM-address arithmetic, epoch/identity-to-controller admission, and high-fanout HUD SHA block-enable control. The new constant shift/add/subtract successor preserves original truncation and all state/latency behavior. It passed 740,672 arithmetic comparisons, 349,440 native gather pixels, 691,200 full-composite pixels and the physical burst-abort model. It removes ten DSPs (47→37). Matched **unplaced** local estimates improve gather −1.968→+0.856 ns and HUD +0.014→+3.897 ns, but global setup remains −2.277 ns. These are not routed-board improvements.

Next, stage the remaining identity/cancel/ready and block-enable control paths, preserving immediate invalid-transfer masking, owner identity, settled drain and quarantine. Re-run targeted cancellation/error tests before whole-composite tests. The separately tried registered-result-fault change regressed global timing to −2.649 ns and is not selected. Then integrate the qualified address/control changes into a fresh board candidate and repeat implementation with unchanged clock and I/O budgets. Do not lower clocks or weaken constraints to label this closed.

Final mapped ROM reconstruction and actual RAMB primitive reads match all 17,412 fixture bytes; 576 factor vectors cover all 384 eight-bit quantizer entries and their zero extension. These prove mapped content, not complete mapped-loader handshake, electrical behavior or warm-reset retention. An uncapped inventory retains all 403 unwaived RAM-control warnings across 112 RAM cells. Reset/CDC containment and external QSPI hold remain qualification gates.

## Portable reproduction

- `fpga/exports/cp23-address-strength-component-source-20261105-0541`: exact arithmetic successor, source verifier, native oracle inputs, short/full replay helpers and measured reports. Manifest `b007b6bf9a11998695f143562b0c03488eac9bde7f6d382938faeaf76daba791`.
- `fpga/exports/cpl1-source-replay-v002-20261105`: exact actual-board source, constraints, five runtime assets, digital primitive/memory models, source verifier, smoke/full replay helper and independent snapshot checker. ZIP SHA-256 `5ba475b23aee08dbb2accbc40d9f2a11ae178270bab61d42fec3ae85b7041c7f`. It contains no BIT, DCP, executable or vendor libraries. Digital replay requires Icarus; board synthesis requires separately installed licensed Vivado/device support.
- [Measured timing lineage](FPGA-TIMING-PROGRESS-20261105.md), [source/rate budget](30FPS-SOURCE-BUDGET-20261105.md), and [retained v30 correlation closeout](V30-SEQUENCE-CORRELATION-CLOSEOUT-20261105.md) separate source simulation, unplaced estimates, route results and physical evidence.

The original source-bound full board replay passed, and the fresh extracted v002 smoke replay passed. A new extracted-package full-helper replay is being recorded separately; its final result must be checked before claiming that additional integration run passed.

## Hardware sequence toward 30 fps

1. Run the [controlled legacy regression](NEXT-HARDWARE-TESTS-20261105.md) with v31 as the single candidate variable and build50 unchanged. Freshly verify device identity, endpoint/source filtering, counters, camera coverage and packet capture through STOP. Keep v33 and host pacing experiments separate.
2. Close actual custom-board setup, reset/CDC/I/O and mapped-image gates before producing a programming candidate. First physical custom test is local ROM only, using v32 observation and independent CRC comparison.
3. Prove two distinct complete KEY frames and safe old-reader retirement before general bank reuse. Repeated scanout of one held image is not unique displayed FPS.
4. Agree custom transport/session recovery and credits; measure FPGA-only throughput, then concurrent receiver throughput. Only then run a measured unique-frame ladder toward 30, followed by audio/controller coexistence.

The first two synthetic fixtures alone need approximately 4.18–4.25 Mbps of JPEG-independent compressed payload at 30 fps, before protocol overhead. A 4 Mbps cap cannot carry those exact fixtures at 30 fps. This is a calculated budget, not a selected network rate or a physical throughput result. No unsupported 30 fps acceptance claim is made.
