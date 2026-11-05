# SDRAM capture alignment investigation — 2026-11-05

The isolated native-pad simulations reproduce a read-beat shift independently
of writes. A focused capture/retiming candidate now passes the tested strict
model envelope. **No candidate BIT exists, no new hardware was programmed, and
the physical CRC failure is not yet fixed or independently localized.**

Current installed state remains v32 / restored build50, with no network session
started by this work. See [physical results](CPL1-LOCAL-HARDWARE-20261105.md).

## Reproduction and improved model

The runner is `scripts/sim_cpl1_sdram_alignment.py`. It copies the sealed
controller, native ODDR/IOBUF primitive models and SDRAM model into a fresh
output directory. It never defines `SIMULATION` or contacts hardware.

Each case checks six aligned bursts across row boundaries (addresses 0, 8,
504, 512, 520 and 1024), reads independently preloaded memory, performs full
and byte-masked writes, compares the modeled memory contents after every
write, then verifies all eight returned words. Each case covers 96 physical
modeled write beats, 96 returned read words, and at least one operational
refresh in addition to initialization refreshes. These are bounded patterns,
not a full-memory or all-bank test.

With the original capture (7.75 ns) and retiming, flight=0 / access=2 ns
returns `b001,b002,...,b007,Z` instead of `b000,...,b007` from **preloaded**
memory. All write comparisons pass. This locates this simulated failure in
read return/capture rather than write generation. It does not establish the
unmeasured physical board timings. In particular, the simulated final Z does
not independently reproduce the physical repeated-last-word CRC fingerprint.

The old model stretched a previous word throughout the new access interval.
The strict model now invalidates DQ 0.5 ns after the device clock during each
beat transition and releases the final beat after that hold interval. The
principle is also present in the GameBub SERDES4 model. The 0.5 ns value and
access/flight ranges below are sensitivity assumptions, not fitted-part or
board timing measurements.

| Executed experiment | Cases | Result |
|---|---:|---|
| Original model, 3 capture phases × 5 flight delays × 3 access delays | 45 | Zero write errors; original phase has read failures at short delays |
| Strict hold, original falling-edge retime; 5 phases × 3 response delays × 15 delay pairs | 225 | Zero write errors; original phase/response delay passes only 3 of 15 pairs |
| Strict hold, candidate rising-edge retime; same matrix | 225 | Zero write errors; 3.75 ns phase / original response delay 5 passes all 15 pairs |

Flight delays: 0, 0.5, 1, 2, 4 ns. Access delays: 1, 2, 4 ns.
Capture phases: 3.75, 4.25, 5.5, 6.25, 7.75 ns in strict sweeps.
Response countdowns: 4, 5, 6. These 495 executions intentionally include failing
controls; they are not 495 passes or exhaustive phase qualification.
The 4.25 ns / rising-retime / delay-5 point also passes these 15 pairs.
The 5.5 ns point coincides with a modeled hold boundary and is not selected.

## Isolated implementation candidate

`fpga/candidates/cp23-sdram-capture135-20261105-v001/` preserves the original
frequencies, pins, controller response countdown and provisional external
delay budgets. Its two product RTL changes are:

1. SDRAM capture PLL phase: 279° (7.75 ns) → 135° (3.75 ns).
2. Capture retiming: command falling edge → command rising edge. The response
   process consumes the preceding registered retime value; no combinational
   bypass or response-count adjustment is added.

This gives the capture register more time to reach the retime stage than an
earlier phase combined with the old falling-edge retime. It still needs routed
setup/hold evidence.

The constraint candidate removes the **old** phase-specific input multicycle
and guards the new 3.75 ns phase. At that phase, the preceding forwarded clock
rise is already the default setup launch edge (−5 ns → 3.75 ns). Ordinary
single-cycle setup/hold applies. No new false path or input delay relaxation
is introduced. The old qualified image/constraints remain frozen.

`candidate.json` binds the changed files. `prepare_cpl1_capture_candidate.py`
creates a fresh candidate and refuses to overwrite an existing directory.
`sim_cpl1_capture_smoke.py` separately tests the actual candidate top/PLL and
bootstrap/lock-loss behavior: 16 normal-start checks and 18 lock-loss checks
passed with the strict model and zero modeled clock flight. That smoke cannot
establish rendered correctness. Its retained first-run normal log has a stale
literal `read_phase279=1` label; the executed assertion actually checked
3.749–3.751 ns and the source used 135 degrees. The runner's label is corrected
for future executions; the historical raw log is preserved unchanged.

## Does this need SERDES4?

**Not established for this alignment defect.** The focused candidate tests a
smaller correction at the existing 100 MHz serial rate. Selecting a complete
PHY replacement before independently checking readback would combine new
clocking, command packing, reset/CDC and memory arbitration changes.

The supplied GameBub workspace already contains useful SERDES4 source at
`gamebub-source/fpga/vivado/sdram_serdes4/`: OSERDESE2 commands/data,
ISERDESE2 + per-lane IDELAYE2 receive, explicit capture delay/slot selection,
128-bit response assembly, bounded asynchronous FIFO, reset/park ownership,
rate counters and runtime phase/tap control. The app README, RELEASE,
INTERNAL_TIMING_REVIEW, PHY, controller, read aligner and burst model were
reviewed. Its historical release evidence does not qualify a MoonBub port.
The workspace HEAD was `54f5fa980b327cece0d2b9e3b2127c17d6590f1f`;
unrelated research-document changes were left untouched.

Consider SERDES4 as a separate throughput/margin candidate after correctness:
adapt its reserved 128-bit request/response protocol, preserve all eight beat
indices and byte masks, integrate backpressure and reset epochs, qualify the
actual board constraints, and measure accepted bandwidth concurrently with
scanout. Faster serial frequency alone is not proof of 30 unique displayed
frames/s. No additional repository or information is needed for the current
simulation investigation; fitted-part timing and physical readback/eye data
will be needed to select a hardware sampling point confidently.

## Remaining gates

1. Run the exact complete board fixture with the stricter hold model at early
   and late delay corners; require the unchanged `4c5725e5` oracle, correct
   tags/counts and zero line/ownership faults. Top smoke is insufficient.
2. Route the candidate, report real setup/hold/pulse and external I/O paths,
   and review the single-cycle edge selection. No BIT before those gates pass.
3. Add a bounded hardware readback diagnostic that distinguishes raw memory
   contents from returned beat order, then test the candidate locally with
   build50 recovery retained. Do not reinterpret the old wrong CRC as success.
4. Only after independent readback and golden rendered CRC pass, measure
   sustained bandwidth and decide whether a SERDES integration is warranted.
   Custom network transport remains a separate, versioned capability gate.

Local detailed logs are under `evidence/cpl1-sdram-alignment-20261105-v001`,
`v002` and `v003` (three complete directory names with the same prefix).
Selected result matrices and logs are published with this report; they describe
simulation only and do not supersede the physical failure record.

Published selected evidence: `evidence/cpl1-sdram-alignment-public-20261105/`.
It includes the three matrices, representative logs, top-smoke results and
an evidence checker. Full per-case logs remain local; result-file log names
refer to those original run directories.
