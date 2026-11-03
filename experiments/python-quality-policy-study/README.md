# Causal quality restoration and scene-cut policy

This study extends the frozen MA01 packet/finite-stage model in a new directory.
It does not modify existing codecs, models, firmware or installed Sunshine.
Selected captures are actually encoded/decoded against an ACKed reconstructed
anchor; decoded RGB hashes must match the host reconstruction. Timing is still
virtual and is not a claim of Python/native/FPGA real-time service or hardware
30 fps.

## Bounded policy

`PolicyConfig` and `Config` are immutable configurations. `QualityPolicy` is
the state machine. Scale is inverse quality:8 is finest,32 coarsest. Its
declared ladder is8→16→32; a cap failure advances **the next capture attempt**
one level. An oversized frame is never truncated/sent. Actual rejected
preparation still consumes the assumed encode time, and refresh waits for
old P credits to drain.

Three modes are implemented: fixed8, monotone backoff, and restoring backoff.
Restoration needs four accepted ACK observations at the current scale, actual
packet sizes below50% of the48 KiB cap, ACK age at most80 ms, and at least six
capture IDs since the last scale change. A successful step moves one level
finer; a later cap miss can back off again and is counted. Old-scale/old-ID
observations cannot manufacture a restoration. There is no future frame,
future size or reconstructed-error oracle in control decisions. A maximum
quantizer scale is a policy/syntax bound, **not a measured visual-quality floor**.

The scene-cut detector computes normalized sampled-luma SAD of the current
and previous captured source frames, with threshold0.20 and ten-capture
cooldown. It uses the full canvas including bars. A cut only requests a
drained key refresh; it does not directly reduce quality. Thumbnail detection
overhead is not separately measured or charged beyond assumed preparation.
This simple detector has not been tuned or validated across games.

The timed model is adapted from `python-anchor-study/timed.py`: two finite
P credits/packet slots, serialized encode/network/QSPI/decode stages and three
logical framebuffer roles. There is one replaceable capture waiting slot.
Epoch/frame-bound ACKs and actual packet CRC/coefficient checks are inherited
from unchanged MA01/MT02. Packet arrays release on complete decode/rejection.
Front/back roles remain a metadata oracle; physical memory, DMA/CDC and wire
feedback/session reset are unqualified. Source arrays, transform workspace,
temporary oversize host packets and integrity oracles are not device RAM.

## Reproduce

Use the existing [pinned environment](../python-codec-study/requirements.txt)
and local source-media layout. From this directory:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python extended.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python cut_ablation.py
```

`tests.log` records eleven passing tests: six pure policy tests and five
actual-packet model tests. Tests cover hysteresis/cooldown, bounds, stale
observations, source causality, failed fine trials, post-noise restoration,
recovery/lost ACK, finite resources and negative cap conditions. Expected
rejections are not successful stream runs.

`results.json` binds sources/helper hashes before/after execution and records
eight real video cases plus three synthetic controls. `extended-results.json`
adds two exploratory longer held-out cases without retuning the policy.
`cut-ablation-results.json` adds one detector-off synthetic control against
the already-recorded detector-on fixed case. All14 scenarios use actual
selected-frame packet preparation and verified reconstruction. Original
source files/PTS/canvas hashes and synthetic labels remain in manifests;
raw video is outside Git. Regeneration replaces artifacts.

## Inputs, windows and metric limits

Video cases use60 consecutive native frames from the prior four windows:
two precompressed Mass Effect sources starting at1 s/4 s. Native source rates
are25/29.88 fps, scheduled here at hypothetical30 IDs/s with no interpolation.
These are short related windows, not broad held-out or native30 capture proof.
The exploratory90-frame combat window extends only the held-out4 s case;
it overlaps the first60 held-out inputs and is not independent. The primary
combat window is **not extended to90**, which would overlap the held-out PTS.

Virtual defaults are2 ms preparation, ideal8 Mb/s network,160 Mb/s QSPI,
8 ms decode,10 ms feedback and60 Hz presentation. IPv4/UDP wire accounting
adds40 application and28 header bytes per1,024-byte payload; RF/link/retry,
control/input/audio bytes and actual source capture/scale are excluded. These
service assumptions are not inferred from the slower Python wall timings.

The strict interval is `[0,1000*N/30)` ms; for60 inputs the separate
diagnostic window is `[500,1500)` ms and drain1,000 ms. Ninety inputs use
`[500,2500)` ms. Independent validation checks exact half-open counts and a
disjoint presented/dropped/pending capture partition. A one-second diagnostic
count cannot establish sustained30 fps; endpoints are never shifted to pass.

Quality pools active RGB565-output MSE before converting to PSNR. Reports
separate common-presented IDs from newly admitted/lost IDs. Even common IDs
can have different reconstructed references/pixels. PSNR alone is not visual,
HUD or temporal acceptance. Network totals include admitted data during drain.

## Results

The four60-frame real pairs show **no restoration difference**. No coarse
period earns all required headroom/cooldown conditions before the input ends.
Primary combat presents59/60 and counts29 diagnostic IDs/s; the second clip
presents60/60 and counts30. Held-out combat presents54/60, counts27, has one
cap rejection, backs off at ID51 and ends at scale16. Held-out second clip
presents60/60 and counts30. The two policies have exactly matched presented
IDs/quality in these four pairs; this does not demonstrate restoration during
ordinary gameplay.

The90-frame exploratory held-out combat pair also remains identical:75/90
eventual frames,25 diagnostic IDs/s, two cap misses and final scale32 after
backoffs at51/86. Common75-ID quality is34.79 dB in both. The conservative
headroom gate never earns a finer trial in this busy window. This negative
result is retained rather than relaxing thresholds after seeing it.

The seeded synthetic60-frame sequence contains simple frames, moving ramps,
five noise frames, then a simple recovery tail:

| Policy | Eventual/60 | Diagnostic IDs/s | Cap misses | Final scale | Pooled presented PSNR |
| --- | ---: | ---: | ---: | ---: | ---: |
| Fixed8 | 55 | 25 | 5 | 8 | 36.22 dB |
| Monotone backoff | 55 | 25 | 5 | 32 | 34.44 dB |
| Restoring backoff | 55 | 25 | 5 | 8 | 35.21 dB |

All three present the **same55 IDs**. Restoration earns its first step after
ACK38 and its second after ACK44; the next prepared frames use16 and8.
Against monotone backoff this gains0.77 dB over the same55 presented IDs with
no cadence or frame-admission gain. On the simple flat tail45–59, fixed8 and
restoration are52.90 dB versus36.00 dB for monotone backoff. That large flat
color gain is not a claim of comparable improvement in a game scene. All
policies still reject the five high-entropy inputs.

The detector-off/on synthetic ablation also presents the same55 IDs and has
25 diagnostic IDs/s with five cap rejects. Detection adds a key (2→3) without
a rate gain, and common-ID PSNR changes36.286→36.219 dB. This threshold is
therefore **not a winning scene-cut optimization** on this fixture. The default
headroom policy should remain experimental; it is not a recommendation to
enable this detector or restore earlier in busy gameplay.

## Next gate

Measure detector/encoding/feedback costs, extend source diversity and quiet
recovery coverage, and agree a visual-quality floor. Improve headroom estimates
without a future-size oracle and test trial/rejection oscillation on real cuts.
Restoration should reclaim quality when safe; it cannot create capacity or
guarantee delivery of noise frames at fixed rate/cap. Combine only after
latency, memory/reference lifetime and actual service gates are measured.
