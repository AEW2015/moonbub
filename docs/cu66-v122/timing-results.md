# V122 routed timing results: local gain, global regression

**The 125 MHz candidate fails and is not promoted.** A fresh RTL synthesis,
placement and route completed using the unchanged V120 core recipe, Vivado
2026.1/build6511674, `xc7a100tcsg324-1` and an 8 ns source clock loaded before
synthesis. No clock relaxation, timing exception or directive sweep was used.

The [terminal receipt](../../experiments/python-gamebub-v122/native/20261110T011206751721Z/receipt.json)
binds source, recipe, reports, checkpoints and command. The
[independent audit](../../experiments/python-gamebub-v122/audit/native-independent.json)
passes **722 integrity checks** while independently reporting timing FAIL.
Successful tool execution and evidence integrity do not qualify the clock.

## Complete component

| Routed metric | V121 at 125 MHz | V122 at 125 MHz |
| --- | ---: | ---: |
| Worst setup slack | −1.347 ns | **−1.949 ns** |
| Total negative slack | −3,248.192 ns | **−4,597.575 ns** |
| Failing setup endpoints | 9,407 | **11,866** |
| Hold slack / failures | +0.069 ns / 0 | +0.028 ns / 0 |
| Pulse slack / failures | +2.750 ns / 0 | +2.750 ns / 0 |
| Unconstrained internal endpoints | 0 | 0 |
| Routing errors | 0 | 0 |

Global WNS worsens by 0.602 ns; absolute TNS increases by 1,349.383 ns and
2,459 additional endpoints fail setup. All 74,013 routable nets are routed.
The worst path is unchanged ingress RAW logic into scratch validation/state:
`raw_mode_reg/C` → `scratch/state_reg[0]/D`, with 9.896 ns data delay
(3.361 ns logic, 6.535 ns route), 18 levels including three CARRY4s and twelve
LUT6s. The RAW RTL is unchanged; the new source composition changes physical
implementation. This run does not demonstrate a favorable global trade.

Other fresh reported family worsts remain negative: RAW coefficient −1.441 ns,
context-emitted −1.357 ns and kill −1.112 ns. External OOC ports still have
1,101 missing input delays and 12,887 missing output delays. Internal coverage
does not qualify those ports or a complete board clock/CDC design.

## Targeted read-only checkpoint comparison

Separate source-bound queries use the existing routed checkpoints without
altering them. Both receipts confirm unchanged checkpoint hashes:
[V121 baseline](../../experiments/python-gamebub-v122/request-inspection/baseline-v121-20261110T005154876282Z/receipt.json)
and [V122 candidate](../../experiments/python-gamebub-v122/request-inspection/candidate-20261110T013703104890Z/receipt.json).
Each row is the worst returned path for that explicit family, not necessarily
the same physical start/end pair in both designs.

| Family | V121 slack | V122 slack |
| --- | ---: | ---: |
| Admission cursor → state | −1.347 ns | **−0.250 ns** |
| Admission cursor → full64 cursor base | Absent | +4.545 ns |
| Cursor base → partial word sum | Absent | +5.110 ns |
| Partial word sum → length total | Absent | +4.640 ns |
| Length total → invalid-length predicate | Absent | +3.560 ns |
| Wrapped number sum → outside predicate | Absent | +3.817 ns |
| Invalid-length predicate → state | Absent | +3.608 ns |
| Number-outside predicate → state | Absent | +2.814 ns |
| Unchanged refill issued → RAM enable | +0.303 ns | +0.234 ns |
| Unchanged refill prepared address → RAM enable | +0.581 ns | +0.284 ns |

The cursor/state family improves **1.097 ns** but remains negative. Its new
worst data path is 8.104 ns and eleven levels. Every new bounds-source
all-endpoint family queried has positive slack; the smallest is +1.250 ns from
the invalid-length predicate to plane-length CE. This is a local measured gain.

The unchanged queue's RAM-enable paths remain positive, but its prepared-address
**all-endpoint** query now finds −0.318 ns to `max_owned_reg[0]/D` (8.265 ns,
eleven levels), versus V121's +0.581 ns all-endpoint worst. Do not describe the
whole queue as closed based only on the RAM-enable subset. Explicit empty and
optimized selections remain in the query gap reports.

## Mapping and methodology

| Routed resource | V121 | V122 |
| --- | ---: | ---: |
| Total LUTs | 33,636 | 33,686 |
| FFs | 43,083 | 43,134 |
| RAMB36 / RAMB18 | 32 / 12 | 32 / 12 |
| DSP blocks | 42 | 42 |
| CARRY4 | 4,198 | 4,214 |

Matching synthesis CARRY4 counts are 4,201/4,217. This moves arithmetic across
existing edges and adds preparation; it does not reduce global carry usage.
The 226 declared new payload bits map to **135 FFs**: cursor base 32, partial
sum 34, final sum 35, number sum 32 and two scalar predicates. The read-only
inventory and independent EDIF check agree. Missing named upper/lower bits and
constant trimming are mapping observations, not an arithmetic proof; the
full-width functional checks supply separate evidence. The unchanged queue
retains 32 prepared-address FFs and zero old offset FFs.

The fresh routed methodology report has SYNTH-6=28, TIMING-16=800,
TIMING-18=1,000 reported entries and ULMTCS-1=1. TIMING-16 (large setup
violation) rises from V121's 125 entries. The timing-summary's cached count 110
is not the fresh routed methodology result. ULMTCS-1 reports 1,241 control sets
against the tool's 7.5% guideline; RAM output-register warnings and missing OOC
delays remain explicit. No warning was waived and no exception was added.

The run took 1,482.263 seconds with two threads and eight GiB RAM/combined
RAM-plus-swap caps; no resource/watchdog stop occurred. There is no unchanged
negative reroute, positive qualification repeat, 125 MHz handoff or board
bitstream. Keep qualified 100 MHz Source B for the remote board team.

The [next experiments](next-timing.md) target measured RAW/scratch ordering
validation and the remaining admission guard separately. Parent cycles remain
unchanged; clock closure alone would still leave the modeled stalled latency
above 10 ms and would not prove sustained hardware 30 fps.
