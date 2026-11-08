# IV113.1: owned coefficient commit and finite inverse results

The candidate is `fpga/experiments/cu66-v113-inverse/cu66_inverse_stream_v91j.sv`.
It retains the exact `cu66_inverse_stream_v91j` port interface. The frozen
V110 source and its exact checker are unchanged. This is a latency-changing
inverse-local experiment; it supplies no PCTL1 supervisor, admission credit,
physical memory ledger, warm-reset service protocol, full-parent timing, or
hardware result.

The measured V112 path was `fill_bank` to a coefficient payload CE through
bank selection, ready and input validation. Here acceptance, validation and
commit are separate edges. A coefficient accepted at E captures its entire
input tuple, both precomputed static error flags, bank, expected index,
expected metadata, token reservation and wrap predicate. E+1 validates those
registered coherent operands. A valid tuple writes its fixed bank/word at E+2;
the bank becomes READY only when word 63 actually commits. The 2048 payload
bits have no reset and their CEs use local registered commit state, bank and
word, plus the local running/reset/start/cancel/fault guard. Live input-ready,
metadata and error-sideband pins do not qualify those payload CEs.

A commit can accept the next complete tuple on the same edge. The acceptance
frontier forwards the committing slot's registered index/bank/token/metadata,
including first-word metadata and word-63 bank rollover. All other acceptance
edges use the committed bank frontier. The complete slot is replaced, rather
than modifying some held fields. Capacity is one tuple and maximum coefficient
intake is one beat every two cycles. There is no claim of one coefficient per
cycle. An earlier, immutable II=3 proof is retained in the attempts directory;
only the II=2 source is selected.

`input_done` is a sticky EOF intent and suppresses new acceptance. The caller
must retire its held final coefficient before asserting this interface's EOF,
as in the existing coefficient handoff. EOF waits for the accepted slot to
validate and commit before deciding partial-tile error 4. Success additionally
waits for both coefficient banks, arithmetic ownership, both result slots and
the final residual handshake to drain. A held sample 63 keeps its complete
identity and value and prevents done. Acceptance and commit are distinct:
accepted malformed/canceled tuples do not count as committed writes.

Two physical result slots each contain 64 reset-free 24-bit registers (3072
payload bits total), metadata and FREE/RESERVED/READY state. The controller
reserves a free slot before arithmetic launch and snapshots the complete
identity. Verified IDCT completion copies all 64 words in parallel in one
edge using 64 real register writes. That edge acknowledges the IDCT producer,
marks the reserved slot READY and frees the math coefficient bank. Result
emission uses a combinational 64-word sample read plus two-slot selection and holds the result slot until
sample 63 transfers. There is no assumed RAM or uncounted copy port. The next
math tile can run while an older result is offered or stalled. Two occupied
result slots stop new math reservations; coefficient banks can then fill and
backpressure ingress. A final pop permits reallocation on the following edge;
there is deliberately no same-edge free-slot bypass for result allocation.

An owner is one accepted standalone start interval, refined by the existing
coefficient token and complete epoch/child/plane/scale/block/tile/qcell tuple.
The enclosing PCTL1 supervisor's unique generation/admission identity is not
implemented by this unchanged-port local module. All local producers flush
synchronously on start/reset/cancel, preventing an old local computation from
surviving into the next interval even when supplied epochs repeat. This local
synchronous property does not establish uniqueness for external service
responses or replace PCTL1's required transaction/session protocol.

External reset/start/cancel masks public transfers before the edge and clears
private eligibility at that edge. An input fault appears after validation E+1
and masks public transfers at E+2. Partial EOF failure appears after its first
empty-slot check. Dequant/IDCT faults retain their original codes and are
reported at their owned response observation edge. Same-edge priority remains
input-index 1, metadata 2, domain 3, token-wrap 7 (or deferred partial EOF 4),
then dequant 5 or IDCT 6 according to the active math phase. A sticky fault
retains the first failure until reset/start/cancel. `fault_pending_o` retains
the existing same-edge unacknowledged-fault semantics. An already validated
coefficient commit or result copy can update private payload on an edge where
an unrelated arithmetic/input fault also revokes the owner; that payload has
no eligible owner and cannot launch or emit afterward. Reset/cancel themselves
suppress payload writes.

All existing public counters retain accepted-event meaning: `count_inputs`
counts ingress transfers (including subsequently rejected ones), `count_tiles`
counts committed full tiles, launch/dequant counters count producer transfers,
and output/completed-tile counters count residual handshakes. `count_inputs`
can exceed `count_tiles*64`. Cancellation counts owned coefficient banks, as
before; it is not a result-cancellation count. Internal public-flat-rw fields
add `count_commits`, `count_result_full_stalls`, `count_math_emit_overlap`,
`result_occupancy`, `max_result_occupancy`, `accept_pending` and `flush_ack`.
`flush_ack` certifies only empty local private resources. Diagnostic
`math_state` now uses IDLE=0, DQ_SEND=1, DQ_WAIT=2, IDCT_WAIT=3; emission is
independent and old M_EMIT=4 is removed. `dbg_*` coefficient/math identity and
payload are meaningful only with `dbg_launch`/`dbg_dequant`; output tags are
meaningful with `out_valid`. Inactive private/debug payload is unspecified.

The independent C++ oracle starts from accepted external tuples and immutable
`experiments/python-gamebub-v91j/vectors/boundary.tsv` math goldens. It checks
complete launch coefficients, dequant values, ordered residual values and tags,
held output tuples, E+2 write accounting, finite result occupancy and EOF.
The expected queue is retained independently of candidate busy/done; only an
explicit externally driven reset/cancel or independently expected error permits
retirement. It uses deterministic seeds 113101 and 113102. Both pass all 48
boundary rows and 25 directed cases, including simultaneous acceptance/commit,
full results plus full coefficient banks, next math under held output, held
last sample, deferred partial EOF, input metadata mutation, malformed input
priority, cancellation/reset at slot/math/result phases, and repeated supplied
IDs on retry. The delayed-output quarantine lasts 160 edges after each kill.
It does not claim arbitrary-state proof, all possible error injection races,
token/generation wrap execution, or physical transaction coverage.

Reproduce the source recipe and tests with:

```sh
python3 scripts/cu66-v113/inverse/prepare.py
python3 scripts/cu66-v113/inverse/qualify.py --run
python3 scripts/cu66-v113/inverse/benchmark.py --run
```

Both RTL workflows explicitly select Verilator with assertions, fatal `-Wall`
warnings, one compiler worker, 2 CPUs, 8 GiB memory with memory-swap also 8 GiB,
no network and finite compile/run watchdogs. They use the retained tools image.
The recipe verifies both forward and reverse edits byte-for-byte and records
source hashes. The selected receipt pins source snapshots, commands, logs and
independent event metrics. Baseline exact-cycle checkers are never altered or
shifted. Resource fit and timing require actual implementation of the complete
candidate composition; the new result-register CEs and output mux must be
counted in that measurement.

The selected independent proof is
`experiments/python-gamebub-v113/inverse/attempts/20261108T205423994425Z/receipt.json`.
Each seed accepts 5,019 tuples, commits 5,003, and accepts 3,904 residuals;
16 accepted tuples are discarded by expected fault/cancel/reset. Peak result
occupancy is two. Math and offered output coexist for 532/555 cycles; both
result slots are occupied for 1,916/1,948 cycles. Maximum tested EOF response
is 239/240 cycles under the bench's randomized bounded consumer stalls. These
are campaign observations, not universal latency bounds for an unbounded stall.

The independent same-stimulus throughput comparison is
`experiments/python-gamebub-v113/inverse/benchmarks/20261108T205614490604Z/receipt.json`.
Each row streams 16 identical golden tiles with no input source gaps. Profile 0
always accepts residuals; profile 1 accepts when `cycle % 257 < 83`.

| Golden tile / output profile | Frozen cycles | IV113.1 cycles | Difference |
| --- | ---: | ---: | ---: |
| Zero / always ready | 1,153 | 2,118 | +965 |
| Zero / bounded stalls | 3,412 | 3,368 | −44 |
| AC positive limit / always ready | 3,329 | 2,434 | −895 |
| AC positive limit / bounded stalls | 4,175 | 3,411 | −764 |

The candidate's minimum accepted-coefficient spacing is exactly two edges in
all four rows, versus one for the frozen source. The zero/always-ready row has
all 1,023 inter-input gaps equal to two, establishing its sustained half-rate
intake directly from accepted events. The candidate coefficient span is 2,047
cycles for 1,024 coefficients; its first residual appears at offset 133 versus
68 for the frozen source. AC/always-ready coefficient span is 2,216 cycles,
and first residual offset is 269 versus 204. This is a measured arithmetic
workload improvement and an intake-limited fast-path regression, not a uniform
speedup. The raw benchmark's `math_and_offer_cycles` counter means non-IDLE
math state plus offered output; the frozen source includes emission in that
state, so its old and new values must not be compared as equal overlap metrics.
Only the candidate's independent math phases establish actual overlap.

The candidate is frozen at SHA-256
`c727e7a71c8da5ace352df1e9483aa87c83a5d6a95d5b3127d9578653d0b9403`.
No synthesis, mapped resource, place/route, achieved-clock or calibrated service
result is supplied by this inverse-only work. Full composition must evaluate
whether timing and the whole-workload schedule justify the fast-path tradeoff.
