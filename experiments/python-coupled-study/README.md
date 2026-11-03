# Capture/codec/feedback coupled stop-and-wait study

This closes a gap in the earlier fixed-length feedback schedule: every selected
capture is actually encoded against the currently ACKed MT02 reconstruction.
If intervening captures are skipped, the next packet is recomputed, not taken
from a precompressed all-frames trace. The real packet is parsed and decoded
at its scheduled receiver event, and its RGB must equal the host reconstruction.
The virtual stage durations are assumptions, not Python/hardware measurements.

## Run and interface

`model.Config` and `model.run(frames, manifest, config)` are the public Python
model API. Frames are uint8 RGB; `manifest['active_rects']` names each source's
active quality region. It imports the unchanged MT02 and common image helpers.
Use the existing [pinned Python environment](../python-codec-study/requirements.txt):

```sh
cd experiments/python-coupled-study
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v test_model.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py
```

`tests.log` records ten passing focused model tests. The independently supplied
`validation.py`/`test_validation.py` provide additional count/age/conservation
checks; their tests can run separately. Tests include actual packet agreement,
re-encoding after skips, stale/duplicate ACKs, data/ACK/CRC loss and independent
recovery, cap/age rejection, incomplete horizons, and bounded quality backoff.
Passing a deliberate failure-condition test is not a successful stream run.

`benchmark.py` reads the prior motion JPEG-reference source manifest, then
loads **60 consecutive native frames** starting at1 s and4 s from each of the
same two precompressed Mass Effect clips. Source SHA-256/PTS/canvas hashes
are recorded. All images are the common720×480 BOX-resampled/letterboxed
canvas. Source cadence25/29.88 fps is retained in manifests, but this experiment
schedules them at hypothetical30 fps; it neither interpolates nor proves
native30-distinct-frame/s capture. Related windows from two clips are limited
held-out evidence, especially when the source contains repeated images.

## Timing, admission and recovery

The default virtual pipeline has2 ms preparation, ideal8 Mb/s network,
160 Mb/s QSPI,8 ms reconstruction,60 Hz display and configurable feedback.
Network accounting is packet bytes plus40 application and28 IPv4/UDP bytes
per1,024-byte chunk. RF/link framing, retransmission/control bytes and audio/input
are absent. The source canvas already exists; capture/scale CPU cost is absent.

Only one logical transaction can await ACK. One host waiting capture is
replaceable by a newer capture. The selected capture's actual encode happens
against the exact ACKed reconstruction; successful receiver commit and ACK
advance the host ref. Configured source-ID gaps therefore affect later packet
sizes and quality. A forced independent refresh occurs at the first selected
capture at least30 IDs after the preceding key, rather than silently missing
refresh when the exact multiple-of30 capture was skipped.

The host checks a complete packet against48 KiB and source age before send.
Oversize or stale packets are never transmitted; abort invalidates the host
reference so the next attempt is independent. Preparation's assumed service
time is charged even for these rejects. There is no truncation. Optional
`cap_backoff_scales=(8,16,32)` moves one level coarser **on the next captured
attempt** after a cap failure. It does not retry/rewind the same frame, never
exceeds32 and never raises quality again during this short experiment.

ACK timeout is200 ms from send-ready by default. Lost data/ACK or corruption
leaves the host waiting until timeout; abort then forces a fresh independent
frame. A timed-out physical transaction is allowed to drain before new
admission. Its eventual receiver commit may occur, but its stale ACK generation
cannot advance the new host ref. The decoder's monotonically increasing IDs
and epoch-bound MT02 ACK API provide additional checks. Duplicate ACKs are
counted and ignored. No NACK feedback, session replacement event or actual
wire control protocol is implemented.

Presentation is a next-vblank metadata swap: latest committed pending output
replaces the front. Older pending candidates can be superseded. This model
does **not** allocate or prove finite RGB/YUV front/back/reference memory, DMA,
CDC, packet reassembly or real SDRAM service. Complete expected RGB and packets
are Python integrity oracles, and event timers may retain them for bookkeeping;
those Python arrays are not device buffer measurements.

## Windows, counters and quality

The strict capture window is `[0, N/30)`; eventual drain results are separate.
For60 frames, the predeclared diagnostic steady window is `[500,1500)` ms.
It is only one second: each frame changes its rate by1 fps, so it cannot
establish sustained30 fps. No successful verdict is manufactured by moving
the window after examining the data. Default drain is1,000 ms.

`validation.summarize_presentation` checks strictly increasing IDs/timestamps
and exact half-open count semantics. `terminal_outcomes` is a disjoint
presented/dropped/pending partition of every captured ID, independently
checked by `validate_conservation`. In contrast, `drop_counts` counts **failure
and policy events**: one frame can lose an ACK, time out and already have been
presented. Those event counts must not be summed as unique dropped frames.

The result separately exposes physical transactions still draining, physical
busy-until time, host waiting/ACK-waiting work, pending back and current front
at the horizon. A timeout cannot hide physical work merely by clearing the
logical ACK slot. Incomplete-horizon tests keep those states visible.

Quality is pooled active RGB565-output MSE/PSNR over actual **presented IDs**.
Adaptive and fixed settings can select different subsets and reconstruct
different pixels; their pooled PSNR is not a matched-corpus or perceptual
comparison. Record scale histograms and presented IDs alongside quality.

Python encode wall time includes actual MT02 preparation/reconstruction but
excludes `prepared_rgb()` and original source decode/scale. The reported
receiver wall interval includes parsing/reconstruction plus quality conversion
and measurement overhead. Neither replaces the assumed2/8 ms virtual service,
and neither establishes an optimized Windows or FPGA implementation's speed.

## Result interpretation

| Window | Feedback0 ms: presented/60, short steady rate | Feedback10 ms | Feedback20 ms |
| --- | --- | --- | --- |
| Combat primary | 60,29 IDs/s | 60,29 IDs/s | 54,27 IDs/s |
| Second clip primary | 60,30 IDs/s | 60,30 IDs/s | 51,25 IDs/s |
| Combat held-out | 47,28 IDs/s | 44,25 IDs/s | 36,20 IDs/s |
| Second clip held-out | 60,30 IDs/s | 60,30 IDs/s | 49,24 IDs/s |

These presentation totals include drain; strict two-second counts are separate
in the artifact. A60/60 eventual total does not convert the fixed one-second
steady29 count into30. The held-out combat cap failures cause9/8/8 cap events
at0/10/20 ms, in addition to latest-slot replacements. All16 cases pass the
disjoint presentation disposition check and have no physical/ACK work left
at the default drain horizon.

Next-capture backoff improves held-out combat eventual presentations from47
to54 at0 ms feedback and44 to49 at10 ms. Both adaptive cases have one cap
rejection instead of9/8. They keep the same short steady rates28/25, and
switch only to16: presented-scale counts are47×scale8+7×scale16 and
44×scale8+5×scale16. Pooled presented quality changes from36.21/36.17 dB to
35.87/35.88 dB. Those are different presented subsets and reconstructed
references, so they do not isolate a pure quantizer quality penalty.

Each primary fault campaign has exactly one network loss, one ACK loss, one
decode rejection and three timeouts. Final presented totals are42/43 of60
with independent recovery and conserved source IDs. Failure-event counts
overlap: ACK-lost frames can already be presented, whereas each terminal
capture disposition occurs exactly once.

`results.json` records the source/helper hashes and all events for16 cases:
four windows at feedback0/10/20 ms, two primary fault campaigns, and two
held-out combat quality-backoff cases. The logs preserve the exact observed
counts, cap failures, selected scales and presentation ages. Source hashes
are checked before and after execution; no old codec is modified.

The fixed-scale campaign shows why compression averages alone were insufficient.
The second clip reaches30 IDs/s in this short steady window with0/10 ms extra
feedback, but20 ms feedback skips frames. Primary combat can commit all60
captures at0/10 ms while still counting only29 presentations in its fixed
one-second steady window. Longer held-out combat additionally reveals48 KiB
failures not visible in the earlier30-frame sample. These are failed count/cap
conditions, not hardware-qualified successes.

Use the adaptive cases to judge whether next-capture quantizer backoff trades
quality for recovery. It is a bounded diagnostic policy, not an established
optimal controller. Longer capture coverage, real service/feedback traces,
actual age/cap admission and a finite memory/reference architecture remain
required before claiming hardware30 fps. The parallel immutable-anchor study
explores overlap under a different dependency policy; compare exact matched
sources/configuration and separate its extra reference/slot costs.

## Additional sensitivity and cut/noise stress

Run `python extra_cases.py` to produce `extra-results.json`. With10 ms feedback
and the assumed decoder increased to20 ms, primary combat drops to26 IDs/s
in the short steady window and the second clip to24. Eventual totals are51/49
of60. This is another virtual service sensitivity, not measured decoder timing.

The separate synthetic60-frame sequence has simple frames, moving gradients,
five seeded noise frames, then a simple recovery scene. At48 KiB, both fixed
scale8 and bounded8→16→32 backoff reject all five noise frames and replace two
waiting captures. Both eventually present53/60, count23 IDs/s in the declared
middle window and recover to final ID59. Backoff retains scale32 afterwards;
pooled presented PSNR falls from36.38 to34.49 dB over the same number of
presentations. It neither restores those high-entropy frames nor automatically
returns to high quality. The source is explicitly synthetic, not gameplay.

The stress corpus and metric helpers add nine independently passing tests to
the ten model tests. The parent-run complete suite records19 passing tests
in `tests.log`. See the separate [Python service measurement](../python-service-study/README.md)
for actual reference-program wall costs; those are slower than the virtual
2/8 ms assumptions.
