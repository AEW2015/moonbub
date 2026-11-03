# Game Bub application-specific codec: selected direction and gates

This plan follows the executable [iteration7 results](custom-codec-prototype-v7-2026-11-03.md).
It selects what to combine next; it does not claim the combined codec exists.
The current JPEG implementation remains the hardware control. New RG01 and
DT01 Python packets require their own decoders and cannot be sent to JPEG RTL.

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
| RG01 macroblock quality map | Add to a new residual profile | Improves declared-region error at similar same-frame byte budget, with visible background tradeoff |
| Word CP02 reader | Carry into software oracle | Exact valid-output and sampled malformed-rejection compatibility; measured receive cost reduction |
| DT01 independent dirty tiles | Exclude from gameplay base | Frequent cap failures and header/context cost; static tail is a possible separate UI mode |
| Two asynchronous replacement anchors | Later measured option | Extra reference, control decode, lifetime and retirement costs remain |
| Palette/lossless HUD patches | Next optional experiment | Could preserve colored glyph edges; no rate/quality/decoder win established yet |

Independent ROI is implemented as RG01; adding its map to temporal residual
coding changes reconstruction semantics and therefore needs a **new negotiated
profile/version**, not a silent MA01 flag. Do not claim ROI gains and temporal
rate savings multiply before actually encoding/decoding the combination.

## Work package A: executable combined reference

Build a new Python profile with an epoch, increasing capture/frame ID, explicit
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

## Work package B: a practical bounded rate controller

Replace the current237–395 ms offline ROI search. Reuse source transforms and
prepare at most a declared small number of real candidates (initial target:
one normal map plus one fallback). Count transform, entropy, candidate assembly,
selection and every rejected attempt in actual sender service. Never use an
unmeasured constant because the average key benchmark is favorable.

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

1. Freeze one combined syntax with golden packets, corrupt/partial/reordered
   fixtures, reference/ACK/abort rules and a standalone sender/decoder adapter.
   Add explicit capability negotiation before integrating a Sunshine output mode.
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

The word reader can be adopted into the **software custom-codec decoder** after
its tests are reproduced. ROI and dirty-tile methods are executable experiments;
there is no combined temporal-ROI sender, firmware or bitstream yet. Existing
JPEG host telemetry/age/size policies can be tested with the matching hardware
receiver independently. Hardware remains on another system; this study has
not programmed or measured that board.
