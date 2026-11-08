# Timing follow-up and reset scope

The frozen-source matrix measures implementation effects at 10 ns. Its m0
checkpoint-reload control is a fresh observation, not a reproduction of V107's
earlier route: m0 WNS −2.758 ns versus V107 −2.333 ns. Compare each matrix row
with m0, and keep the earlier result as a separate frontier. Placement estimates
are not final routed timing evidence.

The completed m0 worst path runs from synchronous ingress `fetch_index[2]` to
its state CE, with seventeen logic levels and 12.505 ns data delay. The frozen
V107 route's read-segment/cache-selection path remains another failing cone.
The capacity fallback shortens packet-plan control arithmetic; it does not
claim to fix every cache, parser or payload control path.

## Reset and fanout changes need a read-ownership contract

The m0 routed fanout report lists scratch cancellation at 7,143 loads, including
7,130 set/reset pins; another scratch reset net has 2,381 loads. A large net is
a useful target for investigation, but it is not evidence that all its sinks
may lose reset. V107's retained netlist inventory found that most cancellation
loads belonged to observable telemetry. Those counters have feedback and time
origins; arbitrary unreset values would change their public meaning.

AMD's [reset guidance](https://docs.amd.com/r/en-US/ug949-vivado-design-methodology/When-and-Where-to-Use-a-Reset)
recommends evaluating data-path reset necessity separately from control reset.
Its [fanout guidance](https://docs.amd.com/r/en-US/ug949-vivado-design-methodology/Replicate-High-Fanout-Net-Drivers)
recommends measured implementation replication and cautions against applying
MAX_FANOUT indiscriminately. The [physical optimization guide](https://docs.amd.com/r/en-US/ug949-vivado-design-methodology/Use-Physical-Optimization)
explains why fabric-register-driven control nets are suitable for replication.
The m4 trial applies pre-route AggressiveFanoutOpt to the unchanged design.

Further RTL experiments should distinguish:

- Private payload which is overwritten before any owned read: leave payload
  resetless while resetting its validity/ownership state, with arbitrary-initial
  payload, reset/abort/retry and held-response proof.
- Operational ready/kill/error/ownership: retain required immediate semantics.
  A delayed global cancellation cannot replace a same-edge safety fence.
- Diagnostic snapshots: a separately versioned valid/epoch API can permit
  pipelined sampling and local counter baselines. The current public debug and
  counter outputs remain exact; changing the API requires a separate wrapper
  and cannot be hidden inside the present equivalence check.

For a new local control pipeline, capture the complete owner/tag tuple together
with the data, define flush priority on every stage and commit only while that
owner is current. The capacity candidate uses existing header slack for this
purpose. A future one-hot cache-selector experiment must cover all four banks
0–3 and every selector write. A stronger extracted-tuple pipeline must forward
same-edge foreground and background cache writes before validation.

No reset removal, one-hot selector or diagnostic API change is credited merely
because it appears in this follow-up. Each needs its own source snapshot,
unweakened focused and canonical RTL proof, and a fresh routed comparison.
