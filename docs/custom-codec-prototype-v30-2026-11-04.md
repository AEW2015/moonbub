# V30: finer residual candidates and local entropy context

V30 proves small real compression gains from finer block/band decisions at
unchanged 720×480 coded / 720×405 active resolution. It also supplies an exact
local sparse-run cost oracle that can reduce the work of future residual RDO.
GM27/CP27/JA27, the exact HUD and the complete 49,152-byte envelope stay fixed.

The current full Python candidate controller is **slower**, so this is a codec
design result rather than a deployment recommendation or a 30 fps proof.

## Actual causal stream results

The control repeats v29 quiet-block motion search. Two new policies generate
AC-tail candidates at zigzag cutoffs 21 and 6, retaining DC, low frequencies,
protected UI/ROI coefficients and the chroma halo. Strict mode permits no
per-block clipped-source YUV SSE increase. Budget mode allows each block
`min(incumbent_SSE//100,64)` extra YUV squared-error units. Exact whole-plane
legacy/EC26 byte costs choose only actual savings, with incumbent winning ties.

The integrated controller also constructs the original zero-motion and searched
packets on the **same accepted reference**. Their original controller winner
forms a shadow. A new band packet must fit, save complete bytes, and have active
RGB565 SSE ≤ the shadow's SSE (strict) or ≤101% of it (budget). All attempts,
including the rejected shadow and band trials, remain paid and retained.

| Window | Policy | Complete body Mb/s at nominal 30 IDs/s | Active MSE | Base-policy service ms/frame |
| --- | --- | ---: | ---: | ---: |
| 2600 | V29 adaptive control | 2.765395 | 14.395686 | 152.69 |
| 2600 | Strict band selection | 2.763095 | 14.386886 | 317.21 |
| 2600 | Budgeted band selection | 2.758705 | 14.393187 | 317.71 |
| 7200 | V29 adaptive control | 6.166030 | 26.339495 | 216.19 |
| 7200 | Strict band selection | 6.148865 | 26.303889 | 420.25 |
| 7200 | Budgeted band selection | 6.127300 | 26.483553 | 419.98 |

Relative to the separate causal control histories:

- Strict mode saves **0.083% / 0.278%** complete bytes, while measured MSE falls
  **0.061% / 0.135%**. It selects modified packets in 34/48 and 37/48 frames.
- Budget mode saves **0.242% / 0.628%** complete bytes. Primary MSE falls 0.017%,
  while complex MSE rises **0.547%**. It selects modified packets in all 96 frames.
- CPU service grows roughly **2.08× / 1.94×**. Do not deploy this full trial
  controller as a speed optimization.

Same-history shadow savings differ from whole-controller savings: strict saves
0.129% / 0.188%, and budget saves 0.245% / 0.425%, against shadow byte totals
on its own reconstructed histories. Those shadows are diagnostic encoder
candidates, not another independent stream to add to reported bandwidth.

Strict mode's per-frame guard does not mathematically bound accumulated error
relative to a different reference history. The tiny favorable MSE changes above
are measured on these particular windows, not a general no-quality-loss claim.
Budget mode's allowance is likewise per-frame against the current shadow,
not a global error budget against the historical control or perceptual quality.

The six cohorts reuse **96 retained source images**, 48 from each 29.88 fps
window. Each policy has its own accepted decoded reference, with keys at IDs
0 and 24; policy order rotates each source frame. All **288 accepted packets**
fit the complete cap and retain exactly 21,120 RGB565 HUD words per frame.
The repeated control reproduces all 96 corresponding v29 packet/ACK/metric
goldens exactly. The experiment retains **940 actual candidate encodes**.

Timing pays all analyses, trial encodes, current-source RGB quality evaluation
and binding checks. It excludes source acquisition/conversion, preencoded HUD
generation, offline debug decoding, archive I/O, network waits and presentation.
Receiver clocks are separate. Nominal 30-ID/s rates project actual serialized
CP27 bytes and exclude ACKs and transport framing. They are not measured FPS.

## Why the gain is small

The conservative source-error and ROI gates admit few AC edits.
The strict accepted edits remove only 633 / 2,583 coefficients across the two
windows. Budget mode removes 1,114 / 4,247. Much of the complete stream is also
the exact HUD: 310,961 / 623,615 bytes of the control's 553,079 / 1,233,206 total.
These tail edits do not change that HUD cost. This is not a path to HEVC/AV1
compression parity by itself.

The useful proof is that bounded, source-aware block edits can beat the v29
whole-plane selector, which won no candidates. Richer candidate generation and
cheaper context costing are needed before these small gains become worthwhile.

## Exact local sparse-run cost oracle

The context prototype indexes nonzero positions, runs, level-token lengths and
prefix sums for a block-major AC band. Deleting a contiguous coefficient interval
removes its tokens and repairs at most one following run. With **fixed Rice
parameters**, two binary searches and a prefix difference give the exact bit
delta and the stream's exact byte-padding change. No coefficient scan occurs
inside a query. DC, coefficient insertion and layout changes are outside this API.

On 24 retained v29 frames / 72 plane indexes:

- All **322** independent deletion queries match full fixed-parameter recounts.
  The 322 modified EC26 serializations are separately verified against retained
  packet hashes and full optimized lengths.
- Local query cost is **0.0123–0.0127 ms**, versus **0.266–0.302 ms** for equivalent
  full fixed-parameter recounting: **20.9–24.5× faster after setup**.
- Index setup costs **0.248–0.277 ms per plane**, excluding initial band extraction.
  Maximum retained index storage is **113,948 host-memory bytes**. This is not
  an FPGA BRAM allocation or ESP32 memory-fit result.
- The fully reoptimized entropy counter costs 1.76–1.83 ms, but performs stronger
  work, including Rice parameter selection and fallback. Comparing it directly
  with the local fixed-parameter query would overstate an equivalent speedup.

The old isolated CP02 proxy predicts a different byte saving in **132/172**
sampled single-block edits. Rice parameters change in **25/322** queries.
Adjacent deletion costs are nonadditive in **11/50** fixed-bit comparisons and
**24/50** reoptimized byte comparisons. Do not sum independent deletion savings
or treat a stale index as updated after an accepted edit.

These are independent coefficient edits without source-distortion or accepted
frame admission. Their diagnostic byte deltas are **not stream compression
savings**. The local oracle is not integrated into the causal controller above;
its component speedup cannot be applied to the full encoder's clocks.

## Next application-specific codec experiments

1. Use the local context oracle to screen bounded block/band candidates cheaply,
   then evaluate actual clipped reconstruction error and full optimized packet
   cost before admission. Charge index setup, mutation/rebuild and every fallback.
   A fixed-parameter local cost is exact only for its declared coding parameters.
2. Add small AC coefficient shrink/dead-zone candidates, rather than removing
   an entire band only. Protect UI detail and the exact HUD. Compare the actual
   rate/quality/work frontier over causal histories and error tails.
3. Share immutable incumbent coefficients, predictions, reconstructions and
   source-error maps between trials. Current code deliberately recomputes these
   to qualify decisions; avoid paying that work twice in a native architecture.
4. Add fresh long footage with camera pans, fine text, scene cuts and motion.
   Measure temporal artifacts and packet/error tails. These short reused windows
   do not establish gameplay experience or HEVC/AV1 parity.
5. Port only a selected host policy using packet goldens. Keep the ESP32 focused
   on bounded transport/credits/reset. Qualify the FPGA's fixed-point inverse,
   prediction taps, memory arbitration and atomic publication against goldens,
   then measure RF/QSPI contention and physical presented-frame age.

The target remains full resolution at 30 fps, but Python work is still far above
33.33 ms before capture/HUD/transport. Native service, FPGA resource/timing fit,
and sustained physical 30 fps remain open. Preserve JPEG and the v20 handoff.

## Offline verification

```sh
python experiments/verify_prototype_v30.py
```

The package retains source snapshots, byte archives, source/reference identities,
all trial work and deterministic replay. Full replay decodes every candidate
and accepted reference chain, recomputes source RGB metrics and exact HUD pixels,
checks DC/low-frequency/ROI/halo preservation, per-block YUV and final RGB guards,
and reconciles full byte/selection/timing accounting. It checks **3,045,600 block
comparisons** across 1,128 band planes. Component replay qualifies the band menu
and local context deltas; the independent Luna audit binds results and replay
hashes while checking framing, references, admission and all summaries.
All 15 focused tests pass: four band-selection, four local-context, four
controller-admission and three independent-audit tests.
