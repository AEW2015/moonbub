# V104 baseline audit

This is a read-only provenance and primitive inventory for V104. The task
baseline is V103 commit `1d0a702a758787522723ac52ff44a1bf220c39d1`. The V103
selection artifact retains the V102 combined memory/predicate sources as its
measured starting point; its own source-audit ancestry pin is
`6d2ca3ae9abe207215d6130cfb0087fd07928917`.

## Provenance and profile

`experiments/python-gamebub-v103/selection.json` selects `baseline`, naming the
V102 native receipt and two source overrides. Both override files match their
selection SHA-256 values and the corresponding blobs at the selection's Git
baseline. The selected receipt SHA-256 also matches its recorded value and
reports `COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN` for `cs88_pipeline_v91k` on
`xc7a100tcsg324-1` with a 10 ns comparison clock.

The retained source functional audit has 19/19 checks passing. The native
evidence audit has 5/5 checks passing, with four variants measured and no
pending variants. These PASS statuses validate the retained evidence and
provenance; they do not close signoff obligations. The selected workload remains
720×480 with a 49,152-byte packet cap, as specified in the V102/V103 handoffs.

## Routed DSP48E1 inventory

The selected routed baseline's `route-dsp-registers.tsv` contains 28 DSP48E1
instances, matching the routed utilization report. Register configuration is
reported as AREG/BREG/MREG/PREG:

| Hierarchy | DSP48E1s | Configurations |
| --- | ---: | --- |
| `coefficients/admission` | 1 | 1 × `0/0/0/0` |
| `coefficients/child` | 3 | 3 × `1/0/0/0` |
| `transform/dequant` | 8 | 8 × `0/0/0/0` |
| `transform/inverse` | 16 | 15 × `0/0/1/0`; 1 × `0/0/0/1` |

Thus the eight dequant multipliers have no absorbed DSP input, multiplier, or
output registers. In the 16-DSP IDCT hierarchy, 15 instances use MREG and one
uses PREG; none use AREG or BREG. The three child hierarchy DSPs use AREG. The
admission DSP is unregistered. These are implementation facts, not evidence of
shorter paths or improved clock speed.

## Routed resource footprint

| Hierarchy | Total LUTs | Logic LUTs | LUTRAMs | FFs | RAMB36 | DSPs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Top | 48,522 | 45,804 | 2,718 | 34,795 | 32 | 28 |
| Coefficients | 31,378 | 29,814 | 1,564 | 22,869 | 32 | 4 |
| Admission | 18,138 | 16,614 | 1,524 | 9,161 | 16 | 1 |
| Child pipeline | 12,724 | 12,692 | 32 | 12,684 | 16 | 3 |
| Reconstruction | 4,640 | 4,640 | 0 | 3,754 | 0 | 0 |
| Transform | 12,156 | 11,002 | 1,154 | 8,170 | 0 | 24 |
| Dequant | 3,471 | 3,471 | 0 | 2,351 | 0 | 8 |
| IDCT inverse | 6,200 | 6,200 | 0 | 5,132 | 0 | 16 |

V104's stated focus is measured control closure and DSP arithmetic pipeline
mapping. The inventory supports testing registered dequantization and control
precomputation as distinct candidates. Any timing conclusion must come from
comparable path and routed clock evidence; neither DSP presence nor source-level
register declarations establish speed. Profile, schedule and validation remain
frozen. The machine-readable hashes and full hierarchy rows are in
[`baseline-audit.json`](../../experiments/python-gamebub-v104/baseline-audit.json).
