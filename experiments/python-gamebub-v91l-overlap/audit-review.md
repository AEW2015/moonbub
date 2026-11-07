# Concurrent verification contracts

Decoder and RGB display each retain their own immutable source descriptor.
The previous serial checker could use one current-frame context; that would
misattribute key RGB rows and reference reads when delta decoding overlaps.
The new replay maintains accepted source history separately from the active
RGB owner and classifies real physical read requests by actual mux ownership.
It preserves the frozen global pin oracle, scratch child-epoch accounting,
source-backed candidate/canonical/reference/RGB bytes, exact complete SHA job
groups, quantizer history and publication checks.

A delta commit may coincide with an unrelated display READ. It still requires
all candidate write/hash and reconstruction-reference/scratch work drained.
The guard binds actual RGB start to the qualified lease, protects the source
bank and gates publication. Display closure is bound to the actual terminal
and two-idle drain release edge. Raw RTL owner-change observations are pre-NBA
and appear at the next clock: a C++ RGB closure at the end of the release
clock precedes that raw owner-down observation by half a clock. This
observation offset is checked explicitly; counters cannot invent completion.

Reported commit source/epoch, native start, packet-complete, engine-done and
RGB closure counters are checked against actual source/edge receipts. All
completed native SHA groups must be present and no unchecked group may remain.
Lease replay additionally verifies captured full generation, terminal/error
history, alias metadata and two consecutive terminal physical-drain samples.

The guard rejects new aliasing candidate handshakes; it does not evict an
already accepted writer. Native start preconditions and allocator ownership
protect that case. The directed native hold retains a final consumer pixel,
not a pending SDRAM burst at that exact instant. Unit pending/error/cancel
stimuli are abstract and complement the actual native controller/pin runs;
none of these checks constitute exhaustive formal or electrical proof.
