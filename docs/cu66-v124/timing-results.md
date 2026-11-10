# V124 routed timing: owner lanes improve one return path; 125 MHz still fails

The fresh 8 ns route fails setup. V124 is **not promoted** and is not rerouted
unchanged. Its [terminal receipt](../../experiments/python-gamebub-v124/native/20261110T044515396884Z/receipt.json)
is independently rehashed by the [terminal audit](../../experiments/python-gamebub-v124/audit/native-independent.json).
That audit passes 1,177 evidence checks; its `design_timing_pass` is false.
Evidence integrity and design timing are separate results.

| Routed component metric | V123 control | V124 | Change |
| --- | ---: | ---: | ---: |
| WNS, ns | −1.086 | **−1.170** | −0.084 |
| TNS, ns | −1,709.649 | **−2,527.615** | −817.966 |
| Setup-failing endpoints | 6,724 | **9,787** | +3,063 |
| WHS, ns / hold failures | +0.028 / 0 | +0.098 / 0 | Hold passes |
| WPWS, ns / pulse failures | +2.750 / 0 | +2.750 / 0 | Pulse passes |
| Fully routed / routable nets | 73,287 / 73,287 | 73,306 / 73,306 | Zero routing errors |
| Unconstrained internal endpoints | 0 | 0 | Coverage retained |
| Total LUTs | 33,308 | 33,424 | +116 |
| FFs | 43,515 | 43,494 | −21 |
| CARRY4 | 4,215 | 4,220 | +5 |
| DSP / RAMB36 / RAMB18 | 42 / 32 / 12 | 42 / 32 / 12 | Unchanged |

Only the producer origin changes from V123. The RTL adds no state or public
cycle; physical register replication/optimization can still change mapped FF
counts. The part is `xc7a100tcsg324-1`, Vivado 2026.1/build6511674, with the same
pinned image and byte-identical V120 core Tcl/XDC recipe: 8 ns loaded before fresh
RTL synthesis, default synthesis, Default optimization, ExtraNetDelay_high
placement, Default routing and no separate physical-optimization trial. No
checkpoint starts implementation, and no timing exception or guessed board I/O
delay is introduced. The run took 1,679.283 seconds of host wall time; that is
build time, not decoder latency.

## Matched checkpoint observations

The frozen query ran read-only on both routed checkpoints and verified that
their hashes stayed unchanged. The [comparison](../../experiments/python-gamebub-v124/owner-observations.json)
retains all 47 returned timing families, path endpoints, widths and explicit
selection gaps. These are the same declared source/target families, not an
assumption that the worst physical endpoints remain identical.

| Worst slack in query family, ns | V123 | V124 | Delta |
| --- | ---: | ---: | ---: |
| Emit-bank → all timed endpoints | −1.086 | −0.972 | +0.114 |
| Emit-bank → scratch busy | −1.086 | −0.562 | **+0.524** |
| Emit-bank → scratch state | −1.011 | −0.972 | +0.039 |
| Current child epoch → all | −0.154 | −0.798 | −0.644 |
| Expected block → all | +0.171 | −0.860 | −1.031 |
| RAW mode → all | −0.891 | −1.143 | −0.252 |
| RAW position → all | −0.916 | −1.016 | −0.100 |
| Rank mask → all | +0.159 | −0.382 | −0.541 |
| Admission cursor → all | −0.427 | −0.274 | +0.153 |
| Admission cursor → admission state | −0.040 | +0.226 | +0.266 |
| Prepared refill address → all | +0.567 | −0.059 | −0.626 |
| Issued refill counter → RAM enable | +0.959 | +0.455 | −0.504 |

The targeted return to busy improves, but the full emit-bank family remains
negative. Upstream owner tags and several unchanged RAW/rank/refill families
regress. This is a placement/routing tradeoff, not overall timing closure or
evidence that a later tile-only change will close every failing family.

Both full32 bank epochs and full16 bank blocks remain observed. Emit-bank has
17 physical register names for one declared bit; the 64-bit rank mask has 63
physical bits with bit zero absent. The query records these differences without
treating replicas as wider state or an absent name as a timing pass.

The routed design contains the exact scalar net names `tile_owner_match[0]`
and `[1]`, plus inferred-name logic. Their routed `KEEP` properties are blank.
The independent source audit verifies the two-bit RTL synthesis hint, but names
and blank properties do not prove two isolated complete comparison cones or a
physical placement boundary. The observed path delays decide the result.

## New worst path and methodology

The global worst is `coefficients/admission/tile_reg[8]/C` →
`coefficients/admission/tile_reg[24]/CE`: 8.881 ns data delay, of which 1.448 ns
is logic and 7.433 ns is routing, through eight LUT levels and no CARRY4.
The [next bounded proposal](next-timing.md) traces the real source and its
tile/coordinate/mode-write control consumers; it is not an implemented fix.
The previous bank-selection path dropping out of a top-50 list does not prove
that family passed. The matched query above remains the comparison control.

Fresh methodology counts are SYNTH-6 28, TIMING-16 33, TIMING-18 1,000 and
ULMTCS-1 1. V123 had 28/2/1,000/1 respectively. The control-set detail remains
1,252 sets. These categories and capped report counts do not replace setup,
hold, pulse or coverage checks. No methodology waiver was added.

External input/output delay counts remain 1,101/12,884. This is an out-of-context
component study, with no complete-parent/board clock, CDC, physical memory or
display qualification. Qualified Source B100 is unchanged. The unchanged row
parent still measures 1,145,104/1,553,197 post-input→validated-commit cycles;
at an assumed complete-parent 125 MHz, that projects to 9.160832/12.425576 ms.
Sustained distinct hardware 30 fps and validated hardware decode below 10 ms
remain open. No board was contacted or bitstream generated.
