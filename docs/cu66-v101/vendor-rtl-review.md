# V101 native Vivado baseline: RTL review and V102 experiments

Native Vivado **2026.1 build 6511674 successfully synthesized the unchanged
`cs88_pipeline_v91k` component for `xc7a100tcsg324-1`**. The corrected flow loads
the 10-ns component clock before synthesis. **Placement did not run:** its DRC
preflight rejects the design's distributed-memory utilization. No routed
clock, hardware frame rate or under-10-ms decode result exists.

The [terminal log](../../experiments/python-gamebub-v101/constraints/2026-build/20261107T203934371554Z/vivado.log)
and its source/recipe snapshots are the evidence. The earlier attempt stopped
before synthesis on unsupported `read_verilog -include_dirs/-define` options;
the fresh corrected attempt uses the fileset properties. That was a Tcl flow
issue, not an RTL defect. The corrected run accepts the original scratch loop
and original `zigzag` function: the old Yosys iterator errors do not reproduce
in this native flow. Keep the separately verified V101 scratch variant as an
optional compatibility experiment, without assigning it a physical benefit.

## Actual implementation boundary

The synthesized hierarchical utilization report records:

| Scope | Total LUT | LUTRAM | FF | RAMB36 | DSP |
| --- | ---: | ---: | ---: | ---: | ---: |
| Entire component | 74,340 | 22,286 | 34,985 | 16 | 28 |
| Admission | 44,040 | 19,956 | 9,464 | 0 | 1 |
| Scratch | 5,373 | 32 | 3,523 | 0 | 1 |
| Dequantizer | 3,484 | 0 | 2,352 | 0 | 8 |
| IDCT | 6,222 | 0 | 5,096 | 0 | 16 |

Whole-component logic LUTs are 52,054; the remaining LUTs are memory. These are
**native synthesized counts**, distinct from V100's intermediate Yosys DSP
checkpoints. They are not placed resources or a fit pass.

Three `UTLZ-1` errors identify the actual blocker: LUT-as-distributed-RAM and
LUT-as-memory each require **22,286 sites versus 19,000 available**, while
RAMD64E requires **19,956 versus 19,000**. `Vivado_Tcl 4-23` explicitly says
“Placer not run.” Do not downgrade these errors with
`drc.disableLUTOverUtilError`, change the target, or shrink the packet cap to
make this baseline appear qualified.

The synthesized timing report has **WNS −16.629 ns** against the 10-ns clock.
Its worst reported setup path is `reconstruction/plane_reg[1]` to
`reconstruction/count_copy_tiles_reg[0]/CE`, with 49 logic levels including
32 CARRY4 cells and a 26.376-ns data path. Routes in this report are estimates;
this is not achieved Fmax or routed timing.

## Every emitted synthesis warning class

The synthesis phase emits **198 warning messages**, zero critical warnings and
zero errors. Its four warning classes are below. The terminal flow summary's
204 warnings includes subsequent reporting/implementation messages; it is not
another count of synthesis diagnostics.

| ID | Emitted messages | Actual source-backed interpretation and action |
| --- | ---: | --- |
| `8-2898` | 100 | Original scratch concurrent assertions at lines 144/148 are ignored by synthesis. `Common 17-14` explicitly suppresses further occurrences after 100, so this is an emitted count, not the number of assertion instances. Keep the assertions active in simulation; synthesis does not turn them into hardware fault gates. |
| `8-4767` | 9 | Eight messages at IDCT line 152, including unnamed objects and `intermediate_reg`; one at admission line 157 for `scales_reg`. Inspect actual write/read structure before changing memory architecture; the log lists alternative reasons rather than proving every reason applies. |
| `8-6014` | 69 | Removes 64 unused header-byte registers, assertion-only state and a local padding temporary. Review each use; do not preserve dead registers with `dont_touch` or remove validation in response. |
| `8-3917` | 20 | Five upper reconstruction-error bits, five upper inverse-error bits, and ten generated IDCT-helper port bits are constants. The source error domains fit the lower three bits. Preserve public widths; generated helper names require netlist-cone inspection before any source change. |

All referenced source locations were inspected, including the following
important distinctions:

- [Admission header bytes](../../fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv#L209): the removed bytes are **52–115**, corresponding to the C2 content root and frame seal in the [independent reader](../../scripts/cu66-v99/audit_cs88.py#L266). Their copies have no consumer in the selected component. Outer CRC still covers packet bytes; complete content-root/seal validation and atomic publication remain missing integration endpoints. Connect those validators before claiming a complete decoder; retaining unused copies alone adds no validation.
- [Padding check](../../fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv#L214): `padding_ok` is a blocking-assigned local temporary, and `!padding_ok` remains in the rejection predicate. Removal of its sequential element does not establish removal of the padding check. Preserve nonzero-padding rejection vectors during later synthesis changes.
- `owner_initialized`, `consumed` and `latched_size` feed simulation assertions in their respective [reconstructor](../../fpga/experiments/cu66-v91k/cu66_reconstruct_stream_v91k.sv#L211), [refill queue](../../fpga/experiments/cu66-v91i2b/byte_refill_queue_v91i2b.sv#L90) and [coefficient wrapper](../../fpga/experiments/cu66-v91k/cs88_coefficients_v91k.sv#L400). Their synthesis removal does not justify weakening assertions or the ownership/drain protocol.

The log-adjacent external `vendor-review/` folder retains the skill's parsed
CSV/checklist/report. It accounts for all 198 non-INFO messages, including
repeat occurrences; source snapshots match the historical files. The skill's
referenced `oasys_severity_lists.csv` asset is absent, so interpretation uses
the actual messages, dispatch table, inspected RTL and primary documentation.
No source fixes or waivers were applied by this review.

## V102-A: make packet-memory access explicit, then measure inference

This is the first area experiment because admission dominates the failed fit.
The synthesis memory ledger maps admission `memory_reg` as implied **64K × 8**
to **4,608 RAM64M primitives**, while admission uses no BRAM. The source's
logical packet cap remains 49,152 bytes; an inferred physical shape is not a
new wire cap.

At [lines 152–164](../../fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv#L152),
one byte-write port serves receive traffic, and two address-selection branches
read into the same registered `ram_data`. The backing packet RAM is explicitly
**not reset**. A whole-array-reset diagnosis would be wrong here. The observed
LUTRAM mapping is established; the precise inference-choice root cause remains
a hypothesis to test.

Prepare one isolated candidate that expresses a common read-enable and
read-address mux before a single synchronous RAM read:

```text
read_enable  = stage_read_req OR (replay_req AND replay_ready)
read_address = stage_read_req ? fetch_addr[15:0] : replay_addr[15:0]
```

Keep the existing metadata latching under exactly the same priority. Preserve
receive-write behavior, read-before-write semantics on address collision,
response latency, held outputs, reset/start/cancel behavior, replay bounds and
error-data contracts. Keep logical depth, packet cap, initialization policy,
port names and public counters. Test simultaneous writes/reads, both read
requests, first/last addresses, rejected/out-of-range replays and reset/abort
with an owned response. Compare all fresh/historical seeded transcripts and
cycles against V100/V101 before rerunning the exact same vendor flow.

Measure whether this template changes the actual mapping. If it does not,
inspect the synthesized RAM ports and documented templates before trying one
narrowly justified memory attribute or XPM alternative. Do not claim recovered
LUT sites or a fit until actual reports and placement confirm them. AMD's
[UG901 memory inference guidance](https://docs.amd.com/r/en-US/ug901-vivado-synthesis/Memory-Inference-Capabilities)
is the primary reference for the port/collision contract.

Treat `scales` separately: [cache writes at line 155](../../fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv#L155)
and [decoded run writes at line 335](../../fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv#L335)
can describe different writes in the same process, while lookup reads occur in
`FINISHED`. A two-port design must preserve different-address simultaneous
writes, same-address source-order priority and lookup read-first behavior.
Serialization requires a real backpressure/ownership contract. The tiny
64×24-bit IDCT intermediate has 16 element writes in a first-pass group; compare
banked registers/LUTRAM against a changed BRAM schedule rather than assuming a
BRAM directive can satisfy those ports cheaply.

## V102-B: remove the actual variable-divisor validation cone

The critical path's source function is
[`safe_hidden`](../../fpga/experiments/cu66-v91k/cu66_reconstruct_stream_v91k.sv#L78).
It computes `t % (p==0 ? 90 : 45)` and `t / (p==0 ? 90 : 45)` using 32-bit
expressions before checking fixed rectangles. The plane chooses the divisor
inside the arithmetic operator. This is a concrete candidate for the long
validation-to-counter-enable cone; the counter must remain observable.

Use the equivalent interval predicate already present in
[admission's `hidden`](../../fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv#L94):

- Luma: 633–651, 723–741, 993–1011, 1083–1101, 4071–4110, 4161–4200, 4251–4290, 4431–4460, 4521–4550.
- Other plane values: 1046–1064.

A read-only integer comparison confirms equality for **all 32,768 combinations
of the complete two-bit plane and thirteen-bit tile domains**, including plane
3 and out-of-picture tiles. This is a design hypothesis check, not an RTL or
physical-result claim. Implement it as a separate candidate, exhaust the same
inputs through actual original/candidate RTL, and run both fresh and historical
two-seed integrated regressions. Require exact requests, metadata, values,
counters, initialization, cancellation/drain behavior and cycle parity.

Then synthesize/place/route baseline and candidate under the same tool, part,
source visibility and clock constraints; compare complete area and internal
setup/hold paths. If the unchanged baseline cannot place, retain that failure
and compare synthesized cones before qualifying a candidate route. Neither a
shorter source expression nor the integer equality proves timing improvement.
Keep packet-memory and interval changes separate until each passes its own
functional/physical comparison, then test their combined candidate.

## Methodology accounting

The actual report lists **2,451 reported findings**: `SYNTH-5` 378, `SYNTH-6` 8,
`TIMING-16` 1,000, `TIMING-18` 1,000, `ULMTCS-2` 1 and `RTGT-1` 64. The text and
JSON headers say `Max checks: <unlimited>`. The recipe supplies no explicit
limit, but per-rule enumeration-limit properties were not captured. Two rule
counts of exactly 1,000 do not prove either exhaustive enumeration or a cap;
record these as reported findings and verify the rule properties before using
the counts as a closure metric. The captured `SYNTH-5` examples concern
`modes_reg`; do not reassign that reason to packet `memory_reg` without evidence.

Missing interface delays remain explicit board/controller obligations. Do not
invent delays or false paths to remove `TIMING-18`, weaken DRC severity, or
count an OOC synthesis report as board timing/CDC signoff. The command and
report semantics are documented in
[UG835 `report_methodology`](https://docs.amd.com/r/en-US/ug835-vivado-tcl-commands/report_methodology).
