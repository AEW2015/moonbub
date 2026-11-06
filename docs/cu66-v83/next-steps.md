# Application-specific codec implementation gates after V83

The application-specific opportunity is to avoid work that this game-streaming
profile does not need: derive COPY from decoded zero residuals, generate hidden
CONST128 regions locally, reuse certified candidate contents, and validate a
changed content tree instead of rereading the complete picture for flat SHA.
These preserve the quantized native picture. V83 studies how to execute that
profile with bounded groups; it adds no compression-rate improvement or new
Sunshine/ESP32 wire implementation.

## First implement the bounded streaming path

Implement the [pipeline design](pipeline-design.md) as isolated RTL variants,
retaining the existing native pixel and HUD oracles. Start with one group and
one hash lane, then change only group capacity to four, then hash lanes. This
matches the controlled Python comparisons and distinguishes buffering gains
from arithmetic gains. Generate the stream of operations with bounded hardware
state; do not implement the Python scheduler's full future-task graph in RAM.

Four groups reserve 4 KiB of output bytes. Conservatively reserving reference
inputs, the existing signed 24-bit inverse results, and output pixels requires
20 KiB for these three tile stages. Coefficients, inverse working storage,
hashes, descriptors, control, and physical RAM rounding are additional. Bind
every request and response to generation, bank, tile and buffer slot. Refuse
admission when a slot or response buffer is unavailable; demonstrate stable
data under backpressure rather than assuming a nominal service interval.

Keep the current three-bank canonical layout initially. Publish candidate
identity, content root and residency maps only after content/HUD checks and
physical drains. Tests must inject aborts at outstanding reference reads,
inverse outputs, physical writes, digest writes and publication fences. Reset
and lost-ACK replay must preserve the accepted reference or explicitly require
a key; speculative old-bank certificates cannot be restored on abort.

## Qualify memory service separately from the codec

The V82 cold-delta case still requires **68,904 data/HUD BL8 operations** even
with COPY and residency. In the illustrative V83 scenario reserving 20% of a
100-MHz server, a 10-ms window has at most 800,000 available clocks. Its necessary
average cost is therefore **less than 11.61036 clocks per operation**, before
any additional arbitration loss or unhidden computation. This is a conditional
requirement, not a controller specification or a feasible measured rate.

Twelve clocks per operation already exceeds that budget; eight clocks is only
the x16 payload-transfer ideal. Use RTL traces to measure real BL8 acceptance
and completion intervals with direction changes, bank/row changes, refresh and
continuous LCD/HUD traffic. Prototype command coalescing, queued descriptors
and response snapshots as separately controlled changes. More DSP or SHA lanes
cannot remove a memory-service requirement by themselves.

If the real controller cannot meet the necessary service, examine a separate
layout/profile experiment that reduces mandatory cold-frame traffic. Shared
tile storage or reference indirection would require allocation, reference
counts, generation-tagged display translation, bank leases and recovery; the
current residency model does not provide those semantics. Do not silently treat
COPY eligibility as permission to omit an uncertified candidate store.

## Define and replay the actual host-to-FPGA profile

Specify an explicit opt-in binary envelope for V82's content commitment,
preserving AB38 residual coding initially. Bind version/capability, geometry,
grouping, frame/reference/generation, encoded lengths, content root/seal, HUD
semantics and fallback behavior. Unkeyed SHA commitments are not peer
authentication. Retain independent canonical SHA only as the verification
oracle; retaining its full-frame hardware read requirement would invalidate
the intended avoided-read benefit.

Implement a host encoder and an independent bounded receiver/parser before
changing Sunshine or the ESP32 relay. Exercise truncation at every header
field, oversized lengths, reordered fragments, stale references, CRC failures,
timeouts, lost/duplicate ACKs, capability mismatch and reset. Replay exact
encoded byte streams through finite ESP32 receive/forward buffers, including
Wi-Fi/QSPI stalls and simultaneous GUI/input activity. V83 begins with the
packet available and does not simulate ESP32 throughput or memory.
Replay actual entropy/dequant output arrival times as well: V83's tile modes
are available at admission, whereas the retained coefficient stream must be
decoded before a safe COPY can be established. Any host scheduling hint remains
untrusted until that decoded-zero condition is checked locally.

## Close the two milestones in order

First require at least 1,800 distinct accepted source frames over 60 seconds at
fixed 30-fps releases, with a following 18,000-frame/600-second hardware run.
Repeated pictures, replayed small corpora, four independently reset histories,
and per-frame times below 33.33 ms cannot substitute for that test. Verify
displayed identities, output pixels, queue bounds, reference/HUD integrity and
zero detected underruns throughout.

Then require the complete validated FPGA decode interval below 10 ms for every
qualified source, with the release/end fences defined and entropy, memory,
hashing, metadata, HUD and concurrent display included. Separately report
capture, encode, transport and scanout latency. Compare alternative codecs at
the same source, quantized quality/resolution, latency definition and error
recovery behavior before making any HEVC/AV1 comparison claim.
