# V91f two-line write ownership contract

This contract describes the proposed V91f **overlap-enabled ownership events**,
not an RTL state machine or a cycle-accurate/performance model. The selected
overlap mode is latched at transaction start; when disabled, the existing V91e
writer path retains its prior behavior. The standalone Python reference exercises
small line IDs, payload tags and epochs. It does not establish synthesis,
physical storage fit, memory timing, or product throughput.

## Owners and request lifecycle

The prototype has two 16-byte payload owners:

1. The assembler owns the line currently being built. It may hold a partial or
   completed line. Completing a line assigns its next aligned address and
   immutable payload tag.
2. The single write slot owns the completed line offered to external memory.
   The slot can be locally offered (valid under backpressure) or accepted (one
   externally outstanding request). `offer_assembler` transfers ownership into
   the slot. There is no third 16-byte payload queue. The existing scalar
`pendingrecord` remains a separate coefficient handoff/control owner and is
outside the two-line payload highwater.

The external interface permits at most one accepted request. Request address,
epoch and all four 32-bit payload words stay fixed from the first offer through
acceptance and the matching physical ACK. Ready-low does not transfer ownership.
Only a matching physical ACK retires an accepted write slot. A matching error
ACK also ends that physical transaction but fails the logical transaction; it
does not count as a successful commit.

While the slot is occupied, the assembler can fill the second 16-byte line.
When both are full, enqueue stalls until slot ownership transfers or retires.
The oldest address is always offered first. A successful ACK may retire the old
slot and transfer the held assembler line into the now-free slot on the same
hardware edge. The reference models this as
one atomic `ack_match_ok_and_enqueue` ownership event. The next external request
cannot be accepted before that slot is offered and accepted. A matching error
ACK has priority over enqueue; it fails the transaction and clears both local
assembler and offered-slot ownership. The V91f RTL's enqueue, ACK and full-wait counters should reflect these event
definitions.

## Cancellation, replacement, seal, and read

Abort or warm reset clears partial assembly and local `write_slot_valid`. It
cannot revoke an accepted external write: the physical owner retains its payload,
address and request epoch until the real matching response arrives, including
during DRAIN. Thus local slot-valid may be clear while the accepted physical
owner remains immutable and blocks bank reuse. A replacement epoch must wait until this ownership is gone. A stale abort for a
prior epoch must not affect the current owner.

A response with the wrong epoch is an error and clears local assembler and
`write_slot_valid`, but it does not retire the actual pending physical owner.
The retained payload/address/epoch wait for a later matching response to drain
the external transaction.
A stale abort from a prior epoch is ignored; the model includes this as a
no-op event and a directed replacement-epoch check. An
accepted write's physical memory effect cannot be rolled back by logical abort;
the independent memory model must commit it on the delayed ACK, including when
its owner was cancelled meanwhile.

Data lines are written in increasing aligned address order. The input-side
`seal_valid/ready` handshake is accepted after all data writes have received
physical ACKs and no data assembler/slot owner remains. The model represents
that handshake as `seal_request`. The RTL then writes descriptor 0 and descriptor
1 sequentially through the same slot, each requiring its own physical ACK. The
model event `sealed_publication_barrier` represents both descriptor ACKs being
complete and the sealed/read fence becoming available; it does **not** represent
the earlier input seal handshake. Read/publication is not legal before this
final barrier. A failed transaction requires cancellation/recovery and cannot
reach it.

## Bounded reference evidence

`experiments/python-gamebub-v91f/write-ownership-model.py` runs a breadth-first
state exploration to depth 20 with deduplication of equivalent ownership
states, plus a deterministic 2,500-event seeded scenario and directed
ACK/enqueue, error-priority, seal-barrier, abort/drain, stale-response, stale-abort
and replacement sequences. The finite alphabet includes two data addresses, two
ordered descriptor addresses, small epoch increments, matching/wrong-epoch/error
ACKs, abort/reset, stale abort, replacement, seal request and final sealed/read
fence events. Each transition checks the ownership and fence invariants. The generated JSON pins
the reference source SHA-256 and reports event coverage, shortest stale-response
trace, visited state/transition counts, and seeded event counts.

The reference does not model the coefficient producer's separate semantic-
failure event. In RTL, a producer-side failure after an accepted request must
likewise retain the accepted physical owner through DRAIN.

This is a bounded executable contract. It is not formal RTL verification, a
proof for unbounded identifiers, a cycle model, or evidence of hardware
performance. RTL validation must separately show that its handshakes implement
these event semantics and that abort/reset races preserve the external bus
owner.
