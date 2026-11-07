# Game Bub application-specific codec: selected direction and gates

## Active roadmap after V90 and the literature review — 2026-11-07

**V100 partial checkpoint: implementation evidence with explicit tool gates.**
[V100](cu66-v100/README.md) now runs the fresh V99 q16 fixtures through unchanged
RTL under two seeds. The standard-converted V91k component passes a separate
paired regression: transcripts, cycles, stage events and canonical bytes match,
and all 308 public ports are checked. Reconstruction leaf mapping repeats;
complete generic mapping fails at a converted loop iterator. Exact Artix-7
placement/routing is blocked by device support in Vivado 2025.2, while a second
2026.1 installation fails during startup. These are reproducible prerequisites,
not a qualified physical baseline. Keep 720×480, the frozen packet profile and
the 30-fps/under-10-ms goals. [Next RTL work](cu66-v100/next-rtl-experiments.md)
prioritizes synthesis compatibility and measured arithmetic/memory scheduling;
complete HUD/C2/shared-display/ESP32 integration remains open.

**V99 research RC1: fresh input and an RTL-compatible packet subset.**
The [V99 candidate](cu66-v99/README.md) selects restricted CS88/all-BR88 q16,
with key map0/Pgroup3, QM87 run2/inherit6 and a complete 49,152-byte cap.
Fresh CU66/GU66 and CS88 native parity each cover 360 frames; independent
BR88/C2 auditing checks 186,624,000 coefficients. All four complete q16 cases
fit (120 frames, maximum 36,119 bytes). The direct sender reproduces all 120
packets exactly and adds 32 synthetic cross-key ACKs. A bounded new-source
RTL-facing golden bundle is retained; V100 now supplies its RTL execution.
[Results](cu66-v99/results.md) identify Python HUD encoding as a major host
bottleneck. Original captures, native real-time sender, live ESP32/QSPI and
complete RTL/HUD/C2/display integration, memory/ports and physical qualification
remain open. The research profile is frozen; product promotion is not. Keep
the existing JPEG/MSV1 image as a separate supported fallback and continue the
V100–V110 mapping/P&R/timing phase with explicit incomplete endpoints.

**V98 partial checkpoint: reproducible common-input controls.**
The [V98 study](cu66-v98/README.md) measures 52 HEVC/AV1/JPEG/historical-GM01
software runs, 1,560 encode/decode round trips and the new supplied combat
sample selected at 30 Hz. Thirteen unit tests and an independent 6,459-check
audit pass. The [frontier and host timing](cu66-v98/results.md) use shared
RGB/YUV420/RGB565 arithmetic and actual complete bytes. Keep standard codecs
as software anchors and JPEG as the existing intra control. The tested GM01
points and unconditional global-motion option do not justify promotion.
That V98 encoder gap is now closed by V99's fresh CU66/CS88 path and independent
pixel audit. Original raw gameplay, verified
HUD readability, calibrated long-run tails, complete-path decoder/display
integration and physical 30 fps/under-10-ms decoding remain open. V99 candidate
freeze is gated by that work; V100–V110 mapping/P&R/timing plans are unchanged.

**V97 partial checkpoint: compact transport and live native-Rust/RTL ingress.**
The [V97 study](cu66-v97/README.md) adds explicit setup/profile/cap negotiation,
12-byte fragments, two aligned Rust staging slots, tokenized FIFO queries,
logical-length DMA and a separate ingress commit-ACK fence. Native Rust passes
23 tests and 138 shared wire cases; three strict C-ABI tests also pass. The
interactive gateway/RTL join completes 11 ingress transactions with exact bytes
and malformed-frame recovery; the combined regression passes 4,423,970 checks.
An independent 469-row header audit measures 3.528% fewer IPv4/UDP bytes after
setup overhead. [Results](cu66-v97/results.md) separate host preparation from
RF/device performance. The production worker remains MSV1, custom profiles are
opaque research only, and native-host execution does not emulate ESP32/Wi-Fi.
Production QSPI/UDP integration, Sunshine capture/service calibration and V97d
hardware/input/audio/UI gates remain open. Earlier full decoder/display gates
and V100–V110 physical qualification remain unchanged.

**V96 partial checkpoint: exact reference inventory and standalone materialization.**
The [V96 study](cu66-v96/README.md) independently verifies 1,371 research streams
and 11,105,100 canonical tile outputs across 457 retained sources. Bounded
64/256-entry dictionaries find 37,295/63,164 additional exact cross-position
copies (2.76%/4.68% of active residual blocks). Every copy is materialized;
no memory-read reduction or residual-packet compression is inferred. A new
COPY/CONST128/literal RTL engine passes 2,601 checks through the retained timed
SDRAM controller, including dynamic protection, cancellation/drain and retry.
The separate constant consumer model prices a potential 3.63% display-read
reduction, with generation work charged; it is not an RTL raster-reader join.
[Results](cu66-v96/results.md) separate those evidence scopes. V96d remains
open: integrate the supported descriptor path with complete reconstruction,
validation, HUD and shared continuous display, then measure full-path latency
and traffic before promotion. Existing codec, V91l/V92d/V94 gates and the
V100–V110 7-series physical implementation plan remain unchanged.

**V95a–c exact-palette software checkpoint qualified; no rate promotion.**
The [V95 pixel-palette study](cu66-v95/README.md) checks 8,226 plane variants,
2,542,828 independently decoded records and 4,113 complete native frames.
Canonical/reference pixels, HUD, RGB565, roots and seals remain exact; palette
tiles bypass coefficient reconstruction, so original-coefficient parity is not
claimed for those tiles. Minimum bytes remain 7,781,939 across 457 sources and
select no palettes. Work5/work15 bypass 2.15%/6.88% of active residual blocks for
3.47%/12.22% more complete bytes, with every selected frame below 49,152 bytes.
These are uncalibrated work/traffic tradeoffs. Keep the control; no palette RTL
or hardware milestone is qualified. Median diagnostic host preparation is
63.15 ms, excluding target generation. V95d's research decision is recorded;
product promotion, lossy clustering and wider-corpus validation remain open.
[Results](cu66-v95/results.md) retain the limits. Proceed to V96 actual addressed
reference/constant/display-memory service accounting, preserving the V91l,
V92d and V94 full-path gates and V100–V110 physical implementation focus.

**V94 remains partial: inline byte-rANS and an RTL symbol kernel qualify.**
The [bounded-rANS study](cu66-v94/README.md) tests two/four interleaved states
with precision 8/9/10, transmitted frequency models, independent readers and
5,484 complete native frame reconstructions. A separate rANS-rate Rice-parameter
search improves the local minimum by only eleven bytes across 457 sources;
retain the current control. Uniform tuned rANS fits every target-cap source
but averages more bytes than BR, whose largest source exceeds the cap.
The real RTL kernel checks 203,019 category/state/cursor outputs, including the
optimized winning context, with input/output stalls and cancellation/retry.
A same-edge cancel handshake defect was reproduced and repaired. This is an
entropy-kernel boundary, not complete FPGA frame decoding. tANS, calibration-only
fixed models, acknowledged caches, integrated memory/display costs and routed
qualification remain open. See [measured results](cu66-v94/results.md).

The separate no-refill bypass reduces matched kernel clocks by 17.93% on the
19 actual-source context encodings (21.67% on the combined synthetic/actual
55-vector set). It preserves exact state/cursors and recovery. The extra
normalization check can lengthen the multiply/update critical path; retain the
staged control until routed clock/resource results are available.

**V93 research lane: V93a–c software evidence qualified; promotion remains open.**
The [prefix/suffix and small-group Rice experiment](cu66-v93/README.md) adds
real EC93/CS93 bytes with independently decoded HY and SG controls. All 6,855
component packets and 4,113 complete packets preserve exact intended outputs;
1,710 independent grammar checks and 48 protocol/recovery checks pass.
Uniform HY removes 41.30% of uniform AB's arithmetic decisions for 3.101% more
complete bytes, with all 457 frames below 49,152 bytes. SG32 lowers plain bit
reads but its group headers increase complete bytes; reject it as the default
size policy on this corpus. Minimum bytes remain exactly the V92 result.
The bounded work policy is a counter-based experiment, not calibrated latency;
its extra metadata/traffic needs integrated costing before promotion. See
[measured results](cu66-v93/results.md). V91l and V92d remain open.

**V92 research lane: V92a–c software evidence now qualified; V92d open.**
The [per-context entropy study](cu66-v92/README.md) emits actual EC92 alternatives
for the four DC/AC streams in each plane, with an explicit CS92 frame profile.
All 21,936 candidates across 457 sources pass native coefficient checks;
independent Python verifies every distinct stream and its recombination.
All 1,828 selected complete packets preserve exact pixels, references, HUD,
RGB565, roots and seals. The bounded selector matches 1,871,872 exhaustive
combinations. At the same 15% byte allowance, context selection reduces remaining
adaptive decisions 1,444,956 → 464,660 while using 31,453 more complete bytes
over the corpus. This is a work/byte tradeoff, not a measured FPGA speedup.
Minimum-byte coding saves only 2,560 complete bytes versus the old AB38 control.
Host preparation is measured, including discarded candidates; full integrated
costing and the mixed-context RTL receiver remain V92d gates. See
[results and limitations](cu66-v92/results.md). The V91 control below is retained.

**Current checkpoint: V91l remains partial.** The
[bounded reference-tile grant experiment](cu66-v91l-tile-grant/README.md)
retains exact source bytes and display leases while granting up to four
contiguous 16-byte reference chunks per tile. Five modes preserve ten exact
RGB outputs and 10,250 checked SHA jobs; directed tests pass 2,056 entries
with 18 corrupted policy receipts rejected. Natural pair completion improves
98.832–98.837 → 97.043–97.051 ms, and delta commit 40.118–40.127 →
38.328–38.341 ms at assumed 100 MHz. Key RGB slows to 36.865–36.866 ms.
This changes read-credit weighting as well as locality; retain it as an
experimental tradeoff and compare balanced service before product selection.
Hardware 30 fps and complete under-10-ms decoding remain open.

The preceding native overlap checkpoint remains the control. The
[native shared-memory overlap control](cu66-v91l-overlap/README.md) passes
four natural modes plus a separate directed lease hold, preserving ten exact
RGB outputs and 10,250 checked RTL SHA jobs across two native source images.
The measured pair interval improves 18.89% (121.85 → 98.83 ms at assumed
100 MHz), while competing display reads increase delta decode to 40.12 ms.
The tile-grant experiment above now measures bounded scheduling/locality;
fixed-source cadence and complete latency remain unqualified. All-RTL HUD,
ESP32/transport and exact-device physical/hardware gates remain open.

The [physical BL8/base-RGB join](cu66-v91l-readbridge/README.md) advances
**V91l**, with a tagged read bridge, real controller/timed pins, the retained
canonical reader and the actual frozen base RGB565 converter. The bridge drains
eight controller words and two consecutive idle observations before ACK;
cancel/reset, held responses, invalid ownership and both read/write turnarounds
are checked. Native retained canonical reads improve from 15.654 to 8.467–8.468
ms at the modeled 100 MHz, with all bytes exact. These are read-consumer fences,
not complete validated decode latency.

The actual scalar converter is included. Its matched logical-service
comparison improves 3.500M → 3.067M cycles (12.35–12.37%), with eight complete
native base RGB outputs exact. Its timed controller/base-RGB path is about
33.6 ms/frame at assumed 100 MHz, slightly beyond the isolated 30-Hz budget.
The [direct owned-line consumer](cu66-v91l-burst-converter/README.md) now removes
486,000 redundant external byte leases per frame using the existing 48-byte
plane-line payload. It preserves all 518,400 consumed canonical bytes, 32,400
physical BL8 reads, registered chroma RAM/rounding and exact base RGB output.
The matched timed comparison is about **28.70 ms versus 33.61–33.63 ms**
(roughly 14.6% fewer cycles) at the same assumed 100 MHz. Exact ranges and
pairings are in its independent audit and summary. No additional payload memory
or new coding syntax is introduced; physical area/timing remains unqualified.

The Python model checks both native frames and a nonuniform edge fixture. The
RTL campaign uses both static converters, two seeds and both selected tAC
corners, with independent byte/RGB/pin replay and a separate cache-probe
ownership/error/recovery test. This is isolated preloaded base RGB conversion,
excluding semantic HUD, live reconstruction and shared traffic. **Hardware
30 fps and complete validated decoding below 10 ms remain open.** Being inside
a nominal component budget does not close either milestone.

The [serial shared-controller control](cu66-v91l-shared-service/README.md)
connects actual BR88 reconstruction, physical candidate writes, RTL validation
and same-memory base RGB. Its [physical accepted-reference extension](cu66-v91l-reference-reader/README.md)
now replaces the finite C++ reference responder with an RTL 64-byte tile reader
on the same controller. Each delta performs 7,806 reference requests, 31,224
physical BL8 reads and 249,792 additional x16 transfers. The source-derived
Python model checks three actual deltas; native RTL uses the selected key/first
delta pair. Full 64-bit reference identity and source-bank lifetime are retained.

Four native seed/tAC configurations pass eight exact RGB outputs and all 8,200
RTL SHA digests. The reference adapter and real-pin mux tests pass 1,920 check
entries; independent replay rejects 28 deliberate corruptions. There is no
canonical/pixel SDRAM preload. New reader payload is 64 bytes plus metadata,
with no whole-design mapping/fit/timing claim. Candidate writes, reference reads
and RGB are real controller clients in that retained control; its scratch and
native HUD endpoints remain software. The newer scratch-inclusive control below
replaces the scratch endpoint. Native decode/display overlap remains unqualified.

At assumed 100 MHz, key start→commit is 27.68396 ms and delta is
31.39967–31.39980 ms, then RGB is about 29.37 ms. Serial start→RGB closure is
57.04772–60.76776 ms. The observed packet-complete→commit windows are
27.30185 ms for the key and 31.12271–31.12284 ms for the delta, still excluding
physical scratch/native HUD/full-system costs. These are simulated partial
windows, not hardware latency or a completed 30-fps/under-10-ms result. Historical
logical-reference timing is not a matched speedup denominator.

The [physical packed-scratch extension](cu66-v91l-scratch-service/README.md)
now moves the remaining 128-bit memory endpoint onto the same actual controller.
It reserves a nonaliasing 256-KiB aperture in modeled SDRAM bank 3, preserves
video banks 0–2 and issues eight single-word WRITEs or one BL8 READ per full
16-byte line. Candidate writes, accepted-reference reads, scratch and display
are now RTL memory clients; native HUD interpretation remains software.
The same key/first-delta pair is checked with no canonical/pixel memory preload.
See its [measured results](cu66-v91l-scratch-service/results.md) for the four-run
cycle ranges and traffic totals, independent pin replay and exact SHA/RGB checks.
These newly charged costs are not a codec speedup or HEVC/AV1 quality change.
At assumed 100 MHz, delta start→commit is 33.460–33.465 ms, just over a
33.333-ms frame slot; serial decode plus RGB is 58.691–63.152 ms.
Decode/display overlap must be accompanied by reduced decode cost.

The [native decode/display overlap follow-up](cu66-v91l-overlap/README.md)
now runs the accepted key RGB consumer while decoding the next delta through
this same controller. An immutable source lease gates candidate aliases and
real publication drain. Four natural seed/tAC runs are separate from a fifth
directed final-pixel hold across delta commit. Its
[measured results](cu66-v91l-overlap/results.md) compare actual two-source
completion intervals, contended decode latency and exact source outputs.
A shorter pair interval does not prove 30-fps cadence: competing display
traffic increases delta decode time. The lease adds control/metadata, no frame
payload memory. Full native HUD and physical qualification remain open.

Next compare balanced read service against the bounded tile grant and
per-line controls, separating credit weighting from locality. Preserve the
natural overlap and scratch-inclusive serial controls. Keep the earlier finite-scratch
control as a historical boundary. Preserve accepted-bank/qcache history and atomic
publication; close all-RTL HUD and mixed entropy or negotiated fallback before
V91m. Actual ESP32 costs and exact-device physical qualification remain open.
Codec bytes, resolution, quality and HEVC/AV1 rate/quality comparisons are
unchanged. Sustained hardware 30 fps and complete validated decoding strictly
below 10 ms remain unproven.

The [bounded eight-byte tile-row writer](cu66-v91l-rows/README.md) remains the
qualified live-path scheduling control. Its static row mode preserves the live
key/delta canonical/HUD bytes, accepted-bank references, captured quantizer cache,
all C2 hashes and publication behavior. Candidate requests reduce from 560,640
to 70,080/frame; declared x16 candidate payload transfers reduce from 560,640
to 280,320. The payload register grows from one to eight bytes, without a second
row or overlap. Two strict seeds pass 16 validated commits, all 16,400 checked
RTL SHA digests and 39 integrated entries per mode/seed. Under the declared
candidate service, FAST uses 36.64–38.56% fewer cycles and SLOW 55.65–57.51% fewer.
See its independent audit/summary for exact source and bounds; prior FAST numbers
use a different response rule and are not its performance control.

**The standalone row-to-word gate is now qualified above.** Next connect its
actual controller schedule to the live path and shared clients, and implement
byte-control masking/RMW. The current controller uses write-single mode and has no byte-enable
request port. The comparison prices candidate responses only: frozen scratch
and 64-byte reference actors still have separate logical service. Price all
scratch/reference/candidate/RGB/scanout traffic on one finite x16 schedule before
using frame cycles to infer a hardware clock, 30 fps or complete under-10-ms
latency. The Python controller-cost model makes the missing command work explicit;
it is not integrated RTL timing. HUD decode/overlay and processor/ESP32 costs
remain required gates. Compare bounded two-row overlap only after preserving
this single-row control and implementing that service boundary.

The [live canonical/write-ACK follow-up](cu66-v91l-live/README.md) joins the
unchanged supported BR88 parser, entropy decoder, inverse transform and canonical
reconstruction directly to tagged candidate writes, actual C2/HUD/seal hashing
and validated publication. It targets the real c0/f0 key → c0/f1 delta chain;
the delta uses the key's actual accepted memory and captured registered quantizer
cache. Canonical replay no longer substitutes for the producer in this lane.
Two strict seeds pass eight validated commits, 8,200 independently checked RTL
SHA jobs and 4,485,120 reconciled write/ACK/hash deliveries. FAST start-to-commit
is 3,101,135 cycles for the key and 2,795,859 for the delta; this is not a
complete software/transport/display latency fence. See its [summary](../experiments/python-gamebub-v91l-live/summary.json) and
[independent audit](../experiments/python-gamebub-v91l-live/audit.json) for the
qualified current-source runs, cycle fences and exact coverage.

**V91l remains partial as an all-RTL milestone.** Native C++ HUD semantics and
start-header preparation precede the RTL fence. RTL HUD decode/overlay, mixed
entropy or negotiated fallback, shared memory/RGB/display service, actual ESP32
transport and physical qualification remain open. Component cycles are neither
sustained hardware 30 fps nor validated under-10-ms decoding.

The [tile-row comparison](cu66-v91l-rows/README.md) now implements those 64,800
canonical plus 5,280 HUD row requests with exact hashing and ACK ownership under
declared candidate service. That live lane has not yet joined the separately
qualified physical bridge or a shared controller; those promotion gates remain.

[V91l's validation partition](cu66-v91l/README.md) now qualifies real RTL C2
Merkle roots, semantic-HUD hashes, frame seals and atomic three-bank commit/
presentation. Two strict seeds validate 28 case/profile commits and compare
28,700 actual SHA-job digests with an independent oracle. Late content/receipt/
producer errors and 54 directed entries per seed preserve accepted state;
held writes, vblank and scanout drain gate commit/presentation. Actual HU25/HX
HUD semantic decoding remains native C++, and canonical input is replayed.
**The original replay checkpoint remains a historical control.** Its live
canonical and write-ACK follow-up is linked above; actual HUD semantic decoder/
overlay and full shared memory/display service remain open.
Reported RTL cycles exclude CPU HUD decode, fixture I/O and packet CRC parsing.

The [aligned line reader](cu66-v91k-lines/README.md) adds 48 logical payload
bytes behind the frozen chroma cache. It fetches each of the 32,400 canonical
16-byte lines once, replacing 518,400 byte transactions. Responses explicitly
cost eight x16 data beats plus response/stall service; this is not a widened
physical bus assumption. FAST conversion improves from 2,938,320 to 2,743,921
cycles (about 6.62% fewer), with exact output and physical/inner-byte drain
checks. Command-accurate SDRAM, arbitration/refresh, target timing and hardware
frame rate remain unqualified. No wire or quantization change is introduced.

[V91k](cu66-v91k/README.md) connects the actual BR88 frame path through
accepted-reference prediction, COPY/hidden CONST128, signed residual addition
and clamping to complete canonical Y/Cb/Cr candidate memory. Separate RGB565
RTL reads those **actual committed candidate bytes**, with native interpolation
and conversion checked against independent source-backed goldens. This is an
explicit memory-replay join, not a monolithic shared controller. Per seed,
12 successful rows compare 6,220,800 canonical bytes and 4,147,200 base RGB565
words; provisional late-CRC prefixes are checked separately. Six inputs include
four related native frames and two labeled synthetic cases. New reference and
candidate-memory service is charged; accepted read owners survive warm reset
and cancellation until matching ACK drain. No encoding or quantization changes.

The [registered chroma cache](cu66-v91k-cache/README.md) now qualifies against
the unchanged uncached converter: **1,440 logical payload bytes** reduce external
reads from 3,110,400 to 518,400/frame, sixfold fewer. FAST conversion falls from
10,022,400 to 2,938,320 cycles (**70.68247% fewer**), including startup and local
registered reads. Prefill increases first-accepted-read to first-word latency
from 28 to 4,328 FAST cycles. Two final seeds also check a nonuniform synthetic
edge frame and late-eviction cancellation; each path checks 9,676,800 RGB565
words across the combined main/diagnostic campaign. SLOW compares measured
runs under the same seeded service rules, with different absolute stall traces.

Continue the remaining **V91l HUD and shared-service integration** described
above, using the live producer/write-ACK control, then qualify finite transport/
memory/display integration at V91m. Further
memory optimization should compare actual bounded multi-byte reads and local
lookup overlap against this exact cache control. No physical clock or full
validated latency follows from converter-only replay. Hardware 30 fps and
complete validated decoding under 10 ms remain open.

[V91i2b](cu66-v91i2b/README.md) qualifies bounded registered-read refill
overlap with **5.1656% fewer FAST native-frame coefficient cycles** and
**4.2342–4.2450% fewer SLOW cycles** under the stated seeded service rules.
Two static configurations per seed preserve exact output; the disabled mode
matches all 506 previous case fields and 63,412 ordered tile records per seed.
The queue permits at most two queued/pending owners, with standalone legal
backpressure tests and integrated abort/reset coverage. Mode initialization,
wire bytes, quantization and the 98,304-byte packet staging budget are unchanged.
[V91j](cu66-v91j/README.md) now connects the actual BR88 frame path through
two bounded coefficient banks to the unchanged RTL dequantizer and two-pass
Q14 IDCT. Exact Python goldens qualify signed, unclipped residuals, including
quantizer placement, metadata, stalls and cancellation. V91k above adds accepted-reference prediction, COPY/constant handling,
reconstruction and base RGB565 conversion through actual candidate-memory
replay. AB38, HUD/content validation and atomic publication remain open.
Hardware 30 fps and complete validated decoding under 10 ms remain open.

[V91i2a](cu66-v91i2/README.md) connects **actual all-BR88 CS88 frames to the
frozen V91h coefficient pipeline**, retaining provisional modes/scales and
binding each dense coefficient to its plane, native tile, qcell and qscale.
Two final seeds each pass 22 FAST/SLOW rows, 4,058,368 exact coefficient/tuple
checks, 63,412 observed tile records and 10 directed checks. Four related native
frames have exact older goldens; synthetic cache/empty/error cases are separate.
Mixed AB38 frames reject before any child job. A third-plane CRC failure never
completes, and a clean retry works without reset. Packet staging explicitly
uses two 49,152-byte banks (98,304 bytes total), before tables/caches; fit is not
proven. The slowest tested integrated native coefficient path takes 1,140,868
cycles from frame start, with QM6 preload separately charged. V91i2b above
qualifies refill overlap against this control; V91j above adds actual RTL
transform integration on the supported BR88 path. Hardware 30 fps
and complete validated FPGA decode under 10 ms remain open.

[V91i1](cu66-v91i/README.md) passes the **restricted CS88 structural-admission
checkpoint**. Independent Python parsing and two strict RTL seeds agree on
86 vectors: 51 retained native packet variants, one structural-only all-COPY
case and 34 malformed/unsupported/state rejection cases. Each seed passes
14 interface/recovery checks and 156 plane-slot comparisons. The native
fixtures represent 25 distinct packet byte strings and eight cohort/frame
identities, not 51 new gameplay frames. The gate validates the supported
envelope, grouped modes, QM87 and bounded chunk descriptors before issuing a
held receipt; it cannot decode entropy, commit references or publish pixels.
The wire and quantization are unchanged. V91i2a above adds all-BR88 residual
dispatch and positional/quantizer binding; transaction ownership and actual
pixel/reconstruction/validation integration. Sustained hardware 30 fps and
complete validated FPGA decode under 10 ms remain open.

[V91h](cu66-v91h/README.md) qualifies **explicit synchronous packet-staging
RAM ports**. The static registered-read implementation preserves every packed
byte and dense coefficient with **0.1000% FAST and 0.0865–0.0921% SLOW added
actual-packet cycles** versus V91g2. This is a functional RAM-port promotion,
not a speedup or proven BRAM mapping. Two seeds pass separate static binaries,
720 exact legacy control metric values, 56 synchronous integrated checks
(including nine staging groups), 47 legacy checks and nine standalone checks per
seed. The independent Python port model and exact per-byte/purpose accounting
are retained. The slowest tested SLOW coefficient sum is 990,859 cycles;
complete validated latency and achieved clock remain unqualified. V91i1 above
adds outer structural admission; residual dispatch and V91j–m actual
pixel/reconstruction/validation integration follow. Hardware 30 fps and complete
validated decoding under 10 ms remain open.

[V91g2](cu66-v91g2/README.md) completes the bounded coded tile-preparation/
delivery overlap part of V91g. Two tile banks reduce actual-packet coefficient
service cycles **16.08% FAST and 16.30–16.31% SLOW** relative to V91g prefetch.
Both seeds preserve exact output, all 720 disabled-control metric values and RAW
scheduling in both modes. Each seed passes 47 integrated recovery checks plus
nine standalone checks; independent Python bank ownership and RTL audits are
retained. At that checkpoint, the slowest tested three-plane SLOW coefficient
sum was 990,205 cycles. That is not validated 10-ms decoding: achieved clock and the complete
pixel/reference/HUD/hash/publication path remain unqualified. V91h above
qualifies synchronous staging; V91i–m full-frame integration follows. Hardware
30 fps and complete validated decoding under 10 ms remain open.

[V91g](cu66-v91g/README.md) qualifies the **bounded needed-line read-prefetch
part** of its checkpoint: actual-packet coefficient service uses **0.94% fewer
cycles FAST and 5.18% fewer SLOW** than V91f. Both seeds preserve packed bytes,
dense output and all 720 disabled-control metric values; 36 integrated checks
per seed include eight read-prefetch recovery/hold tests. An independent Python
ownership reference covers bounded cache/ACK/output-hold events. Prefetch reuses
the four existing cache payloads and retains one accepted physical request.
V91g2 and V91h above qualify next-tile merge and synchronous staging. Complete-
frame integration follows. These are coefficient-processing results, not hardware
30 fps or complete validated decode latency.

[V91f](cu66-v91f/README.md) now qualifies bounded physical-write overlap for
the coefficient endpoint: **6.79–6.80% fewer actual-packet service cycles** in
the stated slower-memory scenario, effectively neutral under one-edge memory.
Both final seeds preserve every packed byte/coefficient and all 720 V91e control
metric values; 28 integrated recovery checks and nine direct scratch-interface
checks per run cover ACK, cancellation and semantic-error races. The independent
Python ownership reference checks bounded event sequences. Only one physical
request can be accepted at a time and two line owners are allowed. This is
scheduling progress with unchanged wire/quality, not hardware throughput proof.
V91g and V91g2 above qualify needed-line reads and next-tile merge overlap;
V91h now qualifies synchronous ports; complete-frame consumers/publication follow.

[V91e](cu66-v91e/README.md) now reconciles all active cycles and event fences
without changing V91d behavior. Both seeds exactly match all nine legacy metrics
on the original 17 cases, with three C3/f28 stress packets added. In the expanded
SLOW scenario, dense delivery/consumer hold occupies 46.67%, write ACK wait
9.76% and read ACK wait 10.88%. V91f/g/g2 above measure the subsequent
write/read/tile scheduling changes. Full-frame publication timestamps remain
unset; coefficient completion cannot be reported as validated decode latency.

[V91d](cu66-v91d/README.md) connects validated packet metadata to packed scratch
RTL, acknowledged external memory and dense coefficient output. A validity mask
removes 63 clear cycles per coded block: actual-packet cycles fall 34.43%/27.10%
in FAST/SLOW memory scenarios. Both final seeds pass exact images/output and a
repaired replacement/error race. At that checkpoint, two SLOW source sums
exceeded the 1,000,000-cycle reference budget before frame consumers. V91g2
reduces the coefficient sum below that reference; reconstruction/reference/HUD/
hash integration, hardware 30 fps and complete <10-ms decoding remain open.

[V91c](cu66-v91c/README.md) established complete BR88 chunk bytes/CRC and
autonomously runs DC/AC/raw in RTL. A separate Python packed-scratch prototype
matches every coefficient and reduces corpus peak storage from 658,432 B to
134,352 B. V91d above implements that store and metadata/credit handshakes.
V91h above replaces the packet staging array's combinational reads with explicit
synchronous ports; physical mapping is still unqualified.
V92 selection and the V100–V110 physical phase retain their planned scope.

The preceding controls remain frozen. [V91](cu66-v91/README.md) qualifies the
unchanged-byte word Rice reader; its real-stream symbol comparison is 605,514
versus 855,682 cycles. [V91b](cu66-v91b/README.md) adds derived DC/AC requests,
run/scatter checks and one sparse credit, with 685,304 versus 937,735 context
cycles. V91c adds packet work on the same inputs (751,062 versus 1,003,493
cycles). Full-corpus coefficient equality holds; native CPU word parsing remains
slower and is not promoted. These component fences do not replace complete
validated-frame decoding or physical 30-fps qualification.

Follow the [V91–V110 development plan](gamebub-v91-v110-development-plan.md).
Its [lettered execution path](gamebub-v91-v110-development-plan.md#lettered-execution-path-from-v91d)
now assigns V91e–V91m to functional integration, V92a–V99d to bounded codec/
transport selection, and V100a–V110d to physical implementation and ordered
hardware qualification. Letters are reviewable checkpoints, not calendar dates.
V91–V99 turn the [literature-review findings](literature-review-2026-11-06/README.md)
and [E1–E7 experiments](literature-review-2026-11-06/experiments.md) into a
qualified codec candidate: word-parallel Rice, finer/selective entropy coding,
bounded ANS, small host-selected palettes, exact reference reuse, real memory
service and a finite ESP32/QSPI arrival-service contract. Retain common-input
HEVC/AV1/JPEG controls and exact reconstruction/quality gates.

**V100–V110 are reserved for 7-series RTL technology mapping, placement,
routing and timing closure on `xc7a100tcsg324-1`.** The sequence covers a
reproducible baseline and constraints, elastic pipelines, LUT/carry parser
mapping, DSP48E1 arithmetic, BRAM/LUTRAM/SRL inference, fanout/control sets,
CDC/reset integration, bounded routing trials, integrated closure and hardware
qualification. Every change needs exact-output and recovery checks plus
mapped-resource and routed-timing evidence; higher assumed clock rates do not
remove memory/display service limits.

The goals remain **720×480 at sustained hardware 30 fps**, followed by
**complete validated FPGA decoding strictly under 10 ms**. Both gates remain
open. [V90](cu66-v90/README.md) supplies packet/model/native correctness evidence,
not physical signoff. The new roadmap defines each version's deliverables,
timing and publication fences, reports and 60/600-second hardware gates.

The sections below retain earlier checkpoints and historical next-step/status
statements; the active forward schedule is the linked V91–V110 roadmap.

## Historical research direction through V39

The [v39 checkpoint](custom-codec-prototype-v39-2026-11-05.md) extends exact
adaptive coefficient coding to both 48-frame causal histories: complete bytes
fall 11.98% / 10.07% versus CS37, with no pixel/reference change. Rank coding
among decoder-derived distinct predictors cuts spatial signaling about 81% / 75%
while preserving old modes and coefficient payloads. The finer bit/rank proxy
has a small complex-scene Pareto point but still regresses flat fixtures.

Next test spatial alternatives only when the entire reconstructed block equals
mode0 exactly, then accept only a smaller actual complete packet. This preserves
future reference semantics and rejects local-cost failures. Qualify fixed choices
on timestamp-defined additional scenes using the [source notes](v39-source-qualification-notes.md).
The arithmetic result still leaves a sampled 3.43–8.97× video-component gap to
native anchors at worse MSE; no hardware 30 fps or standards superiority follows.
The six-hour run is active, and JPEG/v20 remain unchanged.

The following v38 and older sections retain their historical evidence.

The [v38 checkpoint](custom-codec-prototype-v38-2026-11-05.md) implements direct
CS37 emission with exact 102-frame parity. Separate adaptive binary coefficient
coding reduces complete bytes 11.00% / 10.41% on two retained 12-frame prefixes
without changing coefficients, references or images. It needs a new CS38/AB38
profile and currently uses a Python proof adapter; logical arithmetic state is
not FPGA resource or throughput evidence. Native anchors remain ahead.

The spatial-edge pilot improves source MSE but regresses bytes by 15.63% / 7.15%.
Prioritize lossless coding of ranks among decoder-derived distinct predictors,
then signaling/context-aware selection. Tile top-left has no choice when all
predictors are equal. Keep the matched no-RDO spatial control distinct from
CS37's old RDO controller. Retain this negative result and its actual mode costs.

During the active six-hour run, extend arithmetic coding to longer and held-out
content, build a direct receiver/sender and quantify work distributions before
selecting it. Use the [prediction inventory](v38-prediction-inventory.md) to avoid
repeating old methods. Neither local byte improvements nor Python timings prove
physical 30 fps or superiority over HEVC/AV1. JPEG/v20 remain unchanged.

The following v37 and older sections retain their historical evidence.

The [v37 study](custom-codec-prototype-v37-2026-11-04.md) removes redundant CN36
proof encoding with exact wire parity, then integrates a zero-map predictor into
host analysis. Actual paired sender means reach 46.13 / 57.75 ms on this Python
host, still above 33.33 ms before receiver/transport/display. Original global
plane RDO/reversion decisions remain paid and preserved. These measured fixed-
policy improvements must not be multiplied with earlier component ratios.

Separate CS37 implicit hidden-block syntax saves another 1.51% / 0.28% complete
bytes with exact causal output, totaling 5.55% / 4.45% against matched fixed
legacy. The current grammar proof transcodes already encoded CN36 and is not
integrated into those sender clocks. Its explicit fixed profile needs a new
receiver; FPGA inverse bypass and native ESP32 support are still proposals.

Next integrate direct coefficient-to-CS37 emission and measure full sender
service. Use the profile to target native entropy/cost loops while retaining
exact global decisions. For larger compression gains, prioritize bounded causal
inter/SKIP/copy and spatial prediction with actual residual packets, then real
searched-motion integration and held-out long clips. After removing identical
HUD/bindings, the remaining custom bytes are about 4–12× the sampled native
remainder at worse MSE. Header-only work cannot close that gap. Compare quality,
latency and hardware resources under the [v37 deployment gates](v37-next-deployment-gates.md).
Preserve JPEG/v20; no firmware, bitstream or hardware was modified in v37.

The following v36 and older sections retain their historical evidence.

The [v36 results](custom-codec-prototype-v36-2026-11-04.md) implement the
canonical-reference hypothesis in new CN36 framing. Full/skip normalize hidden
reconstructed samples identically before committing them. Actual skip saves
4.10% / 4.19% complete bytes versus a matched fixed-policy legacy baseline,
with identical displayed frames on the two retained zero-motion-policy clips.
A directed fractional-motion probe separately preserves entire normalized
reference equality during hidden-to-visible prediction. This is stronger than
v35's local source guards, but does not prove unchanged old-profile motion quality.

Next integrate early hidden-coefficient suppression and precompiled support plans
into the real sender; the current proof pays full encoding plus extra skip work.
The separate exact mask component falls 4.29→0.111 ms after one-time setup, not
a measured whole-sender improvement. Then test an implicit hidden-block grammar,
searched-motion integration and long held-out scenes. Compare old-profile quality
separately from exactness within CN36. Retained original-input HEVC/AV1 points,
freshly redecoded with equal 80-byte binding budgets, remain smaller at better MSE.
Seek a measured latency/quality/resource advantage without assuming a bitrate win.
Use the [v36 acceptance checklist](v36-application-codec-acceptance-checklist.md);
preserve JPEG/v20 and require native sender, FPGA and ESP32 service measurements
before claiming physical 30 fps. No firmware or bitstream has changed in v36.

The following v35 and older sections retain their historical evidence.

The [v35 results](custom-codec-prototype-v35-2026-11-04.md) establish an exact
HM34 host optimization: validated reuse of already-paid parent/child maps and
winner-only serialization preserves all 184 components / 368 frames while
reducing paired component time 44.10→3.34 ms. Port and measure this exact path;
retain initial map-generation, HUD and full-sender costs rather than extrapolating.

Transform-aligned source masking reduces error substantially relative to v34.
Guarded causal core8 saves 4.33% / 3.09% complete bytes, but independent-control
MSE still rises 0.047% / 0.172%. All local guards pass. The expensive original
shadows on the changed histories are not the standalone control baseline.
Fresh HEVC/AV1 runs consume the exact accepted source trace and remain smaller
at better sampled MSE. Quality-neutral streaming has not been established.

Next test a **codec-domain occlusion/canonical-reference hypothesis** in a new
explicit profile: normalize fully hidden support-safe reference tiles identically
for both control and skip variants, then omit hidden residual work and prove
complete normalized-reference and visible-output equality across the entire
causal chain. Compare that new canonical baseline separately against the old
profile; do not assume global old-profile parity or a large compression gain.
The feature is not implemented in v35. Add held-out long gameplay and temporal/
boundary error before selecting a default. Preserve JPEG/v20 and qualify native
sender, FPGA memory/compute and ESP32 transport before physical 30 fps claims.

The following v34 and older sections retain their historical evidence.

The [v34 study](custom-codec-prototype-v34-2026-11-04.md) implements actual HM34
parent/child motion components, GM34 frames and CP34/HX33/JA34 atomic host
composition. Shared encoder work is integrated with 96 exact legacy base-packet
matches. Fixed 21,120-word HUD and inner geometry checks precede allocating decode.
The causal full-hierarchy policy saves 0.40% / 0.95% bytes, but costs much more
host work and slightly worsens complex mean error. No default promotion follows.

Prioritize **visible-error-aware source formation** next. Neutralizing hidden
detail under exact HUD saves 3.36% / 2.97% complete bytes at ~1% higher mean error.
A full chroma mask corrupts visible source pixels; preserving boundary chroma
restores precodec RGB equality. Next align masks to transform/interpolation
support and apply actual visible/temporal quality guards. Rerun HEVC/AV1 on the
same processed input and HUD; fresh v34 comparisons still favor the standards.

Keep sparse hierarchy and selective refinement as measured experiments. Reduce
exact HM34 planning work before adding search, and qualify longer unseen gameplay.
Then port the bounded profile and independent decoder goldens to native code,
implement negotiation/reset/retry/drain fences, and measure actual inverse,
entropy, prediction, HUD, memory and ESP32 transport service. The two-bank model
remains conditional on an unclosed clock; physical 30 fps and compression parity
remain open. Preserve JPEG and the v20 hardware handoff.

The following v33 and older sections retain their historical evidence.

The [v33 results](custom-codec-prototype-v33-2026-11-04.md) establish two useful
building blocks: actual lossless HUD run coding saves 35.77% / 17.75% versus v32,
and exact shared candidate evaluation reduces measured pair work 32.97%. Neither
is a whole-sender throughput result. Give the same HUD benefit to HEVC/AV1;
their sampled complete budgets remain lower at better MSE.

Sparse camera/grid search trades more bytes/error for lower work. Grid lowers
selected decoder prediction reads 8.47% / 28.79%, without changing the wire.
Guarded uniform 32→16 refinement saves 0.356% in 24 fixed-reference probes, but
raw motion metadata consumes its residual savings. **Next prototype actual
parent32 + sparse child16 syntax**, preserving vectors and decoded pixels and
paying every mask/escape/header/CRC byte. Follow with causal qualification and
confidence-triggered search. Do not add independent study gains.

Integrate shared encoder work and reproduce full-selector winners. Constrain a
new HUD profile to an explicit geometry/word budget before using small external
banks; its generic fallback grammar has a much larger memory domain. Then build
bounded entropy/run decoding, the prior two-bank inverse schedule and integer
prediction fast path with actual resource/cycle/memory-arbitration measurements.
Long unseen gameplay, native ESP32 transport and physical 30 fps remain gates.
Preserve JPEG and v20. Compression superiority over HEVC/AV1 is still unproved.

The following v32 and older sections retain their historical evidence.

The [v32 Python qualification](custom-codec-prototype-v32-2026-11-04.md) keeps
full resolution and exact HUD. Bounded Huffman HUD components save 0.089% / 9.83%
HUD bytes; the same savings must be credited to HEVC/AV1. Those sampled standards
still use roughly 37–40% fewer complete bytes at better MSE. New residual shrink
adds work and is dominated by earlier policies. Sparse wide-motion exceptions
save only 0.33% / 0.58% prospective complete bytes in a noncausal probe.

Prioritize shared exact rate/distortion work, causal game-motion/SKIP/copy modes,
longer unseen gameplay and temporal error checks. Implement two-bank overlap of
the existing inverse kernel before adding DSP lanes: the dependency model gives
6.20 / 7.39 ms average component service at assumed 100 MHz, but independent ports,
external stalls, fitted memory and routed timing still need RTL qualification.
Then integrate bounded entropy/dequantization and negotiated HUD syntax with
atomic reference/commit checks. Seek a measured quality/latency/resource advantage;
compression superiority and native 30 fps remain goals, not established results.
Preserve JPEG and v20. The detailed report records gates and all negative results.

The following v31 and older sections retain their historical evidence.

The [v31 isolated RTL kernel](v31-rtl-acceleration-2026-11-04.md) now exercises
actual fixed-point FPGA arithmetic: exact Q14 inverse, prediction add and clipping,
eight shared DSP-oriented MAC lanes, and zero/DC shortcuts. Three full behavioral
cases check 33,054 blocks each; directed four-state and mapped functional tests
check reset/backpressure and output goldens. Generic Series-7 mapping uses 8 DSPs
and no block RAM for this kernel. Clock-scaled component times are projections;
whole-decoder fit, routed timing and physical 30 fps remain open.

Next build the bounded EC26 coefficient reader and dequantizer, then fractional
prediction and reference-memory arbitration, color/HUD composition and bank fences.
Compare any HLS variant against the same integer/handshake goldens. Preserve JPEG.
The [ESP32 compact transport notes](esp32-compact-transport-plan.md) record the
versioned header/DMA/credit proposal and validation gates; firmware is not changed.

The following v30 and older sections retain their historical evidence.

The [v30 block/band prototypes](custom-codec-prototype-v30-2026-11-04.md)
keep full resolution, GM27 wire and the exact HUD. Strict source-aware AC edits
save 0.083% / 0.278% complete causal bytes with slightly lower measured MSE.
The budgeted variant saves 0.242% / 0.628%, with complex MSE rising 0.547%.
These gains are small and Python trial work roughly doubles; retain as design
experiments, not a product default. All 288 accepted pairs and 940 attempted
encodes are retained, including same-history incumbent shadows and all losses.

A separate fixed-Rice local sparse-run deletion oracle is exact and 21–25×
faster than equivalent full recounts after setup. It does not include parameter
reselection or prove accepted-stream savings. The isolated CP02 proxy disagrees
with actual EC26 marginal bytes in 132/172 sampled edits; neighboring edits also
have nonadditive costs. Avoid summing independent savings or reusing stale context.

Next combine cheap context screening, actual source-distortion checks and final
optimized costing; add bounded AC shrink/dead-zone candidates, and share the
incumbent's immutable work. Extend fresh long gameplay and temporal-error tests
before choosing a native host/FPGA implementation. Native service, ESP32 transport
contention, FPGA memory/publication timing and physical 30 fps remain unproved.
Preserve JPEG and the frozen v20 hardware handoff.

The following v29 and older sections retain their historical evidence.

The [v29 prototypes](custom-codec-prototype-v29-2026-11-04.md) keep GM27 wire,
720×480 coded / 720×405 active video and the exact HUD. Quiet-block search gating
reduces causal host base-policy work **277→149 ms / 301→211 ms**. Primary bytes
rise 2.19% and MSE 1.28%; complex bytes fall 0.15% with MSE rising 0.078%.
All 384 accepted CP27/JA27 pairs and 752 candidate encodes are retained.

Exact EC26 size counting now matches actual sparse runs, row-reset DC, Rice
escapes, padding and raw fallback. The first whole-plane guarded selector wins
no alternatives and adds work: retain the counter, reject that policy as a
default. A fixed-reference probe is insufficient; full causal histories revealed
a different rate/quality trade-off for quiet search.

Next generate bounded **block/band residual candidates** using actual EC26
costs and decoded-source RGB error, protect UI/HUD, and add confidence-triggered
dense search fallback. Validate fresh longer gameplay and temporal error tails,
then port the selected host encoder and FPGA reconstruction using the retained
goldens. ESP32 credit/reset and RF/QSPI contention, FPGA memory/publication
fences, and native source service still require qualification. Python service
remains above 33.33 ms; preserve JPEG and the v20 handoff.

The following v28 and older sections retain their historical evidence.

The [v28 runtime prototypes](custom-codec-prototype-v28-2026-11-04.md) preserve
GM27/CP27/JA27 while reducing work. Exact lazy planning avoids discarded CP02/
SP01 construction and keeps every accepted exhaustive packet/pixel unchanged.
Tap-aware interpolation is pixel-exact with2.46× faster predictor calls and
50.22% fewer logical reference gathers on the retained causal P inputs.

Mixed sample4coarse/sample2refine search is a new encoder operating point:
base-policy CPU662/687→276/300ms, body2.706/6.175Mb/s and MSE14.21369/26.31895.
It trades about3.3% more bytes and1.10%/0.55% more error for2.40×/2.29× less
measured host work. Full resolution and every exact HUD word remain mandatory.
All288 new transactions and564 candidate encodes are retained/replayed;25 tests
pass. These costs exclude capture/HUD/transport waits and do not prove30fps.

Next port the exact implementation improvements, prototype confidence-triggered
search effort/fallback, and test EC26-aware residual RDO against actual sparse
run/DC context. Keep causal histories, all losing work, complete-frame admission
and source/ref identity checks. Qualify native source service and FPGA memory/
publication timing, then fresh long captures and hardware. Preserve JPEG/v20.

The following v27 and older sections retain their historical evidence.

The [v27 unified profile](custom-codec-prototype-v27-2026-11-04.md) now emits
actual GM27/CP27/JA27 with compact fractional vectors, counted RDO and EC26
block-major coefficients. Fixed v26 histories preserve all pixels while cutting
complete bytes9.78%/7.01%. A real causal selector projects2.620/5.978Mb/s at30IDs/s,
with mean MSE14.05861/26.17453; primary error rises0.13% versus v26 while complex
error improves. All complete packets fit49,152bytes and carry exact HUD.

The decoder now uses bounded MV syntax checks rather than searching for the
encoder's optimal representation. Metadata checks defer coefficient semantics
to full decode before publication, avoiding repeated work in binding and ACK
checks. The new profile explicitly changes acceptance; old protocols stay frozen.

Next port/qualify this single arithmetic and wire contract, measure real memory
and native service, reduce host search, and integrate negotiated reset/credits/
fences. Extend temporal quality control on fresh long footage. Do not treat the
Python658/694ms source builds or34/52ms receiver measurements as physical30fps
proof. The custom stream still uses about1.5–1.6× the native HEVC/AV1 complete
bytes at sampled quality thresholds with the same HUD. Preserve JPEG and the
v20 handoff.

The following v26 and older sections retain their historical evidence.

The [v26 application-specific prototypes](custom-codec-prototype-v26-2026-11-04.md)
now supply three measured tools at720×480 coded /720×405 active:

- Exact CP02 bit counting preserves every v25 packet while reducing paired
  Python encode-prepared work359.5→39.7ms; shared analysis still totals54.7ms
  before HUD and transport. Port this host optimization independently first.
- EC26 sparse-band runs produce actual CP26/JA26 streams at2.859/6.328Mb/s,
  saving9.54%/7.82% complete bytes with identical displayed pixels and exact HUD.
  A four-cursor block iterator proves the coefficient order with one128-byte
  output block. Hardware ports/arbitration/clock timing remain unproved.
- Compact half-pixel vectors plus a causal actual-byte/current-source-SSE guard
  produce actual CP2F streams at2.905/6.446Mb/s with lower measured error. All
  losing work is paid; Python build cost652/676ms and four-tap reference fetches
  show why native/FPGA qualification is still required.

Next combine EC26 block-major coefficient streams and compact fractional vectors
in one negotiated codec, then remeasure full bytes, quality, credits, memory and
native/RTL service. The independent gains cannot be multiplied. Keep all exact
HUD words, complete49,152-byte admission and real reconstructed reference tags.
The Python fractional decoder currently re-encodes map alternatives to check
minimality; retain bounded syntax checks while qualifying a cheaper validation
policy for the native/RTL decoder.
The standards comparison still favors HEVC/AV1 by roughly1.6–1.7× body bytes at
sampled quality thresholds; neither compression parity nor physical30fps is
proved. Existing JPEG and v20 hardware support remain unchanged.

The following v25 and older sections retain their historical evidence.

The [v25 results](custom-codec-prototype-v25-2026-11-04.md) reduce complete custom
video/HUD bodies4.600→3.160Mb/s and10.287→6.865Mb/s, preserving720×480 coded /
720×405 active resolution and21,120 exact HUD words/frame, with improved measured
mean MSE on both48-frame windows. HD25 component/Rice/temporal coding and more
frequent reconstructed base references supply most useful gains; SAD-selected
block motion often loses against zero prediction plus residual RDO.

The goal remains HEVC/AV1-like compression with a bounded Gamebub decoder.
Reapplying the same new HUD to the native standards leaves a1.8–1.9× complete
body gap at sampled quality thresholds. No real-time/native/RTL30fps result
follows: the selected Python base encoder alone costs252/502ms per source.
Do not trade away resolution, silently relax exact HUD, or compare against the
standards' older HUD to declare the target reached. Keep49,152bytes as the
complete cap, distinct from any sustained network-rate budget.

Next gates, with actual bytes, reconstructed references and all losing work paid:

1. Exact CP02 bit counting to remove Python probe serialization, then native
   byte/image parity. Measure full service including HUD, pair and ACK handling.
2. Causal actual-byte zero/block/global choice, bounded half-pixel prediction
   and small intra modes. Compare each tool separately at fixed resolution.
3. Position/context-aware coefficient codes and integer4×4/8×8 transforms;
   bound map storage, DSP work, reference reads and external-memory arbitration.
   Add any reconstruction filter to both encoder and decoder reference paths.
4. In a separate experiment, specify a restricted standards decoder/tool set;
   reject unsupported syntax rather than assuming encoder presets guarantee it.
   Compare rate/quality and compiled resource/service costs against the custom
   path. Keep JPEG working while these studies remain unqualified.
5. Port the selected grammar and real credit/reset/ACK/fence rules, qualify
   at least1,800 fresh distinct30fps captures and then10 minutes on hardware.
   The new CP25 Python grammar is incompatible with frozen AR03/CP23 peers;
   the v20 hardware handoff stays unchanged until a qualified replacement exists.

The following v24 and older sections preserve their historical evidence.

The [v24 comparison](custom-codec-prototype-v24-2026-11-04.md) measures HEVC/AV1
against the exact v23 source windows with common YUV arithmetic and the same
exact HUD sidecar. Selected HEVCq32/AV1q48 hybrids need2.335/2.254 Mb/s on2600
and5.378/5.280 Mb/s on7200 versus custom4.600/10.287, while meeting or improving
custom mean active MSE. These are sampled operating points, not matched-quality
BD-rate or Gamebub decoder-fit proof. Bare codec savings are larger but do not
preserve exact HUD words; do not substitute them for the complete hybrid budget.

Owned/lazy analysis now preserves every CP23/JA23 byte while replacing203 source
SHA guards with one private snapshot per source. In one host trial the complex
build improves6.63% versus plain; no-retry work is near parity. Functional RS24
reset agreement covers one-sided reboot/loss and fresh key/full-HUD restart,
under explicit persistent-ledger and transport-drain assumptions.

Next prioritize bounded block motion/skip and exact-HUD temporal prediction,
fresh gameplay validation and integration with real frame/packet credits and
target service. Current native standards decoders run on the host; neither a
Gamebub HEVC/AV1 decoder nor physical30fps has been proved. Keep the v20 hardware
handoff and all prior comparison branches frozen.

The [v23 Python study](custom-codec-prototype-v23-2026-11-04.md) implements actual
HC22/HD22 packets inside CP23/JA23 joint transactions. Its fixed-image sequences
confirm the former v22 projections: complete bytes fall another 1.55–2.07% with
identical decoded images. All288 joint decisions fit the cap and preserve all
requested HUD words. The adaptive complex case now uses37 fine-background frames
and 11 coarse, with mean error30.08 versus 31.08 in v22 at 0.72% fewer bytes.

Shared prediction/forward analysis produces identical packets/ACKs/images on 96
paired decisions. Complex source work falls59→48 analyses /177→144 plane forwards,
but measured build time improves only3.90%, and the no-retry case slows3.23%.
The eager host context retains 5,184,000 array bytes plus an extra referenced-reader
descriptor and paid SHA guards. Next prototype immutable capture ownership/lazy
reuse, negotiated reset/rekey and a real bounded transport/shared-resource model.
No ESP32/RF/RTL/DMA or physical 30 fps claim follows from these Python results.

The [v22 Python study](custom-codec-prototype-v22-2026-11-04.md) now executes joint
video/HUD prepare/admit/commit, private decode, explicit write-drain/vblank gates
and whole-pair ACKs. All 192 native-source decisions preserve requested HUD words
within the complete cap. Its adaptive complex-scene policy improves mean error
34.09→31.08 at 2.74% more bytes; this is a quality/rate tradeoff with changed later
reference history. The fixed v20 profile trace is only an image/byte control.

A separate exact HD22 span grammar saves another 3.27–4.07% of native HUD bytes
at identical cache histories. Integrating those sizes projects 1.55–2.07% complete
savings, but the current joint dispatcher still implements HD21. Next implement
real HD22 joint dispatch, share prediction/forward analysis across paid map
attempts, then negotiated reset/recovery and bounded pipelined bank ownership.
No endpoint/RTL/DMA/ESP32 calibration or physical30fps proof follows from the
synchronous Python transaction. Keep the v20 hardware kit and JPEG baseline.

The [v21 display-cache study](custom-codec-prototype-v21-2026-11-04.md) now tests
acknowledged exact RGB565 HUD reuse without changing the v20 video base or YUV
prediction history. On 96 reused native-source updates, HUD bytes fall 9.04–11.29%.
Complete bytes including the new 57-byte binding container fall 4.67–5.42%; all
96 projected pairs fit the cap, with only 130 bytes of worst-case headroom.
Ten full-display goldens and all HUD words match exactly. Synthetic static/noise
controls remain separate: static gains are larger, while noise adds wrapper cost.

The next application-specific step is whole video+HUD candidate admission and
private atomic publication, followed by negotiated capabilities/reset, explicit
cache refresh and measured endpoint/memory service. The current cache model is
bounded stop-and-wait with two banks plus staging (126,720 pixel bytes before
scratch). It is not an ESP32 memory/ISA model or native endpoint implementation.
The complex forward projection remains 10.876 Mb/s at 30 scheduled IDs/s,
including two frame controls but excluding radio/retries/input/audio. V20's
decoder timing gap remains open. See [v21 integration tasks](v21-display-cache-integration.md).
Keep the following v20 hardware-development kit frozen while testing this extension.

The [v20 hardware-development handoff](custom-codec-prototype-v20-2026-11-03.md)
provides a portable C11 inverse oracle, complete packet and generated-tile golden
vectors, byte-level contracts, team prompts and acceptance gates. Start at
[hardware/gamebub-v20](../hardware/gamebub-v20/README.md). It is ready for offline
hardware/software development; a full FPGA decoder, native endpoint, fitted
resources/timing and sustained physical 30 fps remain open.

The mandatory-HUD component now carries all four requested regions on all 96
accepted frames while preserving 720×480 geometry and the 49,152-byte cap. The
complex scene needs 23 paid retries and coarser background quality: expanded
RGB565 channel MSE rises 27.03→34.09. Source/reference histories differ after
adapted publications; this is a coverage/quality tradeoff, not free coding gain.
Its forward data projects to 11.376 Mb/s at 30 fps before controls/radio overhead,
so the former 8 Mb/s assumption is insufficient for that case.

Actual reconstruction-fed inline tags match all 16 AR03 vectors and eliminate
4,147,200 native compact-bank reread bytes. Conditional matched service improves
67.6298→62.8622 ms (7.05%) with hash/padding/backpressure paid. All native profiles
still miss 33.33 ms. The conservative local plan is 107,504 bytes, not fitted RAM.
The native C11 oracle matches 101,667 blocks with UBSan; it is a component reference.

Next port/simulate exact kernels and tag/bank logic, integrate mandatory candidate
admission with FG19, implement profile/reset/recovery and calibrate real endpoint/
memory/scanout service. Revisit explicit acknowledged display-cache reuse to cut
static HUD bytes, and pre-granted capacity leases to hide per-frame request RTT;
both need fresh identity/generation/loss proofs and are not v20 implementations.
Keep JPEG selectable while the custom AR03 profile passes the acceptance gates.
Validate on fresh long footage before selecting operating defaults.

Historical [v19](custom-codec-prototype-v19-2026-11-03.md) added frame-slot grants,
FINISHED/RELEASE separation, exact sparse inverse and compact banks. Historical
[v18](custom-codec-prototype-v18-2026-11-03.md) supplied actual packet/controller
integration and AR03 traces. Their frozen branches remain reproducible; separate
component rates are not additive end-to-end throughput proof.

## Historical v16 contracts and service budgets

The [iteration 16 results](custom-codec-prototype-v16-2026-11-03.md) move the
AR02 application-specific codec toward an implementation contract. Portable
complete packets, reconstructed YUV banks, display words and binding-negative
vectors now let host/native/FPGA developers test the same outputs. Actual packet
coefficient traces feed an explicit cycle/memory budget; full-frame scratch and
publication hashing are now explicit planning costs rather than implicit free
work. These remain Python models and conditional architectural assumptions.

GM periodic-refresh tests preserve all four exact UI regions and full resolution.
Coarser refresh-key backgrounds save 16.07% on five matched independent-key bodies,
but change source quality and future prediction history; they do not save net
wire bytes in the measured coarse-30 case. Refresh-30 gives 26.6–27.0 modeled IDs/s,
refresh-90 reaches 29.2 and initial-only 29.8. Robust 30 fps refresh remains open.

Current order: freeze/expand the golden contract, qualify the ESP32 gateway,
then port bounded integer decode, replace full coefficient scratch with block/stripe service, prove canonical
inline-tag ordering, model burst/scanline deadlines, then design bank-local/sliced
refresh with explicit loss/publication rules. Qualify actual mapped memory ranges
and arbitration; the current 2 MiB functional-model window is not physical capacity.
The current ESP32 snapshot is ordered MSV1 JPEG with no enabled PSRAM; it does
not implement AR02/GF02. Calibrate bounded RX queues, CRC/driver costs, DMA heap,
RF bursts, QSPI/UI contention and actual FIFO backpressure before an end-to-end
rate claim. An assumed service budget is not ESP32 CPU/firmware emulation.
Use fresh gameplay for policy validation; the refresh regression window was
already used in v15. The report gives concrete assumptions and next gates.

## Historical v15 integration results

The [iteration 15 results](custom-codec-prototype-v15-2026-11-03.md) complete
one experimental AR02/GF02/AF02 path with acknowledged recent YUV references,
GM/SR inner selection and display-only exact RGB565 patches. One shared analysis
pays actual candidate work and complete cap validation before admission. UI
validation precedes bank publication; tagged feedback binds the outer body CRC.

GM + all four UI patches reaches 150 distinct native/decoded images in five
modeled seconds at 720×480, with 175 strict / 178 eventual presentations out of
180. Always-evaluate exact SR reduces base bytes 0.86–4.73% against matched GM
controls but lowers full-UI cadence to 28.8 modeled IDs/s on the long scene.
Prune-4 is explicitly lossy and drops to 21.6; full refresh every 30 IDs reaches
26. The fixed sparse gate enables SR on none of 174 preparations and adds cost.
Keep GM+UI+recent references as the first native port profile, exact SR optional.
These are conditional Python outcomes, not native/live or hardware 30 fps.

Next export bounded complete-packet/bank/UI/feedback golden and negative vectors,
port native encoder/decoder against them, and drive a cycle/memory model from
actual AR02 traces. Account for entropy, zero/DC bypass, inverse transforms,
upsampling, UI mux, burst arbitration and display deadlines. Explore DSP mapping
only with explicit cycle/resource budgets. Qualify refresh/loss recovery and
broader held-out gameplay before selecting production policy. See the v15 report
for ordered gates, evidence boundaries and exact reproduction commands. Installed
JPEG/GM01/standard Moonlight peers do not understand AR02/AF02.

Historical [iteration 14](custom-codec-prototype-v14-2026-11-03.md) introduced
the separate recent-reference, sparse-residual and bank-specific overlap studies.
Its gains are not added to the integrated v15 measurements. Old evidence remains
frozen; source-pinned publication/expiry and lost-ACK safety are retained in v15.

## Historical v13 and earlier rationale (superseded selection)

The following results and work packages are retained as research history. Their
references to “current”, “next” or “ready now” describe those earlier iterations.
For the current profile, qualification order and handoff, use the v17 section
above and the linked v17 report. In particular, the older below-30 UI result,
GM01/HG01/GA01 selection and v9 verification instructions do not describe v17.

The [iteration 13 results](custom-codec-prototype-v13-2026-11-03.md) implement
the candidate/commit integration that v12 lacked. Exact full-source reuse now
checks complete cap before commit, including cached rejections and fallback maps.
An independent four-region RGB565 cache reuses exact UI payloads even while the
game background changes: 176 region hits occur on changed full-source images.
All paired output bytes match controls. Native misses pay small overhead.

The finite measured-stage combination of source reuse and decoder bypass improves
delivery but still exposes substantial credit waiting. Its 180-distinct-image
held-out UI case improves from 119 to 121 strict presentations and 19.6 to 20.0
diagnostic IDs/s. A separate study integrates UI reuse and tests three host
transactions while retaining two receiver ingress slots and three framebuffer
roles. Credit changes require bounded/fault-tested admission and negotiation;
they are not an installed hardware default.

Keep plain GM as the native-source motion default: the cheap causal screen avoids
full BM search on all tested real images, trading away at most 2.61% possible
byte savings. Its large compression win remains synthetic. Progress the coherent
GM01/HG01/GF02/GA01 path through native ports and physical memory service before
adding a full standards decoder. More compression should use a separately
versioned ACKed-P reference/skip design with quality and recovery gates.

Qualification must report warm-up, rolling cadence, frame age, interior losses
and drain alongside strict capture-window counts. Last captures can legitimately
display during drain in a real-time pipeline; strict count alone is insufficient.
None of the Python/link assumptions proves live sustained hardware 30 fps.

The [iteration 12 results](custom-codec-prototype-v12-2026-11-03.md) preserve
720×480 and measure four improvements rather than reducing resolution. Exact
zero/DC bypass plus cached tables improves complete Python receive by 8–11%
with identical GM01/HG01 output. Exact source reuse improves repeated-frame
host preparation but adds a small miss overhead on distinct content. Actual
dual-motion selection saves little on real samples while tripling preparation;
use a cheap causal shortlist before enabling more search.

Controlled refresh scenarios add two strict deliveries per 60-ID native window
when removing the mid-window key, but no case delivers all 60 on time. New
scheduler code rejects ACKs after requested expiry and drains physical readers;
frozen v11 evidence is preserved with its known late-ACK issue documented.
The fixed service tables are conditional scenarios, separate from measured
per-call wall times and from target execution.

Next implementation order is native exact decoder bypass, preview/commit-aware
host reuse, causal motion/skip selection, then separately versioned ACKed-P
references and bounded UI change processing. Every step must retain complete
packet costs, reference correctness and 720×480/30 requirements. The detailed
v12 report defines tests, memory and integration gates. Standalone memoization
currently does not run through the finite controller; do not add its gains to
the refresh results or infer a hardware frame rate.

The [iteration11 results](custom-codec-prototype-v11-2026-11-03.md) integrate
actual HP01/HR01 selection with GM01 temporal prediction, then carry complete
HG01/GM01 bytes through GF02 and outer-content-bound GA01 in the finite model.
Temporal compact packets shrink34.44% versus HP01 at identical exact area.
A separate BM01 integer block-motion prototype produces mixed real results;
its sidebytes and search cost prevent a general improvement.

Keep **720×480 at30fps** as the primary coded target, preserving720×405
active16:9 game content. Resolution and frame rate remain product requirements;
512×288 and20fps are diagnostic comparisons, not the preferred delivery mode.
The current short720×480 replay remains below30 diagnostic IDs/s, especially
with exact UI patches, so the performance gap is an open engineering requirement.

Improve compression, decoder service and refresh scheduling at this resolution.
The [FPGA decoder study](gamebub-hevc-av1-fpga-plan.md) compares constrained HEVC
with custom inspired decoding at720×480; full standards support still requires
an exact supported syntax and measured whole-design fit. Smaller-picture results
remain useful for identifying bottlenecks, without satisfying the primary target.

The [iteration10 results](custom-codec-prototype-v10-2026-11-03.md) implement
bounded selective UI admission and exact GM01 fallback, plus a separate HR01
row-run/HG01 patch codec. Compact real-region packets shrink40.0→31.2kB mean
when adding row coding; all16 fit48KiB. These experiments are separate: the
selective GH01 policy does not yet emit HR01, and neither wrapper is in the
finite GF02/GM01 transport model. Charged BOX/transport CPU service retains
27–28 diagnostic IDs/s; hardware30fps remains unqualified.

Same-source, common-color HEVC/AV1 references expose a substantial coding gap:
at selected short-sample points native codecs use10–24times fewer coded bits
with higher active/ROI PSNR. This is not a universal ratio or decoder-fit claim.
The next compression work should target bounded motion/skip/reference decisions
alongside selective exact UI, rather than imply shared primitives equal standard
compatibility. Full HEVC/AV1 streams require matching decoders that are absent.

The [iteration9 results](custom-codec-prototype-v9-2026-11-03.md) connect the
GM01 temporal/priority codec to actual GF02 chunks and serialized GA01 feedback
in a finite software pipeline. Short diagnostic windows reach27–28 distinct
presented IDs/s with measured Python decode; they do not prove physical30 fps.
The optional GH01 lossless RGB565 UI wrapper works, but all36 broad-region main
samples exceed48 KiB. Two deliberately flat low-color probes fit17.9–20.0 kB.
Keep these findings separate: GH01 is not integrated into the GM01 pipeline.

The [iteration8 results](custom-codec-prototype-v8-2026-11-03.md) preserve the
combined codec/controller and golden vectors. Its GF01 lab reassembler has a
known delivered-pin ownership bug, reproduced and corrected by v9 GF02. Use the
new transport contract for further implementation; leave the old snapshot frozen.
Capability negotiation, native firmware/FPGA support, physical memory service
and hardware30 fps remain open. JPEG remains the hardware comparison control.

## Product target and split of work

The primary target is a720×480 coded canvas with720×405 active16:9 content,
30 distinct displayed frames/s, legible HUD/text and bounded frame age. Preserve
full-frame spatial resolution while optimizing coding and execution. The lower
resolution/FPS studies remain explicit comparisons and require an explicit
product decision before becoming a delivery target. Native display mapping and
fixed scanout traffic still need qualification. Rate alone is insufficient if
fresh input waits behind stale frames. Keep the existing JPEG path as a control
using the same captures, canvas, display and wire accounting.

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
| GM01 immutable anchor + CP02 residual | Implemented Python gameplay base | Combines temporal prediction and ROI map; actual finite feedback replay now tested |
| RG01 macroblock quality map | Implemented in GM01 Python residual profile | Improves declared-region error at similar same-frame byte budget, with visible background tradeoff |
| Word CP02 reader | Carry into software oracle | Exact valid-output and sampled malformed-rejection compatibility; measured receive cost reduction |
| DT01 independent dirty tiles | Exclude from gameplay base | Frequent cap failures and header/context cost; static tail is a possible separate UI mode |
| Two asynchronous replacement anchors | Later measured option | Extra reference, control decode, lifetime and retirement costs remain |
| HP01/GH01 selective UI | Implemented cap/deadline-aware Python policy | Compact real regions fit with exact565 output and byte-identical GM fallback; Python cost remains high |
| HR01/HG01 temporal UI | Integrated in Python selection and finite transport |34.44% fewer temporal compact bytes than HP01; exact565 and outer ACK binding checked |
| BM01 block prediction | Optional research candidate | Mixed real byte results and high search cost; not in finite HG/GM link |
| Constrained HEVC / full AV1 | Feasibility research only | Resource/state/memory/syntax qualification needed; no standard decoder supplied |

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

The implemented HP01/GH01 wrapper preserves original RGB565 words in configured
UI rectangles without altering GM01 reconstructed-YUV reference state. Main
campaign patches use8-bit palettes or RAW on many regions; all36 wrappers fail
48 KiB. Treat the two deliberately low-color flat probes as a separate favorable
case. Full wrapper receive/preparation costs include base validation and duplicate
parsing; small palette/overlay component costs do not establish real-time service.

The implemented **conditional small-region UI mode** follows this contract: declare exact regions and
measure actual unique-color/index cost plus every wrapper/patch byte. Admit a
patch only with whole-frame headroom and remaining deadline. Otherwise send the
unchanged GM01 base and record that lossless UI was not selected. Compare smaller
regions, row spans/RLE and repeated-patch reuse against this baseline, charging
state/control/memory traffic. Any reuse needs epoch, patch identity, ACK and reset
rules; it must not silently change the YUV predictor. Keep the low-color fixture
as a best-case control and require held-out antialiased/real gameplay evaluation.

## Work package D: sender, firmware and FPGA handoff

1. Review GM01 golden packets and the GF02/GA01 laboratory contract. The finite
   replay now exercises real chunk/feedback bytes and delivered-reader ownership.
   Freeze capability/version negotiation, reason enums, security and reset rules
   before integrating a Sunshine output mode. The new HG01/GM01 adapter now exercises actual outer-content ACKs; capability
   negotiation and installed target support remain absent. BM01 is separate.
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

## Next qualification sequence

1. Replace the new measured BOX/transport CPU model's independent-server
   assumptions with the intended shared-resource schedule. Live capture/readback
   is still absent; link/QSPI/vblank timing is assumed. Sweep phase/jitter/loss
   and long tails before rate claims. Keep every rejected call and reader paid.
2. Qualify the integrated HG01/GM01 path at720×480 under fixed replayed service
   traces, periodic/scene-aware refresh, true distinct-source capture and long
   fault/load/phase tests. Initial-key-only probes are not a production policy.
   First measure refresh/key/ACK stalls, native decoder/parser service and shared
   resource scheduling. Add paid actual-rate zero/block choice, per-block residual
   skip or bounded intra modes after BM01's mixed results. Charge every attempted
   mode and side byte; do not silently reduce resolution to pass. Keep UI patches
   bounded by complete-frame cost and report exact-area coverage. Native/JPEG/
   common-color HEVC/AV1 controls stay at the same720×480 target.
3. Collect native distinct30-fps captures covering scene cuts, particles, text,
   menus and dark motion, then run at least1,800 captures with fixed strict,
   diagnostic and drain windows. Preserve unselected and rejected capture IDs.
4. Port the frozen arithmetic and GF02 ownership/GA01 binding to native host and
   target parser tests. Use GM01 goldens for bit-exact comparison. Then implement
   CP02/inverse transform/map/refetch and framebuffer publication in target RTL,
   prove memory/CDC/backpressure/read-drain behavior and compile/place/route.
5. Qualify real simultaneous Wi-Fi/QSPI/input/display service and the10-minute
   physical30-fps campaign on the board. Record presented IDs, frame age, recovery
   and memory/FIFO/CRC errors; retain JPEG as a working comparison and fallback.

## Ready now and remaining scope

The combined GM01 Python decoder/controller, binary goldens, GF02/GA01 functional
adapter, finite deadline/read-pin replay and HP01/GH01 UI experiment are available.
The v9 verifier reconciles stored evidence, source pins, test logs and window/byte
accounting. There is no installed custom Sunshine mode, ESP32 decoder support or
new FPGA bitstream from these experiments. Existing JPEG policies can be tested
independently on the other system's hardware. No board was programmed here.

## V40 research checkpoint — 2026-11-05

[457-frame qualification and fresh HEVC/AV1 grid](custom-codec-prototype-v40-2026-11-05.md) reports exact arithmetic savings of 10.2732%, all 2,742 alternatives and 5,484 fresh native access units. Native codecs remain smaller on sampled comparable-quality walkthrough points; combat peak-rate controls are a subsequent study. No physical frame-rate or FPGA fit claim.

## V41 research checkpoint — 2026-11-05

[Global raster, host profiling and native peak-rate controls](custom-codec-prototype-v41-2026-11-05.md) retains the 13.31% flat-fixture win and zero gameplay spatial wins. HEVC VBV closes the coarse combat gap: 21.32% fewer bytes with no worse error on every frame. Direct bounded reception and shared host work are next; physical FPS and FPGA fit remain open.

## V42 research checkpoint — 2026-11-05

[Exact HUD planning and packed construction](custom-codec-prototype-v42-2026-11-05.md) preserves all 24 qualified HX32/HX33 outputs and measures a 4.006× host speedup in the paired HUD stage. HU25 generation is outside that timing; the optimization is shared by native/custom hybrid paths. Whole-chain profiling remains diagnostic, with an unresolved pstats aggregation mismatch. No compression gain or physical frame-rate result is claimed.

## V46 research checkpoint — 2026-11-05

[Direct receive, coefficient delivery and rate work](custom-codec-prototype-v46-2026-11-05.md) reports a 38.76% host receive-time reduction versus the old proof adapter on 577 retained frames, exact one-block coefficient delivery and a symmetry-based logical multiply reduction. V46 measures 902 fewer complete packet bytes (0.2281%) on 24 prefixes. Hardware mapping, full-pipeline timing and physical frame rate remain unproved.

## V50 research checkpoint — 2026-11-05

[Strict whole-frame motion guard](custom-codec-prototype-v50-2026-11-05.md) rejects all 192 tested same-reference grid proposals and preserves the fixed-zero outputs on 96 frames. The V48 integrated receiver remains slower in Python despite reduced coefficient staging. V49's tile-bank schedules are assumption-based component demand, not RTL cycles or a 30-fps result. Hardware fit and physical throughput remain open.

## V58 research checkpoint — 2026-11-05

[V58 evidence](custom-codec-prototype-v58-2026-11-05.md) records bounded transport, scanout, motion, and error-diagnostic studies. The latest cell16 zeroing probe changes no visible post-RDO coefficients and produces no packet savings; V53 motion savings carry higher cumulative source error. Device throughput and resource fit remain unmeasured.

## V67 research checkpoint — 2026-11-05

[V67 findings](custom-codec-prototype-v67-2026-11-05.md) and the [hardware handoff](gamebub-v67-hardware-research-handoff.md) summarize fixed-filter qualification, 69 sampled native points, forwarding constraints, exact tile-to-row hash delivery and independently verified cached canonical-tag profiles. Prioritize the bounded decoder/filter/hash architecture; do not deploy the tested mixed-motion quality trade as a quality-preserving default. Native HEVC/AV1 remain smaller at the measured quality gates. The current transport/backend is JPEG-only; physical throughput and FPGA/ESP32 fit remain unmeasured.

## V68 research checkpoint — 2026-11-05

[V68 findings](custom-codec-prototype-v68-2026-11-05.md) measure a zero-motion prediction-stage shortcut with unchanged packet format, receiver decisions and exact output. The optimization borrows validated readonly references for zero-vector P frames and uses compact immutable backing for key predictions. Stage timing is not whole-receiver timing, physical frame rate, or hardware memory fit.

## V69 native reference and connected base-layer RTL

[V69 handoff](cu66-v69/hardware-handoff.md) implements the next pre-hardware milestone: fixed-profile native C++ decoding, actual AB38/dequant/inverse/reconstruction/canonical-hash RTL, packet preflight, bank control and portrait-layout proofs. The paired native host campaign includes HUD and RGB565 composition and measures 7.60878 ms versus 97.33174 ms Python across 457 retained frames; no encoding/quality change is introduced. Keep [component scope and result gates](cu66-v69/component-matrix.md) separate from target implementation and hardware. Next, wire the qualified packet/qmap and HUD endpoints into real shared-memory/bank control and rotated scanout, then obtain exact-device timing/fit and physical ESP32/SDRAM/presentation measurements. General RTL simulation needs no DAP/JTAG access.
