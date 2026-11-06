# V78 continuous direct-YUV scanout

`cu78_direct_scanout` combines the frozen V77 bounded cache/converter with the
frozen V70 native LCD line buffers. It repeats an immutable committed source
at native refresh and changes visible source identity only at a qualified
frame boundary, after the old source's accepted work drains. It accepts a
canonical bank rather than a portrait RGB framebuffer slot.

## Epoch and descriptor ownership

A one-entry pending queue captures generation, source ID and bank. Invalid
zero/stale generations, invalid IDs/banks, nonincreasing visible IDs and reuse
of the current immutable front bank return an error without publication.
`descriptor_ready` stays low while a committed pending source is retained.

The renderer cache is a **per-raster epoch**, not the global canonical owner.
After its last 480-pixel source line has entered the native line buffer and
its strip/response/pixel work drains, the cache finishes. The scheduler prepares
the pending committed source, or the same visible front if no pending source
exists. Its visible front remains unchanged while old native pixels finish
scanning from the line buffers. Preparing a pending source can therefore use
new-bank reads while the old globally held front is still visible.

At the qualified native frame boundary, the prepared pending source becomes
visible and produces `presented` with its exact generation/source/bank. The
old-reader drain observation is held through that entire pulse using
`scanout_drained = old_front_drained || presented`; the parent bank controller
can sample the matching ACK on the following core edge. New pending-source
prefill is not misclassified as an old-front reader.

If a new descriptor arrives after a repeat epoch is already prepared, it stays
pending for the following safe epoch. The design does not replace cached data
mid-raster, drop the descriptor, or label the repeat's old pixels with a new ID.
That conservative choice can add a native refresh of latency. Throughput and
latency qualification must include that delay rather than treating safe
repeat frames as new game-source frames.

## Native line path and cache schedule

The source line counter expects physical rows 40 through 759, in order. It
checks each held LCD request address against `expected_line * 480`; it does
not reverse a wide address with `/480`. Each accepted line issues exactly 480
coded cache queries and streams 480 converted RGB565 words into the native line
buffer. Coordinate/error checks accompany every accepted output.

A strip is consumed only after its final converted line has drained into the
output line buffer, and the render wrapper retains query/converter ownership
through response drain. Prefetch is ordered and bounded to current plus two
future strips, with the established 29,184-byte cache organization. Black
margins provide normal startup preroll before the first canvas request. The
native line-buffer request/complete toggles and pixel-clock ports are reused
unchanged; no target timing/CDC signoff is inferred from behavioral simulation.

`cache_read_commands`, `cache_read_words` and `cache_pixel_queries` are aggregate
32-bit modulo counters across cache epochs. `raster_count` counts completed
source-cache epochs after all converted source lines drain; the last native
pixels may still be scanning from the line buffers at that instant. Complete
physical rasters and distinct source IDs are counted separately by the oracle.

## Independent continuous test

Run:

```sh
python3 scripts/cu66-v78/run_scanout.py
```

The bench predecodes three actual chronological key/P fixtures using the native
C++ decoder, independently lays their planes/HUD into physical tile-major
memory, and returns eight-word streams with deterministic ready/gap schedules.
No golden sample bypass feeds the RTL caches. This test's memory is an ideal
streamed fixture source, **not the SDRAM controller or FPGA compressed decoder**;
root full-system integration provides that separate evidence.

Both seeds run continuously with no per-source reset. Every one of the 480×800
native pixels is checked, including black borders and active RGB565 data. The
visible generation/source/bank must stay constant throughout each complete
raster. A deliberately late pending source is retained while an already
prepared old-source repeat is shown. A stale descriptor held behind that
pending source exercises descriptor backpressure and is rejected after its
turn arrives. Four further malformed/stale descriptors are rejected while the
last source continues to display. The bench also checks held memory request
addresses and that no accepted old-bank read remains at the source-switch ACK.

Each seed checks three distinct committed sources and seven complete correct
portrait rasters, with repeats 3/2/2: **2,688,000 exact native pixels per seed**,
zero underruns and zero memory errors. Repeated rasters do not count as new
streamed sources. Aggregate read traffic includes the already prefetched prefix
of the following repeat at the end of the run; it is not silently discarded
from command accounting.

The result retains source/fixture and command/log hashes. Hashed internal
archives preserve the initial qualification and the verification-only reporting
extension; they are checked against their archived sources, not current ones.
Production scanout RTL was unchanged after its first native pass.

## Limits and next work

This finite continuous replay does not prove sustained 30 distinct source-fps,
strict validated FPGA decode below 10 ms, actual SDRAM deadlines, target Fmax,
board fit, live transport or physical pixel-clock timing. The parent integration
must retain canonical front/reference/pending/candidate leases; local cache
finish is not permission to overwrite a bank still held as a reference or front.

A cache/memory fatal error latches diagnostic stop and prevents further source
publication until reset. Accepted cache read drain remains owned by the cache,
but whole-display mid-line recovery and resumption are not qualified here.
No fabricated successful frame or fake painter completion substitutes for a
failed descriptor, cache result or native line.
