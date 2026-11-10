# V122 exclusive wait trace schema

`v122-exclusive-wait-trace-v1` is a finite JSON trace format for a future
edge-level instrumentation run. The validator is in
`scripts/cu66-v122/wait_trace.py`. It is not itself instrumentation, an RTL
model, a memory-controller simulation, or hardware qualification. Existing
aggregate counters are never expanded into per-edge causal data.

## Trace contract

A trace covers a successful single-epoch frame from `trace_start_cycle` through the
half-open interval `[trace_start_cycle, trace_end_cycle)`, and declares
`trace_scope: "full_frame_before_first_acceptance"` plus an explicit empty
`initial_outstanding` ledger. This prevents assuming the write debt is zero at
the decode-start fence when writes may have been accepted earlier. The decode
measurement interval is separately delimited by named `decode_start` and
`decode_end` fences. `decode_end` must equal the publication cycle. Abort,
reset, retry, or cross-epoch traces are unsupported by this version and must
use a future schema that models their debt transitions explicitly; unknown
control fields are rejected.

The header also declares frame ID, bank, epoch, transaction token, nominal
clock Hz, a plain-language timebase assumption, a one-write outstanding credit
limit (matching the retained baseline), one-hot `condition_bits`, the owner
priority policy, and exact declared totals. Every cycle in the full-frame
interval must appear exactly once. An edge has one exclusive `wait_owner`
(`none` or the first active wait condition in the declared priority) and a raw
condition bitmask. Multiple raw conditions may overlap. The selected owner is
an explicit accounting policy; the mask and owner do not establish causation
or independent latency.

Write accepts and ACKs carry bank, epoch, token, and byte count. The ledger
starts empty, accepts must use the frame's bank and epoch, and a matching ACK
must pay the exact token and byte count. No abort/reset silently clears debt.
The full-frame trace must finish with zero debt. If accept and ACK are listed
on the same edge, the validator processes acceptance first and ACK second;
this ordering only defines ledger semantics and does not imply zero physical
service latency. The current maximum outstanding credit is explicitly one.

Required fences are `frame_start`, `decode_start`, `reconstruct_done`,
`canonical_validated`, `hud_validated`, `root_validated`, `seal_validated`,
`commit_ready`, and `decode_end`. Each fence carries the frame, bank, epoch,
and transaction token. Reconstruction and validation fences may occur in
different orders because work can overlap, but all must be at or before
`commit_ready`; publication must be strictly after `commit_ready`, match those
identifiers, and occur with zero outstanding writes;
no write event may occur at or after publication. Owner totals, overlapping
raw-condition totals, accepted/ACK counts, and byte totals must match declared
totals exactly.

The validator caps a row-only JSON trace at 4,000,000 edge records and a
serialized input size of 1 GiB. This allows the retained roughly 1.8-million
edge full-row traces with headroom. JSON parsing holds the decoded trace in
memory, so peak RAM use can exceed the file-size cap; do not submit arbitrary
large traces or run this concurrently with constrained jobs. No actual trace
was run through this validator. A nominal clock is required to document an
assumed timebase, but cycle-to-time conversion is not reported as measured
timing.

## Run the synthetic validator checks

```bash
python3 scripts/cu66-v122/wait_trace.py --self-test
```

The bounded tests cover valid overlapping-condition and reordered validation
fences, and rejection of
missing or duplicate edges, invalid owners and masks, incorrect owner priority,
frame/epoch/token mismatch, unpaid writes, premature decode-end/publication,
ACK at publication, reused tokens after ACK, bad totals, a nonempty initial
ledger, and unsupported abort controls. Results are written to
`experiments/python-gamebub-v122/memory-study/wait-trace-self-test.json` and
are explicitly labeled synthetic validator tests only. A production trace must
be emitted by a separately designed instrumentation change and independently
validated against its RTL/source provenance before interpreting counts.
