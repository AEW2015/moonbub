# Iteration5: less host work, asynchronous anchors and quality recovery

This continues [iteration4](custom-codec-prototype-v4-2026-11-03.md) with four
parallel Python studies. The strongest result is less actual host preparation
work with identical packets. Reference scheduling and quality recovery improve
some conditional cases, while retaining important failures. There is no new
hardware30 fps qualification or integrated Sunshine/ESP32/FPGA mode. Keep the
existing JPEG implementation as the hardware control.

## Actual host preparation improvement

The [host optimization study](../experiments/python-fast-entropy-study/README.md)
first replaces repeated CP02 coefficient scans with batched sparse discovery
and cached Rice bit strings. Frozen quantization, syntax, CRC, decoder and
reconstruction remain unchanged. Seventy-two paired MT02 packets across the
two clips are byte-identical; receiver RGB is also exact. Eighty deterministic
coefficient families test sparsity, width contexts, extreme coefficients and
RAW fallback in addition to frame/reference-state tests.

An architecture-specific MA01 optimization goes further: an immutable anchor
is the only future predictor, so the host need not reconstruct a P frame just
to send it. P preparation omits host IDCT/snapshot/RGB work; the receiver still
performs its required reconstruction. An optional lazy RGB/hash oracle runs
outside production preparation. Seventy-two additional old/new MA01 packet
pairs and decoded hashes match. Pending oracle packets have bounded extra host
ownership until ACK/expiry; they are not hidden receiver memory.

| Actual measured host call | Original median | Optimized median | Optimized p95 |
| --- | ---: | ---: | ---: |
| MT02 combat, all frames |47.46 ms|30.80 ms|37.84 ms|
| MT02 second clip, all frames |58.04 ms|31.59 ms|35.16 ms|
| MA01 combat, P frames only |53.97 ms|24.87 ms|26.64 ms|
| MA01 second clip, P frames only |61.34 ms|22.86 ms|23.71 ms|

MT02 mean-time speedups are1.64×/1.86×; MA01 P mean-time speedups are2.15×/2.68×.
There is no compressed-size or quality gain in these pairs because their wire
bytes match. This is a useful optimization for the host→ESP32→FPGA split: it
removes host work without adding a decoder feature or ESP32 image processing.

**Keys still stall.** Unchanged MA01 key means are111.19/77.83 ms. All-frame
optimized means32.13/27.29 ms hide p95 values106.32/77.69 ms. The benchmark has
only three key samples per source and twelve consecutive native input frames,
repeated three times with alternating old/new timing order. Host load is
uncontrolled; source acquisition/scale, lazy RGB checks, network, QSPI, decode
and presentation are excluded. Neither the P result nor an average below
33.33 ms establishes real-time30 fps or the assumed2 ms host service.

## Background reference replacement

The [AA01 study](../experiments/python-async-anchor-study/README.md) creates a
separate reference-only KEY transaction, visible DISPLAY transaction and
explicit RETIRE transaction. Two persistent anchors allow new DISPLAY packets
to use the ACKed old anchor while the replacement is prepared/transferred.
KEY installation never increments a presentation count or regresses the visible
capture ID. A new reference becomes usable only after its epoch/transaction ACK.
Old-reference retirement requires both returned DISPLAY credit and explicit
physical-read drain; credit alone cannot release a read pin. Lost key ACKs retry
the same transaction and bytes. Forbidden reverse retirement is rejected before
mutation; permanent retry exhaustion remains an explicit recovery condition.

The default model actually encodes/decodes selected packets and charges KEY,
DISPLAY and RETIRE against the same two packet slots and serialized services.
Defaults remain hypothetical2 ms host preparation,8 ms decode,8 Mb/s network,
160 Mb/s QSPI,60 Hz vblank and10/20 ms feedback. Forty application plus28
IPv4/UDP bytes per1,024-byte chunk are included. RF/link/feedback overhead,
source capture and actual target memory service remain excluded.

| Exact comparison | Diagnostic MA01→AA01 IDs/s | AA01 strict / eventual |
| --- | ---: | --- |
| Combat primary60, feedback20 ms |29→29|56 /57|
| Second clip primary60, feedback20 ms |29→30|58 /59|
| Second clip primary90, feedback20 ms |29→30|88 /89|
| Combat held-out60, feedback10 ms |27→26|46 /46|

For60 inputs, the fixed strict interval is `[0,2000)` ms and diagnostic interval
`[500,1500)` ms;90 uses `[0,3000)` and `[500,2500)`. These short diagnostic
counts cannot establish sustained cadence. The extra key/anchor burden hurts
the held-out combat case, which has ten DISPLAY cap rejections. A lost initial
KEY ACK plus first DISPLAY loss recovers to final visible ID59, but only52/60
captures eventually present. No fault or control packet counts as a displayed
frame, and all seven cases drain slots/control/P credits.

The extra immutable reference costs another518,400 logical8-bit YUV420 bytes.
Peak Python int16 anchor arrays total2,073,600 bytes **per endpoint**, excluding
construction/prediction/transform/output temporaries. Shared packet payload peaks
at94,000 bytes within two49,152-byte slots. The additional host key retry cache
peaks at39,238 bytes and is separately counted. Three framebuffer roles are a
metadata ownership oracle, not a validated SDRAM allocation or physical fit.

A separate four-case sensitivity raises declared host preparation to32 ms,
informed by MT02 timing but **not a per-packet MA01/AA01 measurement**. Diagnostic
counts change28→29 and27→28, while eventual delivery stays56/60 and55/60. The
second strict count worsens53→52. AA01 uses4.2%/5.5% more total forward wire
bytes including drain. This counterexample shows why favorable scheduling with
2 ms service cannot be promoted to a real encoder/streaming result.

## Quality restoration and cuts

The [causal policy study](../experiments/python-quality-policy-study/README.md)
adds bounded8→16→32 backoff and cautious restoration based only on past ACKs,
packet sizes and age. Four good current-scale ACKs below half the48 KiB cap,
age≤80 ms and a six-capture cooldown are required for a finer step. Old-scale
ACKs cannot trigger a new-scale restoration. The quantizer maximum is a syntax
and policy bound, **not a measured visual-quality floor**.

On the seeded cut/noise/recovery sequence, monotone backoff and restoration
present the same55/60 IDs with five cap rejects and25 diagnostic IDs/s.
Restoration returns32→16 after ACK38 and16→8 after ACK44. Pooled active RGB565
PSNR improves34.44→35.21 dB (**+0.77 dB on the same55 IDs**). This is a synthetic
recovery result with no frame-rate gain; the large flat-tail PSNR difference
must not be extrapolated to detailed game scenes.

The four real60-frame policy pairs show **no restoration improvement**: none
earns the declared headroom gates during its coarse tail. Exploratory90-frame
held-out combat also remains75/90,25 diagnostic IDs/s, two cap failures and
final scale32 in both policies. Its extension overlaps the original held-out
sample and is not independent. These negative results remain in the artifacts.

The sampled-luma scene-cut detector is causal but unqualified. Its synthetic
off/on ablation adds a key (2→3), gains no frames or cadence, and changes
common-ID PSNR36.286→36.219 dB. Detector overhead is unmeasured. It should not
be recommended as a winning default on this evidence.

## Corpus, reproducibility and next gates

The [independent corpus audit](../experiments/python-cohort-study/README.md)
catches a tempting invalid extension:90 combat frames starting1 s overlap the
4 s held-out window by15 exact native PTS. All15 paired rendered hashes match;
seven distinct hash values reflect repeated source content. Only75 primary
combat timestamps precede4 s. Therefore no90-frame combat-primary comparison
is called held out. The90-frame second-clip primary window ends before4 s and
is safe. Both source files are already-compressed related Mass Effect footage,
with native25/29.88 fps scheduled at hypothetical30 capture IDs/s, not native
30-distinct-frame/s capture or broad game generalization.

Each component README gives commands, source/input hashes, actual result JSON
and test logs. The [final snapshot](prototype-v5-provenance.json) binds this
iteration. Thirty-nine passing tests
cover syntax compatibility, policy causality, reference/retirement lifetime,
fault recovery, resource bounds and cohort helpers. Model cases and timing
pairs are separate from test counts. Finite passing checks do not qualify
physical memory, FPGA fit, link throughput or visual acceptance.

Next implementation order:

1. Use the fast CP02 serializer and lazy immutable-anchor P preparation in a
   controlled native-host prototype. Optimize key entropy/reconstruction and
   measure capture/scale, per-kind service tails, ACK and transport costs.
2. Feed those measured per-frame/key service traces into the finite scheduler;
   the32 ms scalar sensitivity is insufficient. Combine optimizations only with
   preserved packet/pixel equivalence, bounded retry lifetime and drain rules.
3. Couple reference/stripe decode to explicit physical SDRAM read/write service,
   packet ingress and scanout arbitration. Two references need capacity and
   bandwidth qualification, not just an array-byte count or DSP estimate.
4. Extend to varied native capture with a declared visual-quality floor, HUD
   and temporal checks, longer quiet recovery and real cuts. Complete the plan's
   1,800-distinct-frame model gate, then physical10-minute30 fps qualification.
   Keep failed counts, quality loss, cap misses and all drain frames visible.
