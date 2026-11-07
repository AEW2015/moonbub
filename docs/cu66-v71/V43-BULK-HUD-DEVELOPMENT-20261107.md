# V43 / V025 bounded bulk HUD development

This is the next development candidate after the physical V42/V023 KEY/P pass. It is not installed, timing-qualified or a live-video/30 fps result. The physical V42/V023 endpoint and final-image lease remain held and untouched.

## Measured reason for the change

The same original KEY/P pair took V42 35.050912 seconds, including 28.430830 seconds of HUD write/readback and 392,927 QSPI attempts. Every one of 42,240 HUD words was read back and verified. The native HU preparation itself took 304,230 and 209,963 microseconds, so bulk transfer is one bottleneck repair, not a complete 30 fps solution.

## Candidate implementation

V025 adds a 512-byte scratch buffer (two RAMB18E1 primitives) and a checked sequential AUX engine. V43 packs up to 256 16-bit HUD words into one QSPI payload transaction, requests actual AUX completion, then reads back blocks and compares every word with the unchanged native endpoint output. The existing owner, HUD ticket, SDRAM completion, drain and commit authorities remain in force. No count-only readback assertion replaces memory equality.

The FPGA system/decoder stays `cu71_system_final_v023`. LCD timing, placement, clocks, SDRAM budgets and pin constraints are unchanged. The separately explored V024 packet-capacity changes are not merged.

Profile: CSR magic `44593731`, ABI `00020000`, capabilities `1f`; intended BIT USERID/USR_ACCESS `4459373d`. V43 refuses the old ABI before writes. V42 refuses the new ABI. DYN1 on UDP 5535 and the original Windows uploader at `cbbd85fda` are unchanged; JPEG/MSV1 cannot drive this decoder.

The payload aperture is `0x400..0x5fc`. HBU1 status is `0x600..0x618`, avoiding the existing LD14 LCD observer at `0x380..0x3ac`. Opcode 22 sets up the identity-bound offset/count/mode; opcode 23 completes the actual word requests. Busy writes, incomplete/duplicate/out-of-order payloads, identity mismatch, owner loss and memory errors fail closed. Already accepted AUX operations drain before returning an error. Payload RAM is not reset; valid metadata is reset.

## Executed verification

- Actual native golden HUD output: 42,240 written words and 42,240 actual readback words, 84,480 AUX requests/responses; deliberate readback corruption is detected.
- Pin-level burst/control/CDC tests at 8 and 16 MHz with two clock phases, odd counts and scalar AUX regression. These use modeled owner/AUX memory, not the whole decoder/physical SDRAM.
- Old/current CSR regression: complete 4 KiB read sweep, ordered writes, queue overflow and reset. Declared differences are ABI/capabilities, new HBU registers and one synchronous-read settling cycle.
- AMD XSim against the synthesized standalone bulk engine and actual UNISIM models: unit/failure tests and all native words pass. The same tests also pass against the exact bulk cell exported from full build v003 (`xsim-full-synth02`, netlist SHA-256 `9b4c76459103f9fe89b55ed197505a432ec12f739849facfd9e95d9906e0e2a2`). Structural checks confirm both writable, unreset RAMB18s in that export. These are functional simulations without SDF; routed timing and physical playback remain separate.
- V43 host failure/loopback tests, target build, updater parser and effective SRAM build guard pass. Final ELF SHA-256 is `efd0a8650853f8d996dd22bfa4fb33d0d1b4da8678f453cb8304ac9579880fb9`; UF2 SHA-256 is `476520418833411a5f712bda2193ec17ea2132cbced7804627cd494e564fd33c`. Static shared SRAM is 130,932 bytes; runtime heap/stack still require device measurements.

An earlier inferred-RAM candidate passed behavioral simulation but failed official post-synthesis XSim: its CPU write address was mapped to the read address. That failed attempt and logs are retained. The current explicit-primitive implementation passes the same gate. The old full build `dy71-v025-20261107-v001` was stopped and superseded before any BIT/programming.

Full build v002 synthesized successfully, but cross-boundary optimization redistributed the exported bulk cell's ports; the component harness could not elaborate that export. This is a verification-boundary limitation, not an observed functional mismatch. A control-plane synthesis probe with `KEEP_HIERARCHY` on only the bulk instance preserved its semantic ports and passed both XSim unit/failure and complete native-word checks. The current frozen full build is `dy71-v025-20261107-v003`, with that narrow hierarchy attribute and no broad `DONT_TOUCH`, placement fence, timing exception or clock change. V002 continues as a reports-only timing diagnostic; it is not the image candidate. Final V43 firmware remains the same release-v002 ELF/UF2.

## Remaining gates and hardware sequence

1. Finish current full synthesis; audit writable bulk/chroma RAM ports and preserved reset/metadata/LCD structures. Re-run the native-word tests against the actual full-design bulk-cell export.
2. Place and route with unchanged constraints. Require strictly positive routed setup, hold and pulse slack, complete routes, unwaived DRC with no errors, and exact source/identity binding before emitting a BIT. No hardware readiness claim follows from synthesis or standalone simulation.
3. Publish the qualified source, reports, hashes and bounded test instructions. The manual evidence manifest must state that `c_check_handoff` is unavailable; inherited V023 decoder tests cover unchanged source only.
4. With Windows stopped, clear the old retained endpoint by a full power cycle/update-mode step; install the explicit V43 app-only image and verify its exact ELF. Load only the timing-qualified V025 BIT over volatile JTAG; verify DONE/USERCODE and ABI/HBU probes before writes.
5. Run the unchanged original KEY then P once, using the same waiting uploader and DYN1 handshake. Require matching presentation replies plus independent accepted/presented/error counters, all-word equality, heap/stack and visual checks. Retain the final lease on error; do not force-release an active owner.
6. Compare HUD write/readback and total times with V42. Only after correctness and measured gains, optimize native HU CPU work separately with byte-exact golden results. Live encoder/network streaming and sustained 30 unique panel frames/s remain later gates.

## Follow-on measurements before another optimization

Retain the existing per-frame packet-complete, admission, HU CPU, HUD-write-done, HUD-readback-done, drained, software-commit and actual-presentation timestamps, with QSPI attempts and verified words. Compare intervals only within each receiver run. The uploader wait/network interval must not be mislabeled as FPGA decode time.

If bulk HUD succeeds, inspect packet staging next: the current driver still checks completion for each small packet-store write. A credit-limited packet burst aperture is a candidate, but is not part of V025/V43 and needs its own admission, CRC, overflow and recovery tests. For native HU CPU, first profile entropy decode, reconstruction and tag/hash work separately; preserve all frozen KEY/P bytes, tags, word equality and memory limits before accepting an optimization. Do not increase the QSPI frequency, drop readback, or merge another codec/capacity profile to manufacture an isolated bulk comparison.

Another firmware candidate is to retain only the bounded compressed HU span while receiving the packet, rather than retrieving that same span from FPGA staging through one opcode-21 read per four bytes. The current path constructs the HC70 buffer after admission, so moving the same bounded buffer earlier may avoid a round trip without retaining a whole frame. This is not implemented. It requires a precise SRAM/lifetime analysis, checked span/copy coverage, unchanged whole-packet integrity and owner/ticket/tag checks, plus corruption and failure tests. Actual HUD SDRAM readback equality remains required. Measure this staging interval separately before selecting it as the next fix.

## Timing closure observations and fallback

The superseded v002 reports-only attempt had first-route setup -0.387 ns and hold +0.032 ns, with the remaining critical group in existing entropy control. It was stopped before final reports/BIT to free the second owned job slot for a useful implementation of the verified v003 synthesis. Keep its intermediate results separate from final signoff.

V003 conventional placement estimates setup -0.665 ns and hold -0.140 ns before routing. Its worst reported path is `control_plane/command_state_reg[1]_rep/C` to `system_core/receiver/base/canonical/rows/captured_tile_reg[70]/CE`: nine LUT levels through kill/abort/ready logic and a final 512-sink payload-capture enable. Of the estimated 10.493 ns data delay, 8.859 ns is routing. These are pre-route observations, not final failure or a measured video-throughput limit.

The parallel `incremental01` implementation uses the identical constrained v003 checkpoint and input hashes, with the actual qualified V023 routed checkpoint as placement/routing reference (SHA `9dbc13affc87cfddf612398bd6aaacff4f4d94eca4419887dd8b57e7e48a70ea`, setup +0.003 ns / hold +0.021 ns). No clocks, pins, delays or RTL change. Reference reuse does not itself qualify timing; the candidate needs fresh routed checks. The reference is loaded after `opt_design`, as described in [AMD UG904](https://docs.amd.com/r/2025.1-English/ug904-vivado-implementation/Using-Incremental-Implementation-in-Non-Project-Mode).

The parallel incremental attempt failed placement (Place 46-13 / 30-99); its error/evidence is retained and it produced no image. The conventional v003 implementation still has negative intermediate setup slack after its first routed pass and is continuing physical optimization/final routing.

The focused fallback captures the 512-bit tile payload while the row writer is idle and holds it while `write_busy` is set. It keeps the existing handshake, bad-tile validation, write authority and token resets. This removes kill/ready from the wide payload enable and removes its payload reset, while leaving validity resets intact. Driver/state replication alone cannot remove nine dependent logic levels.

That fallback is now the separate V026 candidate, `fpga/experiments/cu66-v71/rows-idle-capture-v026`, build `dy71-v026-20261107-v001`, intended USERID `4459373e`. It retains the exact V43 firmware/ABI2 bulk interface. Paired simulation passed both bank configurations with over two million qualified bytes and matching controls/counters under stalls/abort/reset/invalid cases. Actual-RTL projection induction proves control equality and `write_busy -> old/new captured payload equality` for both bank counts, with a proved cache-valid/bank-full invariant, a caught always-capture mutant and non-vacuity check. Unobserved strip RAM/read data was projected out, so this is not a formal whole-codec claim. The earlier depth-limited proof remains recorded as inconclusive. Both new fast/slow native raster runs passed (two original frames presented and all 42,240 HUD words verified per case); full FPGA implementation remains in progress. Neither candidate changes the physical V42/V023 held endpoint during development.

V025 conventional final routed result is -0.092 ns setup / +0.027 ns hold / +2.000 ns pulse, with all 55,347 routable nets routed and no routing errors. Its worst final setup endpoint is `system_core/receiver/base/scatter/pending_valid_reg_replica/D`, from `system_core/receiver/base/entropy/tile_reg[0][4]/C` through a 17-level carry/logic path. Strict timing gates correctly blocked BIT emission. A single same-source `postroute01` physical cleanup is in progress from that exact failed routed checkpoint, alongside V026 synthesis. No clock or timing budget is relaxed for that attempt.

V025 `postroute01` finished at -0.006 ns setup / +0.027 ns hold; a second critical-pin/routing/clock-skew cleanup (`postroute02`) finished at -0.001 ns setup / +0.027 ns hold. Both are failures under the strictly-positive setup rule, and neither emitted a BIT. These attempts are now stopped/completed; V026 is the active implementation candidate. V026 full-synthesis bulk-cell XSim and writable-RAM mapping checks have also passed. V43 firmware remains unchanged and uninstalled.

## V026 final result and current V027 candidate

V026 finished routing with setup -0.272 ns, hold +0.015 ns and pulse +2.000 ns. Its functional proof/native raster checks passed, but routed timing failed; no BIT was emitted. The worst path was entropy stream selection into the decoder state register, with 11 logic levels and 7.625 ns of routing delay.

V027 retains the proven V026 row-capture change and adds one explicit BUFG on the existing fourth-stage synchronized core reset. It adds no reset stage, changes no clock/IO/SDRAM budget and retains all four protected synchronizer registers. Actual AMD BUFG-model simulation passed 100 asynchronous assert/release events and 1,416 comparisons. Full synthesis mapping confirms the buffer and four ASYNC_REG stages; full-build synthesized bulk-cell simulation also passes. Routed timing is still pending. Positive reset-path coverage and all existing image gates are mandatory before BIT emission.

Current active build: `dy71-v027-20261107-v001`, intended USERID `4459373f`. V43 release-v002 remains unchanged and uninstalled. The physical V42/V023 endpoint remains untouched. Intermediate negative routing numbers are not final timing results. The development manifest records completed failing attempts as failures, rather than merely incomplete evidence.

## Qualified V027 lab image

V027 finished with strictly positive routed setup +0.019 ns, hold +0.012 ns and pulse +2.000 ns. All 55,412 routable nets are routed, with zero routing errors. Native audit passed: protected reset stages, explicit reset BUFG, timed reset-path coverage (worst reported +1.355 ns), LCD paths/IOB storage, writable chroma RAM and interval/metadata mapping, zero unwaived DRC errors. BIT emission and the identity parser passed. An audit generator path bug was corrected so new V026 raster evidence and inherited V023 evidence are checked in distinct directories; no check was waived.

Selected BIT: `C:/mb70/dy71-v027-20261107-v001/image01/moonbub-v027-lab.bit`, SHA-256 `9922aa617c21a03e8a31f932d45e22d905e91d4e263ef593692898d363d07dee`, intended USERID `4459373f`. This supersedes the failed V025/V026 candidates for the bounded hardware comparison. The V43 release-v002 ELF/UF2 is unchanged. Neither new image is installed; physical DONE/USERCODE, original KEY/P equality, runtime memory and speed remain open. See `V43-V027-HARDWARE-COMPARISON-20261107.md` for the exact test sequence. Overall handoff remains INCOMPLETE pending physical evidence; `c_check_handoff` is unavailable and manual hash integrity is not represented as that checker.
