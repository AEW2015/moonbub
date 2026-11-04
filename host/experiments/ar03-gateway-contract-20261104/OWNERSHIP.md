# Offline FG19 receiver ownership ledger

`gb_ownership.c` is a bounded epoch-1 laboratory receiver ledger built beside
the reviewed native parser. It reserves exactly two frame slots and consumes
the `gb_frame_control`/`gb_data_route` values that parser produces.

The receiver accepts sender-direction REQUEST, CANCEL and FINISH controls only.
A REQUEST reserves its requested free slot if its request serial is newer than
both accepted and released serials. An identical retransmitted REQUEST repeats
the same GRANT. CANCEL frees only an exact owner that has not observed any
matching GF03 fragment. FINISH records the sender's control barrier and leaves
the frame reserved. RELEASE is produced only when FINISH and a separately
supplied `gb_ownership_physical_drain` event have both occurred. Drain may be
reported before or after FINISH. With FINISHED-ACK mode enabled,
`gb_ownership_control` returns the FINISHED response and the caller must enqueue
that response before calling the separate `gb_ownership_take_release` poll.
There is no on-wire acknowledgement of FINISHED receipt, so the receiver cannot
know whether the host saw it. A lost FINISHED response requires host safe stop;
the ledger adds no invented recovery message. Wrong identities, stale controls
and reply-direction controls cannot free an owner.
`gb_ownership_safe_stop` is sticky and retains all owners after an unknown
outcome. Like the frozen receiver, a fresh REQUEST serial is consumed even if
its explicitly requested slot is busy.

The GF03 observation path validates bounded route geometry and records only a
unique fragment-index bit in a 64-bit bitmap (at most 49 indices). It does not
consume PC18 packet permits or prove FIFO capacity; it is not packet admission.
The drain hook returns 1 when evidence is recorded for the exact owner and 0
for a stale/unowned identity. The caller must provide trustworthy physical
drain evidence after ingress and all readers have drained. The ledger does not
infer drain from fragment count,
FINISH, parser success, CRC, decode, or publication.

This is not production negotiation, reset/rekey, a network endpoint, or a full
gateway. It has no packet-credit ledger, permit handling, bounded ingress FIFO,
DMA/QSPI path, decoder, publication, or hardware connection. Epoch is fixed to
1 and exhaustion/unknown outcomes require caller-directed safe stop; this does
not claim a production recovery protocol.

Run `test_ownership.py` against the pinned source checkout. The harness parses
all 1,725 retained serialized FG19 history messages. Histories do not encode
the independent physical-reader-drain event, so replay intentionally does not
invent drains or claim each history's later releases. Targeted tests provide
explicit drain calls and check the release boundary.
