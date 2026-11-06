# V85 findings into the next application-specific codec prototype

## Reduce real wire overhead before adding fine chunks

Retain the current CS85 V1 receiver and all four profiles as immutable controls.
The whole-residual-plane candidate is only 1.57% larger than the original
application packets, but is not a bitrate win. Chunk16 nearly doubles corpus
bytes and exceeds the old packet budget on 133 sources. Chunk256 fits all 457
sources but still carries substantial overhead. Keep entropy resets separate
from the 16-tile content-hash groups and four output buffers.

Prototype a distinct compact envelope. The current header sends 64 bytes of
fixed context/mask identity, 32 bytes of already cached previous root, and
32 bytes of expected semantic HUD hash. A negotiated fixed-profile receiver
could infer context/mask, obtain the previous root from accepted state and
compute HUD semantics before checking the seal. This could remove 128 bytes
per frame without weakening C2 bindings, but needs an actual serializer,
independent parser, stale/replay/error tests and measured bytes. Do not change
the meaning of the published V1 header silently.

The nested CM84 map repeats 20 bytes of geometry/method/CRC framing already
protected by the outer packet. Compare an explicitly embedded map body with
its method bound in the outer header. Also test a bit-packed binary group map:
uniform visible COPY, uniform visible RESIDUAL, or a mixed visible mask, with
hidden CONST positions implicit. Compare actual bytes against the existing
976-byte bitset/RLE selection, including all headers and parser bounds. Do not
assume it is smaller on this corpus.

Build actual complete all-visible controls using the same envelope and encoder,
not just component totals. The all-visible mode map can be very small; counting
the full COPY map against no map at all is not a matched whole-codec comparison.
Report every candidate's actual paired bytes, largest packet, compatibility
budget failures, decoded pixels, HUD and seals. Quantized coefficients and
quality remain fixed initially.

## Prototype two arithmetic lanes with real rendezvous

V85 found unequal work across DC and the three AC streams. Two arithmetic lanes
are the first useful comparator; four lanes give much smaller further benefit
in the selected prospective model. Add full-corpus per-context arrival replay
for both the old stream and the actually re-encoded residual streams. Their
work and resets differ, so the old-stream model cannot supply CS85 timing.

Keep each context's decision/probability order and the DC predictor. Include
CRC, initialization, byte fetching, event lookahead, coefficient scatter,
dequantization and input/output backpressure. Compare fetch-before-arithmetic
batching with an instruction-level event trace; include shared port stalls.
Retain bounded pending events and eight-credit staging as a conservative
starting point. Measure COPY transfer/alias work and physical RAM ports rather
than assuming that copy-ready has zero cost.

In an isolated RTL experiment, measure interval/probability multiplier mapping,
DSP/register cost, feedback latency and achievable clock. One front-end model
millisecond or a primitive-product count is not a synthesized DSP/Fmax result.
Require exact coefficient and native pixel/C2 parity before integrating the
decoder with the shared memory/controller/LCD path.

## Strengthen protocol and implementation qualification

The native receiver already checks state publication, late content failures,
valid recovery and exact replay. Next add bounded fragmented-input parsing,
timeouts, duplicates/reordering, resets and explicit abort/drain events. Keep
accepted reference, HUD, generation and root coherent while candidate writes
are outstanding. The host receiver's whole-packet/coefficient arrays are not a
bounded streaming FPGA implementation.

Define negotiated packet/chunk capacities before modifying the ESP32 relay.
Replay exact encoded bytes through finite Wi-Fi receive, QSPI forwarding and
GUI/input buffers; the current 2-MiB host parser bound is not a resource claim
for the board. Include transport overhead and loss/recovery when comparing
gameplay experience or bitrate.

Preserve the milestones: fixed-release 1,800 distinct frames/60 seconds, then
18,000 frames/600 seconds on hardware, with exact displayed identities and
pixel/HUD/reference integrity and zero detected underruns. Afterward require
the complete defined validated decode interval below 10 ms for every qualified
source, with entropy, memory, metadata, HUD and publication fences included.
Report first-byte and last-byte latency separately when ingress overlaps decode.
