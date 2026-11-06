# Post-review experiments and acceptance gates

These are proposed experiments after the [completed literature review](README.md).
They are not implemented codec features or hardware results. Keep V90 and its
artifacts frozen; create a separate experiment/version for each wire change.

## Shared controls and measurement contract

Use V88 AB38, V88 BR88 and V90 selected packets as controls. Retain the source
identity, quantizer, reconstruction rounding, content root/seal, HUD pixels,
RGB565 output and admitted-reference history. Representation-only experiments
must reproduce all of them exactly, including rejected/replayed packet behavior.
Exactness is to the current quantized output, not the original game capture.

Start with all 457 retained sources, but split training/calibration from testing
before tuning. These related clips cannot establish generalization. Add separately
captured games, text-heavy menus, scene changes, dark motion, noise/particles and
fast camera movement. Obtain raw captures before building new complete-codec
rate/quality curves. The combat source's native 25-fps cadence cannot establish
30 unique gameplay updates per second.

Record full serialized frame bytes, table/reset/header/padding/CRC bytes,
transport/ACK/retry bytes separately, live host encode/select time, peak memory,
finite ingress occupancy, every stall and the source of each result. A CRC
failure must preserve the accepted reference/model/cache and drain or cancel
outstanding writes before buffer reuse. Exercise resets at every parser state,
malformed lengths, truncated final words and delayed consumers.

Use separate latency fences:

- **Host:** capture-ready → selected packet ready, including actual candidate
  generation; offline oracle cost is not free.
- **Ingress:** first received fragment → complete qualified packet available,
  including finite ESP32/QSPI queues and retransmissions.
- **Validated decoder:** full packet available → content, HUD and publication
  checks complete, with all reference/candidate ownership changes safe.
- **Presentation:** publication → actual scanout latch and last required pixel.
  Report repeated/dropped frames separately from unique completed frames.

Report min, median, p95, p99 and max, with source counts and clock/cost assumptions.
The strict under-10-ms gate applies to every qualified validated-decode sample;
an average or a necessary-work floor cannot pass it. Presentation and ingress
remain in the end-to-end budget even when outside this decoder fence.

## E1 — Existing-byte BR88 word parser

**Purpose:** determine whether the one/two-cycle-per-bit sensitivity assumption
is hiding a useful, inexpensive parser architecture. Inspired by the
[FCCM design](https://www.cs.ucr.edu/~najjar/papers/2013/FCCM-2013.pdf); implement
our own capped-escape grammar.

1. Implement a Python 32-bit-refill / 64-bit-reservoir decoder with exact bit
   consumption and per-event traces. Treat 15 zeros as an escape, not an
   unterminated unary prefix. Handle the maximum 39-bit code at every word offset.
2. Replay all 1,371 retained BR chunks, raw fallback and malformed fixtures
   against the independent bit reader/native oracle. Include every allowed k,
   stream boundaries, nonzero padding and coefficient/range checks.
3. Build a single-symbol elastic RTL lane with ready/valid, refill credit and
   no speculative out-of-range reads. Compare 16/32-bit refill and 1/2 lanes.
   Add multi-symbol extraction only after measuring downstream demand.
4. Measure actual cycles for refill, prefix, suffix, escape, run accumulation,
   scatter and stalls; preserve pending AC lookahead and per-block DC resets.
   Reprice the causal graph using traces, not a scalar speedup multiplier.

**Gate:** identical accepted/rejected results and bytes, bounded stalls/storage,
then demonstrably lower full-path cost on the hard sources without hidden
regressions. A parser-only cycles/symbol win does not close the decoder gate.
Collect LUT/FF/BRAM/DSP/ports and achieved clock before claiming FPGA speed.

## E2 — Finer entropy choices plus selective bypass

**Purpose:** recover rate while eliminating feedback only where it pays.

- First allow AB/BR choice for each of four contexts in each plane: at most
  12 selectors, versus V90's three. Specify new version/method tags, lengths,
  resets, CRC coverage and raw fallback explicitly. Re-encode actual bytes;
  adding selectors to an AB38/BR88 packet without changing its grammar is invalid.
- Compare exact exhaustive selection on small cases against a bounded host
  search on real frames. Reuse precomputed coefficient/event work across
  candidates; do not encode every frame thousands of times in production.
- Separately split statistically useful prefixes from selected raw suffixes.
  Collect bit-position histograms on the calibration set; freeze bypass choices
  before testing. Raw suffix reads and arithmetic prefix reads need independent
  bounds, framing and terminal checks. This is custom syntax, not HEVC CABAC.

**Gate:** complete bytes and calibrated publication time improve the Pareto
frontier relative to AB/BR controls. Retain the 49,152-byte cap and qualify the
new grammar independently. Measure actual host throughput and memory, including
the cost of candidates that are discarded. Do not trade away exact pixels here.

## E3 — Table-bounded ANS challenger

**Purpose:** test whether a small statistical decoder can recover BR88's byte
penalty more cheaply than adaptive arithmetic feedback.

Start from the [pinned rANS](https://github.com/rygorous/ryg_rans/blob/c9d162d996fd600315af9ae8eb89d832576cb32d/rans_byte.h)
and [FSE](https://github.com/Cyan4973/FiniteStateEntropy/blob/9f30e0918f87bd835fa040d922a208d7b219e50b/lib/fse.h)
interfaces as independently inspectable references, not unbounded production
parsers. Compare direct run/level categories with symbol-plus-literal escapes.
Test 256/512/1,024-state tANS tables and byte-rANS with 2/4 states. All table
generation and reverse encoding belongs on the host initially.

Run fixed tables trained only on the calibration split, per-chunk tables with
actual metadata, and acknowledged cached-model IDs. Cache updates become visible
only after acceptance. An ID without its required accepted model must reject
and recover via an explicit reset/table packet. Four interleaved states incur
state/framing cost even when no per-symbol tags are needed.

Record each table lookup, multiplier width, state-update dependency, byte refill
and output credit stall. Model table-port replication when several lanes access
the same memory. Logical table bytes alone are insufficient. Four log-9 FSE
tables already add 8,208 bytes; they cannot silently share the previous 9,216-byte
pipeline staging allowance.

**Gate:** new full-frame wire and decoder frontiers, exact coefficient/native
parity, deterministic resets, bounded worst-case code/model construction, then
RTL evidence. Reject a method that wins kernel throughput but loses full
publication time or board fit. No Python-versus-RTL speedup is an ASIC/FPGA result.

## E4 — Decoder-aware host policy and receive-buffer contract

**Purpose:** turn component gains into a deliverable 30-fps stream. This applies
the [DERDO optimization principle](https://arxiv.org/html/2203.01099v1) and a
Game Bub-specific arrival/service contract inspired by
[VESA's HRD](https://vesa.org/wp-content/uploads/2024/03/HRD-Buffer-Model-Intro121026.pdf).

Keep distortion fixed for entropy changes. Use an explicit byte cap, a calibrated
decoder-completion predictor and queue/service constraints, rather than minimizing
feedback count or treating V90's serial work score as time. When pixels change,
compare `distortion + lambda_R * complete_bytes + lambda_C * decoder_cost`,
subject to hard packet/buffer/latency limits. Fit weights on calibration data
and publish held-out errors, especially underestimated slow frames.

Simulate correlated Wi-Fi burst/delay traces, ESP32 copies, QSPI transactions,
parser consumption and SDRAM/display arbitration. Negotiate actual buffer
capacity and permitted outstanding fragments. Put the same rejection/drop/
resynchronization rules in host and receiver. Missing a deadline must not cause
an unbounded queue of stale game frames or a reference mismatch.

**Gate:** trace-verified bounds on every queue and ownership state; conservative
service parameters calibrated on the target before claiming sufficiency. A
49-KiB packet cap or adequate average Mbps alone does not guarantee this.

## E5 — Small palette/prediction combination for actual game content

**Purpose:** test the new [HLC lead](https://arxiv.org/html/2603.29864v1) without
porting its entire codec. Its reported decoder area is not the cost of a tiny
optional palette path.

Compute 2/4/8-entry palettes on the PC; compare literal indices, left/top runs,
reused palette IDs and explicit escapes. Begin with existing 8×8 canonical
tiles and exact colors; keep current reconstruction/hash/HUD semantics.
Admit palettes by actual full cost, with residual/raw fallback for unsuitable
gameplay. Avoid paying a large palette header on high-color blocks.

Only then compare a 16×4 or stripe profile: retiling changes context and storage
ordering and requires an explicit adapter to canonical tile/hash order. In a
separate lossy study, allow clustering and tune on held-out raw sources with
fixed HUD/text and temporal-error gates. The host computes clusters; no reason
exists to reproduce HLC's encoder cluster search on the receiver FPGA.

**Gate:** a game-content win beyond flat fixtures, complete metadata included,
no extra quality loss for the exact lane, and no hidden full-frame staging. Our
earlier palette trials are negative controls. Separately report how often
palettes are selected and whether the worst frame gets better or worse.

## E6 — Bounded exact copy and grouped memory layout

**Purpose:** borrow screen-content reuse and burst-friendly layout while
respecting our publication and scanout ownership rules.

Before adding more motion, count exact tile matches in the *accepted* reference
and within a bounded already-validated dictionary. Signal source addresses and
charge reads, descriptors and any destination writes. Cross-position copying
does not automatically fit the current three-slots-per-position alias scheme;
arbitrary source aliases require their own lifetime/reference-count proof.
Materialize copies until that proof exists. Avoid same-frame dependencies first.

Compare group-aligned burst storage with existing layout using actual addresses,
row openings, refresh, read/write turnaround, map ports and continuous raster
reads. Schedule the fixed hidden CONST128 generator and its hash/display
consumers explicitly before combining it with V90. Keep the physical address
window unchanged until a compacted layout is independently verified.

**Gate:** exact pixels and root/seal through abort/replay/held-scanout histories;
lower full-path latency with no extra display underruns. A memory-busy reduction
is necessary service evidence, not a completion-time saving.

## E7 — Standard-codec and alternative-transform controls

Repeat HEVC/AV1 comparisons on identical raw input, crop, chroma, bit depth,
timing, HUD handling and quality gates. Pin encoder/decoder versions, presets,
threads, reference limits, filters, GOP, scene-change policy and no-lookahead/
reorder choices; inspect emitted syntax. Measure host latency, first-frame
startup and worst packet, not only mean rate. Separate CPU/native hardware
decode from a custom FPGA implementation estimate.

Retain HLC/JPEG XS/DSC in the study with their correct rate ranges. Include
JPEG/intra controls for reset/recovery and small wavelet or bit-plane residual
experiments only if they improve an actual frontier. Any transform change is
a new lossy profile; recompressing CU66 output cannot establish superior quality
on the original game. Decoder block geometry, transforms and raw memory traffic
must be included. An encoder-search accelerator is not decoder evidence.

## Promotion to hardware

Promote the simplest Pareto-winning candidate with an independently parsed wire
spec, finite memory/ports, native golden vectors, adversarial RTL traces and a
whole-design placed timing/resource report. ESP32 telemetry must include Wi-Fi
and QSPI together with UI/audio/input active; report clocks and DMA/copy sizes.

Pass 1,800 **distinct** frame identities at 30-Hz releases over 60 seconds, then
18,000 over 600 seconds, with exact intended displayed identities/pixels/HUD,
bounded queues and zero underruns. Replaying a short clip or counting repeated
LCD refreshes cannot meet unique-content coverage. Validate complete decode
under 10 ms separately under the frozen fences. Keep recovery and transport
loss/delay trials separate from the zero-drop qualification run.
