# V127 focused RTL results

**PASS across all six selected seeds.** Both strict models were rebuilt after
a preserved verification-adapter compile failure. Production RTL stayed unchanged.
This report is behavioral functional evidence, not a routed clock or board pass.

## Frozen source and selected evidence

Exactly three aliases differ from V126: scratch, child pipeline and producer.
The selected [receipt](../../experiments/python-gamebub-v127/owner/attempts/20261110T181016571888Z/receipt.json) has SHA-256
`5f8c123eb807d92ba97d1bdb7cdec3df30363d6a76f1fd46919401279ad9b1d6`, 61 source pins and 85 artifact pins.
All nine commands exit zero; host execution lasts 624.035 s. That duration is
compiler/simulator runtime and does not measure FPGA decode latency.

The independent [focused audit](../../experiments/python-gamebub-v127/audit/full-independent-focused.json) has SHA-256
`0607cb3c4aa4f65ba4c2e7aacf1b2e828092c91e9b428b4b24deefbf42b1596e`. It verifies actual
scalar, generic and caller records, source/artifact closure, all original
oracles, the complete baseline source map and the three new candidate bindings.
The selected revision-2 freeze is
`9f71d27f33789381c2962e0b20f3bc21075b16b873a04e553500bce852529606`.

The backend remains standalone Verilator 5.020 in its pinned image, with
`--assert -Wall`, C++17/O2/Wall/Wextra/Werror, compile job1, finite watchdogs
and two CPUs / 8 GiB RAM with an 8 GiB combined RAM-and-swap limit. The old two KEEP bits
remain; no production register, reset, public cycle or synthesis attribute is added.
The private comparison-expression edit count is one; its all-cycle value
contract changes by zero. All original assertion/require bodies remain.

## Scope and counts

| Campaign | Seeds | New coverage per seed | Retained coverage |
| --- | --- | --- | --- |
| Extracted scalar | 127501 / 127502 | 90,112 cases = 24,576 boundary + 65,536 random; 90,112 clocks / 270,336 evaluations | Original 98,304 full13/all-plane successor cases, 1,190,177 clocks, 294,912 held edges, 1,120 cancellation contexts |
| Paired whole producer, generic | 127501 / 127502 | 425,984 wire cases; 1,152 clocked cases; 864 cancellations, 192 error67, 16 wraps | All five V126 records and old cache/owner/nonce/bank/successor oracles |
| Actual paired callers | 127601 / 127602 | Raw scalar and selected owner observed on real caller callbacks, without adding clocks | 11 vectors, 22 profiles, two configurations and at least 12 directed checks each |

Scalar and bank tags vary independently over full32 epoch/full16 block inputs,
all four raw/tile-overlap encodings and both emit selections. Readiness or
validity is never treated as proof of an owner. Scalar-only and bank-only
matches have positive coverage. Original source fragments, explicit identifier
binding and independent full-field selection are checked alongside actual new
comparison results. These finite two-state cases are not exhaustive formal
proof over all tag values.

The generic run retains the original **275,334** instrumented owner/campaign
clock ledger, including V126’s 534 contexts, 3,664 campaign clocks, 1,428
actual-writer primers and 2,236 nonprimer clocks. It then adds **2,308** clocks:
1,152 new case edges and 1,156 reset primers. Unclocked prepared wire cases
and observer evaluations are not new DUT clocks or natural packet chronology.
Repeated high-level evaluations are deduplicated by the generic clock observer.
Legacy cache-driver counters retain their own original measurement scope.

No new comparison result, ownership certificate or successor payload is forced.
New terminal fixtures keep the child’s bank/active lease internally coherent,
vary only the original parent key for foreign-owner cases, and preserve reset,
abort, first-error and terminal-release ordering. Physical request debt is not
erased to satisfy a test. The new baseline raw-view wires are checked against
the actual baseline scratch registers as well as against the new design.

Actual caller observer totals are measured separately:

| Seed | Observed clocks | Equality evaluations |
| --- | ---: | ---: |
| 127601 | 10,222,880 | 40,590,919 |
| 127602 | 10,222,146 | 40,587,973 |

Both caller runs retain exact old/new public, metadata, scale and dense tuple
comparisons. Every selected case passes, requests and acknowledgments balance,
and no case leaves pending drain. Observation counters are not throughput or
displayed-frame measurements.

## Preserved first failure and narrow repair

The [first official attempt](../../experiments/python-gamebub-v127/owner/attempts/20261110T180509258442Z/receipt.json)
compiled the scalar model but stopped before any simulation when strict lint
reported two `PINCONNECTEMPTY` warnings on baseline-only child outputs. Its
receipt remains `actual_RTL_run=false`; it is not a failed production RTL test.

The [fixture repair](../../experiments/python-gamebub-v127/owner/repair-history/20261110T180823389365Z-baseline-port-binding/repair.json)
preserves the old five input files, exact patch, failed snapshot and log. It
connects the two baseline outputs to private wires and consumes them in two
additional raw-view equality checks. The [plan correction](../../experiments/python-gamebub-v127/owner/repair-history/20261110T180828817132Z-plan-output-binding/repair.json)
changes only the description of those connections. All three production
hashes, C++ oracles, counts and compiler flags are unchanged. The original
tooling freeze remains intact beside revision2.

The independent [repair review](../../experiments/python-gamebub-v127/audit/focus-adapter-repair-review.json)
passes fourteen checks. The retained [diagnostic reference](../../experiments/python-gamebub-v127/orchestration/warning-reference.json)
distinguishes actual 5.020 behavior from current documentation defaults. The
fresh full build and all six successful runs above verify the repair; no
warning suppression, stale binary or skipped assertion supplies the PASS.

The frozen [design](owner-design.md) and [verification plan](verification-plan.md)
define the test contract. Complete decoder/transport, peer and byte/row-parent
regressions remain separate gates before fresh native implementation.
