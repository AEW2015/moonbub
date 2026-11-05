# V71 hardware-development handoff

The CU66 receiver now has a dedicated, elastic BL8 LCD path, an auxiliary
four-line cache, bounded LCD arbitration and one-clock request-gap grace.
The final command-level key/P simulation reconstructs exact output and scans
both source frames without LCD underruns. **30 fps and validated decoding under
10 ms remain open.** This is an experimental source handoff, not a board image.

The baseline is v70 commit `fcc02c58d46f96a26790ce02826a0bf937c2478b`.
All 4,879 v69 bundle files, 460 v70 bundle files and 15 reviewed v70 source pins
remain unchanged. The [plan](plan.md) and [milestone checklist](milestone-checklist.md)
retain the next acceptance gates.

## What changed

- `cu71_word_bridge`: independent aligned LCD BL8 requests, an eight-word
  elastic response buffer, one canonical cache line, four associative auxiliary
  lines, write-alias invalidation, at most four consecutive LCD grants while
  scalar requests wait, and one finite grace clock for adapter request gaps.
- `cu71_memory_system`: preserves canonical-tile and guarded scalar contracts;
  adds LCD burst ports and retains global busy through every held response.
- `cu71_scanout`: requests 60 bursts per 480-word line. Descriptor generation,
  source ID, RGB-slot ownership and drained-boundary presentation are retained.
- `cu71_system`: routes LCD directly to its independent memory port. HUD and
  painter share the remaining scalar arbiter. The frozen v70 packet/base owner,
  controller, memory map, exact strip painter and LCD line banks remain in use.
- The system bench records packet-complete, admission, validated-ready,
  RGB-ready, commit-ACK, descriptor-presentation and correct-raster events. It
  checks every raster x/y in order and counts unique source IDs separately
  from repeated LCD refreshes.

No CU66 packet format, encoder, ESP32 firmware or decoded image quality changed.
The controller still issues **single-word writes**.

## Measured evidence

Model clocks are 100 MHz memory, 279-degree read sampling, 34.058 ns pixel
period, and approximately 65.0755 Hz panel refresh. These are simulation inputs,
not achieved device clocks.

| Scope | Final result |
| --- | --- |
| Memory service | 28/28 executions: two simulators, two tAC corners, two seeds, three traffic patterns, plus four reset runs |
| Worst tested LCD line | 1,502 clocks / **15.02 µs**, within the **18.425378 µs** native line period |
| Memory checks per normal run | 231 tile operations, 5,871 auxiliary operations, 250 LCD bursts / 2,000 words, 43 abort probes, three rejected bursts |
| Backpressure/reset | First/middle/last and invalid response held for 32 clocks, flushed, followed by fresh bursts; finite grace and four-grant saturation exercised |
| Standalone display | 10 raster executions / **3,840,000 exact pixels**; normal schedules have zero underruns; intentional starvation produces 1,440 whole-black lines and 1,440 underruns |
| Display control | 31 independent Icarus checks for ownership, gaps, malformed LAST, reset and orphan responses |
| Integrated guard/abort | Two headers parsed, two visible HUD writes/readbacks, seven denied writes, two abort drains, premature HUD completion rejected, no partial frame accepted |
| Full key/P command model | Exact 518,400 canonical bytes, 21,120 HUD readback words and 384,000 portrait RGB565 words per frame; lost COMMIT ACK retried |
| Full-system LCD | **Zero underruns**, 14,660 complete clean lines; both source IDs have a complete exact raster |
| Exact-target OOC preflight | Vivado 2025.2 exit 2: `xc7a100tcsg324-1` unavailable; synthesis and implementation did not start |
| Generic bridge elaboration | Yosys hierarchy/process/structural checks pass for both versions; not technology-mapped FPGA resource or timing evidence |

The full-system run observed 7,036,996 pixels. It contains 18 complete exact
raster refreshes: 17 of source frame 0 and one of source frame 1. That is **two
new source presentations**, not 18 new game frames. The trailing partial raster
is not counted as complete. Separate standalone display totals also include
repeated test rasters.

| Modeled phase | Key frame 0 | P frame 1 |
| --- | ---: | ---: |
| Full admitted transaction to commit acknowledgment | 109.58523 ms | **260.18963 ms** |
| Complete immutable packet to validated YUV/HUD-ready | 35.02723 ms | **90.66040 ms** |
| Validated-ready to RGB-ready | 74.55797 ms | **169.52854 ms** |

The one-clock admission wait is retained in the validated interval. The
validated-ready observation is entry to frozen receiver state WAIT_RGB, after
base/HUD integrity and required memory fences, before painting. Native processor
HUD execution, readback hashing and control service consume wall time in the
bench but do not advance simulated time; the phase numbers are therefore **not
validated target decode latency**. The native preparation diagnostic is also
not a measurement of the complete processor workload.

V70's comparable strip P transaction was 229.84583 ms. V71 is about 13.20% slower
while maintaining clean concurrent scanout; v70's unequal-duration run recorded
11,762 underruns. This iteration closes the tested starvation cases, not the
throughput budget. Do not claim a speedup or a normalized underrun-rate ratio
from these different-duration schedules.

## Counterexamples retained

`system/initial-buffered/` archives 58 source/log files in a hashed ZIP. Waiting
for the whole LCD burst before forwarding it preserved exact memory contents
but took about 428 ms for the P transaction and retained underruns.

`system/elastic-before-grace/` archives 89 source/log files. Cut-through delivery
made the full pair clean, but a one-clock request gap let scalar writes interrupt
every burst. Component lines then took 1,899–1,935 clocks, or 2,364–2,379 with
same-bank backslot conflicts, exceeding 1,842.5378 available clocks. The final
finite-grace scheduler passes those explicit scenarios. Arbitrarily stalled
consumers or larger unbounded request gaps still cannot carry a deadline claim.

## Reproduce and integrate

From this checkout, with the existing tool containers mounted at the same
absolute repository path:

```sh
python3 scripts/cu66-v71/verify_baseline.py
python3 scripts/cu66-v71/run_memory.py
python3 scripts/cu66-v71/run_display.py
python3 fpga/experiments/cu66-v71/system/run_control.py
python3 scripts/cu66-v71/run_system.py --frames 2 --strip
python3 scripts/cu66-v71/run_elaboration.py
python3 scripts/cu66-v71/compare_system.py
python3 scripts/cu66-v71/verify_evidence.py
python3 scripts/cu66-v71/bundle_manifest.py
```

Runners retain commands, source/log hashes, tool outputs and bounded terminal
checks. Builds use one job each in separate `/build/v71-*` directories, under
the shared 4-CPU/4-GiB tool-container limit. The environment image is recorded in
`fpga/experiments/cu66-v71/environment.json`. Re-running producer tools replaces
qualified logs and requires regenerating the evidence and bundle manifests.

Use `system/sources.json` for the integrated source set and include paths. For
hardware, select top `cu71_system`, `USE_STRIP=1`, remove the simulation wrapper
and SDRAM model, and omit `SIMULATION`; retain actual I/O primitives. Integrate
the separate LCD request/response channel and preserve its eight-beat contract.
Use the existing HC70 processor endpoint contract and bank map; real packet
staging, CPU/HUD service and transport still need board integration.

The staged `build/ooc_system.tcl` uses the exact device and an explicit hardware
source list, with `USE_STRIP=1` by default. The recorded Vivado 2025.2 preflight
returns `UNAVAILABLE_EXACT_PART` (exit 2); synthesis and implementation did not
start. `build/status.json` pins the Tcl, source list, executable identity and
logs. No substitute device was used. Once that exact device package is available,
the OOC flow still requires review of unconstrained interfaces and board-specific
integration before its reports could support hardware signoff.

Exact `xc7a100tcsg324-1` implementation remains an open gate. Generic leaf
elaboration establishes neither full-system fit, BRAM mapping, routed Fmax, CDC
signoff nor SDRAM/panel electrical behavior. Board pin/clock/reset/CDC constraints,
processor service and live ESP32/QSPI transport must be qualified on the fitted
hardware. No hardware was programmed during this iteration.

## Next measured milestones

1. Add and qualify true BL8 writes, including masked four-word canonical rows,
   strip-painter bursts, partial-abort drain and actual final-write recovery.
2. Re-profile the full memory schedule, safe phase overlap and direct transposed
   YUV scanout if RGB copy traffic remains limiting. Preserve exact HUD and
   reference ownership. Decoder arithmetic is not yet the demonstrated remedy
   for the memory service deficit.
3. Run all 457 retained histories through the changed memory path, then the
   predefined 1,800-distinct-source fixed-arrival campaign. The v70 histories
   remain frozen baseline evidence; this v71 full-command replay covers two.
4. Close target implementation/clock/CDC gates and the ten-minute physical
   30-fps campaign before declaring verified throughput. Then validate strict
   observed maximum decoding below 10 ms with real processor timing, all queue
   time, memory completion and failed-attempt costs included.
