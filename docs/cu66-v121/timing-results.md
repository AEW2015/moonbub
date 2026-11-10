# V121 native timing and mapped-path results

The fresh 125 MHz implementation completed in **1,608.26 seconds**. Setup still
fails. Source B's 100 MHz repeat qualification does not transfer to this new
composition or to any complete board design.

- [Fresh native receipt](../../experiments/python-gamebub-v121/native/20261109T234502249779Z/receipt.json)
- [Independent terminal audit](../../experiments/python-gamebub-v121/audit/native-independent.json)
- [Machine summary](../../experiments/python-gamebub-v121/results.json)
- [Original B125 comparison](../cu66-v120/B-native-initial-mapping.md)

## Fixed method and complete result

Fresh RTL, `xc7a100tcsg324-1`, top `cs88_pipeline_v91k`, Vivado 2026.1/build 6511674,
and 8.000 ns loaded before synthesis. Default synthesis by omission, Default
optimization/route, ExtraNetDelay_high placement, no added physical optimization.
The V120 core Tcl and report scripts are byte-identical. The source map has all
18 aliases; only the refill queue origin differs from qualified Source B.

| Metric | Source B125 | V121 |
| --- | ---: | ---: |
| WNS | −1.517 ns | −1.347 ns |
| TNS | −3,931.934 ns | −3,248.192 ns |
| Setup failures | 10,524 | 9,407 |
| WHS / hold failures | +0.082 ns / 0 | +0.069 ns / 0 |
| WPWS / pulse failures | +2.750 ns / 0 | +2.750 ns / 0 |
| Internal unconstrained endpoints / clockless endpoints | 0 / 0 | 0 / 0 |
| Routing errors | 0 | 0 |
| Fully routed / routable nets | Retained in B receipt | 73,823 / 73,823 |
| Complete component target pass | False | **False** |

The independent audit recomputes 606 integrity checks, including native source
and recipe snapshots, selected functional proofs, actual synth command,
clock/part/tool/resource identity, timing/check/routing reports, methodology and
external checkpoints. Evidence-integrity PASS does not mean design-timing PASS.

No constraint was modified or waived. Both before/after effective XDC files and
native methodology reports are retained. Missing external input/output timing
requirements remain an explicit OOC limitation; no guessed I/O delays or false
paths make the internal result look better. Complete-parent CDC, board I/O,
SDRAM/QSPI and scanout qualification remain separate.

## Targeted request-family measurement

Separate bounded read-only jobs opened hash-bound existing B125 and V121 routed
checkpoints using the same tool image. They made no implementation or timing
constraint changes and are not fresh physical trials or qualification repeats.

| Selected source family → packet RAM enable | B125 worst slack / data | V121 worst slack / data |
| --- | ---: | ---: |
| Issued counter | −1.517 ns / 8.990 ns | **+0.303 ns / 7.170 ns** |
| Offset register | −1.105 ns / 8.578 ns | No offset registers or returned paths |
| Prepared request address | Not present | **+0.581 ns / 6.892 ns** |

The issued-family path falls from 12 to eight logic levels, gaining 1.820 ns.
Its worst launch bit and physical RAM bank differ, so this compares the worst
of each selected family rather than pretending it is the same placed wire.
The prepared-address family's worst path is also its worst returned all-endpoint
path. Queries return at most 50 paths/family; empty selections are recorded as
gaps and never silently broadened into unrelated paths.

Both the independent EDIF inventory and read-only register query confirm:

| Queue registers | B125 | V121 |
| --- | ---: | ---: |
| Offset FFs | 32 | 0 |
| Prepared-address FFs | 0 | 32 |
| Issued FFs | 32 | 32 |
| Global routed CARRY4 | 4,198 | 4,198 |

This is address arithmetic/ownership relocation. Source-level addition of 32
payload bits does not imply a net increase of 32 mapped FFs or global carry
removal. No inference is made from a missing name alone.

- [Candidate query receipt](../../experiments/python-gamebub-v121/request-inspection/candidate-20261110T001226933929Z/receipt.json)
- [Candidate targeted paths](../../experiments/python-gamebub-v121/request-inspection/candidate-20261110T001226933929Z/targeted-paths.tsv)
- [Baseline query receipt](../../experiments/python-gamebub-v121/request-inspection/baseline-b125-20261109T233158499545Z/receipt.json)
- [Baseline wrapper revalidation](../../experiments/python-gamebub-v121/request-inspection/baseline-b125-20261109T233158499545Z/wrapper-revalidation.json)

The original baseline-query wrapper incorrectly looked for the completion marker
in stdout; the unchanged Tcl correctly wrote `status.txt`. Vivado exited 0 and
the checkpoint remained unchanged. The original FAIL receipt is preserved;
the separate revalidation checks the retained status file and every original
artifact hash. No tool or physical trial was rerun for that correction. The
candidate query used the corrected wrapper and completed normally.

## Remaining critical families

The global worst moves to admission `cursor_reg[1]/C` →
`state_reg[0]_rep/D`. Data delay is 9.232 ns: 3.502 ns logic and 5.730 ns route;
14 logic levels include eight CARRY4s. Full32 cursor arithmetic is still feeding
state decoding, and the path includes the word-accumulator control cone.

Actual source inspection finds cursor/chunk checks around `CHUNK_NUMBER`,
`CHUNK_BLOCKS` and `CHUNK_LENGTH`, including the full-width expression
`{32'd0,cursor}+4+{32'd0,word_value}>{32'd0,residual_end}`. These are concrete
candidate preparation boundaries, not proof that every failing path belongs to
one source expression. Preserve both literal 32-bit wrap behavior and the wider
chunk-end comparison; narrowing or assuming a validated caller requires a
separate proved contract.

| Retained source family | B125 worst slack | V121 worst slack |
| --- | ---: | ---: |
| RAW mode | −1.462 ns | −1.174 ns |
| Context emitted | −1.386 ns | −0.825 ns |
| Kill | −1.357 ns | −0.705 ns |
| RAW coefficient | −0.862 ns | −0.656 ns |

These are bounded family samples and can overlap; they do not enumerate every
failing endpoint. Keep all families in the next regression and route review.

## Methodology and limits

Fresh explicit routed methodology JSON and RPT agree on **125 TIMING-16 large
setup warnings**, versus 355 in B125. The timing-summary's cached methodology
section says 105; the independent audit deliberately does not use that stale
embedded count. Warning count is not failing-endpoint count.

SYNTH-6 remains 28, TIMING-18 remains 1000 and ULMTCS-1 remains 1. These are retained
warnings, not new waivers or claimed resolutions. The OOC check_timing report
separately records 1,101 missing input delays and 12,887 missing output delays.
Internal clock coverage and routing pass, but overall setup fails. No negative
source is promoted and no unchanged-source negative fresh repeat is launched.

The existing row-cycle schedule is unchanged; this repair does not establish
latency reduction, production endpoint integration, physical 30 fps or hardware
validated decode below 10 ms. See the [next-step plan](README.md#next-bounded-experiment).
