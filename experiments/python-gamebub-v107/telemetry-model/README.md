# Reset-free telemetry counter bank: model feasibility

This bounded prototype asks whether the basic reset-free counter rule can
preserve a defined public view. It is motivated by the mapped fanout report's
7,125 telemetry data FF reset sinks. That count is an investigation target;
this model does not reproduce the current telemetry families, ports, readsites,
or update API and does not prove any of those resets removable.

Run the finite comparison with:

```sh
python3 experiments/python-gamebub-v107/telemetry-model/telemetry_model.py
```

The retained [results](results.json) are `PASS_MODEL_ONLY`. Four fixed seeds
cover 50,000 clocks each and compare all 32 public bins every edge against an
independent functional reference interpreter. The baseline stores resettable
32-bit counters. The candidate starts with arbitrary 32-bit payload and
snapshot data, resets only a per-bin valid bit and snapshot-valid control, and
uses zero as the base of a first post-invalidation increment. The finite run
includes repeated resets/aborts, all-bin visibility, zero sets/captures,
counter wrap, same-bin set/increment conflicts, consecutive same-bin updates,
captures coincident with updates, held snapshots while live bins change, and
3-bit snapshot-tag wrap. The recorded output-mask-only negative control fails
on the expected stale increment after reset.

## Modeled edge rules

1. Synchronous reset or abort clears all baseline counters, invalidates every
   candidate counter, invalidates the snapshot, and resets the next snapshot
   tag to zero. It dominates updates, capture, and hold on that edge.
2. Otherwise, each bin may accept a set or increment. Set wins if both target
   the same bin; distinct bins may update together. Increments wrap modulo
   2^32. An increment to an invalid candidate bin uses `0 + delta` before
   marking it valid.
3. Capture occurs after accepted updates, so it includes the current edge's
   accepted event. It copies all 32 publicly visible bins and records the next
   modulo-eight tag.
4. Hold suppresses capture even when capture is requested. It leaves the prior
   snapshot and tag unchanged while live counters may continue changing.
5. An invalid counter or snapshot reads as zero. The snapshot tag is not a
   globally unique generation: it repeats after eight successful captures.
   A real consumer would need snapshot-valid and ownership/handshake semantics
   that tolerate tag reuse.

The reference interpreter uses value-state transitions rather than the
candidate's validity storage. A conventional resettable-data model and the
lazy-valid model are compared to that reference after every edge. Seeded
initial data exercises the candidate's unowned state; a dedicated broken
control retains valid bits through reset and shows that an output mask alone
can reveal a stale counter when the next increment arrives.

This is a small protocol model, not RTL, full current-source equivalence,
assertion closure, a model of the current snapshot/read API, synthesis, timing,
resource measurement, metastability analysis, CDC signoff, or hardware
qualification. In particular it does not capture the source's pre-edge
telemetry sampling, final `store_done` edge, packet/state histogram families,
timestamps, high-water/max fields, assertions, or child-cancel versus
parent-receipt ownership. Those semantics must be inventoried and modeled
before any RTL experiment. No resource or timing gain is claimed.
