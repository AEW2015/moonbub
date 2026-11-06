# SDRAM alignment repair to full-FPGA hardware test

Status: planned, November 5, 2026 (America/Denver). No new hardware run or
implementation is claimed by this plan.

## Objective and evidence

Qualify the exact MoonBub memory path before loading the rebuilt full CPL1
image. Preserve the working build50 recovery and the completed reset/timing
work. This is a memory-correctness gate toward 30 fps, not a 30 fps claim.

- [SDR1 physical readback](SDR1-HARDWARE-READBACK-20261105.md): three runs each
  returned 32 words with 28 mismatches. Expected burst words are present in raw
  samples 5–12, while the response starts with sample 6. No timeout occurred.
- [Reference PHY measurements](SDRAM-WINDOW-MEASUREMENTS-20261105.md): two
  full-32-MiB, nine-pattern controls passed at 166.015625 MHz/90 degrees;
  the 225-degree full run found 1,485 mismatches. These results support board
  health but do not qualify the different 100 MHz MoonBub controller.
- The completed full candidate met routed timing (+0.022 ns setup,
  +0.018 ns hold), but physical SDRAM correctness remains unproven.

Do not select a SERDES replacement yet. First determine whether a small,
explicit response-alignment change repairs the current path over a defensible
sampling window. Do not copy reference delay/slot values into MoonBub.

## Parallel work and ownership

| Lane | Owner role | Independent work | Deliverable / dependency |
|---|---|---|---|
| A | SDRAM model engineer | Replay physical samples; audit command and pin timing; extend timing models and assertions | Failing-baseline regression and documented timing envelope; starts immediately |
| B | Controller engineer | Add bounded, latched capture/response selection and diagnostic observability in a new candidate | Exact controller/probe RTL plus unit tests; starts immediately, agrees signal contract with A |
| C | Verification engineer | Prepare BL8, masked-write, boundary, refresh and recovery scoreboards; audit full-image source bindings | Reusable regressions and full-image integration checklist; starts immediately |
| D | Evidence/build coordinator | Preserve hashes/recovery, audit constraints and build scripts, prepare result schema and hardware driver | Reproducible build/signoff package; starts immediately |

Use a Luna agent for source inventory, hash checking and report/table assembly;
use engineering agents for RTL, timing assumptions and independent review.
Give each lane separate files/candidate directories. A and B agree trace
sample numbering and cycle semantics before changing shared interfaces.
Keep old source freezes and manifests immutable. One coordinator integrates
reviewed changes. Only one owner may program or access the physical device.

After B freezes RTL, small-probe implementation can run alongside A/C model
regressions. A provisional full-image build may run alongside small-probe
hardware testing once its RTL is frozen; any subsequent RTL fix invalidates
that full build. Limit simultaneous Vivado jobs to available RAM/resources
and leave other workspaces' processes alone.

## Gate 1 — reproduce the physical failure in simulation

1. Import retained SDR1 samples and actual LTX probe mapping as a fixture.
   Drive the real capture/response RTL with those samples. Check literal word
   order, first/last word, response-valid timing and exactly eight responses.
2. Require the unchanged baseline to reproduce
   `1101 1202 1303 1404 1505 1606 1707 1707`, and the candidate to return
   `1000 1101 1202 1303 1404 1505 1606 1707` for an appropriate setting.
   Test neighboring incorrect settings so a disabled checker cannot pass.
3. Separately audit the pin-level model: READ command sampled at the SDRAM
   clock pin, programmed CAS latency, clock forwarding, input retiming and
   nonblocking-assignment stages. Keep a cycle-by-cycle diagram from READ
   command through DQ launch, capture and response-valid.
4. Confirm the fitted part/speed grade from board/BOM evidence and obtain its
   primary datasheet. Bind model limits to named parameters and units:
   tAC/tOH, setup/hold, clock flight/skew, burst and command timing, refresh,
   and turnaround. Mark unavailable PCB/delay measurements as assumptions.
   Preserve the existing CAS3 interpretation unless source evidence disproves
   it; do not alter CAS or invent board delays merely to make tests pass.
5. Retain existing fast/slow models and add the observed earlier first-word
   case. Sweep justified min/max timing combinations around capture edges;
   explicitly flag ambiguous/invalid sample windows instead of silently
   returning a stable value. Add deliberate setup/hold and command-timing
   violations to prove the model/checker detects them.

Pass: baseline failure reproduced, candidate success and incorrect-setting
failures observed, assumptions recorded, and all protocol checks enabled.
Trace replay proves response logic for supplied samples; pin-level simulation
checks the modeled envelope. Neither proves analog margin, metastability or
PVT behavior. Physical qualification remains mandatory.

## Gate 2 — build a bounded diagnostic repair

- Create a new versioned probe; preserve source-v005 and its failed image.
- Expose a supported response-start/capture selection, latch it only while
  idle/at accepted GO, and echo the active setting in every result. Reject
  invalid values and changes during a transaction. Keep mandatory resets,
  initialization, refresh and ownership behavior intact.
- Compare waits 4 and 5 at the existing frequency/phase first. Wait 4 is a
  trace-derived candidate, not the presumed production default. Keep the
  setting independent of data content; never auto-align by matching pixels.
- Record raw samples, accepted command/address, actual response words and
  valid mask, configuration, first expected/observed word, counts, run ID,
  timeout and aborted-run state. Bound trace storage and report truncation.
- Extend verification from four bursts to randomized literal BL8 scoreboards:
  repeated words, unique words, walking bits and pseudorandom data; supported
  chip/row/bank boundaries; back-to-back and read/write turnarounds; DQM/masked
  neighbor preservation; refresh interruption; busy GO, reset and abort.

Pass: exact-source regressions pass, independent review complete, positive
routed setup/hold/pulse checks, complete routing, zero DRC errors, reviewed
CDC/constraint coverage and matching BIT/LTX/source hashes. Do not weaken I/O
constraints, add false paths, or change clock frequency to obtain a pass.

## Gate 3 — qualify the small MoonBub path on hardware

1. Stop senders, confirm hardware ownership, retain verified recovery images,
   and capture fresh ESP32/FPGA identity. Use volatile JTAG only.
2. Run the same literal four-burst fixture with fresh run IDs and raw trace
   for both candidate settings. Record failures too. Reject any setting that
   shifts, repeats or omits words, even if counters or the screen look good.
3. On the passing setting, run longer BL8 fill/verify and masked/boundary
   tests using the exact controller and pin path intended for the full image.
   Verify all regions the full design uses; add full-memory coverage for
   supported address space rather than claiming it from a small test.
4. Characterize neighboring capture/phase points using only supported clock
   profiles and reviewed timing constraints. Select an interior passing point;
   repeat it after reconfiguration and refresh stress. Do not infer MoonBub's
   eye from the reference PHY's sweep or call one passing board PVT-qualified.

Pass: zero mismatches/timeouts at the selected operating point, all expected
comparisons completed, no stale run/configuration results, and repeated
interior control passes. Restore build50 after any failed gate.

Independent write-eye characterization is optional separate work: it needs a
transmit timing knob plus write-at-candidate/read-at-reference sequencing,
with preserved data and explicit reset/reconfiguration semantics. Existing
read sweeps and masked-write passes do not measure a write-eye width.

## Gate 4 — rebuild and test the full FPGA

1. Integrate the same qualified controller/capture semantics and selected
   configuration into the full CPL1 candidate, preserving reset reduction,
   SHA pipeline changes, interfaces and platform clocks. Check source hashes
   against the qualified probe; wrappers/placement differences still require
   full-image timing and physical checks.
2. Run exact full-image pin-level tests with the expanded timing envelope:
   fixture ingestion, memory arbitration/refresh/backpressure, decode,
   presentation and scanout CRC. Retain reset/abort/invalid-input recovery,
   SHA known-answer tests and negative corruption/alignment cases.
3. Require final routed setup, hold and pulse checks to pass, all routes
   complete, no DRC errors, reviewed CDC/bus-skew/coverage and unchanged
   physical I/O budgets. Report actual margins; +0.250 ns across three builds
   remains an improvement target, separate from minimum signoff.
4. Hash/package the exact BIT and sources. Load volatile only after Gates 1–3
   and full signoff pass. Verify DONE and identity; require physical fixture
   CRC `4c5725e5`, literal readback and held scanout before longer local loops.
5. Measure repeated *unique* decoded/presented frames and memory throughput
   locally. A held frame scanned twice is not two unique frames. Keep network
   throughput, audio and controller coexistence as subsequent separate gates;
   the current fixed-ROM custom fixture is not a network loader.

## Reporting and decision points

Each lane reports exact source/image hashes, executed commands, pass/fail,
first mismatch, modeled assumptions, actual clocks/settings and evidence paths.
Keep simulation, static timing, reference-PHY hardware, MoonBub probe hardware
and full-image playback results separate. No new ESP32 firmware is planned
unless observability cannot be provided by the probe/JTAG path.

If alignment cannot pass over a useful window, or the qualified probe passes
but the full image fails, preserve those traces and investigate pin timing,
placement, arbitration and capture boundaries before expanding scope. A
SERDES4 migration becomes a separately reviewed option with clock-domain,
latency, refresh, resource and interface budgets—not an automatic replacement.

The first hardware milestone is the rebuilt small probe after Gates 1–2;
the full-image milestone follows Gate 3 plus full-image signoff. Build runtimes
can be estimated from retained logs, but a completion ETA must include current
regression and implementation status rather than assume the repair will pass.
