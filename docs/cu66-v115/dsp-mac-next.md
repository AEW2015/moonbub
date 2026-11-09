# Next IDCT experiment: interleaved DSP MAC at II=1

A one-coefficient-per-cycle IDCT is a credible next experiment. The existing
alternating even/odd sums can form a two-cycle feedback recurrence using the
DSP's C and P registers, without duplicating complete tile banks. This is a
schedule proposal, not simulated RTL, a resource estimate from synthesis, or a
measured clock result. Freeze V115 and inspect its new routed paths first.

## Current measured baseline and exact source behavior

`fpga/experiments/cu66-v115-inverse/cu66_idct8x8.sv` is frozen at
`640b6729bbfeca8cd19d8514f06e1043be1302029dcebaadbadf9a7b81e6cc8a`.
Eight logical lanes share four signed Q14 basis values. Each normal group visits
k=0..7 using separate MUL and ACC edges. Four groups in each of two passes
therefore require 128 MUL/ACC edges, plus preparation and transfer overhead.
Even k updates `even_sum`; odd k updates `odd_sum`. At k=7 the source computes
both mirrored results from E+O and E−O, rounds, then stores the next pass's
intermediate values or final output words. Source/intermediate/output tile
storage and external inverse-wrapper result slots are already bounded.

The V114B125 routed primitive audit maps **17 DSP48E1 cells in IDCT**, not eight:
sixteen `p_1_out*` cells and one `rounded_return0`, all AREG=1/BREG=1/MREG=1/
PREG=0. Whole component usage is 42 DSPs. Logical lane count must not be passed
off as actual DSP count. The per-cell input widths, cascades and synthesis
operator mapping need inspection before claiming that an eight-cell MAC
implementation replaces this mapping. See the immutable B125
`route-dsp-registers.tsv` and `route-utilization.rpt` under
`experiments/python-gamebub-v114/optimized/native/20261108T235739184089Z/reports/`.

The selected V115 [cycle ledger](performance.md) measures a maximum fast-service
first-decoder-byte-to-done interval of 1,385,090 cycles. At an assumed 125 MHz,
strictly under 10 ms requires at most 1,249,999 cycles: at least **135,091 useful
whole-component cycles** must be removed from that row. This excludes full
host/firmware/display publication work and does not establish achieved 125 MHz.

## Proposed recurrence, with no duplicated tile banks

DSP48E1 provides a signed 25x18 multiplier and 48-bit arithmetic path, with
optional M, C and P registers. A 24-bit signed sample and 14-bit signed basis
fit those multiplier inputs after explicit sign extension. The candidate uses
MREG=1, CREG=1, PREG=1 and the multiply-plus-C operation. This uses one physical
MAC lane per logical lane if mapping succeeds. [AMD UG479](https://docs.amd.com/api/khub/documents/gu4oRPFEh_Pm2uaAlfY6Kg/content),
[AMD UG953 DSP48E1](https://docs.amd.com/r/2025.1-English/ug953-vivado-7series-libraries/DSP48E1)

Route the registered **P output back to C input** through a small seed selector.
Do not use immediate internal P accumulation, which has only one running
context. Seed C with zero for k=0 and k=1. For later k, the P value available at
the C-register capture edge is the result from k−2. Thus CREG/PREG retain the
two interleaved parity contexts. A/B input preparation and its delayed tags
must align with the M/C stage; the table starts after those inputs are primed.

| MAC edge | Operation entering MREG/CREG | CREG input sampled before edge | PREG result produced after edge |
| --- | --- | --- | --- |
| 0 | k0 | 0 | invalid warm-up |
| 1 | k1 | 0 | E0 = p0 |
| 2 | k2 | registered P = E0 | O1 = p1 |
| 3 | k3 | registered P = O1 | E2 = E0+p2 |
| 4 | k4 | registered P = E2 | O3 = O1+p3 |
| 5 | k5 | registered P = O3 | E4 = E2+p4 |
| 6 | k6 | registered P = E4 | O5 = O3+p5 |
| 7 | k7 | registered P = O5 | E6 = E4+p6 |
| 8 | next group k0 or bubble | 0 for a new group | O7 = O5+p7 |

This table describes edge semantics, not an asserted primitive simulation
result. At edge 8 the old P value is E6, so capture it with its group/owner tag.
The final O7 becomes available after edge 8. A separate closing/rounding stage
uses both, with no dependency on the next group's seeds. That closing stage
must sustain one finished group per eight issues; it may overlap subsequent
group issues. The first-to-second-pass barrier must wait for every required
intermediate word, including the last group's rounded words.

A first pilot should infer the multiply, C register and registered sum from
explicit signed expressions, then inspect actual mapping. Keep a small
technology-specific reference only if inference cannot express the required
register/feedback structure. Do not add a blanket DSP primitive or preservation
attribute before measuring the mapped result. P-to-C routing, its seed mux and
high-fanout control still have physical timing costs.

## Arithmetic must remain bit exact

Keep the original input domain ±522,240, signed24 intermediate/sample format,
signed14 basis constants, signed38 products and original two-pass order.
Sign-extend products into the MAC; do not switch to unsigned arithmetic,
saturation, truncating multiplication or a different DCT factorization.
For all signed24 samples and the actual maximum basis magnitude 8,035,
8 × 2^23 × 8,035 = 539,219,722,240, below the signed40 positive limit
549,755,813,887. Consequently the eight-term E±O result fits the original signed40
arithmetic even under that conservative operand bound. Four-term parity sums
also fit. A 48-bit MAC can therefore retain the same integer result here.

At each pass boundary preserve exactly `24'((a + 40'sd8192) >>> 14)`.
The bias is applied before an arithmetic shift; a negative half-way value is
not symmetric round-to-nearest-away-from-zero. Keep the final signed24 cast
and its defined wrap behavior; do not substitute clipping or rely on a looser
range argument to remove the cast. Zero, DC and invalid tiles should retain
independent shortcuts. The existing short DC path need not become a longer
normal MAC job merely to make the scheduler uniform.

## Expected cycle opportunity, not a frame-rate prediction

A fully overlapping eight-group issue schedule has 64 coefficient issue edges
instead of 128 serial MUL/ACC edges, but pipeline fill, parity retirement,
rounding, pass barriers and wrapper transfers consume additional edges. A
conservative non-overlapping 8-issue group plus several closing edges might
save only about 24 edges per normal tile. A useful initial target is at least
32 saved **isolated AC-tile** edges, then measure actual component savings.

A read-only count of the frozen dequant golden tiles gives:

| Corpus case | AC tiles | DC tiles | Zero tiles | Isolated opportunity at 24 / 32 / 64 saved edges per AC tile |
| --- | ---: | ---: | ---: | ---: |
| actual_001 | 2,954 | 3,614 | 1,238 | 70,896 / 94,528 / 189,056 |
| actual_031 (worst fast row) | 5,442 | 677 | 0 | 130,608 / 174,144 / 348,288 |

Source: `experiments/python-gamebub-v91j/vectors/transform_tiles.tsv.gz`,
classified from all 64 signed dequant values per tile. These are arithmetic
opportunities, **not** simulated whole-frame savings. Twenty-four edges per AC
tile would not even cover the worst row's 135,091-cycle deficit under perfect
critical-path overlap. Twenty-five would leave only 959 cycles of arithmetic
margin. A 32-edge target would nominally cover it, but coefficient parsing,
result-slot availability, canonical reconstruction and memory service can
become the actual bottleneck. The existing wrapper serializes each tile's
DQ/IDCT math while overlapping assembly and result emission. Re-run its full
ledger; do not subtract isolated math savings from the frame row and call that
a measured decode time.

## Prototype gates and tests

1. Build a pure integer/Python edge model of the proposed recurrence and delayed
   `(valid, owner, pass, group, k, parity, seed, last)` tags. Compare every prefix
   sum, E/O retirement and rounded output to the frozen two-pass oracle. Include
   sparse AC, dense AC, signed extremes and negative rounding ties. This is an
   algorithm/schedule check, not FPGA timing evidence.
2. Implement one inferred MAC lane in an isolated new experimental directory.
   Qualify actual RTL at one issue per cycle, then arbitrary common freezes,
   isolated bubbles and restart seeds. Assert that no context reads k−1 in place
   of k−2 and that tags/operands/C/P freeze together. Native-mapped register and
   DSP counts must confirm MREG/CREG/PREG rather than assume inference succeeded.
3. Expand to eight lanes while preserving source/intermediate/output storage.
   Track finite in-flight tags, a final-even holding tuple and the rounding
   stage. Do not add complete tile replicas. First stop between groups if needed;
   establish correctness before overlapping group closes with new issues.
4. Retain every original helper/inverse/full-component golden and checker.
   Add abort and reset on each new input, M, C/P, even-retirement, odd-retirement,
   rounding and pass-transition edge. Public transfers must revoke immediately;
   late private DSP values must remain invalid after cancellation. Retry on the
   same object with poisoned old payload, then stall the complete output tuple.
   Test downstream result-slot pressure and accepted physical-debt drain in the
   real parent, not just a standalone MAC model.
5. Measure actual helper cycles and the same full-component/transport rows.
   Route the exact qualified composition at requested 100/125 MHz, inspect worst
   paths, register controls, fanout, placement, utilization and hold checks. Do
   not report a successful Fmax, under-10-ms decode, or sustained 30 fps until
   their separate measured gates pass.

The main unknowns are inference of the desired two-edge recurrence, the real
cost of seed/control routing and coordinate/source muxes, overlap of closing
rounders with subsequent groups, and how much of the worst frame is actually
math-limited. The native V115 route results should decide whether this is the
next implementation experiment or whether another measured control cone comes
first. No frozen source or proof input was changed for this feasibility note.
