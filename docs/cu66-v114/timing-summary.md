# V114 routed results and next implementation gate

**Timing remains open.** Three fresh RTL implementations finished normally;
all fail internal setup. Each has zero hold failures, pulse-width failures and
routing errors. The six older controls are retained evidence, not new runs.

| Composition | Actual clock | Routed WNS | Failing setup endpoints |
| --- | ---: | ---: | ---: |
| [Reserved control A](primary-100-results.md) | 100 MHz / 10 ns | −1.670 ns | 8,299 |
| [Control + prepared prefetch B](optimized-100-results.md) | 100 MHz / 10 ns | −0.965 ns | 3,032 |
| [Control + prepared prefetch B](optimized-125-results.md) | 125 MHz / 8 ns | −2.696 ns | 33,428 |

Raw receipts, all comparison controls and parsed values are linked in
[`results.json`](../../experiments/python-gamebub-v114/results.json) and
[`native-comparison.csv`](../../experiments/python-gamebub-v114/native-comparison.csv).
The same method uses Default synthesis/optimization/routing and
ExtraNetDelay_high placement, with the clock registered before synthesis.
No timing exceptions, guessed I/O delays, new retiming option or separate
physical-optimization stage was added. Placement still performs its normal
register and mapping optimizations; identical arithmetic source does not imply
identical DSP register mapping in the resulting netlists.

B100 gains 0.705 ns over A100 and removes 5,267 failing endpoints, but remains
negative. B125 gains 0.607 ns over V113's 125 MHz result and 0.148 ns over V112's;
it has 105 more failing endpoints than V112125, so it does not dominate every
timing metric. These results do not establish a usable alternate Fmax.
There is no positive result eligible for a fresh repeat or adoption. Three of
the four allowed initial measurements were used; the remaining slot and the
positive-only repeat were not used for unchanged-source timing searches.

## Choose cuts from the actual target's paths

The [earlier proposal](next-timing-cut.md) is explicitly tied to A100, whose
worst-path sample is dominated by kill-owner qualification. Preserve that
evidence, but do not transfer its ranking to the improved B composition.

For B100, the retained 50 worst paths comprise:

- One band-to-ingress prepared-bounds path, the worst at −0.965 ns: 16 logic
  levels and 10.912 ns data delay.
- Twenty context-block-count to scratch metadata/count/used-byte enable paths.
- Three scratch-read-address to state paths.
- Seven cached-replay-remaining to parser output-value reset paths.
- Nineteen math-bank to dequant output-enable paths.

B125 has a different retained sample: 13 dequant-output to IDCT DSP-input paths,
16 parser cached-remaining to reservoir-enable paths, 12 band to ingress
offset/size/Rice-parameter enables, five scratch-read-address to state paths,
and four replay-remaining to parser output resets. Neither B sample contains
kill-owner paths; absence from 50 paths does not prove that all such paths pass.

The B125 worst path starts at `transform/dequant/out_dequantized_reg[172]/C`
and ends at `transform/inverse/p_1_out/A[28]`: 17 logic levels, including 12
CARRY4s and five LUTs, with 10.250 ns data delay (2.790 ns logic and 7.460 ns
interconnect). Its DSP has AREG=1, BREG=1, MREG=1, PREG=0. This is an input
preparation/selection cone reaching a DSP input, not an observed multiplier
propagation path. The source contains range/zero/DC and sample/prefetch/rounding
selection logic; the report alone does not attribute the entire cone to one
exclusive source expression.

Next prototype coherent registered operands and validation/selection flags
before IDCT admission, local per-band request descriptors and bounds, parser
continuation controls, and bank/dequant enables. Capture each tuple and its
owner together; prove held stability, first-fault behavior, immediate public
revocation, accepted physical debt drain, and clean retry under the declared
new latency contract. Inspect exact signed-width/range semantics before
replacing comparisons or narrowing arithmetic. Requalify canonical bytes and
cycle counts before fresh 10/8 ns routes. Extra DSP lanes alone do not remove
these measured cones.

## Packing and system limits

All three components use 42 DSPs and 38 BRAM tiles. B100 uses 36,052 LUTs and
39,747 FFs but occupies 14,707/15,850 slices (92.79%); B125 uses 36,883 LUTs,
39,522 FFs and 14,479 slices (91.35%). Available DSP count is not a whole-parent
lane budget. Control sets, local placement, memory ports and concurrent JPEG,
custom decode, overlay and scanout still need a real integrated implementation.

The [cycle ledger](performance.md) also remains above the strict latency target:
the unstalled worst case takes 1,383,951 cycles before complete-parent validation.
The [SR14 study](syntax.md) is a software/native restart-container prototype,
not an implemented parallel FPGA decoder or production wire format.

The roadmap's V114 complete-parent exit remains unqualified: native Sunshine
encoding, negotiated ESP32 execution, production QSPI/CDC, actual memory
arbitration, C2/HUD seal and display publication are not integrated by this
branch. Neither 300 distinct displayed frames over ten simulated seconds,
sustained hardware 30 fps nor validated full decode below 10 ms is established.
No board bitstream was generated or hardware contacted.
