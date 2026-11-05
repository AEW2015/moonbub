# V36: compile fixed opaque geometry once

This independent Python component optimization produces exactly the same owned
planes as frozen v35 core8 masking. It retains complete aligned8x8 transform
blocks only when their entire RGB interpolation footprint is opaque. It handles
overlapping rectangle unions, holes, odd boundaries and clamped image edges.

The compiler converts the fixed geometry to immutable merged horizontal runs.
`apply_plan(planes, plan)` validates all three integer420 planes, makes owned
copies and writes128 along those runs. A plan is trusted local compiled state,
not an untrusted wire object. Recompile when geometry or opaque rectangles change.

Across all96 retained source frames, three alternating paired repetitions give:

| Component | Mean of per-frame paired medians |
| --- | ---: |
| Frozen mask with planning each call | 4.288245ms |
| Precompiled apply, including validation and plane copies | 0.110502ms |

This is **38.81x at component scope**. Compilation costs4.196960ms once, excluded
from per-frame apply. Both outputs are byte-identical across all96 inputs.
Amortizing that single compile over these96 frames gives0.154220ms/frame
(about27.8x versus frozen); this remains component arithmetic, not sender timing.
Three tests additionally cover random rectangle unions, interpolation boundaries,
partial transforms, ownership and invalid inputs without source mutation.

The fixed profile has256Y+19Cb+19Cr blocks (18,816 stores) and88 merged row spans.
A hypothetical uint16 `(y,x0,x1)` serialization would occupy528 bytes; this is
an estimate, not Python tuple memory or a new transmitted header. Current owned
int16 output planes occupy1,036,800 bytes (518,400 logical uint8 samples).
Compiler coverage/integral temporaries are host allocations.

Timing excludes fixture decoding, equality checks, output hashing and archive I/O.
It does not time a whole sender, ESP32, FPGA or display. It is not combined with
the separate canonical-reference experiment or v35 map reuse into a sender claim.
There is no changed wire syntax or image quality in this component experiment.

```sh
cd experiments/python-game-maskplan-v36-study
python -m unittest -v test_model
python verify.py
```

`results.json` pins producer code and all inherited input dependencies. The replay
checks exact ordered source identity, frozen-output parity and output hashes.
