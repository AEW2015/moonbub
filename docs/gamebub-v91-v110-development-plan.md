# Game Bub V91–V110: codec selection and 7-series implementation

Updated 2026-11-06. This is the active forward plan after V90 and the
[literature review](literature-review-2026-11-06/README.md). Version numbers below
reserve work phases; they are not completed results or promised calendar dates.

**Product goals:** retain 720×480 coded video, sustain 30 distinct source frames
per second, then validate complete FPGA decoding strictly below 10 ms. Preserve
exact intended canonical/reference pixels, HUD composition, RGB565 output and
publication checks for representation-only optimizations. Keep quality-changing
experiments in a separately versioned, matched-quality lane.

**User-requested focus:** V100 through V110, inclusive, concentrate on improving
RTL for **7-series technology mapping, placement, routing and timing closure**.
Freeze the selected codec before that phase so a physical implementation change
can be compared against a stable function and workload.

## Evidence entering this roadmap

[V91](cu66-v91/README.md) now supplies full-corpus coefficient parity,
directed/native/sanitizer checks and clocked RTL symbol-component evidence.
Its 32-bit all-ready real-stream comparison reduces cycles by 29.24%; CPU
candidates are slower. Full packet/context integration, complete decoder timing
and physical qualification remain pending; the V100–V110 phase stays reserved.

[V91b](cu66-v91b/README.md) now derives DC/AC requests and emits validated sparse
addresses through one output slot. The full-corpus Python transaction matches
all coefficients; the clocked real-context comparison is 685,304 word versus
937,735 serial cycles. Packet CRC/raw ingress, four-context arbitration,
zero-default scratch and whole-frame consumers still require integration. This
substep matures E1 without renumbering V92's finer entropy-choice experiment.

[V90](cu66-v90/README.md) evaluates 3,656 actual packet candidates from 457
retained sources. Its selected packets average 18,203.64 B and reach 48,744 B,
within the 49,152 B experimental admission cap. The four-source exhaustive
timing study still has a hard source at 10.80320/12.29713 ms under assumed
LOW/HIGH costs and 100 MHz. Those are conditional model results, not routed
clock timing or measured FPGA latency.

The [review](literature-review-2026-11-06/README.md) favors word-oriented Rice
parsing, finer/selective statistical coding, bounded-table ANS and host-selected
small palettes. It also prioritizes memory service and a receive-buffer
contract. Earlier HEVC/AV1 comparisons remain compression controls, not evidence
that the custom codec has surpassed their rate/quality performance.

Keep all V90 and earlier experimental artifacts frozen. Start new source/result
directories and record exact parent commits; do not rewrite historical results
to make a later implementation look like the original experiment.

## V91–V99: implement the review's experiments and select a candidate

The detailed functional tests and latency fences remain in
[E1–E7](literature-review-2026-11-06/experiments.md). This table assigns their
work to versions; a failed experiment can retain its control and negative result.

| Version | Work | Required result before promotion |
|---|---|---|
| V91 | E1: Python word-reservoir BR88 parser, bounded escapes and initial elastic RTL/counter calibration. | Existing bytes and coefficients match independent readers; refill, escape, scatter and stall costs are explicit. |
| V92 | E2: per-context AB38/BR88 choices, rather than only three whole-plane choices. | Actual new framing/bytes and bounded host selection; exact output and reset/replay parity; full cost frontier recorded. |
| V93 | E2: arithmetic-prefix/raw-suffix variant; small-block Rice and RLGR controls. | Measure statistical gain per coded field; retain finite escapes/raw fallback; account for all tags, resets and dependencies. |
| V94 | E3: 2/4-state rANS/tANS with bounded tables, literals and model IDs. | Table-inclusive packets, independent decode, lookup/port/state costs and accepted-model recovery; no kernel-only speed claim. |
| V95 | E5: 2/4/8-entry palette, left/top runs and residual/raw fallback, with clustering on the PC. | Real gameplay/UI wins beyond flat fixtures; exact canonical/HUD lane first; quality-changing clustering reported separately. |
| V96 | E6: bounded exact reference copy, group-oriented bursts and scheduled CONST128 generation. | Addressed traffic and lifetime/abort proof; charge generators, descriptors and display consumers; no free cross-position alias assumption. |
| V97 | E4: calibrated host selection plus finite Wi-Fi/ESP32/QSPI/decoder arrival-service model. | Held-out prediction errors, real host preparation cost, bounded occupancy and explicit stale-frame/reference recovery behavior. |
| V98 | E7: refresh HEVC/AV1/JPEG controls on common inputs; evaluate alternative transforms only when justified. | Complete rate/quality/latency curves, peak packet failures and scene-change/HUD/temporal results; distinguish original raw captures from old quantized reconstructions. |
| V99 | Select and freeze one implementation candidate plus a simpler fallback. Publish its independent decoder, grammar and RTL-facing goldens. | Explicit reasons for selection, supported tools/model bounds, resource/port budgets and integration gaps. A theoretical entropy win alone is insufficient. |

The 457-frame related corpus is an initial regression set, not the final
qualification corpus. Obtain independent raw captures with native 30-fps cadence
for the physical milestone; replay counts and the old 25-fps combat clip do not
create new distinct gameplay updates.

## Target and technology-mapping contract

Use **`xc7a100tcsg324-1`**, as identified by the retained
[routed JPEG report](../fpga/build-final/utilization.rpt), unless an explicitly
recorded board/part correction supersedes it. Freeze board revision, package,
speed grade, pinout, memory parts and the integration top in V100.

The retained report lists 63,400 LUTs, 126,800 registers, 135 BRAM tiles and
240 DSPs available. Its JPEG design uses 7,362 LUTs, 120.5 BRAM tiles and
32 DSPs. This is a historical comparator, not a custom-decoder fit. Do not add a
new decoder to those figures without accounting for replaced JPEG buffers and
all retained display/control/transport logic. Logical memory bytes do not prove
RAM primitive, port, placement or whole-device fit.

Prefer portable inferred RTL first, then compare a small 7-series wrapper only
when the mapped netlist shows a missed opportunity. Keep a generic simulation
model and a technology-bound implementation under the same transaction tests.
Inspect primitive counts and registers actually absorbed into DSP/BRAM blocks;
an RTL attribute or multiplier operator is not proof of mapping.

| Resource / design concern | Planned mapping experiment | Correctness condition |
|---|---|---|
| DSP48E1 | Dequantization and inverse-transform arithmetic; optional selected rANS state multiply. Compare sharing against parallel lanes and A/B/M/P pipeline registers. | Explicit signed widths, extension, intermediate overflow bounds and original Q14 rounding/saturation order. Align data, valid, coefficient/tile/epoch IDs and enables through every stall. |
| RAMB18E1 / RAMB36E1 | Coefficients, entropy tables, descriptors, line buffers and hash state; synchronous read and optional output registers. | Budget real read/write ports, banking, byte enables, latency and replication. Define or prevent every same-address collision; generic array behavior must match the implemented primitive. |
| SRL16E / SRLC32E and LUTRAM | Short delay alignment, small queues and local lookup tables where they reduce cost. | SRL payload storage lacks a reset function: retain reset/epoch/valid bookkeeping and prove stale data cannot be consumed. An elastic queue needs its own correct occupancy/control logic. |
| LUT6 / LUT6_2, carry and mux logic | Bounded prefix/escape decoding, comparisons, counters, address calculation and small decoders. Compare a pipelined LUT implementation with inferred arithmetic/CARRY4. | No assumption that leading-zero detection automatically benefits from a carry chain. Exhaustive small-function checks plus routed comparisons decide. Dual-output LUT packing must respect shared-input constraints. |
| Registers and control sets | Register long ready/credit chains; localize high-fanout control; simplify compatible enables/resets; compare FSM encodings. | Preserve drain/abort/publication ordering. Reset payload removal requires a validity proof; preserve CDC synchronizers and required reset behavior. |
| External-memory and display service | Burst grouping, bank/row locality, bounded outstanding work and line buffers. | Faster decoder logic does not accelerate an unchanged SDRAM clock or eliminate refresh/turnaround. Charge continuous scanout and prevent accepted-reference overwrite. |

These resources and inference practices are grounded in AMD's
[7-series CLB flow](https://docs.amd.com/r/en-US/ug474_7Series_CLB/Recommended-Design-Flow),
[carry-chain reference](https://docs.amd.com/r/en-US/ug474_7Series_CLB/Carry-Chain-Primitive),
[DSP48E1 guide](https://docs.amd.com/api/khub/documents/gu4oRPFEh_Pm2uaAlfY6Kg/content),
[7-series memory guide](https://docs.amd.com/api/khub/documents/9gZGbqBxtlKXxBfkBt~lAg/content)
and [2025.2 primitive library](https://docs.amd.com/r/2025.2-English/ug953-vivado-7series-libraries/RAMB36E1).
Do not import DSP48E2, CARRY8, UltraRAM or UltraScale-specific packing assumptions.

## V100–V110: dedicated RTL and physical implementation phase

| Version | Focus and concrete work | Evidence / exit gate |
|---|---|---|
| **V100** | **Reproducible 7-series baseline.** Freeze the V99 candidate, top, part, source/IP/memory-init/XDC hashes, Vivado build, parameters and supported packet profile. Recreate the design in a clean build directory. Route the unchanged baseline where possible; inventory remaining simulation-only endpoints. | Baseline synthesis/route checkpoints and reports, primitive/resource breakdown by hierarchy, top paths and full-cycle workload counters. Missing Artix support or incomplete endpoints remain explicit gaps. |
| **V101** | **Constraints, clocks and methodology.** Audit primary/generated clocks, real external I/O delays, clock interaction, CDC/reset domains and existing exceptions. Run methodology/DRC checks at synthesis and implementation. | No unreviewed critical methodology issue, unintended unconstrained functional path, or unjustified timing exception. Record actual board/interface requirements and each unresolved item. |
| **V102** | **Elastic pipelines and retiming.** Cut long ready/credit, mux and arithmetic cones with registered/skid stages; test retiming only where semantics permit. | Exact transaction/epoch ordering under arbitrary stalls, reset and abort; measured cycle/occupancy changes and placed/routed path comparison. No accidental combinational ready loops or throughput bubbles hidden by an always-ready test. |
| **V103** | **Entropy parser LUT/carry mapping.** Optimize the selected BR88/hybrid/ANS path: bounded prefix tree, reservoir mux/refill, run/scatter control or table address logic. Compare width and lane alternatives. | Inferred primitive/path evidence, escape/boundary/reject parity and stall-inclusive full-frame counters. Keep the smallest design that improves the relevant frontier. |
| **V104** | **DSP48E1 arithmetic mapping.** Pipeline dequantization/IDCT and any selected ANS multiplication; compare exact symmetry, sharing, pre-add/cascade use and parallel lanes. | DSP input/output pipeline usage confirmed in netlist; exact rounding/width proof and golden parity; routed frequency versus frame-cycle/resource tradeoff. DSP utilization alone is not the objective. |
| **V105** | **Memory inference and locality.** Replace accidental register arrays/large muxes with suitable BRAM/LUTRAM/SRL structures; bank tables/coefficient buffers; register outputs and distribute local memories. | Per-memory depth/width/port/collision/latency ledger, primitive counts and physical footprint. Re-run consumers with actual read latency, arbitration, refresh and display contention. |
| **V106** | **Fanout, control sets and congestion.** Localize grants, epoch/valid/reset distribution, descriptor selection and memory interfaces. Compare hierarchy boundaries and measured driver replication. | Before/after fanout, control-set and congestion reports plus routed path delay. Do not spread MAX_FANOUT, DONT_TOUCH or manual placement constraints without path evidence. |
| **V107** | **Clock/reset/CDC integration.** Close transport, decoder, memory and display crossings with proper synchronizers/async FIFOs and synchronized reset release. Treat any new decoder-clock option as a separate integration variant. | CDC inventory and reviewed exceptions, stable tags across crossings, reset/abort/clock-start tests, interface timing and metastability assumptions documented. Preserve memory/LCD clocks unless separately qualified. |
| **V108** | **Bounded placement/routing study.** Compare a recorded small set of synthesis/place/physical-opt/route strategies from the same source/constraints. Try soft hierarchy/pblocks or local placement only for measured locality/congestion problems. | Full trial matrix including failures, exact directives/tool version and route completion. Repeat the winner from a clean build; no unsupported random-seed knob or lucky single run as robustness evidence. |
| **V109** | **Integrated closure and calibrated decode.** Merge only individually qualified changes, re-route the complete top, and replay the fixed workloads with real primitive latencies and finite interfaces. Run targeted post-route simulation where it resolves implementation risks. | Setup/hold/pulse-width and route/methodology signoff, native/pixel/hash/HUD parity, full decoded-frame latency distribution and stall/queue accounting. OOC timing and zero-time software endpoints cannot pass full-system gates. |
| **V110** | **Hardware qualification and handoff.** Freeze the clean rebuild, routed candidate, fallback, bitstream hashes, constraints and device counter map. Test on the hardware system when accessible. | 60-second then 600-second distinct-frame 30-fps evidence, followed by strict validated-decode <10-ms evidence. If hardware is elsewhere/unavailable, deliver the exact test bundle and leave those gates pending rather than calling simulation a hardware pass. |

Every version may iterate until its gate is satisfied. Later physical experiments
can proceed on an available qualified control when a new coding tool fails;
there is no requirement to implement every speculative codec tool in one design.

## Timing, latency and experiment controls

Start with a **100-MHz decoder-domain target** (10-ns period) for comparison with
the existing conditional model; achieving it requires implementation evidence.
After a valid baseline, consider 125/150-MHz decoder-only targets as optional
experiments. Preserve actual memory/display timing and CDC boundaries. Do not
scale every old cycle count by a new decoder frequency and call that new latency.

For a single 100-MHz domain, strictly below 10 ms means **fewer than 1,000,000
cycles** between the frozen validated-decode fences. Added pipeline stages,
table initialization, CRC/hash/HUD service and waits all count. In a mixed-clock
design, use correlated timestamps or a common measurement clock; adding raw
cycle counts from different domains is invalid.

Make one architectural change at a time before combining winners. Keep source
frames, packet bytes, clock constraints, memory service, release schedule and
endpoint behavior matched for an A/B comparison. Route-only trials hold RTL
fixed; RTL changes retain a baseline strategy as well as the best tested one.
Record all failed trials and stop expanding a strategy sweep without evidence
that more trials address the diagnosed bottleneck.

Begin with at most six recorded strategy combinations and one clean rebuild of
the selected winner; expand only to test a stated new hypothesis. Respect the
host's available-RAM/memory-pressure build gate and disk budget. Start with one
heavy implementation run at a time, record thread limits, and keep independent
source/report review parallel without multiplying memory-heavy builds.

Use post-route setup/hold/pulse-width analysis at the tool's required timing
corners and verify routing is complete. Require WNS/WHS nonnegative and TNS/THS
zero for the qualified design, with no unexplained unconstrained functional
paths or pulse-width failures. Also inspect I/O, recovery/removal and clock-domain
requirements. Justified asynchronous/test exceptions need a documented scope;
do not hide a functional data path, invent a multicycle assumption or relax
clocks to report a pass. These rules follow the
[2025.2 timing-signoff guidance](https://docs.amd.com/r/2025.2-English/ug906-vivado-design-analysis/Report-Timing-Summary)
and [UltraFast methodology](https://docs.amd.com/r/2025.2-English/ug949-vivado-design-methodology).

Freeze the available Vivado version initially. The installed timing skill's
automated JSON workflow declares Vivado 2026.1+ compatibility; do not assume its
new flags work in 2025.2. Use reports supported by the installed version, and
record any tool upgrade as a separate baseline. Artix-7 device support is needed
for target synthesis/implementation; generic Python/RTL development can continue
while that dependency is resolved. No tool installation or design run is started
by this planning update.

## Required reports and handoff artifacts

Each physical trial retains its source manifest and exact build Tcl/XDC,
tool/version/part/parameters, command log, exit status, checkpoint hashes and
runtime/peak host RAM. Keep large generated checkpoints/logs in a documented
artifact store rather than duplicating them through source Git. The source
bundle must recreate the project without an undocumented local cache.

Collect, using the installed tool's supported commands:

- Utilization by hierarchy and mapped primitive: LUT logic/RAM/SRL, FF, control
  sets, CARRY4, DSP48E1, RAMB18E1/RAMB36E1, clocks and I/O. Include debug logic.
- Synthesis, placement and routed timing summaries; worst setup and hold paths
  by clock group, logic versus net delay, high-fanout/congestion findings,
  methodology/DRC, clock interaction, CDC, route status and exceptions.
- Parser/refill/escape/table/transform/hash/HUD/memory counters, stalls by cause,
  outstanding requests, FIFO high-water marks, abort drain and publication events.
- A comparison CSV containing trial/source/constraint/tool hashes, requested
  clocks, route status, WNS/TNS/WHS/THS, pulse-width/unconstrained-path status,
  resources, workload cycle distributions, complete bytes and exactness status.
  Label each value as simulation, implementation timing or hardware measurement.

Retain a generic reference implementation and small wrappers for any explicit
7-series primitives, with simulation/elaboration libraries and build instructions.
Golden cases must cover key/cold/reference reuse/hard-combat sources, mixed
entropy choices, maximum escapes, raw/dense input, stream boundaries, malformed
packets, bad CRC, lost ACK/exact retry, resets, aborts, held scanout and descriptor
ownership. The full HUD/validation/display endpoints cannot remain software
stubs in a claimed hardware pass.

## Product milestone gates

| Gate | Required evidence |
|---|---|
| Functional RTL candidate | Independent exact decoder and golden-output agreement; bounded interfaces and failure/recovery behavior. |
| Physical implementation | Complete selected top fits the exact part and meets routed timing with valid clocks/I/O/CDC constraints. Fmax and OOC fit alone do not establish frame throughput. |
| Sustained hardware 30 fps | 1,800 distinct frames over 60 seconds, then 18,000 over 600 seconds at fixed 30-Hz source releases; intended displayed identity/pixels/HUD, bounded queues and zero underruns, with Wi-Fi/QSPI/UI/audio/input contention represented. |
| Validated hardware decode <10 ms | Every qualified packet-complete → validated-publication sample is strictly below 10 ms, including entropy, reconstruction, memory waits, content/HUD checks and safe ownership publication. Report min/median/p95/p99/max and worst identities; no average-only pass. |
| Handoff | Rebuildable source/constraints, routed artifact and fallback hashes, negotiated profile, counter definitions, hardware run procedure, known gaps and all failed trials. |

Transport, capture/encode and presentation latency remain separately reported
end-to-end costs. Retain atomic validated publication; a partial early scanout
would need its own explicit integrity contract. Preserve the native resolution
and frame-rate goals throughout this phase.
