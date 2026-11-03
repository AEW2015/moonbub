# Game Bub application-specific codec: selected direction and gates

The [iteration8 results](custom-codec-prototype-v8-2026-11-03.md) now include
an executable GM01 temporal-ROI Python codec, shared-transform two-candidate
admission and replayable golden vectors. The prior
[iteration7 results](custom-codec-prototype-v7-2026-11-03.md) selected this direction.
These remain software prototypes: capability negotiation, actual firmware/FPGA
support, physical memory service and hardware30 fps are not implemented gates.
The current JPEG implementation remains the hardware control. Custom formats
cannot be sent to JPEG RTL.

## Product target and split of work

Target a720×480 transmitted canvas, with720×405 active16:9 content letterboxed
inside it. First qualify30 distinct displayed frames/s, stable HUD/text and
bounded frame age. Rate alone is insufficient if the newest input or game
response waits behind stale frames. The working comparison is the existing
JPEG path, using the same captures, canvas, display and wire accounting.

The PC performs motion/region decisions, transform/quantization, entropy and
byte-budget selection. Game-specific profiles declare HUD/text rectangles;
current-frame activity can distribute remaining bits. No privileged game-state
API, future-frame oracle, hidden reconstruction-quality search or automatic HUD
recognition is assumed. Explicit profile/version metadata must identify those
priorities. A wrong profile must remain decodable and have a uniform fallback.

ESP32 forwards bounded opaque chunks, manages ingress/credit/session recovery
and input/control service. It does not need to reconstruct video or classify
HUD pixels. Its real concurrent Wi-Fi/QSPI, buffer occupancy and reset behavior
must be measured on the target firmware.

The FPGA uses bounded parsing, integer coefficient reconstruction, a small
quantizer map, immutable-reference prediction, color conversion and atomic
framebuffer publication. Keep complex decisions on the host. Logical map and
reference sizes are inputs to physical-memory qualification, not proof of
BRAM/DSP fit or bandwidth. Existing exact Q14 arithmetic remains the golden.

## Selection from current evidence

| Candidate | Decision | Reason |
| --- | --- | --- |
| MA01-style immutable anchor + CP02 residual | Base for next combined experiment | Better tested byte demand than independent dirty tiles; explicit ACK/reference identity |
| RG01 macroblock quality map | Implemented in GM01 Python residual profile | Improves declared-region error at similar same-frame byte budget, with visible background tradeoff |
| Word CP02 reader | Carry into software oracle | Exact valid-output and sampled malformed-rejection compatibility; measured receive cost reduction |
| DT01 independent dirty tiles | Exclude from gameplay base | Frequent cap failures and header/context cost; static tail is a possible separate UI mode |
| Two asynchronous replacement anchors | Later measured option | Extra reference, control decode, lifetime and retirement costs remain |
| Palette/lossless HUD patches | Next optional experiment | Could preserve colored glyph edges; no rate/quality/decoder win established yet |

Independent ROI was implemented as RG01. The combined GM01 version now actually
encodes/decodes the temporal residual and map together; it is not a silent MA01
flag. Its measured region gains cost extra bytes versus uniform GM01, and the
coarser background alternative has explicit quality loss. Actual capability
negotiation remains required before a real peer can use this profile.

## Work package A: implemented reference, now qualify coverage

The GM01 Python profile now implements an epoch, increasing capture/frame ID, explicit
key/residual kind, exact anchor ID, even geometry, declared macroblock map,
bounded three-plane CP02 payload lengths and complete-frame CRC. Each16×16
luma /8×8 chroma region selects scale8/16/32. At720×480 the uncompressed2-bit
map is338 bytes; include all envelope/chunk/CRC bytes in the budget.

Keys reconstruct independent YUV420; residual frames predict from the exact
ACKed reconstructed immutable anchor, then apply the current frame's transmitted
quantization map. RGB/display conversion stays frozen. P output never advances
the predictor. Require sender and independent decoder equality for coefficients,
reconstructed YUV/RGB, map edges and reference IDs at every step.

Start with one immutable reference, bounded in-flight credits and drained key
replacement. Wire ACK/session reset and physical read-drain are distinct
contracts. Receiver state commits only after a complete valid packet. Wrong,
lost, repeated or old-epoch packets/ACKs must never manufacture a reference or
publish a partial frame. A reference-only key must never inflate displayed FPS.

DT01's source-equality RGB copy is not automatically equivalent to YUV residual
SKIP, especially at chroma boundaries and after a quality-map change. A later
copy mode needs an exact new reconstruction/reference contract. Do not splice
these formats together by copying output tiles without a proof and tests.

## Work package B: implemented bounded controller, now qualify worst cases

The implemented controller reuses one source/prediction/forward analysis and
tries a normal ROI8/background16 map, then at most one ROI8/background32 fallback.
It measures the complete preparation call and leaves state unchanged on total
rejection. This replaces the old offline candidate search with a different,
fixed two-map policy; their quality/budget targets are not identical.
Keep every failed attempt and selected key reconstruction in sender service.
The separate exact-size and conservative lower-bound experiments now avoid
serializing some provably oversized candidates. The cheap gate cuts seeded
noise-reject service substantially, but ordinary pressure/normal paths do not
show a general speedup. Treat it as a measured rejection guard, keep the final
actual-size check, and validate decisions against the unguarded codec.
Worst-case noisy rejection and fallback tails still require qualification;
never substitute a favorable mean for per-call service or a deadline bound.

Declare a per-game priority-quality floor and maximum frame age. Size selection
uses current data and past measured headroom, with hysteresis. Keep ROI at its
configured floor while coarsening background only within allowed bounds. If
no candidate fits, drop the whole stale/oversize frame and record why; never
truncate or pretend it was displayed. A reliable independent-key delivery
strategy must be specified separately if keys exceed receiver capacity.

A uniform16 reference-size budget is an RD comparison, not a negotiated48 KiB
packet cap. Qualify the receiver's actual buffer/staging capacity, or enforce
its real cap. Larger SDRAM staging is a separate integration/throughput option,
not a codec quality or instantaneous bandwidth guarantee.

## Work package C: application-specific comparisons

Use declared profiles for real game HUDs plus synthetic small-font/color-edge
fixtures. Add camera pans, scrolling, particles, dark scenes, menus, loading,
scene cuts and rapid HUD changes. Retain fixed uniform and JPEG controls.
All methods receive the same native captures and observation windows.

Compare total bytes and packet-cap failures, pooled area-weighted active/ROI/
background RGB565 error, edge/threshold measures, temporal flicker and actual
HUD/text legibility. PSNR gains inside a rectangle do not prove better gameplay.
Report exact matching source IDs; do not hide quality loss behind different
presented subsets. No repeated precompressed-frame sequence can establish
native30-distinct-frame/s capture.

Prototype palette/lossless patches only in configured UI regions with explicit
fallback to transform coding. Charge palette, mask, mode and patch headers,
bounded parser/table memory and required reference traffic. Compare against
ROI quantization on the same glyph/real-game content before selecting it.

## Work package D: sender, firmware and FPGA handoff

1. Review the implemented GM01 golden packets and GF01 laboratory adapter,
   corrupt/partial/reordered fixtures and reference/ACK/abort rules. Freeze a
   target peer contract, then implement explicit capability negotiation and
   serialized feedback before integrating a Sunshine output mode.
2. Implement FPGA CP02 decode, inverse transform/map lookup, reference fetch and
   framebuffer publication against those vectors. Reuse the existing display
   and JPEG control. Prove real ingress/backpressure/CDC and ownership behavior.
3. Replay actual requests through the implemented reference/scanout memory path.
   Include refresh, stalled clients, reader drain, front/back buffers, cap pressure
   and reset. Compile/place/route the identified target before resource/timing claims.
4. Run the plan's1,800-distinct-frame software/RTL campaign with predefined phases,
   jitter and loss, then a10-minute physical30 fps test. Record actual presented
   IDs, frame age and p95/p99 tails, CRC/FIFO/memory errors, recovery, quality and
   input behavior. Preserve strict and drain counts; do not shift windows to pass.

## Ready now and remaining scope

The combined GM01 software decoder uses the word reader, with uniform-map
compatibility tests and a real two-candidate controller. Reproduce these tests
and the binary fixtures before target implementation. GF01 is an in-process lab
container; it is not firmware ingress or a deployed streaming transport. There
is still no installed custom Sunshine mode, ESP32 support or FPGA bitstream.
Existing JPEG telemetry/age/size policies can be tested with the matching
hardware independently. Hardware remains on another system; this study has not
programmed or measured that board.
