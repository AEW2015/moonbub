# FPGA timing cleanup, 2026-11-05

Physical update: [local CPL1 hardware report](CPL1-LOCAL-HARDWARE-20261105.md).
The fixture failed rendered CRC (`dec6d87d` versus `4c5725e5`) in two fresh
snapshots. Build50 was subsequently restored through volatile JTAG; v32 observer
firmware remains installed. Custom network testing is blocked. The offline
qualification below remains valid within its stated model assumptions.

Next design work: [timing-margin improvement plan](FPGA-TIMING-MARGIN-PLAN-20261105.md),
covering source-level FF replication, complete pipeline stages, bounded widths,
fanout/reset review and a proposed +0.250 ns repeatable setup-margin target.

Declared routed timing now passes. The selected offline image uses `cp23-timing-raster-reservation-20261105`, result `route-qspi06`: setup **+0.017 ns**, hold **+0.032 ns**, pulse **+2.000 ns**, zero violations; all four bus-skew constraints meet (minimum +3.450 ns). All 49,960 nets route without errors. Margins are small and reported exactly. At offline qualification, installed v30/build50 was unchanged; the subsequent physical window is reported above.

The [sealed source/image bundle](../fpga/exports/cpl1-timing-fsmcopy-source-20261105-v002/QUALIFICATION.md) includes the exact source, constraints, assets, physical recipe, generated BIT, reports, licenses and executed model/fault evidence. [Local handoff](../fpga/exports/cpl1-timing-cleanup-local-handoff-20261105.json) binds the retained routed checkpoint as well. Native DRC has zero errors and 472 retained warnings; no severity waivers were added.

The target is the actual `moonshine_top_cpl1` Artix-7 XC7A100T-CSG324-1 design, with its original clocks, pins and external delay budgets. This is the restricted independent-KEY CP23/HC22 diagnostic path, fixed ROM input and CAPS=0. It is not a new MSV1 network decoder, full CP23 implementation or evidence of 30 unique displayed frames/s.

The selected cleanup replaces variable address multiplication with qualified arithmetic, registers accepted SDRAM requests before row lookup, separates HC header validation phases, captures validated patch/frame bounds, replaces a 256-way palette-used reduction with an exact distinct-symbol count, reserves coefficient/prediction writes, and stages envelope replay reads and complete raster tuples. Its canonical physical recipe runs AlternateReplication, AggressiveExplore, AlternateReplication, then inserts one identical QSPI FSM-bit register copy beside its decoder. The image writer independently rechecks the final source/copy D/C/CE/R nets, INIT and available inversion parameters. No clock, pin, delay budget or timing exception is relaxed.

Later experiments additionally reserve SHA byte writes, capture replay descriptors, register pixel-conversion inputs and stage final tag validation. Those changes are not in the selected BIT. The unchanged source assets and wire profile remain explicit; a later version number alone does not imply image selection.

Every source candidate is fresh and frozen. Previous failures are preserved. `fpga/report_cleanup_result.py` binds the implemented input files and requires positive setup, hold and pulse slack, zero violating endpoints and zero routing errors. Process exit status alone is not acceptance.

The selected source changes nine RTL modules relative to the original portable board source. Review these before the generated fixtures:

| Module under the bundle's `inputs/` | Selected change |
|---|---|
| `core/cp23_key_composite_scanout_local.sv` | Strength-reduced geometry/address arithmetic |
| `core/cp23_key_private_join.sv` | Registered child cancellation |
| `core/compute/ar03_envelope.sv` | Complete accepted read reservation |
| `core/compute/ar03_inverse.sv` | Private coefficient-write reservation |
| `core/compute/ar03_reconstruct.sv` | Matching prediction-write reservation |
| `core/compute/ar03_key_tagged.sv` | Complete raster-input tuple reservation |
| `core/parents/ar03_yuv_line_gather.sv` | Qualified address arithmetic |
| `core/parents/hc22_key_hud.sv` | Staged header validation, bounded indices, palette cardinality |
| `core/parents/moonshine_sdram_burst.sv` | Accepted request dispatch before row lookup |

The physical FSM copy is in the final recorded implementation-chain Tcl, with a separate sequential-function proof. These source changes and the physical recipe must travel together. The selected SHA engine is unchanged from the original source.

| Candidate suffix (all dated 20261105) | Final routed setup WNS, ns | Result |
|---|---:|---|
| Original `cp23-local-rom-optimized` | -1.618 | Fail |
| `timing-cleanup` | -0.913 | Fail |
| `timing-dispatch` | -0.488 | Fail |
| `timing-patch-bounds` | -0.177 | Fail |
| `timing-frame-bounds` | -0.503 | Fail |
| `timing-local-load` | -0.172 | Fail |
| `timing-palette-seen` | -0.546 | Fail |
| `timing-raster-reservation` | -0.157 | Fail |
| `timing-sha-write` | -0.292 | Fail |
| `timing-plane-descriptor` | -0.488 | Fail |
| `timing-pixel-reservation` | -0.443 | Full model pass; route fails |
| `timing-raster-reservation`, alternate post-route | -0.063 | 24 setup endpoints fail; hold, pulse and all four bus-skew constraints pass |
| `timing-tag-validation`, default route | -0.004 | Full model pass; default route fails |
| `timing-tag-validation`, alternate post-route | +0.003 | Declared timing/model pass; unselected, no image generated |
| `timing-raster-reservation`, final FSM-copy route | **+0.017** | **Selected; timing/model/image/source delivery pass** |

The actual-board digital replay uses physical pad branches, custom primitive and bounded SDRAM models, native QSPI observer reads, an independent fixture/CRC checker, and scanout line deadlines. It does not define `SIMULATION`. The completed descriptor candidate passes 139 snapshot checks, 40 CSR reads, CRC `4c5725e5`, 259,200 pad writes and all 1,440 line latches. Minimum modeled line lead is 2,818.878 ns. Two held scans of one input image are not a throughput benchmark.

Focused tests include randomized accepted SDRAM requests with poisoned subsequent inputs, refresh/read priority/cancellation, HC malformed/admission/palette boundary cases, SHA known-answer and cancellation tests, replay ownership/error/reset fences, inverse numerical oracles, cropped output drains and whole-core abort/late-tag-failure cases. Each evidence directory retains copied test inputs, commands, logs and hashes. The reconstruction reservation passes 618 blocks, 36,312 visible samples, 50,784 backpressure cycles, seven negative cases, 434 reset/abort cases and 60 cropped drains, including explicit first/last-visible and hidden-tail cancellation. Its unchanged inverse passes stalled and unstalled arithmetic comparisons. The full native board model also passes against this source with the same CRC and minimum line lead as the descriptor candidate.

The unselected tag-validation candidate registers the exact canonical hash owner/epoch/128-bit-tag comparison before allowing completion. No tag check is omitted. Full-board model, smoke, metadata, fault, late-hold and cancellation tests pass, including reset/abort during the new pending-tag state. Its alternate route also meets declared timing, with +0.003 ns setup and +0.016 ns hold. An accepted-command reservation is separately prepared but untested and unselected. A SHA counter-width variant passes 27 known-answer/boundary cases, four negatives and 297 reset/abort cases at its default bound; it has not been implemented or selected. Its first syntax-failed candidate is preserved separately from corrected v002.

Reset distribution was investigated separately. Automatic post-route replication was unsupported; pre-route replication was refused because constraints could not be copied. These attempts failed closed. One explicit-copy trial was rejected for hierarchical reconnect warnings and its owned process was stopped. The guarded follow-up verified every reset load reconnect and each copy's original D, clock, CE, asynchronous PRE and INIT. Only the original asynchronous PRE exception extended to identical copies; synchronous downstream reset paths remained timed. Its final route was worse (-1.452 ns); it is rejected and is not part of a selected implementation.

Retained timing-coverage gaps are explicit: 17 inputs without delay, two outputs without delay and one partial input-delay declaration. Existing asynchronous/diagnostic I/O coverage, including QSPI external hold, is not promoted to board signoff by internal timing closure. DRC, CDC, bus-skew, licensing, portable reproduction and any final image are separate gates.

The selected source package passed a fresh external-directory smoke run and all 305 package-file hashes verify. The full source-level native model and independent CRC check bind the selected 35 product RTL files. The source package supplies the complete P&R recipe; a second full P&R rebuild was not executed during packaging. The routed DCP SHA-256 is `1ba75d3f26a1a6701d560a25cea4d32e8859cafd4659b6b67cf6f94cb7f53eeb`; BIT SHA-256 is `e11a193a8cfe51b90053c852bdbb3d9308225bc1d115564418a64e016d6df789`.

No hardware programming or new stream occurred. This closes the offline declared-timing task for the restricted diagnostic; sustained physical throughput and 30 unique displayed fps remain separate work.
