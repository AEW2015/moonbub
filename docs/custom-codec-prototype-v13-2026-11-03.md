# Iteration 13: hierarchical reuse and finite full-resolution execution

The target remains **720×480 coded video, 720×405 active game content and
30 distinct displayed frames/s**. This iteration moves exact-source reuse into
real admission control, adds exact region reuse for HUD-like content, screens
expensive motion search and executes the combined codec through finite transport.
The paired branch is `handoff/gamebub-app-codec-v13-20261103` in both forks.

These are Python design and protocol experiments. Sunshine's installed encoder,
ESP32 firmware and FPGA bitstream are unchanged. The coherent custom profile is
still GM01 with optional HG01 exact RGB565 patches, GF02 transport and outer-body-
bound GA01 feedback. RM01 block motion remains a separate research dialect.

## Source reuse now respects admission and commit

The [cache admission study](../experiments/python-game-cache-admission-study/README.md)
fixes v12's integration gap: the normal and fallback candidates can reuse a
bounded exact-source cache, but every current-ID packet must fit the complete
49,152-byte cap before commit. Registered cached previews carry generation,
owner, epoch and ACKed-key identity guards. A hit still consumes normal credit
and sends the complete packet; it adds no decoder reference or skip syntax.

One source image and at most two map-specific P payloads are cached on the PC.
Source, map, mode, canvas and immutable ACKed key must match exactly. Rejected
P payloads may be remembered because they still reference that same key; a later
repeat is checked against its current cap again. Key and source changes invalidate
reuse. Both successful and rejected work is paid.

| Native window, 60 source IDs | Cache hits | Mean complete preparation |
| --- | ---: | ---: |
| Combat | 26 | 20.30 → 11.54 ms |
| Second | 0 | 20.51 → 20.65 ms |

The first improvement is 43.1%; the distinct-source case shows 0.67% overhead.
Sixteen held-out key images deliberately do not hit. Across 172 paired IDs there
are 163 admissions and nine paid rejections, with 43 hit decisions and 49 cached
candidate attempts. All accepted complete packets match the frozen controller
byte for byte. Eight tests cover admission before commit, fallback reuse, cached
rejections, capabilities, credit/key drain, expiry and invalidation.

Maximum observed persistent cache data is 1,051,342 bytes in native cases and
1,424,200 bytes in a synthetic case. Python metadata, old/new replacement overlap
and codec workspaces are extra. These figures are not peak memory or FPGA storage
requirements. Full pictures and packets still traverse the link.

## Reuse unchanged UI while the game background moves

The [UI cache study](../experiments/python-game-ui-cache-study/README.md) adds
a separate four-entry cache at the frozen selector's patch-encoder interface.
Its key includes canvas, rectangle and policy. It compares the current rectangle's
actual RGB565 words before reusing immutable HP01/HR01 bytes. Equal RGB565 words
can occur despite RGB888 changes; those discarded low bits were already outside
the exact display-word contract. No approximate match or stale-image substitution
is used. The selector still validates each patch, checks whole-packet cap and
assembles the actual HG01 body. Cached historical candidates are labeled historical;
a hit performs zero new patch-encoding candidates.

| Source | Patch hits / attempts | Whole selector time |
| --- | ---: | ---: |
| Combat, 60 frames | 213 / 240 | 5.78 → 1.68 ms |
| Second, 60 frames | 9 / 240 | 8.60 → 8.64 ms |
| Synthetic moving background, static UI | 44 / 48 | 6.38 → 0.95 ms |
| Synthetic changing UI | 0 / 48 | 6.37 → 6.54 ms |

Across 160 pairs and 640 patch attempts there are 292 hits, including 176 while
the full source RGB image changed. All complete paired HG01 packets are identical;
all selected 21,120 RGB565 words per frame remain exact. Native combat includes
109 region hits despite a changed full source, so the gain is not solely a replay
of whole-frame duplicates. The real configured rectangles are declared priorities,
not independently verified game HUD locations. Six tests and retained verification
pass. Maximum observed persistent words/payload storage is 51,286 bytes; metadata
and transient/peak allocations are excluded.

This is an application-specific opportunity: a verified game HUD profile can
avoid repeated host patch search without changing the game-world resolution or
displayed words. Moving/noisy HUD content instead pays the comparison overhead.
The standalone result does not establish a universal speedup or receiver savings.

## Motion screening avoids expensive candidates that rarely win

The [motion gate study](../experiments/python-game-motion-gate-study/README.md)
uses current source luma samples and the canonical ACKed reconstructed key only.
Four corners per block screen the same bounded motion vector set using 64 times
fewer SAD samples than full block search. Fixed gain, relative-gain, moving-area
and cut-error thresholds decide whether to enable actual GM/BM candidate coding.
The gate reads no future image, coded candidate length or reconstructed quality.
If it enables both modes, both real candidate costs remain paid.

All 136 real temporal/held-out source IDs decline BM; resulting packets and pixels
match GM controls. Native gate cost is about 1.4 ms/frame. The second source gives
up the blind selector's 2.61% byte saving while avoiding roughly 64 ms preparation;
the gated run takes 21.06 ms versus 19.75 ms plain GM. The combat timings are
21.61 ms gated versus 22.63 ms GM, but fixed case order/uncontrolled load prevent
claiming that extra work caused a speedup.

On contrived opposite-moving halves, five of eight frames enable search and retain
the 66.95% byte saving. Static zero-residual BM savings are missed. This is a
working causal screen with useful negative results, not a validated game motion
classifier. Keep plain GM as the real-source default until held-out evidence shows
a rate/quality/service win. Seven tests verify 616 decisions, 775 actual candidates,
604 admissions and 12 paid rejections. Equal quantizer maps do not imply equal
distortion between GM and BM.

## Combined finite execution, with every measured stage paid

The [execution study](../experiments/python-game-execution-study/README.md) combines
admission-aware full-source reuse and exact zero/DC receive bypass. It uses actual
GM01/HG01/GF02/GA01 bytes, normal/fallback maps, two sender transactions, two ingress
payloads, two P credits, three metadata framebuffer roles and the v12 requested-
expiry/late-ACK repair. This particular 16-case run does **not** contain UI caching.

Every actual preparation/rejection, receive, BOX and transport call pays its measured
host wall time; `service_tape` is null throughout. No fixed per-kind budget or assumed
decode time is substituted. Independent serialized virtual servers still differ
from one shared CPU or concurrent physical hardware. Native acquisition is excluded;
8 Mb/s forward/reverse, 160 Mb/s QSPI, 10 ms propagation and 60 Hz vblank are assumed.

| Source / profile | Baseline strict / eventual / diagnostic | Reuse + bypass strict / eventual / diagnostic |
| --- | ---: | ---: |
| Combat, exact UI, 60 IDs | 49 / 51 / 25 | 52 / 53 / 26 |
| Second, exact UI, 60 IDs | 40 / 42 / 21 | 41 / 44 / 21 |
| Combat, GM base, 60 IDs | 54 / 55 / 28 | 55 / 56 / 28 |
| Second, GM base, 60 IDs | 54 / 56 / 27 | 55 / 57 / 28 |
| Held-out second, UI, 180 IDs | 119 / 121 / 19.6 | 121 / 123 / 20.0 |

The run has 1,104 capture-policy events and four passing tests. Strict counts stop
at the end of capture; eventual counts include a separate drain. Diagnostic cadence
excludes the first and last 500 ms. A finite pipeline's last captures can legitimately
appear during drain, so strict count alone is not a steady-frame-rate criterion.
Here the diagnostic rates and missing eventual IDs also show an actual gap.
No case delivers every captured ID. The 150 ms decode-age gate permits the next
vblank; it is not a strict 150 ms optical-age proof.

The held-out input has 180 distinct images at native approximately 29.88 fps,
hypothetically scheduled at 30 IDs/s. It avoids explaining the results solely by
the short combat sample's duplicates. The optimized held-out UI case still spends
1,661 ms waiting on P credits and 1,367 ms encoder-busy over six seconds. These
exclusive waiting categories are not additive attribution of missed frames.
Case histories and measured host costs differ, so isolated percentage gains must
not be added together to predict an end-to-end FPS.

## Three host transactions help while receiver pools stay bounded

The [credit-window study](../experiments/python-game-credit-window-study/README.md)
integrates all three execution optimizations: admission-aware source reuse,
exact UI region reuse and decoder bypass. Both compared arms use them. It changes
host sender slots and P credits together from two to three, retaining **two
receiver ingress slots and three metadata framebuffer roles**. This differs from
the preceding execution study, whose selector always re-encodes UI patches.

The new model validates matching sender/encoder windows, enforces actual pool
bounds and keeps cap, age, key-drain, read ownership and expiry rules. Tests force
the third sender into a full two-slot receiver, pay the failure path and prove
recovery. The clean native runs themselves do not encounter that busy error.
Unsupported resources are not silently made unlimited.

| Exact UI source / refresh policy | Two credits: strict / eventual / diagnostic | Three credits: strict / eventual / diagnostic |
| --- | ---: | ---: |
| Combat, 60 IDs, periodic 30 | 53 / 54 / 28 | 55 / 56 / 28 |
| Second, 60 IDs, periodic 30 | 41 / 44 / 21 | 53 / 55 / 27 |
| Held-out second, 180 IDs, periodic 30 | 121 / 123 / 20.0 | 158 / 160 / 26.4 |

The six-second held-out window gains 37 strict and 37 eventual IDs. P-credit waiting
falls from about 1,661 to 62 ms in that trace; remaining encoder, refresh and other
costs are still paid. These are remeasured-host scheduling scenarios, not a fixed-
service isolated experiment or a physical speedup measurement.

A separately labeled three-credit, initial-key-only held-out probe reaches
**28.4 diagnostic IDs/s**, with 166 strict and 169 eventual presentations out of
180. It does not reach 30, deliver every capture or qualify initial-only refresh
as a production default. Older-key work/packet growth restores 635 ms of P-credit
waiting even with three credits. The reference remains the initial reconstructed
key; ACKing a P frame only releases credit and never advances the predictor.

Selected UI words remain exact with zero mismatches. Mean active RGB565 MSE on
the decoded subsets is 19.446 versus 19.454 for periodic-30 two/three-credit long
cases, and 19.648 for initial-only. Subsets and reference histories differ, so
these values are not an equal-distortion rate comparison. Quality does not become
identical merely because quantizer maps and execution arithmetic are unchanged.

The campaign contains seven cases and 780 capture-policy events. Eight tests cover
two-credit parity with the earlier model, four-entry UI reuse, invalid pool/factory
settings, loss/corruption/duplicate/wrong feedback, full ingress, rejected work
and late-ACK parser drain. The new public model rejects the unsupported `gate`
controller setting; the supplied factory chooses cache-aware normal admission.
Each call still pays actual measured host wall time. A three-credit host is an
experiment, not an installed default.

Review also reproduced a second inherited expiry edge: a valid ACK could wait for
a physical reader, then a matching serialized NACK requested expiry before drain,
yet the old scheduler promoted the deferred ACK afterward. The new credit model
checks requested expiry before deferred promotion, makes no encoder ACK call in
that regression, and still waits for readers. An ACK-only positive control retains
valid deferred promotion. The frozen v12 and earlier execution copies retain this
edge; their clean timing runs do not exercise it. Use the repaired credit model
for further scheduler work, including its two-credit configuration. The final
retained benchmark was rerun after this repair with fresh source pins.

Three maximum-size sender packets represent 147,456 bytes rather than 98,304,
an extra **49,152 bytes of logical host packet capacity**. Existing source/patch
caches, pending objects, packet copies and workspaces are extra. Receiver pool
counts are unchanged, but that does not prove target peak memory, backpressure,
SDRAM bandwidth or firmware compatibility. Credit/resource negotiation and target
failure behavior remain implementation gates.

## Progression to an application-specific implementation

The practical direction is hierarchical exact reuse plus bounded coding work:
reuse whole-source residual payloads when possible, reuse unchanged UI region
payloads when the game world changes, bypass zero/DC inverse arithmetic, and spend
motion-search work only when a causal screen has a demonstrated benefit. These
decisions exploit control of the host, forwarding firmware and FPGA without
pretending to implement HEVC/AV1 syntax.

Next implementation gates are a native host/receiver port with exact golden packet,
RGB/YUV and failure matching; negotiated cap/credit/resource limits; explicit target
reference/output memory service; then RTL throughput and physical display testing.
FPGA DSP work should preserve integer rounding and time-share the transform/residual
pipeline while bypassing zero/DC work. Entropy parsing, RGB565/color conversion and
memory traffic still need whole-design profiling. Persistent host caches are not
extra FPGA BRAM allocations.

For further compression, separately prototype acknowledged reconstructed-P references
and rate/distortion-bounded block skip. Version reference IDs/content tags, protect
reference storage through physical reads and prove loss recovery before using a new
reference. Keep exact UI separate from the YUV predictor. JPEG remains the hardware
control; full HEVC/AV1 remains a distinct decoder-fit project.

The next Python codec prototype should therefore test a bounded two-reference
profile against the same long held-out sources: choose only references whose
decoded content and retention have been acknowledged, keep old references pinned
until every consumer drains, and block promotion when no reference bank is free.
Measure actual full bytes, selected-region error, preparation/receive service,
reference read/write bytes and recovery under loss. Compare this with a cheaper
skip/residual decision under the current immutable-key profile. This directly
addresses the older-key growth observed above; it is not implemented by v13.

The memory cap is not a sustained wire-rate guarantee. Under this model's 8 Mb/s
forward link, 30 frames/s permits 33,333 forward bytes/frame including headers.
A 49,152-byte body plus 48 GF02/UDP/IP overheads of 59 bytes needs 12.48 Mb/s
at 30 frames/s. A constant 30 fps body budget is at most 31,504 bytes with the
declared 1,024-byte chunking. Future rate control should account for rolling
wire budgets and key bursts as well as the negotiated memory cap; this arithmetic
is conditional on model framing and does not measure Wi-Fi throughput.

Qualification should use longer distinct-frame captures with declared warm-up,
rolling display cadence, frame age and interior drop counts, plus full drain and
fault accounting. Report strict and eventual counts together. Related precompressed
25/29.88 fps footage and simulated link/scanout cannot qualify live sustained
hardware 30 fps, regardless of a favorable short diagnostic window.

Each study supplies a README, tests, source-pinned JSON and a read-only retained
verifier. The independent v13 audit and `experiments/verify_prototype_v13.py`
reconcile them; `docs/prototype-v13-provenance.json` pins the complete snapshot
and paired Sunshine laboratory README. Old handoff branches and timed sources
remain frozen. No installed encoder, hardware or visual-test claim is included.
There are 42 passing new tests: 8 admission cache, 7 motion screen, 4 execution,
6 UI cache, 8 credit/expiry and 9 independent audit tests. The audit reconciles
42 unique executed-source pins; the parent manifest pins all retained artifacts.
