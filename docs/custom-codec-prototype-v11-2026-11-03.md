# Iteration 11: temporal UI integration, block prediction and reduced targets

Iteration 11 extends the [application-specific codec plan](gamebub-application-specific-codec-plan.md) and preserves [iteration 10](custom-codec-prototype-v10-2026-11-03.md) unchanged. It delivers actual selective HP01/HR01 patches over temporal GM01, a separate bounded block-motion codec, and actual GM01/HG01 transport through the finite GF02/GA01 software model. It also investigates a more complex HEVC/AV1-style FPGA architecture and reduced resolution/frame-rate targets.

The handoff branch in both Sunshine and moonbub forks is **`handoff/gamebub-app-codec-v11-20261103`**. This report records completed Python evidence; installed peers do not support these new profiles. No BM01/HG01 experiment is HEVC/AV1-conformant.

## Selective row patches now share temporal prediction

The [hybrid study](../experiments/python-game-hybrid-study/README.md) integrates the frozen HR01/HP01 actual-byte chooser with bounded selection. It charges every candidate, including losing modes and rectangles rejected by the complete **49,152-byte** cap. Selected patch bytes are validated and reused during HG01 assembly. With no fitting patch, output is the original GM01 byte string; an oversized base explicitly rejects.

Cheap sender preflight checks header/map/length/CRC without decoding coefficient entropy. Identity extraction is a routing helper, not a decode-success certificate. The receiver enforces its cap and validates every patch before one atomic GM01 decode. Patches affect displayed RGB565 only; they never enter the immutable reconstructed YUV prediction anchor. Malformed patch/base/session and oversized input cannot publish a new anchor. Late observed-budget fallback retains all work already performed.

The campaign uses two 60-native-frame windows from one second, 16 held-out key frames from four seconds, two noisy synthetic UI fixtures and two separately labeled flat glyph fixtures. The same actual base is shared across four independent policies. There are **560 decisions: 552 admitted and eight explicit noisy-base rejections**. Every selected word is exact original RGB565; unselected pixels match the corresponding GM01 base. Seven tests and the persisted-result verifier pass.

|120 temporal inputs|Mean complete bytes|Mean exact pixels / common broad area|Mean preparation / receive|
|---|---:|---:|---:|
|Broad HP01|23,530|15,360 /32.43%|24.21 /26.70 ms|
|Broad adaptive HP01/HR01|29,695|46,827 /98.87%|36.25 /28.98 ms|
|Compact HP01|24,289|21,120 /44.59%|23.94 /27.15 ms|
|Compact adaptive HP01/HR01|15,924|21,120 /44.59%|30.26 /27.71 ms|

Compact adaptive reduces complete bytes by **34.44% at identical exact area and quality**; maximum packet size is 33,962 bytes. Broad adaptive fits both broad rectangles on 118/120 frames. Its larger mean packet buys more exact area, rather than indicating worse patch compression. Common broad RGB565 MSE falls from 9.679 to 0.179. The two failed second-patch attempts remain paid.

Held-out compact means are **40,048 →31,216 bytes**, a 22.05% saving at identical coverage. Main admitted outputs are all HG01; byte-identical raw fallback and mixed GM01/HG01 key/P behavior are unit-tested rather than claimed as native-game fallback-frequency evidence. These configured rectangles are not verified real HUD locations. Exact RGB565 retains RGB888 quantization loss. Mean compact adaptive full service is 57.97 ms: this component experiment does not prove 30 fps.

## BM01: a separate block-motion prototype with useful negative results

The [block study](../experiments/python-game-block-study/README.md) adds a separate BM01 format without changing frozen GM01. It searches 25 even integer vectors within ±4 luma pixels per 16×16 luma/8×8 chroma block, using deterministic full-block SAD against the **ACKed reconstructed key**. Chroma follows half the even luma vector. Bounded vector payloads use the shorter dense or sparse representation, and complete bytes include map/vector/header/CRC overhead.

All 612 actual packets decode to independent reconstructed expectations; keys agree with GM01. The campaign includes two 60-frame 720×480 windows, two 30-frame direct-native 512×288 windows, and separate static/opposite-motion/noise-cut fixtures. Ten tests cover parser bounds, independent prediction, key ownership, loss/ACK/expiry/session behavior and recovery. This is immediate-ACK algorithm evidence, not the finite link integration used by GM01/HG01.

|Real-source window|GM01 mean bytes|BM01 mean bytes|Change|GM01 /BM01 preparation|
|---|---:|---:|---:|---:|
|720×480 combat,60 frames|8,802|9,137|+3.8%|22.15 /55.09 ms|
|720×480 second,60 frames|12,026|11,772|−2.1%|19.61 /50.68 ms|
|512×288 combat,30 frames|5,271|5,447|+3.4%|8.85 /22.18 ms|
|512×288 second,30 frames|6,943|6,475|−6.7%|9.47 /22.69 ms|

Vector/search cost can exceed residual savings. These same quantizer maps do not guarantee equal distortion: recorded active RGB565 PSNR changes range from −0.008 to −0.127 dB on these real windows. The frozen global-motion controls choose zero throughout the real windows, but differ on synthetic motion fixtures. BM01 should therefore remain an optional research candidate, not a universal GM01 replacement.

Whole-P zero-residual packets omit coefficient payloads only after all three actual transforms/quantizations yield zero. Seven static-128 P frames demonstrate the syntax; no real packet uses it. Contrived opposite-moving halves favor BM01 strongly, while noise/cuts do not. Neither favorable synthetic motion nor static results establish 720×480 high-entropy admission or free host work. No per-block skip map or recent-P reference chain is implemented.

## Actual GM01/HG01 bytes through the finite link

The [hybrid-link study](../experiments/python-game-hybrid-link-study/README.md), [main results](../experiments/python-game-hybrid-link-study/results.json) and [compact summary](../experiments/python-game-hybrid-link-study/summary.json) now carry actual complete GM01 or HG01 bodies through GF02 chunks, reassembly, modeled QSPI, full decoding, reference publication and GA01 feedback. This closes iteration 10's separation between row-patch experiments and its GM01-only finite service model. BM01 remains separate.

The main run has **12 cases and 720 scheduled capture-policy IDs**, with **670 actual preparations and 669 successful decodes**: 439 prepared HG01 bodies and 231 GM01 bodies. These reuse two related native source windows; 720 policy IDs are not 720 independently captured gameplay images. Twenty tests include corruption/session/geometry failures, outer identity binding, read-pin ownership and fault recovery.

GA01 binds the **outer** GM01/HG01 body tag and GF02 epoch/frame identity. A tag covering only the nested GM01 cannot acknowledge an HG01 UI packet. Full decoding and the matching serialized feedback result determine publication/release. The functional outer-feedback result verifies this distinction. Pools/credits/read pins are finite logical state; they are not a physical DMA/CDC memory implementation.

Baseline assumptions include independent virtual servers charged with measured preparation, decode, BOX resize, packetization, per-chunk feed and feedback build/parse; ideal 8 Mb/s forward/reverse links, 160 Mb/s QSPI, 10 ms feedback propagation, 60 Hz vblank, a 150 ms frame-age limit and keys every 30 capture IDs. Source acquisition remains unmeasured. These are scheduled host-call costs, not concurrent native target execution.

|Baseline policy|Combat strict /eventual out of 60|Second strict /eventual out of 60|Diagnostic IDs/s, combat /second|
|---|---:|---:|---:|
|720×480,30 target IDs/s, GM01|54 /55|54 /56|28 /28|
|720×480,30 target IDs/s, adaptive UI|49 /51|40 /43|25 /21|
|512×288,30 target IDs/s, GM01|59 /60|59 /60|30 /30|
|512×288,30 target IDs/s, adaptive UI|58 /59|58 /59|29 /29|
|512×288,20 target IDs/s, adaptive UI|60 /60|59 /60|20 /20|

“Strict” counts presentation within the capture window; “eventual” includes drain after that window. The diagnostic rate covers only the trimmed steady window. A 30 diagnostic value is therefore not proof that all 60 IDs met presentation or age requirements. At 20 target IDs/s, the same60 IDs are replayed over three seconds rather than two; this is not a live frame-decimation experiment.

The two 512×288 fault cases deliberately lose an initial-key chunk or ACK. They recover eventually but present only54/52 IDs, with53/51 inside the capture window. A stable mid-window diagnostic does not erase those losses. Main baseline periodic-refresh behavior remains recorded unchanged.

### Separate initial-key-only refresh probe

[Refresh probe results](../experiments/python-game-hybrid-link-study/refresh-results.json) disable periodic refresh for **only two short 512×288 adaptive-UI 30-target-ID/s cases**. Both report30 diagnostic IDs/s. Combat presents58 strict/59 eventual with one initial latest-frame replacement; the second clip presents59 strict/60 eventual. The main periodic-refresh baseline stays29 diagnostic IDs/s on both clips.

This is a promising policy hypothesis, not a demonstrated causal speedup: refresh policy **and remeasured host service times** differ. A two-second initial-key-only probe does not validate long motion, scene cuts, recovery or stale-reference quality/cap behavior. It is not the selected default. Repeat paired runs with retained service traces, explicit refresh/scene-cut policies and longer held-out content before changing that policy.

## More complex FPGA codecs and a smaller first target

The new [HEVC/AV1 FPGA investigation](gamebub-hevc-av1-fpga-plan.md) separates three routes: a constrained conformant HEVC stream subset, a substantially larger complete AV1 implementation/port, and a custom HEVC/AV1-inspired format. BM01/HG01 belong only to the custom research route. Their transforms or block prediction do not confer standard interoperability.

The [architecture model](../experiments/python-game-decoder-architecture-study/README.md) records memory/traffic/transform arithmetic with nine tests and retained provenance. The cited public openav1 implementation exceeds this A100 FPGA's resources unchanged, according to its author's reports; that does not prove every serialized low-resolution HEVC/AV1 decoder impossible. A new complete design, exact supported syntax, independent reconstruction, synthesis/routing and memory-service evidence are necessary. DSP count alone is insufficient: entropy dependencies, references, filters and memory access can dominate.

Use **512×288 at 30 fps** as the first reduced-resolution software-model target, and **20 fps** as the secondary performance/bandwidth point. Keep the assumed720×480 60 Hz display independent; smaller coded video still needs scaling and display service. The actual link model supports512×288 as a more promising next target than720×480 UI streaming, while retaining its short-run/host-timing limits.

|Architecture arithmetic scenario|One-reference frame allocation|No-halo /independent-halo payload|
|---|---:|---:|
|720×480 coded 30 fps,720×480 display 60 Hz|2.307 MiB|110.864 /126.538 MB/s|
|512×288 coded 30 fps,720×480 display 60 Hz|1.740 MiB|84.115 /90.802 MB/s|
|512×288 coded 20 fps,720×480 display 60 Hz|1.740 MiB|70.567 /75.025 MB/s|

These are parameterized capacity/average-traffic calculations, not a memory-controller schedule or codec fit. Assumptions include one reconstruction, one reference, two display buffers and explicit staging/conversion traffic; scratch/stride/context/ownership overhead is additional. The finite link has three metadata framebuffer roles, a separate assumption. A third physical720×480 RGB565 output buffer adds691,200bytes/0.659MiB, raising the512×288 one-reference allocation to about2.399MiB before other workspace. The1.740MiB two-buffer scenario is not a whole-pipeline fit proof. The current physical memory path and 2 MiB functional coverage need qualification. Lower resolution reduces work and buffers; it does not proportionally shrink an unchanged full standards decoder.

## Next work and evidence gates

1. Preserve the periodic-refresh baseline. Compare refresh policies using identical stored service traces, scene cuts, longer held-out motion and explicit error/recovery/cap/quality measurements. Retain both strict/eventual counts and frame-age tails.
2. Continue512×288 30/20 comparisons with true live selection/acquisition assumptions, JPEG controls, matched quality and same-area UI priorities. Separate distinct source images, scheduled IDs and display repeats.
3. For custom coding, try actual-rate selection between zero/block prediction, then bounded per-block residual skip or intra/fill modes. Charge all searches/transforms and side bytes; keep independent reconstruction and immutable reference ownership. Integrate BM01 only through an explicit peer format and outer-feedback contract.
4. For standard HEVC, freeze an enumerated conformant stream subset and inspect actual encoded syntax/tool usage. For a full AV1 route, first reproduce the pinned external decoder and quantify complete-stage state/resources; do not infer fit from a transform subblock.
5. Trace bounded native row/entropy/prediction/transform service and physical external-memory demand before RTL. Then demonstrate clock/resource fit, arbitration, atomic presentation and loss recovery on hardware. Python Renode/Verilator or arithmetic evidence must retain its actual scope.

Validation records hybrid7, BM01 10, hybrid-link20, architecture9 and independent audit11 tests: **57 passing tests**. The [audit](../experiments/python-game-audit-v11-study/README.md) rechecks34 distinct local source pins and two media hashes, keeps prepared/decoded GM/HG counts separate and retains the block-motion counterexamples.

Run `python experiments/verify_prototype_v11.py` from the repository root to check the [frozen inventory](prototype-v11-provenance.json), stored evidence, source bindings and test logs. It does not rerun timing benchmarks. Study READMEs give the independent reproduction commands. No hardware, long-duration, native30-distinct-frame or standards-conformance claim is made.
