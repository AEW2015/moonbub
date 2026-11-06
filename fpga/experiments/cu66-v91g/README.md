# V91g bounded read-line prefetch checkpoint

V91g copies the V91f byte packet → packed scratch → dense coefficient pipeline.
The runtime `read_prefetch` input is captured at integrated start and passed as
`begin_prefetch` at scratch allocation. The measured comparison fixes
`write_overlap=1` and `serial_clear=0`, and compares read prefetch off/on under the
same FAST/SLOW service profiles. Disabled prefetch retains the exact V91f overlap
control path. The unchanged V91/V91b/V91d byte/context/packet parsers remain in use.

This checkpoint implements bounded next-line fetching, not full next-tile merge
or double-buffered tile preparation. Current dense values are owned by the
completed 64-value tile or latched RAW scalar; the reader can use otherwise idle
bus service during those values' delivery. There are no additional 16-byte cache
payload arrays: four existing segment caches remain. Four tag bits distinguish
lines installed by prefetch until their first actual extraction. Physical FPGA
mapping, cache RAM ports and clock timing remain unqualified.

## Safe direct-cache replacement

During a coded tile's `EMIT`, the prefetch candidate selector can fetch the next
block's aligned DC line, or the aligned line at one AC segment's next-unextracted
cursor. It fetches only when that line differs from the segment's existing cache.
AC cursors advance monotonically; a previously extracted next-block AC head is
held in its own scalar head register. Thus replacing the old line cannot destroy
a future-needed byte: the old line's entries before the cursor have already been
extracted. A cursor within the current cache does not trigger lookahead past it.
This is deliberately a bounded needed-line policy rather than speculative
multiple-line buffering. Segment selection is deterministic, DC then AC1–AC3.

No coded prefetch begins on the last block. For RAW, only the next scalar's line
is considered, and only at a line boundary while `raw_value` owns the current
output. The final scalar cannot launch a prefetch. Every successful campaign
requires each allocated 16-byte line to be written exactly once and read exactly
once, including both descriptor lines; prefetched data lines must all be used.

One offered request owns immutable segment/address/epoch fields until matching
physical ACK. At most one request is physically outstanding. Only successful ACK
installs a prefetched line; request acceptance is not cache validity. While
waiting, dense scalar acceptance may continue and held dense payloads remain
stable. If tile/scalar delivery finishes with a newly offered or accepted read,
state27 `PREFETCH_DRAIN` waits before the next demand reader can reuse the shared
bus and transfer registers. This includes an offer launched on the very same
edge as the final scalar transfer. States0–26 retain their V91f meanings;
states28–31 remain reserved.

Abort/start/warm reset withdraws unaccepted local offers but preserves an
accepted physical read's epoch/address until its matching response drains.
Allocation remains blocked while that hazard exists. A wrong-epoch response
cannot retire the physical owner. Error or stale ACK takes priority over cache
installation and dense acceptance on the error edge, clears the logical seal,
and fails closed. These rules preserve bank safety; partial dense coefficient
output is not atomic full-frame publication.

## Evidence and counters

The external model has one 262144-byte scratch bank. FAST uses ready requests
and one-edge responses. SLOW uses write16/read18 plus address/seed jitter0–3,
with deterministic finite input, request and consumer stalls. Accepted writes
commit only at delayed physical ACK, including after logical cancellation.
All packed bytes and dense coefficients are compared against the same frozen
20 independent V91e goldens. The 15 actual packets cover five related source
frames; synthetic/boundary cases are separate and do not establish new content
coverage.

Read scheduling can reorder legal line requests, so the old ordered
`request_service_hash` is retained but is not required to match the candidate.
Two new decimal-string fingerprints are independently reconstructable:

- `request_service_multiset_hash`: modular64 sum of one FNV token per request.
- `ordered_write_service_hash`: continuous FNV over only the unchanged ordered
  write requests (ascending data lines from32, then descriptor lines0 and16).

Each token starts at1469598103934665603, multiplies by1099511628211 modulo2^64,
and mixes each tuple value as eight little-endian bytes: direction (write1/read0),
byte address, assumed latency, and for writes the four zero-extended uint32 data
words. The multiset token resets its offset per request. Exact per-line read and
write visit counts additionally reject duplicates or missing lines, rather than
relying on a checksum. `memory_line_coverage` reports successful read-once and
write-once line counts.

`observability.read_prefetch_counters` gives `offers`, `physical_accepts`,
`physical_acks`, `uses`, `dense_during_pending`, and `drain_wait_edges`. Offers
count installed immutable request owners, ACKs count successful physical
matching responses, and uses count first actual DC/AC extraction from each
prefetched line. All four transaction counts must agree after successful
completion. `dense_during_pending` counts accepted scalar transfers while a real
prefetch read is pending, including its ACK edge. `drain_wait_edges` is state27
occupancy. These event counters overlap state histograms; they are not additive
removable latency. `highwaters.prefetch_offer` is at most1, cache lines remain at
most4 and physically outstanding requests remain at most1.

The integrated harness independently observes all counters/timestamps and checks
full packed images, dense values, source epochs, held request payloads, held dense
payloads and final no-pending completion. It retains the 28 V91f directed recovery
checks and adds eight prefetch checks: ready-low offer/dense hold; ACK during
dense hold; accepted-read abort and drain; error ACK; stale ACK; ACK during held
warm reset; last-scalar demand barrier; newly launched offer on the same last
scalar edge. The separate public scratch-interface harness retains V91f's nine
semantic-error/write/epoch hazard checks with prefetch disabled. Both testbenches
require explicit `TEST_PASS` and have bounded watchdogs.

Root-owned scripts retain source snapshots, strict Verilator/C++ warnings,
assertions, tool versions, raw JSONL results, tile traces, canonical traffic
checks and matched baseline metrics. Consult the selected campaign receipts and
root study README for final measured gains, regressions and qualification.

This is coefficient-endpoint functional simulation. No IDCT, reconstruction,
accepted reference/HUD/hash path, complete-frame publication, achieved clock,
physical memory controller, live ESP32 forwarding, hardware 30 fps or complete
validated under-10-ms FPGA decoding is established by this checkpoint.
