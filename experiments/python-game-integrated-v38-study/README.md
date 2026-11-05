# V38: integrated direct GS37/CS37 sender

This Python sender combines the qualified fast fixed-zero analyzer, exact direct
coefficient/RDO decision path, compiled canonical-reference normalization and
implicit hidden-block grammar. It constructs CS37 directly instead of first
constructing CN36 and then parsing/transcoding its coefficient components.

All **102 actual CS37 packets are byte-identical** to the retained v37 implicit
packets: 96 main frames and a separate six-frame fractional-motion probe. Causal
normalized references, exact HUD pixels and displayed frame metrics are unchanged.
This iteration changes sender work, not compression decisions or image quality.

| Window | Fast CN36 sender + implicit transcoder | Integrated CS37 sender | Ratio | Time reduction |
| --- | ---: | ---: | ---: | ---: |
| Primary, 48 frames | 66.013235 ms | 52.330068 ms | 1.2615× | 20.7279% |
| Complex, 48 frames | 94.977235 ms | 65.397145 ms | 1.4523× | 31.1444% |
| Directed motion probe, 6 frames | 109.839600 ms | 76.966208 ms | 1.4271× | 29.9285% |

The means are calculated from per-frame paired medians. **Every frame has three
alternating paired repetitions**, with order changing by frame/repetition. Both
one-output sender clocks include the same fixed-policy source/reference
validation, fast preparation/forward transform, quantization, RDO and original
unmasked plane-global legacy-size reversion decisions.

The baseline additionally pays actual CN36 entropy construction, reconstruction,
normalization and wrapping, followed by the frozen implicit transcoder's parse,
compact entropy construction, fallback selection and GS37/CS37 sealing. The
integrated sender evaluates the same full-grid and compact costs but serializes
only the winning component per plane, reconstructs once and wraps GS37/CS37
directly. Full-grid fallback retains exact complete-payload ties.

Fixture/source/HUD reads or generation, precompiled geometry import setup,
archives, metrics/hashes/equality assertions, receiver, network, queueing and
display are outside these sender clocks. The directed motion probe retains the
same common preparation adapter cost on both sides: zero preparation followed
by replacement with forced `(-3,+1)` half-pixel vectors/prediction/forward data.
It is not an optimized searched-motion sender. No timing ratios are multiplied
or subtracted across earlier campaigns.

## Preserve visible decisions while avoiding discarded work

```python
encode_prepared(prepared, scale_map, hud, rdo_lambda=1)
# -> actual_CS37_bytes, normalized_owned_planes, work
```

The preparation must use the frozen owned `Prepared` type, epoch25 and720×480
geometry. The main policy keeps key interval24, block32, zero motion and the same
ROI8/background16 map as v37. Both main clips fit the complete49,152-byte cap.

The encoder intentionally preserves quantization, RDO and all original **unmasked
global plane-reversion comparisons before suppressing hidden blocks**. Changing
those comparisons could alter visible coefficients. After their decisions it
zeros hidden coefficients and plans two representations per plane:

- Full-grid frozen entropy grammar with the original raster width.
- Dispatch4 plus frozen entropy for only visible blocks in raster order, width1.

The complete payload winner is selected by exact byte count. The integrated path
performs six plans and only three actual plane constructions. It emits no CN36
intermediate packet, performs no coefficient syntax parse, calls no transcoder,
and needs one output reconstruction and canonical normalization. Original RDO
analysis/its reconstruction work remain paid and are not an inverse bypass.

Header syntax and fixed opaque profile are the frozen GS37/CS37 contract from
v37, with no new bitmap or extra transmitted fields. Inner reconstructed tags and
outer canonical-reference tags are computed directly. The actual fixed HUD is
bound and later independently decoded before receiver publication; this sender
does not replace the separately qualified receiver or its malformed-input rules.

Main complete budgets remain **434,875 /1,057,390 bytes**, with maxima22,569 /
41,224 and active MSE14.38366067 /26.54469598. The motion probe remains109,308
bytes. Main implicit selection counts are138 /74 planes. These are unchanged
v37 packet budgets, not new compression savings attributed to integration.

## Verification

Four producer tests pass. They verify actual key-packet parity, behaviorally
forbid old full encoding/CN36 wrapping and coefficient parsing, count exactly
three component constructions, force complete-payload ties to retain full-grid
fallback, force a three-plane global RDO reversion, and reject invalid inputs
without source mutation. Scoped mocks are restored after each test; production
code never patches frozen module globals. The retained campaign takes no actual
global-RDO reversion branches; the directed test explicitly covers that case.

Independent replay imports no new sender. It checks all actual archived packet
bytes, complete lengths/caps, whole causal normalized references, source/display
hashes, HUD, quant maps, motion and coefficients. It independently recomputes
frozen original quantization/RDO/plane-reversion decisions for each actual causal
reference, and independently constructs full-grid and compact alternatives to
check exact winner/tie semantics. Three independent tests and final replay logs
are retained separately, along with source pins and actual packets.

The reused short Mass Effect windows and directed motion probe are not a held-out
corpus. Sender times still exceed33.33 ms before receiver/transport/display. This
is not physical30fps, native ESP32/FPGA qualification, an inverse-transform bypass,
or evidence of HEVC/AV1 superiority. The frozen wire identity permits carrying
forward v37's byte/quality comparison; it does not improve that comparison.

```sh
cd experiments/python-game-integrated-v38-study
python -m unittest -v test_model
python -m unittest -v test_verify
python verify.py
```

`results.json` binds the exact producer and inherited source dependencies. The
outer v38 portable inventory separately binds independent replay/test files and
all retained evidence.
