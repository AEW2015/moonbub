# V128 routed timing and implementation results

**The targeted paths improved, but the component still fails 125 MHz setup.**
Against V127, global WNS regressed from −1.193 ns to **−1.320 ns**, TNS from
−1,762.554 ns to **−3,146.811 ns**, and failing setup endpoints increased from
6,980 to **10,006**. The candidate is not promoted. One fresh 8 ns implementation
was measured; the unchanged negative composition was not rerouted.

## Source, implementation and evidence

The selected composition changes five of V127's 18 source origins: four implement
full 72-bit RAW/context tuple validation before Boolean selection, and one adds
the unreset header-padding prefix flag. Thirteen origins remain unchanged. The
full functional suite passes four decoder/transport, two peer and four byte/row
publication stream comparisons with **zero public-cycle delta**; see the
[functional results](functional-results.md).

The [native receipt](../../experiments/python-gamebub-v128/native/20261110T215644882105Z/receipt.json)
records a fresh RTL build with Vivado 2026.1 build 6511674 for `xc7a100tcsg324-1`.
The unchanged V120 core recipe loads an 8 ns clock before synthesis and uses
synthesis Default, opt Default, place ExtraNetDelay_high and route Default. No
new timing exceptions, guessed I/O delays, separate phys-opt pass, clock
relaxation or prior-checkpoint implementation start was used. The run took
1,710.275 seconds of host time, which is not FPGA decode latency.

The [independent terminal audit](../../experiments/python-gamebub-v128/audit/native-independent.json)
passes **1,654 evidence-integrity checks** with zero failed checks or errors;
it separately reports `design_timing_pass=false`. Source and recipe snapshots
matched at completion. The retained routed checkpoint is an external artifact,
28,455,566 bytes, SHA-256
`a99038c486a6ee678554a5915e799851ad2581b4b3e80516b9b6ee149220846c`.

## Routed result

| Metric | V127 | V128 | Change |
| --- | ---: | ---: | ---: |
| Setup WNS (ns) | −1.193 | −1.320 | −0.127 |
| Setup TNS (ns) | −1,762.554 | −3,146.811 | −1,384.257 |
| Failing setup endpoints | 6,980 | 10,006 | +3,026 |
| Hold WHS (ns) | +0.075 | +0.073 | −0.002 |
| Failing hold endpoints | 0 | 0 | 0 |
| Pulse WPWS (ns) | +2.750 | +2.750 | 0 |
| Failing pulse endpoints | 0 | 0 | 0 |

All **74,852/74,852** routable nets are routed with zero routing errors, and
the internal clock-coverage check reports zero unconstrained internal endpoints.
The out-of-context design still has **1,101 inputs and 12,887 outputs** without
I/O delays. Board I/O and the complete publication parent have not been routed
and qualified at 125 MHz. V123's historical −1.086 ns WNS remains a better
global comparison than either V127 or V128, although it also fails 125 MHz.

The [worst setup path report](../../experiments/python-gamebub-v128/native/20261110T215644882105Z/reports/route-setup-paths.rpt)
now starts at the packet parser's `cached_remaining_reg[31]/C` and ends at
`out_consumed_reg[23]/D`: **9.311 ns** data delay, consisting of **2.816 ns
logic and 6.495 ns routing**, across 14 levels including six CARRY4 cells. This
is a different measured global bottleneck from V127's ingress RAW-mode path.
The cell names and source should guide the next investigation; a cell name alone
does not prove the exact Boolean operation mapped into each carry cell.

## Matched target paths and gaps

The same bounded read-only query was run on both saved routed checkpoints. Its
[comparison](../../experiments/python-gamebub-v128/pipeline-observations.json)
covers 152 named families. Family minima may refer to different physical
endpoints or replicas, so these numbers are matched-family observations, not
pairwise proof about every endpoint.

| Family minimum slack (ns) | V127 | V128 |
| --- | ---: | ---: |
| Ingress RAW mode → scratch state | −1.193 | +1.118 |
| Ingress RAW mode → all endpoints | −1.193 | +1.038 |
| Current child epoch → scratch state | −0.606 | −1.306 |
| Bank 1 block → scratch state | −0.105 | −1.016 |
| Emit bank → scratch state | −0.367 | −1.085 |
| Scalar epoch → scratch state | −0.671 | −1.207 |
| Scratch stored RAW mode → all endpoints | +0.127 | −0.325 |
| Producer cursor → all endpoints | −0.980 | −0.591 |

The first two rows show the intended local improvement. Other families worsened,
and local positive slack does not override the failed global result.

A separately frozen padding query was run on the
[V127 checkpoint](../../experiments/python-gamebub-v128/padding-inspection/baseline-v127-20261110T215424460066Z/receipt.json)
and the [V128 checkpoint](../../experiments/python-gamebub-v128/padding-inspection/candidate-20261110T222722130673Z/receipt.json).
Both completed with the input checkpoint hash unchanged. Minimum slack from
the named header-register Q family to all timed endpoints improved **−1.165 →
−0.630 ns**; the actual worst endpoint changed from a tile R pin to a tile CE
pin. For V128, the measured all-startpoints → padding-cache D path is **+2.369
ns**, and cache Q → all timed endpoints is **+0.494 ns**. The named cache Q has
two direct loads and 402 returned fanout endpoints; printed lists are capped at
256 entries.

The query returned `NO_TIMED_PATHS` for the selected cache CE inputs and for
cache/header Q → tile R. These are explicit query gaps: they do not establish
that paths were eliminated or that the selected endpoint is qualified. Header
register mapping differs from its 1,024 declared source bits; constant
propagation, replication or renaming cannot be distinguished from the name
inventory alone. The [method and limits](padding-inspection.md) describe the
selectors and bounded reports.

## Cost and methodology

| Routed resource | V127 | V128 | Change |
| --- | ---: | ---: | ---: |
| LUT | 33,576 | 34,504 | +928 |
| FF | 43,594 | 43,432 | −162 |
| DSP | 42 | 42 | 0 |
| RAMB36 / RAMB18 | 32 / 12 | 32 / 12 | 0 / 0 |
| Control sets | 1,253 | 1,233 | −20 |

The actual mapped-name inventory finds one padding-cache FF in synthesis and
route, and no verification-only padding-owner FFs. That observation is physical
mapping evidence for this build; it is separate from the source-level one-bit
declaration. Fresh methodology results report **28 SYNTH-6, 167 TIMING-16,
1,000 TIMING-18 and one ULMTCS-1**. TIMING-16 increased from V127's 55; these
findings and the missing I/O constraints are not waived by the passing evidence
audit. The fresh methodology report is distinguished from the cached
methodology table in the timing summary.

The row-parent tests retain **1,145,104 / 1,553,197** cycles from last accepted
outer input to validated commit. At an assumed complete-parent 125 MHz, those
are **9.160832 / 12.425576 ms**. The stalled profile needs at least **303,198**
fewer cycles for strictly under 10 ms, even before physical memory, transport
and board behavior are validated. Neither sustained hardware 30 fps nor
hardware decoding under 10 ms has been demonstrated by this component run.
