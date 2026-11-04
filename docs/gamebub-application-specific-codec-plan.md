# Game Bub application-specific codec: selected direction and gates

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
For the current profile, qualification order and handoff, use the v15 section
above and the linked v15 report. In particular, the older below-30 UI result,
GM01/HG01/GA01 selection and v9 verification instructions do not describe v15.

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
