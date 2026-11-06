# V91g read-prefetch ownership contract

This document defines an abstract event contract for bounded read prefetch in
the CU66 decoder. The reference model is
`experiments/python-gamebub-v91g/prefetch-ownership-model.py`; its generated
summary is `experiments/python-gamebub-v91g/prefetch-ownership-results.json`.
The model is an executable ownership simulation, not RTL, a formal proof, a
cycle-accurate model, or performance evidence.

## Cache and request owners

V91g prefetch writes the next needed line directly into an existing one of the
four segment caches. The model represents the selected existing cache with one
bounded line; it does not claim an additional line buffer or a complete next
tile cache. A cache line may be replaced only after the old line has been
consumed. The currently held dense output value is a separate immutable owner,
so a matching read response may update the consumed segment cache while dense
output is held without changing that output value.

There is at most one offered or accepted external prefetch. Its immutable
snapshot contains segment, address, epoch, and a payload tag. Before acceptance,
the local offer-valid indication and snapshot remain stable through an
abstract ready-low observation. Acceptance transfers the snapshot to a
separate physical-owner field. Local fill-valid and physical ownership are
independent: abort or reset can clear local intent, but an accepted request
continues to block bank replacement until the physical response fence retires
it.

Only a matching successful ACK with still-valid local intent, matching epoch
and segment, and the requested address may write the returned line into the
existing segment cache. A matching error ACK retires the physical request but
fails the logical transaction and does not fill the cache. A wrong-epoch
response fails local fill closed but does not retire the actual accepted
physical owner; a later matching response is needed to drain it. Segment
replacement advances the epoch and is ineligible while an offer or accepted
physical owner remains.

## Read-phase fences

Prefetch offer is gated by the abstract seal event. The candidate is only the
next required line: the next DC block line, an AC record line needed by the
monotonic cursor, or a RAW line needed after its scalar has been latched. It
does not model speculative `line + 16` traffic, full-next-tile merging, or
overfetch at segment ends. The bounded model uses segment IDs 0 and 1 and line
addresses 0 and 16.

Dense completion is legal only after offered and accepted prefetch ownership
has drained. Thus a final prefetch cannot be silently abandoned as successful
completion. While a dense value is held, a matching ACK may replace the already
consumed segment-cache line, but the held dense value stays unchanged. Error
and wrong-epoch paths cannot write cache data.

The V91g read-side ownership mapping uses a local `PFoffer` snapshot, a physical
accepted-read owner, matching-ACK cache write, local failure invalidation, and
the final `PREFETCH_DRAIN` fence before the next tile's demand read. The model
does not represent RTL state encoding or prove those mappings.

## Bounded checks and limits

The deterministic run performs breadth-first exploration through depth 11,
directed ownership traces, and a seeded 3,000-step walk (seed 910437). Some
steps restart after a terminal state; the JSON reports requested steps, events
executed, and terminal restarts separately. It records the model-source
SHA-256, visited states, checked transitions, event coverage, shortest event
traces, and seeded event counts.
Directed checks cover stable offer snapshot, single accepted request, matching
fill during dense hold, matching error ACK priority over output advancement,
wrong-epoch drain, accepted versus unaccepted abort, replacement blocked by an
accepted request, and seal-before-prefetch ordering.

These finite checks establish only that the stated abstract transitions obey
their assertions over the explored domain. They do not show RTL equivalence,
unbounded safety, actual bus timing, cache-array fit, or throughput. RTL review
must separately verify offer/accept stability, error priority, correct ACK
identity, cache fill gating, segment/cursor bounds, and the final drain fence.
