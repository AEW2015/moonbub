# V107 fixed-tap Rice reservoir

The selected candidate changes the private reservoir to MSB alignment. Public request/input/output timing, counters, errors, priorities and all port widths are unchanged. The starting source is the V106 sixth candidate's suffix24 module, not a replacement behavioral model.

The measured completed V106 route had parser `available_reg[0]` → `out_value_reg[5]/D`, 19 logic levels, 14.025 ns data delay (3.713 ns logic, 10.312 ns routing). Its fixed 10 ns constraint missed setup by 4.034 ns. The later PREFIX route still had available-to-output as its critical cone; the sixth source has no completed placement/routing result. See the frozen [remaining timing plan](../cu66-v106/remaining-timing-plan.md).

## Concrete architecture change

Previously the low `available` reservoir bits held the bit queue. Fifteen PREFIX taps each selected `reservoir[available-1-i]`. SUFFIX extraction right-shifted by `available-suffix_take_bits`. V107 stores the same queue in the high `available` bits instead:

- PREFIX reads fixed taps `reservoir[63-i]`, retaining all original availability guards, remaining-bit window and balanced first-one rank tree.
- SUFFIX extracts the high bounded suffix width; `available` no longer controls its data selector.
- Consumption shifts the reservoir left by the accepted bit count. Input append ORs the padded source word at offset `32-available`.

The input selector still depends on availability. `available` also retains all original readiness, step-enable and error guards. This is removal of the measured data-selection dependency, not a claim that the whole module's timing closes. No false paths, clock relaxation, public cycles or input assumptions are added.

For a queue of length `a`, the representation invariant is `new_reservoir = old_reservoir << (64-a)` with zero unused bits. At `a=0` both queues are empty. Input acceptance already requires `a<=32`; valid `in_bits` are at most 32 and the old word-validation rule requires zero low padding. Thus append places exactly the next bits into the zero tail without overlap. Left-shift consumption produces the same shortened queue. Reset/start establish the invariant, malformed inputs do not modify the reservoir, and output/failed/idle states preserve it. An enabled assertion checks zero padding on every active edge.

The source hashes and reverse-offset exact reconstruction are retained in [edit-recipe.json](../../fpga/experiments/cu66-v107-rice/edit-recipe.json). The baseline SHA-256 is `d0e233eacb849476bac7c18157a6f29bd76228d378e07b2d7613db8a356cf919`; candidate SHA-256 is `f39c3f90d0242097ea3cd2693e6f4d99e58e33a0b49c644c720497f50e6777dc`.

## Verification contract

The explicit backend is historical Verilator in `gamebub-cu66-v69-build`, behavioral mode, with strict `-Wall`, assertions, C++ `-Wall -Wextra -Werror`, bounded compile/runtime and a finite edge watchdog. The Vivado simulation MCP transport is unavailable; this is an explicitly selected backend, not an XSim pass.

The harness instantiates the complete unchanged V106 suffix24 production module beside the complete V107 production module. All 13 public outputs, including all six counters, must match on every pre/post edge. Every common private controller/arithmetic state must match. The candidate reservoir is normalized back to a low-bit queue and checked against an independent loaded/consumed/queue/counter oracle; its representation is deliberately not compared as an unnormalized bit vector. No checker or assertion is disabled for the candidate.

The additional parameter suite creates expected transcripts directly from the Rice bit grammar for every `req_k`/`req_escape` pair 0..31, in parallel/serial and 16/32-bit modes. Every legal pair checks ordinary zero and fifteen-zero escape encodings; every illegal pair checks BAD_PARAM. This is 6,096 tests per seed. The frozen historical generic suite adds arbitrary nonzero values, request/input/output stalls, word-size boundaries, truncation, invalid padding/last/width, failed-stream persistence, reset/start cancellation and held-output behavior.

Prepared-state supplements exercise every reservoir availability 0..64, both PREFIX/SUFFIX states, mode and reset/start combinations; all four states at full32 size boundaries; every six-bit `in_bits` encoding; both last flags and four source data patterns. Full32 cached arithmetic is checked at every edge, with 65,536 seeded arbitrary inactive modulo32 states per seed. Prepared states are additional semantic stress, not a protocol reachability claim. The actual historical and parameter suites use only public interfaces.

Independent [bounded storage identities](../../experiments/python-gamebub-v107/rice/model-results.json) pass 94,073 extraction/consume, 65,696 prefix-rank and 46,912 append checks. The domains include all availability lengths 0..64, suffix takes 0..24, windows 0..15, accepted input lengths 1..32 and each single-bit basis plus zero/all-one/seeded random patterns. This is bounded arithmetic/source evidence; the actual RTL verdict and physical timing are separate gates.

## Actual RTL result

**PASS**, Verilator 5.020, seeds 107401 and 107402. The first strict compile and both bounded runs pass with enabled assertions and no functional warning suppression. The only Verilator filename-warning option accommodates generated old/new module names. Assertions include the existing cache/count/bound checks, selected suffix identity and new aligned-padding invariant. The compile uses `--public-flat-rw` to support prepared-state and private oracle checks; parent production compilation without these probe exports is a separate required gate.

| Campaign | Seed 107401 | Seed 107402 |
| --- | ---: | ---: |
| All-parameter independent transcript cases | 6,096 | 6,096 |
| Parameter-suite edges | 81,606 | 81,441 |
| Prepared-state edges | 189,105 | 189,105 |
| Historical valid/error/backpressure edges | 8,648,286 | 8,650,127 |
| Historical cases × configurations | 1,520 × 8 | 1,520 × 8 |
| Requests per historical configuration | 173,061 | 173,061 |
| Historical directed checks | 104 | 104 |

The campaign checks **17,839,670 actual RTL clock edges**, with no public latency change or cycle tolerance. Testbenches have a finite global edge watchdog and directed operation watchdogs; Docker commands also have bounded timeouts.

The [selection pointer](../../experiments/python-gamebub-v107/rice/probe-results.json) identifies the immutable [receipt](../../experiments/python-gamebub-v107/rice/attempts/20261108T033827058531Z/receipt.json), SHA-256 `629e98b209da0977b3ada807eafa274751efef853e48fbdf5d5509e38ef44b8d`. Its adjacent source snapshots, generated probe, all 27 port declarations, historical source/vector inputs, compile/tool/binary logs, per-seed complete case transcripts and compressed queue-oracle checkpoints are retained. The receipt hashes all 20 artifacts and original source inputs. No attempts were rejected or overwritten.

The independent [artifact audit](../../experiments/python-gamebub-v107/rice/audit.json) verifies all retained hashes, all source input hashes, exact reverse-offset recipe reconstruction, 13 public output comparisons, command exit codes, both terminal verdicts and campaign counts. Reproduce with `python3 scripts/cu66-v107/rice/model.py`, `python3 scripts/cu66-v107/rice/recipe.py`, the serialized `python3 scripts/cu66-v107/rice.py`, and `python3 scripts/cu66-v107/rice/audit.py`.

Parent fresh/canonical integration, matched full-top implementation at 10 ns, setup/hold/pulse/legality, CDC, hardware throughput and complete decode latency remain open. Behavioral simulation does not establish timing closure.
