# Game Bub V126–V130: timing closure to verified streaming

Updated **2026-11-10**. This is the next five-version plan, grounded in the
[published V125 measurements](cu66-v125/README.md). Its exits are targets,
not predictions that a version number will automatically qualify the design.
It carries forward the unmet integration and hardware gates from
[V121–V125](gamebub-v121-v125-spatial-literature-review.md).

The product goal remains **720×480, 30 distinct displayed frames/s over ESP32
Wi-Fi, followed by validated FPGA decoding strictly below 10 ms**. Target
**125 MHz** for the complete FPGA parent, while preserving the qualified
[B100 component control](cu66-v120/handoff.md) for independent remote testing.
A component clock pass does not qualify a board image, and under-10-ms decode
does not mean under-10-ms capture-to-display latency.

## Starting point and budgets

The V125 reference commit is `a38ef4189733d2ebcd9fb3ad930ca926c909bd6d`.
Its [machine-readable results](../experiments/python-gamebub-v125/results.json)
and all referenced proof/source files stay frozen.

| Measured evidence | Implication for the next work |
| --- | --- |
| Global 125 MHz WNS −1.224 ns; TNS −2,209.865 ns; 8,027 failing endpoints | Setup closure is still open; fewer failures alone is insufficient. |
| Producer cursor → cell cache −1.224 ns; 9.171 ns data, 6.967 ns routing | Split successor arithmetic from the lookup ROM, then measure both new stage boundaries. |
| Scratch emit-bank → state −1.219 ns | A producer-only repair will leave another nearly equal failure. |
| Admission tile → coordinates −0.464 ns; group-end → coordinates −0.644 ns; cursor → all −0.498 ns | Repair coordinate/control paths alongside the producer and scratch work. |
| New hidden-predicate D −0.191 ns; its outgoing family +0.182 ns | Preparing a predicate can move the problem to its input; inspect D/CE and Q paths. |
| Row parent: 1,145,104 fast / 1,553,197 stalled cycles | Current cycle count still misses the stalled <10-ms target, even assuming 125 MHz. |
| Functional full-suite comparisons match V124 with zero public-cycle delta | Retain that regression control; it is not a sustained gameplay corpus. |
| V123 historical WNS −1.086 ns / TNS −1,709.649 ns is better globally than V125 | Keep that composition as a comparison control; do not assume stacking every local repair improves the whole route. |
| Production endpoints use JPEG/MSV1; custom CS88 is separately tested | Actual custom-profile negotiation and integration remain necessary. |

The current fast/stalled row counts project to **9.160832 / 12.425576 ms** at
an assumed complete-parent 125 MHz. Strictly below 10 ms means **at most
1,249,999 cycles**, requiring at least **303,198** fewer stalled cycles.
Use **1,125,000 cycles / 9 ms** as the engineering margin target: that needs
20,104 fast and 428,197 stalled cycles removed. Added pipeline/queue latency
counts against the same total; do not subtract only the apparent stall savings.

At 100 MHz the strict bound is 999,999 cycles; the current fast/stalled gaps
are 145,105 / 553,198 cycles. B100 testing can establish independent facts, but
cannot inherit the 125 MHz latency projection.

At a retained 49,152-byte maximum compressed frame, 30 fps requires
**11.79648 Mbit/s of payload** before transport overhead. A hypothetical
four-data-line 40 MHz QSPI transfer takes at least **2.4576 ms/frame** before
commands, gaps or arbitration. These are arithmetic bounds, not measured
ESP32 goodput. The rate controller must use actual frame-size distributions,
recovery bursts and measured sustainable service; the cap is not a guarantee
that every 30-fps scene fits the link.

## Five-version sequence

| Version | Main implementation | Required exit evidence |
| --- | --- | --- |
| **V126 — separate producer address and lookup** | Prepare the successor address and ROM result on existing owned edges; preserve current cache semantics and public cycles. | Focused full-width/wrap/owner tests, complete regressions, and a fresh fixed-recipe route showing both sides of the new registers and every remaining negative family. Global closure is not assumed. |
| **V127 — close distributed control timing** | Partition scratch bank ownership/return and admission coordinate/control cones; add explicit elastic stages if existing-edge preparation cannot close them. | Exact functional and cancellation/debt contracts; a selected component with setup/hold/pulse/coverage/routing passing at 8 ns in two fresh same-source builds. Any failure leaves the timing gate open. |
| **V128 — reduce validated-decode cycles** | Attribute actual blocked cycles, then overlap reconstruction, memory writes and ordered validation with owned ping-pong storage. | All declared qualification profiles strictly below 1,250,000 total cycles, target ≤1,125,000; exact canonical/reference/HUD/hash/seal results, no publication before write completion; renewed timing qualification for changed RTL. |
| **V129 — integrate the custom streaming system** | Connect actual host encoder/packetizer, firmware session/DMA adapter and complete FPGA parent under one deterministic simulation scheduler; implement negotiated custom profile plus JPEG fallback. | Source-bound full-system traces, finite ESP32/memory service, distinct-frame corpus and fault coverage; complete-parent constraints/CDC/reset/resource review and two passing fresh 125 MHz parent builds for the release composition. |
| **V130 — remote hardware qualification** | Deploy the pinned release through the remote hardware team; calibrate service and validate display/decoder timestamps under real contention. | First 1,800 distinct frames/60 s, then 18,000/600 s at 30-Hz releases; afterward every qualified packet-complete → validated-publication sample <10 ms, with tail distributions, exact frame identity and zero scanout underruns. |

Modeling, harness construction and the independent B100 board trial can proceed
alongside V126/V127. Do not wait until V129 to discover transport or memory
limits. A later version may contain useful partial results while an earlier
exit remains open; it cannot claim the dependent qualification. If V127 does
not close timing, carry the named failing cones forward explicitly rather than
marking it passed or renumbering the problem out of sight.

## V126: producer pipeline cut

Implement the source-bound [V125 next timing proposal](cu66-v125/next-timing.md)
as the first bounded trial:

1. Prepare a full 13-bit successor tile on the original tile writers. When
   current tile advances from t to t+1, prepare wrapped t+2 in parallel.
2. On MAP_REQ, register `quant_cell(plane, prepared_successor_tile)` from that
   already registered address. Do not move the same add-plus-ROM expression
   intact onto a differently named register.
3. Consume that owned result on the original MAP_WAIT skip or nonterminal
   DISPATCH completion; hold it through stalls. Preserve NEXT_PLANE's original
   current-cell update, including empty planes and intermediate states.

Preserve all four plane encodings, full 13-bit wrap, old all-cycle cache
assertions, full epoch/block comparisons, accepted-start versus rejected-start
behavior and error priority. Verify earliest lookup responses, repeated stalls,
reset/abort/new-plane, last/non-last coefficients and concurrent lookup use.
Prepared fixtures must execute actual writers and separately count primer
edges; never force the new payload/ownership bits.

After functional qualification, route once under the frozen part/tool/clock
recipe. Query address D/CE/Q, successor-cell D/CE/Q, original cache, plane/state
control, scratch, admission and RAW/refill families. A positive producer subset
does not satisfy V127. If the ROM-only cone remains too long, prepare a bounded
bank-local/registered lookup alternative from the actual mapped paths; preserve
the full truth table and prove its latency contract before another route.
Use V125 as the current functional reference, while retaining the better
historical V123 global result. Select the next composition from fully qualified
comparisons rather than automatically retaining every accumulated experiment.

## V127: spatial control and Series-7 mapping

Use local registered stages and local storage ownership to replace wide
combinational decisions. Prioritize the measured scratch emit-bank/metadata
return and admission coordinate successors; include the negative hidden-D
capture and residual RAW/owner-tag paths in every comparison.

- Snapshot the selected bank's metadata before it drives consumers, with full
  epoch/block ownership. Keep stale-bank poisoning and accepted-response debt
  tests; bank-ready or child-valid assumptions cannot replace an owner check.
- Prepare coordinate successors locally rather than coupling global tile/group
  arithmetic into many enables. Explore the already modeled hidden-boundary
  update only with an owned same-plane unit step and exact jump fallback.
- Register control with its payload. Reset validity/ownership where required;
  omit payload resets only after proving unowned values cannot affect outputs.
  Measure actual control-set count, fanout, replicas and placement distance.
- Examine actual Series-7 RAM output-register, LUT/CARRY and DSP register
  mapping. Arithmetic-lane expansion is secondary while control/routing leads
  the path reports. Do not add DSP stages merely to increase DSP utilization.

There are two explicit verification modes. **Cycle-preserving** trials retain
every original public-cycle comparison. **Latency-changing** trials use a new,
versioned ready/valid/credit contract with declared minimum/maximum latency and
bounded buffering. Their scoreboard must retain exact values, transaction order,
owner/error decisions, cancellation and all accepted read/write debts. Replace
only the cycle-equality requirement with the reviewed latency relation; do not
silently disable an oracle or use relaxed latency to hide an incorrect transfer.
Document externally visible backpressure and ABI implications.

Before promotion, require WNS ≥0, TNS=0, zero failing setup/hold/pulse endpoints,
zero unconstrained internal endpoints and zero routing errors in **two fresh
same-source/tool/recipe builds**. Aim for ≥0.2 ns setup margin as a design target,
not a retroactive waiver. Keep fresh methodology warnings, clock coverage,
resource/control-set counts and family reports, including adverse changes.
No guessed I/O delays or arbitrary false/multicycle exceptions may create a pass.

## V128: useful overlap, not just a faster clock

Instrument the actual selected parent before choosing a throughput architecture.
Record one exclusive blocked cause per relevant cycle, plus a separate overlap
mask. Distinguish input starvation, entropy dependencies, scratch-bank ownership,
memory request/response waits, write drain, validation and downstream backpressure.
Reconcile elapsed cycles against active work, exclusive waits and pipeline drain;
do not add overlapping counters as if they were independent delays.

Use Python transaction models to reject impossible storage/port schedules, then
implement the smallest measured win. Initial candidates are two owned result
banks, queued/burst write service where the actual controller supports it, and
ordered validation while another block reconstructs or drains. Retain canonical
hash order, reference immutability and final write acknowledgments. No frame or
reference may become visible because pixels exist in a private buffer alone.

Only add a second compute lane if traces show compute dominates and a concrete
port/bank schedule fits the real resource budget. Preserve bit-exact fixed-point
rounding, clipping and validation. Compare net cycles, LUT/FF/BRAM/DSP, memory
traffic and routed clock; extra lanes that worsen contention or timing lose.

Run all retained byte/row/caller profiles and expanded frame classes, including
abort after accepted writes and retry into a fresh epoch. State the exact
tested corpus, maximum service gaps and fault envelope. Under unbounded loss or
arbitration denial, clean recovery/drop is required rather than an impossible
finite latency promise. The complete valid-frame qualification envelope must
be declared before measurements. Any added latency updates the published budget.

## V129: one full-system harness and a real parent

The [V124 native seams](cu66-v124/harness-boundaries.md) are useful controls;
they do not run the complete custom system. Close these gaps explicitly:

1. Negotiate the exact CS88 profile/version, pixel/chroma layout, compressed
   cap, reference epoch and recovery behavior in host, firmware and FPGA.
   Keep a checked JPEG fallback. Never send custom bytes to a JPEG-only path.
2. Exercise the actual Sunshine application/session and custom encoder/packetizer
   path with a controlled frame source, then feed its output through the actual firmware
   protocol/session adapter to QSPI pin-level RTL and the complete validated
   parent. A prerecorded file replay is a separate test, not this live harness.
   A compiled `msv1.cpp` fixture alone is not the Sunshine session path. Where
   host capture or the Windows service requires the remote system, retain that
   limitation and attach its executed traces separately.
3. Use one deterministic time authority for source releases, network service,
   firmware scheduling, QSPI edges, memory and FPGA clocks. Wall-clock subprocess
   duration is neither simulated ESP32 CPU time nor FPGA decode latency.
4. Bound SRAM buffers, queue counts, lifetimes, DMA alignment/copies, SPI
   transaction gaps, CPU/task service and feedback. Enable PSRAM in the model
   only if the fitted firmware/hardware configuration supports it. Report
   assumptions and sensitivity ranges until remote traces calibrate them.
5. Stress Wi-Fi loss/reorder/duplication/jitter, recovery bursts, full buffers,
   UI/audio/input contention, memory refresh/turnaround/scanout and reset/abort
   with outstanding responses. Track frame identities and queue residence time.

ESP32 instruction emulation is an optional additional evidence level, gated by
demonstrated support for the fitted S3 CPU and required DMA/SPI/interrupt/network
behavior. Renode is not assumed to provide that support. A native Rust adapter
plus transaction service model must be labeled as such, not an ESP32 emulator.
The modeled path must use physical service budgets; it may not invent unlimited
CPU, zero-copy storage or instantaneous Wi-Fi/QSPI just to reach 30 fps.

Use the existing Mass Effect compressed clip as a diagnostic input with its
provenance retained. Add independent captured/raw material where available and
declare that corpus gate open until obtained. Include static HUD/text, motion,
combat, camera pans, cuts, fine texture, high-entropy frames and recovery frames.
Report quality and worst frame size, not merely an average payload. HEVC/AV1
comparisons can be refreshed on identical inputs/settings as a separate study;
they are not a reason to change codec syntax during timing closure.

Integrate the selected decoder into the actual board parent, using verified
framework memory/display contracts and board I/O constraints. Qualify real
clocks/generated clocks, CDC/reset, memory service and scanout deadlines. A new
parent source composition needs its own complete functional checks and two
fresh full-top 125 MHz routes; component passes cannot be substituted.

## V130: deployable handoff and hardware acceptance

Prepare a source-pinned release for the remote team containing host/firmware/RTL
commits, selected profile, constraints, tool versions, build commands, manifests,
register/counter map, exact bitstream hash, calibration steps and recovery path.
Each artifact must say whether it is a component, integrated parent or verified
board image. Keep B100/JPEG recovery controls and an independently reproducible
clean build. A missing board or external timing calibration leaves a named gate
open; a simulation report cannot fill it in.

Perform the [existing hardware gates](cu66-v110/hardware-gates.md) in order:

1. Calibrate timestamps and Wi-Fi/QSPI/memory service on the actual system;
   confirm panel identity/CRC instrumentation and zero scanout underruns.
2. Demonstrate 1,800 distinct intended frames over 60 seconds, then 18,000 over
   600 seconds, with 30-Hz releases and real Wi-Fi/QSPI/UI/audio/input contention.
   Display refreshes, repeated frames and repeatedly decoding one fixture do
   not count as new source frames. Record loss, retries, drops and queue age.
3. After the frame-rate gate, require every valid qualified packet-complete →
   validated-publication sample strictly below 10 ms. Include memory waits,
   entropy/reconstruction, reference/HUD/hash/seal checks and write drain.
   Report count, min/median/p95/p99/max, worst-frame identities and violations.

Keep the packet-complete boundary explicit in the contract. Record both ESP32
receive-complete and FPGA final-byte acceptance, plus first-input, decode stages,
final memory acknowledgment, validated publication, vblank and displayed frame
identity. Never reset the timer after a queue wait or silently relabel the
retained final-input-byte fixture as a full decode measurement. Report
capture-to-display latency separately, including its clock synchronization
uncertainty. Calibrated hardware timestamps, not assumed MHz multiplication,
decide the hardware result.

## Execution and decision policy

For each version, split work into RTL architecture, independent golden/cancel
verification, service/harness modeling, and documentation/audit tasks. Simple
inventory/model/report checks suit Luna agents; the primary agent owns source
selection, shared-file integration, resource reservations and promotion.
Parallel agents do not imply parallel unlimited vendor builds.

Retain at most two heavy study jobs, each two CPUs, 8 GiB RAM and 8 GiB combined
RAM-plus-swap, with finite timeouts. Gate on available RAM and full memory PSI,
then combined RAM/swap use. Launch only with at least 8 GiB available RAM,
full PSI avg10 <1 and combined used fraction <0.85. Stop the study job for
available RAM <4 GiB, full PSI avg10 ≥5 in two consecutive samples, or combined
used fraction ≥0.90. Account for other host jobs and never stop unrelated work
or change swap to force a run.

Each trial binds source order/hashes, parent/reference, fixture contracts,
commands, tool image, part, clock-before-synthesis recipe and all raw results.
Start with one causal change, qualify function before native implementation,
and keep negative results. Compare global WNS/TNS/failing endpoints together;
also track hold/pulse, all queried families, congestion, resources and control
sets. A new source change invalidates the earlier timing qualification for that
composition. Requalify the release after performance/integration changes.

If a result is negative, choose the next change from actual path/stall evidence.
Do not reroute an unchanged negative candidate until a random positive result
appears. Physical-only strategy experiments, if justified, get separate labels
and unchanged-source controls; they cannot replace functional proof. No clock
relaxation or selective omission of failed profiles may manufacture the goal.

Every version ends with a compact results table: source/branch, changed contract,
functional status, global/family timing, decode-cycle distribution, link/queue
service, resource deltas and remaining gates. **Success is passing the three
separate clock, 30-fps and strict-latency gates—not reaching the V130 label.**
