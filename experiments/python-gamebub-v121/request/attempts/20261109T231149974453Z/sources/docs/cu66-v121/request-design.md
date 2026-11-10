# V121 existing-edge owned request cursor

This candidate substitutes only `byte_refill_queue_v91i2b.sv` in the frozen
V120 Source B composition. Source B itself remains unchanged. It targets the
B125 `issued -> offset + issued -> replay_addr < size_bytes -> RAM ENBWREN`
path recorded in `docs/cu66-v120/B-native-initial-mapping.md`.

The full32 `prepared_req_addr` captures `start_offset` on the existing start
edge and increments by `32'd1` only when `req_valid && req_ready` accepts a
read. Responses, output pops and stalls do not advance it. The original
reset/cancel/clear/start priority, counters, credit predicates, first response
fault, pending owner, last-byte binding and all inherited assertions remain.
The original entire assertion block is byte-identical. A separate invariant
checks `prepared_req_addr == offset + issued` with literal full32 arithmetic.

The public contract is exact-cycle equality, including unqualified `req_addr`
after completion/fault and during reset/cancel/empty/replacement starts. There
is no new latency or ownership stage. Arithmetic still wraps modulo 2^32;
the inherited assertion still forbids an *accepted* request whose wrapped
address is below its offset. A legal final read at `0xffffffff` leaves an
unqualified next address of zero. Nothing narrows the unsigned admission bound
or changes the independent `issued < length` eligibility check.

The timing hypothesis is limited: the physical request address and admission
bound now begin at a register, removing the serial offset-plus-issued adder
from the measured cone. Admission's bounds and ready/enable logic remain.
The full component can still fail timing through credit, cancellation, RAW,
context or another family. Native route and a separate passing fresh repeat
are required before qualifying any clock.

`scripts/cu66-v121/request/prepare.py` creates a reversible source recipe,
module-name-only pair adapters and an extension of the complete V91i2b queue
regression. Every inherited `need(...)` expression remains. The pair compares
every public output before and after every edge. The independent external
memory/byte scoreboard checks exact accepted addresses, epoch, data, order,
last and credits; added cases cover unsigned high addresses, final-address
wrap, length extrema with stalled offers, random legal spans and physical
responses on cancel/reset/clear/replacement edges. Separate original and
candidate builds must both fail the original span assertion on the same
accepted overflowing request. Finite simulation does not prove all states.

`qualify.py` defaults to recipe-only validation. Its `--run --root-grant
ROOT_V121_REQUEST` path uses the pinned Verilator image, one compile process,
two CPU/eight GiB cap, no additional swap, assertions and fatal warnings.
Fresh source snapshots, raw commands, resource samples, successful runs and
the expected-failure logs are retained under
`experiments/python-gamebub-v121/request/attempts/`; the selector is
`experiments/python-gamebub-v121/request/results.json`. Full admission/decoder,
transport, physical-debt peer and guarded parent suites are separate gates
coordinated by the parent agent. This document makes no timing or hardware
qualification claim.
