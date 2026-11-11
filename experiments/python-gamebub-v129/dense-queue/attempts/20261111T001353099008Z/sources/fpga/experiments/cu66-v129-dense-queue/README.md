# V129 standalone dense-owner boundary prototype

This is a proposed **standalone unit**, not an integrated producer/scratch
change, FPGA result or hardware handoff. It exercises a two-slot non-fallthrough
boundary at which upstream readiness is a local occupancy/control decision. It
is intended to separate the producer's full owner comparison from the scratch
dense-ready return. Physical timing and any end-to-end latency benefit remain
unmeasured until integration, verification and routing.

Each slot captures the full 102-bit `{frame epoch, child epoch, block, index,
value}` tuple. Only control/valid registers reset; payload is unowned unless
occupancy is nonzero. Valid, wrong-owner offers are detected even while full or
the sink is stalled. They latch a fault on the next edge and invalidate queued
and provisional entries. `in_ready` is intentionally independent of the owner
comparison, so a bad offer may handshake and refresh an unowned payload on the
fault edge. A previously valid good head may be accepted on that same edge.
Integration must explicitly account for both events: it must never publish the
bad tuple, and it cannot erase an already accepted good output.

The acquisition block advances on accepted index 63 and wraps at 16 bits.
The producer must fence terminal block/plane transitions and prevent an
out-of-range next block; this unit has no block-count input. The downstream
`publication_context_ready` must only permit a queued head when its actual
block's MAP_REQ/MAP_WAIT metadata is installed. A context fence can pause a
held tuple; the parent must prevent metadata reuse and preserve ordered output.

At occupancy one a pop and push may occur together. A full queue does not
accept a replacement on the same pop edge, producing a recovery bubble.
`finish_ready` and `arm_ready` require externally supplied child quiescence and
empty physical memory debt. Those inputs are assumptions supplied by the real
child controller, not proof that a standalone FIFO tracks ACKs. Reset/kill
flushes logical tuple ownership; it must not discard an accepted memory write
or a required matching ACK in the surrounding design. A same-epoch retry is
safe only after the controller honors that drain fence and re-arms.

Before this can be selected for a timing run it needs a real producer/child
adapter, explicit error/cancel/accepted-transaction priority and latency-aware
end-to-end tests, completion/debt fences, equivalence to all frame and hash
oracles, and a fresh implementation. Throughput must be measured; the two
slots alone do not establish one coefficient per cycle or 30 fps.
