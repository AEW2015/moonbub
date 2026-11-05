# V37 CS37: implicit hidden transform blocks

This new research grammar removes fixed, fully hidden8×8 blocks from a plane's
entropy sequence. Dispatch4 carries only nonhidden blocks in raster order with
entropy width1. The known opaque profile determines the missing positions;
there is no transmitted bitmap, per-block index or variable hidden geometry.
The decoder fills omitted coefficients with zeros before frozen reconstruction.

Each plane also tries the existing full-grid payload. Ordinary dispatch0..3 is
retained without an added prefix if compact encoding is larger or tied. Thus
the complete CS37 packet never exceeds its input CN36 skip packet. Compact
dispatch4 adds one byte before an ordinary frozen entropy payload; that cost is
included in every trial. Reflowing visible blocks can improve or worsen entropy
prediction, so omissions are measured rather than priced as free bytes.

| 48-frame clip | CN36 skip bytes | CS37 actual bytes | Additional saving |
| --- | ---: | ---: | ---: |
| Primary | 441,520 | 434,875 | 1.5050% |
| Complex | 1,060,332 | 1,057,390 | 0.2775% |

There are138 /74 selected compact planes out of144 per scene. The other76 main
plane payloads keep the exact fallback representation. A six-frame half-pixel
motion probe saves1.4489% (110,915→109,308 bytes), selecting15 compact planes.
All102 frames have exactly equal reconstructed normalized reference planes,
coefficients, HUD and displayed pixels to the corresponding CN36 skip history.
Scene MSE remains14.383661 /26.544696; maxima remain22,569 /41,224 complete bytes.

Outer magicCS37, inner magicGS37 and a new profile digest distinguish this
grammar. The80-byte outer format binds reference/output tags, geometry, packet
lengths and exact fixed HX33 rectangles. Inner GS37 keeps the frozen map/motion
envelope and adds residual dispatch4. CRC, lengths, semantic decode and both
reconstructed tags precede modeled state publication. This needs a new receiver
and negotiation; it is not a drop-in firmware update.

The independent decoder imports no new encoder or mask implementation. It uses
v36's independent scalar support enumeration and frozen entropy/arithmetic.
It verifies all102 causal packets and expanded coefficient arrays. Four producer
tests and three independent semantic-corruption tests cover fractional motion,
invalid profiles, CRC/truncation, unknown dispatch, wrong reconstruction/prior
tags, replay and failure without publication.

This proof is a **transcoder from already encoded CN36 skip**, not an integrated
sender. Mean per-frame median transcoding costs19.85 /36.98ms on this host;
three repetitions include input parse, compact entropy construction, fallback
choice and sealing. Old encoding is externally paid; equality, fixtures,
archive I/O and receiver work are outside the clock. Do not add/subtract these
times from the separate direct-sender benchmark.

The Python decoder expands arrays and runs existing inverse reconstruction.
An implicit FPGA inverse bypass, new native firmware, ESP32 transport and
physical30fps are unimplemented. The small complex-scene saving is a useful
negative bound on this entropy-only idea, not a standards compression victory.

```sh
cd experiments/python-game-implicit-v37-study
python -m unittest -v test_model test_verify
python verify.py
```

Producer code, actual compressed packets, input dependencies and final replay
files are frozen by the outer v37 provenance manifest. The two gameplay windows
are reused; the directed motion probe is not held-out gameplay.
