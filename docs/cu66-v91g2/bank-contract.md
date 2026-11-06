# V91g2 two tile bank ownership contract

This contract defines an abstract event model for the two tile banks in the
V91g2 decoder. The executable reference is
`experiments/python-gamebub-v91g2/tile-bank-model.py`; its generated evidence is
`experiments/python-gamebub-v91g2/tile-bank-results.json`. The model explores
ownership events. It is not RTL, a cycle-accurate model, a formal proof, or
performance evidence.

## Bank owners and emission

Each of the two banks has one state: `EMPTY`, `PREPARING`, or `READY`. A
preparing bank has one immutable epoch and block owner plus a payload identity.
`READY` means preparation is complete; the same owner remains in the bank while
the consumer emits it. A block is not released when emission starts. It remains
owned through acceptance of its final scalar.

The producer prepares blocks in ascending block order and assigns alternating
banks. It may prepare the next block while the current ready block is being
emitted, but only in the other empty bank. At most two block owners exist,
including a bank still being prepared. A ready or emitting bank cannot be
overwritten. This keeps the emitted payload immutable while the producer
changes the other bank, including while output is held under backpressure.

Emission uses a separate block cursor and scalar index. The model uses three
abstract scalar indices per block so its state space stays small; the RTL block
has 64 scalar indices, `0..63`. In both descriptions, output acceptance
advances one scalar at a time and advances the block only after the last scalar
is accepted. The reduced model checks ordering and ownership invariants; it does
not claim cycle-by-cycle coverage of all 64 RTL transfers.

When preparation of the next block completes on the same abstract edge as the
current block's final output acceptance, that event releases the old bank and
publishes the other bank as ready. Reuse of the released bank is a later event;
the model does not permit a new preparation to begin in that same-edge
handoff. If preparation does not complete on that edge, the ready bank is
published later and emission waits for it.

## External read, cancellation, and error

The model has at most one accepted external read owner. This physical owner
stores its bank, block, epoch, and request identity separately from local bank
validity. A matching successful ACK retires the read owner and permits that
block's preparation work to continue. The model does not simulate cache or
memory contents.

Abort, reset, or a wrong-epoch response invalidates local bank state and
advances or invalidates the logical transaction, but cannot erase an accepted
external request. The physical owner remains immutable and reserves its bank
until a matching ACK drains it. A wrong-epoch response fails closed and does
not retire that owner. A matching error ACK retires the physical owner, clears
local bank state, and fails the transaction; it cannot fill data or advance
output. Replacement starts only after explicit cancellation and physical
drain. Unaccepted request offers and ready-low request stability are outside
this model's event alphabet.

Final completion requires that the final block's final scalar has been
accepted, both local banks are empty, and no accepted external read remains.
Preparation completion alone never counts as consumer completion.

## Bounded checks and limits

The run explores a finite event graph with breadth-first search through depth
36, directed races, and a deterministic seeded 5,000-event walk (seed 910438).
The JSON records the model source SHA-256, bounds, visited states, checked
transitions, event coverage and shortest traces, directed checks, seeded event
counts, requested steps, actual events, and terminal restarts. The seeded walk
may end before a terminal state; `actual_events` counts executed events and
`terminal_restarts` is reported separately. `accepted_outputs` is cumulative
across logical epochs; the per-epoch count resets on cancellation/restart.

These finite checks cover two bank owners, at most one preparing bank, three
blocks, three abstract scalar indices per block, and two preparation steps per
block. They do not establish
RTL equivalence, unbounded safety, actual bus timing, memory/cache fit, or
throughput. RTL review and simulation must separately check bank masks and
metadata, accepted-read retention through DRAIN, output stability, error
priority, and final drain behavior. The 30 fps target and sub-10 ms decode
latency remain open hardware validation goals.
