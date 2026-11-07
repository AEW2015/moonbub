# V91l display consumer lease

`display_overlap_lease.sv` captures the accepted source bank, fid, epoch and
full 64-bit generation when an RGB start is accepted. It validates the frozen
RGB engine's 32-bit generation restriction explicitly, rejecting unsupported
high generations rather than truncating them. Fid zero remains legal.
The lease is immutable while decoding another source frame changes the
accepted-reference descriptor. It adds metadata and control only, no payload RAM.

The engine receives only qualified starts. Invalid descriptor requests pulse
`start_rejected`, create no lease and never start the RGB engine. An active
lease rejects candidate writes to its bank through `candidate_allowed`;
`alias_fault` reports this condition. This is physical backpressure/visibility,
not autonomous upstream error recovery. The wrapper must gate both physical
candidate request-valid and returned request-ready with `candidate_allowed`.
Existing front/pending bank ownership remains the normal allocation protection.

`effective_drained` requires the external downstream hint, no accepted display
lease, no active/draining RGB engine, no pending/busy physical reader and no
display mux ownership. Same-edge RGB starts also suppress presentation drain.
Reset/cancel/error/done marks a terminal display transaction; the lease remains
until two consecutive drain observations. A cold reset while a lease or a
physical read is owned is an illegal integration action. Warm reset does not
throw away the lease.

The standalone C++ bench checks legal fid0 starts, mismatch/invalid/high
metadata, changing accepted hints during a display, same-edge and active
candidate alias exclusion, held physical pending work, mux/engine drain,
reset/cancel/error/done paths, interrupted idle fences and external hints.
Pending/captured-beat semantics here are abstract inputs: this unit campaign
is not an actual SDRAM or wrong-response-tag test. The native overlap campaign
connects those inputs to actual unchanged RGB/controller paths and independently
checks physical pin traffic and protected bank contents.

```sh
python3 scripts/cu66-v91l-overlap-lease/run.py
```

The runner retains source snapshots, strict warning/assertion-enabled commands,
finite watchdogs, transcripts and every failed attempt. Behavioral simulation
only: no hardware frame cadence, full all-RTL HUD, routed timing, CDC or
under-10-ms validation claim.
