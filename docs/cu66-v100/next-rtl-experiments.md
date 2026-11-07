# Bounded V101 RTL experiments

This review inspected the frozen scratch, dequantizer, IDCT and inverse-stream
sources plus retained V100 diagnostics. It changes no RTL and launches no
builds. The three experiments below should be separate V101 variants, each
compared with baseline `f403a5f5149de60ebc128ac57911c4912bec0ddf`.

## 1. Remove the conditional scratch loop iterator from synthesized logic

The first full-component mapping failure is recorded in
[mapping-diagnosis.json](../../experiments/python-gamebub-v100/physical/v100-sv2v-baseline-a/mapping-diagnosis.json):
`Latch inferred for signal packed_scratch_v91g2.sv2v_autoblock_3.b from always_comb process`.
It points to the conditional `for(integer b=1;b<=3;b=b+1)` at
[`packed_scratch_v91g2.sv:231`](../../fpga/experiments/cu66-v91g2/packed_scratch_v91g2.sv#L231).
The iterator only executes inside the enabled-prefetch, non-tile, sealed,
`EMIT` path. Its named storage is introduced by conversion. This diagnosis
does not establish a functional latch in the original source: the unchanged
original/converted behavioral regression passed independently.

**Change:** replace this three-entry candidate scan with explicit fully
assigned address/eligibility expressions and a fixed priority selection:
DC miss, then band 1, band 2, band 3. Keep the raw-mode next-sample branch
separate. Preserve every prefetch enable, state, cancel, outstanding-owner,
error and cache-line predicate. Compute each band's aligned address in a
32-bit temporary, then apply the existing 18-bit request-address cast. Do not
change scratch layout or band cursor arithmetic. Every combinational temporary
and candidate output must receive an unconditional default; eliminate the
conditional procedural iterator rather than inventing storage for it.

**Tests and acceptance:**

- Exhaust the three band-eligibility bits, with DC hit/miss, to prove the
  original priority and chosen segment/address. Include 16-byte line crossings,
  exhausted cursors, final block, raw extraction and disabled/tile modes.
- Exercise reset, matching abort, response error and mismatched response while
  a prefetch is offered or accepted. An accepted external owner must still
  drain; no candidate may leak after cancellation.
- Run both existing full V91k seeds and both fresh V99 key/P/late-CRC seeds,
  including their existing stall/reset/cancel assertions. For this scheduling
  neutral change, require baseline-identical request/event bytes, all public
  outputs and cycle counters.
- Convert the candidate using the same pinned sv2v policy, rerun paired
  original/converted qualification, then check that process lowering no longer
  infers the iterator latch. A later independent mapping failure remains a
  failure; passing this point alone is not full-component synthesis success.

This is the first compatibility fix. It has **no demonstrated area, frequency
or cycle benefit**. Do not report resource savings from merely getting farther
through the frontend.

## 2. Make legal arithmetic widths explicit, keeping wide public contracts

The dequantizer currently multiplies signed16 coefficients by signed9 positive
quantizers into signed25 combinational products, then emits signed20 values
([source](../../fpga/experiments/cu66-v69/inverse/cu66_dequant.sv)).
The IDCT stores signed24 intermediates/samples, signed38 products and signed40
even/odd accumulators
([source](../../fpga/experiments/cu66-v69/inverse/cu66_idct8x8.sv)).
Dynamic packed selects, the 64-entry intermediate store, and output/debug
visibility can preserve substantial mux/register logic. Narrowing is an area
hypothesis to measure, not a DSP-count reduction already established.

**Change:** after retaining the original full-width input validation, capture
legal DQ coefficients as signed13 and use an explicit signed13 × signed9
product. Keep quantizer rounding/clamping exactly as written: scale 0 uses
`(base+1)>>1`, scale 1 uses `base`, scale 2 uses `base<<1`, all clamped to 255;
code 3 remains invalid. Keep the signed20 public DQ output.

For the IDCT, prototype signed22 intermediates/shared samples, signed36
products and signed37 even/odd accumulators and rounding inputs. Keep signed24
public residuals and exactly two separate Q14 roundings. These candidate
widths follow from the existing input bound and basis constants:

The [static bound script](../../scripts/cu66-v100/width_bounds.py) independently
parses all 32 frozen basis entries and reproduces the four equal column norms
and the [integer-bound receipt](../../experiments/python-gamebub-v100/width-bounds.json).
Run `python3 scripts/cu66-v100/width_bounds.py`; this validates the width
hypothesis only, without substituting for the proposed RTL extreme-value tests.

| Bound derived from frozen constants | Value |
| --- | ---: |
| Maximum legal absolute DQ input, `2048 × 255` | 522,240 |
| Maximum column sum of absolute basis coefficients | 43,284 |
| First-pass absolute bound, `floor((522240×43284+8192)/16384)` | 1,379,678 |
| Second-pass absolute bound using that intermediate bound | 3,644,896 |
| Maximum first-pass unrounded absolute sum | 22,604,636,160 |
| Maximum second-pass unrounded absolute sum | 59,717,982,552 |

The intermediate bound fits signed22, and the second sum plus the rounding
bias fits signed37. The proposed signed36 product preserves the full 22×14
multiply. Preserve explicit signed extension, `+8192`, arithmetic right shift
by 14 and mathematical floor for negative values. Do not merge the two
roundings, clip residuals, or truncate a malformed input before validating it.

**Tests and acceptance:**

- Check all 384 quantizer entries (two plane classes, three scales, 64 positions)
  against the frozen table contract, including odd scale-0 entries and
  scale-2 saturation. Exhaust the legal scalar coefficient/product range in
  the reference calculation; run RTL boundary tiles, signed extremes, invalid
  ±2049 coefficients and qcode 3 through the unchanged public interfaces.
- Add IDCT adversarial tiles with signs aligned to each basis column, their
  negatives, DC-only/zero tiles, and values around positive and negative
  rounding boundaries. Verify both intermediate passes against the independent
  integer model, with no range assumption beyond the existing legal contract.
- Preserve both seeded integrated regressions and exact signed20/signed24,
  metadata, cancellation and error behavior. The schedule should be unchanged;
  require baseline-identical cycles as well as values for this experiment.
- Compare mapped LUT/FF/DSP/memory totals under identical source visibility,
  constraints and tool versions. Synthesis may already remove some redundant
  upper bits; eight multiply lanes can still consume the same DSP count.
  Accept an area claim only from complete comparable reports. No throughput
  gain is assumed from narrower declarations.

## 3. Overlap registered IDCT multiply and accumulation microcycles

The general IDCT path alternates `FIRST_MUL/FIRST_ACC` and
`SECOND_MUL/SECOND_ACC`. Four groups, eight terms, two microcycles and two
passes give 128 arithmetic microcycles for a general tile, before surrounding
handshakes. Zero and DC-only paths already bypass that schedule. The inverse
adapter also serializes DQ, IDCT and emission for its active tile
([adapter](../../fpga/experiments/cu66-v91j/cu66_inverse_stream_v91j.sv));
therefore reducing arithmetic cycles may help, but the measured frame can
still be limited by entropy/scratch/input service or output stalls.

**Change:** retain eight multiplier lanes and their registered products, but
compute the next term's products while accumulating the previous valid term.
Carry an explicit product-valid bit and the previous term's parity/group/pass
identity. Clear the pipeline at group/pass boundaries and on cancel/reset;
only round and write a group after its eighth accepted product. Start with
one fill/drain boundary per group rather than interleaving unrelated owners.
A simple eight-product-plus-drain group schedule would have nine arithmetic
edges instead of sixteen; that is a proposed schedule, not a measured latency.
Keep the zero/DC paths unchanged in this first throughput variant.

**Tests and acceptance:**

- Reuse every arithmetic exactness test from experiment 2, initially with
  baseline widths so scheduling and width changes remain independently
  reviewable. Compare per-tile values and ordering while permitting the
  intentionally changed timestamps and `active_cycles`.
- Cancel or reset on product fill, odd/even accumulation, final product,
  group transition, pass transition and held output. Prove no stale product
  reaches a new token/epoch, no incomplete group is rounded, and the two-bank
  owner bound and completion/drain fence remain valid.
- Run fresh key/P/late-CRC FAST/SLOW seeds and full V91k controls. Preserve all
  per-stage value/metadata checks and existing assertions. Compare total cycles,
  first/last coefficient and residual cycles, bank occupancy and stall counters
  to locate any actual gain. Compare candidate-original versus
  candidate-converted runs cycle-for-cycle; compare baseline versus candidate
  semantically where the schedule intentionally differs.
- Require measured cycle improvement and complete comparable area reports.
  A denser arithmetic schedule can change mux/control paths and routing; only
  an eventual supported-part implementation can establish its clock behavior.
  Do not trade signed accuracy or failure recovery for fewer cycles.

## Public interface and performance gates

All three variants must retain the 308 public ports, their widths/directions,
all nine public unpacked-array orders, and all runtime controls. Keep metadata
binding for plane, tile, block, qcell, scale, epoch/child epoch and token.
`quant_cell()` currently includes division/modulo by 90 in its combinational
metadata validation; its mapped cost is unknown, and validation must not be
removed merely because normal upstream traffic supplies correct metadata.
Do not tie off debug/status outputs or remove 64-bit counters to manufacture
smaller synthesis results. The wide coefficient/dequantized debug buses and
public state views must remain equally observable in both compared variants.
Preserve initialization, held tuples, accepted-request acknowledgment drain,
error codes and no-success-on-late-CRC behavior. Never disable existing
assertions or weaken the testbench to make an experiment pass.

The [fresh-key result](../../experiments/python-gamebub-v100/rtl/results.json)
is 1,386,271 FAST component cycles, already above one million. **Conditionally**,
if this exact component ran at the 100 MHz comparison clock, a 10 ms budget
would contain 1,000,000 cycles and these cycles would take 13.86271 ms. Reaching
that cycle budget would require removing 386,271 cycles, about 27.86% of this
measured component workload, before accounting for missing whole-frame work.
This is arithmetic using a comparison clock, **not an achieved FPGA speed**,
timing closure, full-frame latency or publication result. No new clock,
hardware FPS or whole-system throughput follows from any recommendation here.
