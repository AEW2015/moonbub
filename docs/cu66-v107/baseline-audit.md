# V107 baseline audit

This read-only audit anchors V107 to the selected V106 implementation evidence and
records the board-level clock/reset context visible in source. The machine-readable
record and checker are [baseline-audit.json](../../experiments/python-gamebub-v107/audit/baseline-audit.json)
and [audit.py](../../scripts/cu66-v107/audit.py). They hash every input used.

## Frozen V106 timing evidence

The selected `closure` implementation completed native OOC routing for
`xc7a100tcsg324-1` with a 10 ns comparison clock. Its routed WNS is **−4.034 ns**
and **44,630 of 106,218 setup endpoints fail**; hold slack is +0.122 ns and
pulse-width slack is +3.750 ns. The retained route setup report's SHA-256 agrees
with both the run receipt and the V106 native selector. The component timing
target is not met.

The separate post-route strategy diagnostic changes WNS to −3.777 ns but still
has 44,630 setup failures. It is marked unselected/unpromoted and does not change
the baseline selection.

V106's sixth integration receipt records a 1,800.722-second timeout (exit 124)
after synthesis. The synthesized checkpoint exists at the receipt's external
path and its SHA-256 matches the receipt (`fa5845de74b14b0b6773244b97a34acb09270e3e5b3e7fecc7b87bbbf7c72b46`). No placement report or routing checkpoint exists, so this attempt has no route result.

## Actual board clock and reset context

The board top is [moonshine_top.sv](../../fpga/rtl/moonshine_top.sv). It accepts
`clk_50mhz`, instantiates a service PLL and a separate panel MMCM, and routes
clock outputs into QSPI/overlay, core/memory, phase-shifted read, and LCD/pixel
logic. The source names these branches `clk200`, `clk100`, `read_clk100`, and
`pclk`; this audit does not infer board tolerances or add timing values. The
service PLL's lock drives four-stage reset-release shift registers in the local
`clk200` and `clk100` domains; the panel MMCM's lock similarly drives a local
`pclk` chain. Assertion is asynchronous to each local clock and release shifts
synchronously in that domain.

The top connects MCU QSPI, the `moonshine_bus_cdc` SPI/core sides, the memory
controller's `clk`/`read_clk` interface, LCD line request/data signals, and
`esp32_overlay` system/pixel sides. These are interface boundaries for V107's
CDC owner to inventory and qualify. Their real source/sink timing requirements,
board pin delays, memory timing, clock relationships, reset recovery/removal,
and CDC exceptions are not established by the V106 component run.

## Constraint scope and qualification gaps

The only V106 comparison constraint is `create_clock -name component_clk
-period 10.000 [get_ports clk]` in
[component.xdc](../../fpga/experiments/cu66-v106-flow/component.xdc). That file
states that external protocol/diagnostic input and output delays are deliberately
open. V106 synthesizes/routes `cs88_pipeline_v91k` out of context, not
`moonshine_top`; it does not constrain the top's PLL/MMCM clocks or prove board
input/output timing, CDC behavior, reset timing, full-system fit, sustained
hardware 30 fps, or complete decode latency.

The checker verifies retained report/receipt hashes, the selected route metrics,
the sixth-attempt checkpoint hash and the one-clock OOC constraint. It runs no
vendor flow and changes no frozen V106 source or evidence.

The V107 continuation audit binds the copied parent receipt/input snapshot, all
retained run-script/report snapshots, and the checkpoint's recorded
before/after hashes. It does not read the external checkpoint by default. Its
state rule is that a `RUNNING` continuation remains `PENDING_RESUME`; after
termination it parses the retained placement/route timing, clock, exception,
routing, DRC, CDC and methodology reports. The continuation is terminal in
this final readout. A terminated failure is retained as a failure, and a
successful component route still leaves board and hardware qualification open.

## Focused Rice and CDC evidence

The Rice probe's selection/attempt/source/artifact hashes and two terminal seed
records are checked by the V107 audit. Each seed records 1,520 historical
vectors across eight configurations, 104 directed checks, 6,096 parameter
cases, and 8.65 million historical clock edges; the focused audit records
17,839,670 total edges. The test logs contain no runtime warning, failed-test,
assertion-failure, or waiver text. The recorded Verilator command excludes only
the filename-only `DECLFILENAME` warning; this is not functional warning
suppression. The result is a two-state clocked equivalence probe, not timing or
metastability evidence.

The selected CDC receipt passes its behavioral five-channel fabric run for
seeds 107001–107003. Each log reports 120,000 ticks, 45,809 event edges, and six
reset epochs. Across all three seeds, the recorded trace replay accepts 74,060
items, delivers 73,596, and discards 464 on reset; channel-level totals match
the replay receipts. Source snapshots and all retained artifacts match hashes.
No test warning/failure/waiver lines were found. This is behavioral FIFO/reset
evidence only: the inventory says the experimental fabric has no production
parent instantiation, and no result establishes metastability performance or
hardware CDC signoff.

All six required `aligned`, `closure-aligned`, and `quant-aligned`
fresh/canonical matrix lanes now pass. The four standard lanes have 224
case-profile and 272 directed checks; the quant pair adds 112 case-profile and
136 directed checks, for 336 and 408 across all six. The quant pair's initial
fresh attempt ended before compilation when the shared regression lock was
unavailable (`BlockingIOError`; `actual_RTL_run=false`); that failure remains
retained separately from the passing bounded lock-wait retry and canonical
lane.

## Quantization and value-expression evidence

The selected quantization-coordinate probe uses candidate source SHA-256
`58d0fcb876692c2ad38fa0585a5d2e13cd83079f64a84538f8de5a5c4d139d61`. Both
selected seeds pass 86 cases and 35 directed checks each, with independent
packet/run-fill and trace replay. The audited selected run totals 19,518,735
actual clock edges. An earlier attempt is retained as a coverage-floor failure:
semantic replay matched, but it reached only 60,750 fill edges versus its
predeclared >100,000 floor. The selected retry adds 32 complete mode-2 packets
and passes the unchanged floor and checks. This is behavioral equivalence, not
formal arbitrary-state proof, physical timing, or hardware qualification.

The value-expression check verifies 262,144 actual RTL expression vectors and
65,536 Python identity values. It records
`full_module_RTL_run=false`: the expression proof does not qualify the edited
complete module. The later quant-aligned pipeline lanes are the separate
integration gate; neither the expression check nor a focused probe implies a
full-module PASS on its own.

The elastic stage unit has a frozen, hash-matched behavioral PASS: 508,800
clock edges, 288,502 pushes, 288,460 pops, and 42 flush discards across its
three seeds. Its audit explicitly records that the complete pipeline was not
compiled or simulated. The separate canonical full-pipeline candidate has two
retained terminal failures so far: the first stopped at an extra-stage source
count check before RTL execution; the second failed during baseline compilation
with `actual_RTL_run=false`. The later canonical run now passes two seeds, each
with 22 case-profile and 21 directed checks. The audit independently replays
52 ordered good-frame semantic streams per seed, checks canonical bytes, and
rechecks case goldens and stage conservation. Each seed reports 5,495,207
accepted, 5,495,205 delivered, and two explicitly discarded words. The earlier
failures remain retained. These are behavioral cycle counts under the test
model, not routed-frequency or hardware frame-rate evidence; no 30 fps or
sub-10-ms implementation claim follows.

The standalone mapped CDC/reset unit route is legal and its retained reports
hash-match: WNS +2.025 ns, hold slack +0.097 ns, pulse slack +2.000 ns, 240
routed nets, and zero routing errors. It remains review-required. The audit
preserves 8 critical CDC-11 and 10 CDC-6 findings, reset macro/collision
concerns, and 279 input plus 279 output ports without board timing. Gray-bus
physical bounds cover 40 bits in 10 bundles; they do not prove protocol
semantics, metastability performance, production parent integration, or board
CDC signoff. No waivers were added and no hardware qualification is claimed.

The resumed sixth-source checkpoint route has now completed and its report
copies, report checksums, copied run snapshots, parent receipt/input snapshot,
and recorded checkpoint before/after hashes all verify. This is a separate
continuation of the timed-out `local-guards-scratch-area` synthesis source; it
does not replace the selected `closure` baseline. The route reports WNS
**−4.428 ns**, with **43,163 of 106,245 setup endpoints failing**, +0.110 ns
hold slack, and +3.750 ns pulse slack. Its worst path runs from
`coefficients/child/scratch/tile_emit_index_reg[0]_rep__2/C` to
`transform/coefficient_banks[1].words[4].value_reg[5]/CE`, with 14.139 ns data
delay and 12 logic levels. Routing completed with 72,279/72,279 routable nets
and zero routing errors. The 10 ns setup target remains unmet.

The retained single-clock OOC report lists only `component_clk` at 10 ns and
reports no valid exceptions. `check_timing` reports no missing clocks or
unconstrained internal endpoints, plus 1,101 endpoints without input delays and
12,885 without output delays. Methodology reports 2,404 warning findings,
including 1,000 each for TIMING-16 and TIMING-18; these do not disappear because
the OOC internal route is legal. The CDC report's “All paths are Safely Timed”
statement is limited to this single-clock OOC checkpoint and says nothing about
the board's asynchronous domains.

The quant and elastic OOC routes both completed legally but fail setup timing.
Quant has WNS **−4.428 ns** with **49,770 of 107,138 setup endpoints failing**;
hold slack is +0.115 ns and pulse slack +3.750 ns. Elastic has WNS **−3.447 ns**
with **39,420 of 106,867 setup endpoints failing**; hold slack is +0.042 ns and
pulse slack +3.750 ns. Quant is worse than V106's selected −4.034 ns route;
elastic improves the slack but still has thousands of failing endpoints. The
header native attempt was deliberately cancelled for scheduling with exit 143
after 1,831.615 seconds, before writing a synthesis checkpoint; it has no
placement or route result. The retained cancellation record binds the terminal
receipt hash and records the decision time, unchanged 3,600-second watchdog,
unchanged source snapshot, and reason: freeing one of two heavy-job slots for
the qualified TABLES route and requested payload-reset proofs. This is a
scheduling redirection, not a tool timeout or timing result.
The checker verifies the input manifest, copied source snapshots and recipe
snapshots before reporting native results. The quant map has 16 RTL files plus
one include header; the elastic, header, TABLES, payload, and META native maps
each have 17 RTL files plus one include header. It also ties these builds to their
passing behavioral pair reports and exact candidate source hashes. The
payload-reset full-pipeline comparison now passes 44 newly executed candidate
case-profiles and 42 directed checks across two seeds, matching retained
elastic public outputs, events, cycles, and canonical bytes. Its native build
completed a legal route but fails setup timing: WNS −2.735 ns, TNS −20,649.869
ns, 21,836 of 87,472 setup endpoints failing, hold +0.098 ns, and pulse
+3.750 ns. Its worst path runs from
`coefficient_boundary/payload_reg[43]_rep/C` to
`transform/coefficient_banks[0].words[12].value_reg[8]/CE`, with 12.446 ns data
delay and 12 logic levels. All 61,644 routable nets are routed with zero
routing errors; there are zero no-clock or unconstrained internal endpoints.
The guard build was deliberately scheduling-cancelled after 2,129.196 seconds
in synthesis Timing Optimization, before any synthesis checkpoint; it has no
placement or route result and did not reach its 3,600-second watchdog. The
decision freed the heavy-job slot for the prepared count-prefix functional
proof; the unchanged guard source remains included in the META native trial.
This is a scheduling redirection, not a timeout or timing failure. The
separately activated META native build has now completed a legal route but
fails setup timing: WNS −3.146 ns, TNS −22,777.035 ns, 25,263 of 88,089 setup
endpoints failing, hold +0.073 ns, and pulse +3.750 ns. Its worst path runs
from `coefficients/child/packet_decoder/synchronous.ingress/context_blocks_reg[2]/C`
to `coefficients/child/scratch/state_reg[0]_rep__0/D`, with 13.000 ns data
delay and 20 logic levels. All 62,765 routable nets are routed with zero
routing errors; the timing report has zero no-clock and unconstrained internal
endpoints. This remains component OOC evidence, not a timing pass. A timing pass requires a completed
legal route with nonnegative setup, hold and pulse slack, zero failing endpoints
in all three groups, and zero `no_clock`, unconstrained internal endpoint,
timing-loop and latch-loop checks. These remain single-clock OOC criteria;
board I/O, reset, CDC and hardware qualification remain open.

The focused whole-admission header candidate is frozen after two actual RTL
seeds passed 86 cases and 44 directed checks each, with independent coordinate
and packet-run replay. The separate full-pipeline header comparison now passes
44 newly executed candidate case-profiles and 42 directed checks across two
seeds. The audit confirms exact stdout/events/cycles and canonical-byte matches
against the retained same-seed elastic candidate; those reused control runs are
not counted again. Neither the focused probe nor this behavioral comparison is
a timing result or supports a hardware frame-rate claim.

## Scale RAM and combined TABLES evidence

The SCALE candidate's retained two-seed behavioral run and independent replay
pass, including 40,585 scale-port rows per seed: 5,400 old-data collision
observations, 1,350 distinct dual writes, same-address `Q_FILL` priority, held
outputs, and cancellation edges. These prepared-state rows cover every valid
1,350-word address but do not claim packet reachability for every internal
state. The mapped post-synthesis UNISIM unit also passes 27,033 clocks. Its
retained primitive report maps the scale table to one `RAMB18E1` with
`READ_FIRST` on both ports. RTL holds the B output register on a B write; that
behavior is implemented outside the RAM primitive and must not be described as
a `NO_CHANGE` primitive mode. The mapped unit is functional simulation without
SDF and does not provide a placed or routed timing result.
The mapped-unit `xelab` logs contain an XSIM 43-3431 host-environment advisory
about compiler environment variables; the audit records it separately from
simulation warnings. The retained `xsim` test logs have no runtime warning,
waiver, assertion-failure, or test-failure lines.

A read-only timing extraction from the retained elastic route checkpoint
verifies two `lookup_mode` and two `lookup_scale` register endpoints on the
inherited 10 ns clock. Worst mode slack is −2.508 ns; worst scale slack is
−2.587 ns. The checkpoint hash is unchanged, mounted read-only, and the probe
made no RTL, clock, or exception edits. This is a diagnostic of the elastic
route, not a SCALE-variant route. A standalone SCALE full-pipeline canonical
comparison and native route are deferred.

The combined TABLES candidate's focused two-seed whole-admission run passes 86
case-profiles and 44 directed checks per seed. Its mapped UNISIM unit retains
both physical RAM modes: the mode table is `READ_FIRST`/`WRITE_FIRST`, and the
scale table is `READ_FIRST`/`READ_FIRST`; outputs use the candidate's external
hold behavior where required. The unit simulation is not a full-pipeline or
timing result. TABLES full canonical comparison now passes with 44 candidate
case-profiles and 42 directed checks across two seeds; the retained same-seed
elastic controls are reused and not recounted. The TABLES native route is
legal but fails setup timing: WNS −3.076 ns, 21,608 of 89,974 setup endpoints
failing, hold +0.088 ns, and pulse +3.750 ns. Its worst path is from
`coefficient_boundary/payload_reg[43]` to `transform/child_epochs_reg.../WE`,
with 12.459 ns data delay and 13 logic levels. All 62,650 routable nets are
routed with zero routing errors. This component route does not meet the 10 ns
target. Neither the focused pass, unit mapping, nor canonical comparison is a
hardware claim.
An earlier focused attempt is also retained: the simulator exited 134 on an
assertion in the `admission_original.sv` header prepared-cache fixture. Its
runner left `actual_RTL_run=false` because the attempt did not complete, but the
retained simulation log confirms execution reached RTL. The audit labels that
as an executed assertion failure rather than a pre-run failure or a pass; the
later selected two-seed run is audited separately.

## Private payload reset/control proofs

The dequant private-state candidate passes three actual RTL seeds, with public
outputs checked on every edge and an independent public-cycle audit. Across
each seed it accepts 6,716 inputs, retires 6,686 items, and records 30 explicit
discards; reset/abort interruption and upstream-input noise are exercised in
idle, hold, and multiply states. Its mapped component inference covers 1,027
FDRE payload bits. The candidate maps reset and CE control away from those
payload bits. A follow-up mapped-netlist fan-in query corrects an earlier Vivado
query that reported blank port lists for both variants: it finds the original
reset/CE port sources and confirms no such source reaches the candidate payload
reset or CE. Before/after synthesis checkpoint hashes match in that read-only
query.

The IDCT private-state candidate passes two actual RTL seeds and independent
trace replay, covering all 1,023 FSM states, all 1,023 abort/reset mask states,
4,303 tiles per seed, and 30 directed abort/reset cases. Its native component
mapping compares the selected candidate with the actual V106 IDCT source hash
`1ed49416…a5cc32` (not a pathname-based assumption about the V69 alias). The
mapped reports account for 1,280 FDRE source-tile bits: candidate reset and CE
have no external port fan-in and all reset pins are grounded; the original has
external `abort_frame`/`rst` reset fan-in and `abort_frame`/`in_valid`/`rst` CE
fan-in. These are isolated component inferences on a synthetic 10 ns unit
clock, not full-parent timing results.

The payload component proofs establish private reset/CE behavior only; they do
not establish metastability performance, board CDC signoff, or routed parent
timing.

## 32-bit guard proof and routed motivation

The focused guard check evaluates the actual 32-bit RTL expression over 131,072
17-bit operands and nine count cases per operand (1,179,648 rows). Its retained
source/artifact hashes, actual RTL run, and result counts pass independent
checks. This is an expression-level proof, not a full-module standalone
mapping or timing result. A mapped attribution tied to the TABLES checkpoint
identifies a DSP48E1 with constant B=43, AREG=1, BREG/MREG/PREG=0, and 13 of 17
high A bits grounded. A separate read-only timing probe against that unchanged
checkpoint finds the worst DSP path at −2.497 ns slack, 12.208 ns data delay,
and 11 logic levels on the inherited 10 ns clock; no RTL, clock, or exception
edits were made. The combined guard canonical comparison now passes with 44
newly executed candidate case-profiles and 42 directed checks across two seeds,
matched against the retained elastic candidate's same-seed outputs, events,
cycles, and canonical bytes. The payload and META routes have completed and
failed setup timing as reported above. The guard build was scheduling-cancelled
before checkpoint creation. No
full-module or hardware claim is made from the expression proof or the
motivating probe.

## META flag evidence

The separate META flag candidate has two actual stage runs (67,715,579 total
edges) and two inverse runs (41,697 total stage/inverse clocks), all passing.
The stage proof includes 67,108,864 metadata-domain cases, 32,768 helper-plane
cases, and 262,144 scale-value cases. The inverse proof compares prepared and
historical behavior across 128-word state with 51 concurrent math cases per
seed; no public cycles were added. The independent full-pipeline canonical
comparison also passes with 44 newly executed candidate case-profiles and 42
directed checks across two seeds, matching the retained candidate streams
exactly. The independently activated META native build is a seventh trial,
separate from the six earlier native receipts. Its source snapshots and origin
map match the passing canonical qualification. Its legal route nevertheless
fails setup at WNS −3.146 ns, with 25,263 of 88,089 setup endpoints failing;
hold and pulse slack are positive. The route does not meet the 10 ns target,
and the behavioral checks do not support a hardware claim.

## Terminal V107 readout (2026-11-08)

The final independent audit is `TERMINAL_NATIVE_EVIDENCE_RETAINED_NO_TIMING_PASS`
at `TERMINAL_EVIDENCE_READOUT`: all nine native attempts are terminal, every
required source, recipe, artifact, report, checkpoint, qualification, and
activation hash gate passes, and no evidence is pending. The best completed
native result is the single `threshold-runtime` route (synthesis
`RuntimeOptimized`; opt/place/route `Default`) at WNS **−2.333 ns**, with
**21,433 of 89,258 setup endpoints failing**. Hold slack is +0.096 ns with no
hold failures; pulse slack is +3.750 ns with no pulse failures. All 65,912
routable nets were routed with zero routing errors. Its route receipt SHA-256
is `8a24372a70162d2968e255f2c0175e15d4bed9d86e7e5578f7cc84e1a38acd47`.

The separately completed Default-strategy `threshold` attempt used the same
qualified source set and inherited single 10 ns OOC clock. It routed legally
but is worse: WNS **−3.137 ns**, **29,395 of 89,119 setup endpoints failing**,
hold +0.082 ns, pulse +3.750 ns, and zero routing errors. Neither route meets
the timing target; the runtime synthesis strategy is not a matched timing
comparison against Default8. Native reports have no missing clocks or
unconstrained internal endpoints, but OOC results still do not establish board
I/O timing, reset timing, full-top fit, CDC signoff, or hardware behavior.

The terminal campaign retains the earlier completed setup-failing routes and
the two explicit scheduling cancellations. The cancelled HEADER and guard
attempts ended before checkpoint creation and have no timing result. The
earlier V106 sixth-attempt timeout and separately resumed route remain distinct
from the V107 native campaign. No attempt is silently dropped or promoted based
on intermediate optimization data. The separate read-only post-route
`AggressiveExplore` diagnostic on Runtime9 ended with SIGSEGV (exit 139); its
failure audit confirms no final report or new checkpoint. It is recorded as
an optional diagnostic failure and contributes no timing result.

The read-only mapped-pin attribution on the selected payload route identifies
7,141 loads on the scratch/cancel net, including 7,128 slice-SR pins: 7,125
telemetry data FF sinks and three operational FF sinks. The independently
retained model-only counter-bank prototype passes four 50,000-cycle seeds and
compares all 32 public bins each cycle, including a negative control for a
stale increment. The capacity-bound arithmetic model also passes its declared
finite grids and random cases. Both models are explicitly model-only: neither
is RTL/full-source equivalence, formal proof, native resource/timing evidence,
or proof that production reset/control can safely change.

The three central plan inputs hashed into the final JSON are
[`gamebub-application-specific-codec-plan.md`](../gamebub-application-specific-codec-plan.md),
[`gamebub-v91-v110-development-plan.md`](../gamebub-v91-v110-development-plan.md),
and [`literature-review-2026-11-06/README.md`](../literature-review-2026-11-06/README.md).
The reset/fanout guidance at [`reset-fanout-plan.md`](reset-fanout-plan.md) is
also hash-bound as a fourth planning input. The machine-readable audit binds
the terminal receipts and all retained native reports. Its final capacity-model
gate records 33,554,432 full-u17 grid cases, 1,966,080 tied boundary cases, all
131,072 raw block values, and the declared randomized and error-priority cases.
The initial syntax and NumPy preparation failures remain retained as
nonexecutions.

No hardware was contacted. V107 remains an OOC timing investigation, not a
100 MHz closure or a hardware qualification.
