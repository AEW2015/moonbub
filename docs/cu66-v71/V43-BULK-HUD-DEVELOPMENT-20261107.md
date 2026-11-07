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
