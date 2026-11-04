# V21 base and display-cache composition

This component connects the new exact display-cache experiment to the retained
v20 image contract without changing the inner video codec. Geometry remains
720×480 coded /720×405 active. It supplies **offline functional composition and
necessary transport-budget calculations**, not an installed streaming profile.

## Actual image replay

Ten mandatory-HUD v20 goldens retain their exact inner AR03 bytes, quantization,
predictor identity, precondition banks and publication tags. `strip_patches`
sets only the outer patch count/length to zero and recomputes the AR03 CRC. A real
AR03 receiver decodes that valid patch-free packet. A separate HC21 receiver
decodes the four original RGB565 patches. Applying those patches to the base
must reproduce every word of the v20 full display and every reconstructed YUV
sample. AF03 now binds the new AR03 body CRC; the old AF03 must not be reused.

CB21 is a bounded **offline fixture container**: a 53-byte header binds epoch,
frame, component lengths and each SHA256[:16], followed by valid AR03 and HC21
bytes and a four-byte CRC. It costs 57 bytes. Corrupt components still reject
after an attacker repairs only the outer CRC. This is integrity checking, not
authentication. The default admission check rejects a complete fixture over
49,152 bytes. Explicit diagnostic replay can inspect over-cap vectors; that
does not count them as admitted gameplay frames.

The two receiver components are invoked separately. There is **no implemented
joint private prepare/commit**, no protocol negotiation/reset handshake, no
GF03/FG19 carriage of CB21, and no hardware/DMA publication proof. In particular,
HC21 component sequencing cannot be used as a whole-video admission policy.
Native integration must admit a whole bounded pair before consuming identity,
validate both privately, and publish their matching display epoch atomically.

## Honest byte and latency comparisons

All 96 native-source HC21 rows are matched to v20 by frame ID, source-canvas hash
and actual legacy patch bytes. The new accounting body is:

```
original AR03 bytes - original patch section + HC21 bytes + 57 CB21 bytes
```

This conservatively includes the actual offline binding container. No original
base quantizer or YUV history changes, and all requested HUD words remain exact.
This is a candidate integration budget, not proof that existing peers accept it.

For each row, data counts use 1008-byte payload fragments with 31-byte GF03,
16-byte token and 28-byte IPv4/UDP overhead. Two forward and three reverse FG19
messages, one 57-byte reverse PC18 per fragment, one 71-byte AF03 and the new
54+28-byte HA21 are included. Reverse grants/credits/reference/cache ACKs are
distinct. Counts omit retransmissions, queries, Wi-Fi airtime, capture, audio
and input. A symmetric virtual rate is assumed for the optional rate sweep.

The stop-and-wait sweep optimistically overlaps forward and reverse transfers:
`max(forward serial time, reverse serial time) + supplied minimum feedback delay`.
It sweeps 8/12/16/24/40 Mb/s and 0/5/15/30/40 ms. It ignores all CPU, DMA/QSPI,
actual control-round-trip dependencies, display and arbitration. A failed bound
rules out the stated simple operating point; a passed bound proves no feasible
frame rate. It is arithmetic, not ESP32 instruction/RF emulation.

The clips are the same reused two 48-frame 29.88-fps windows as v20. Rate
projections schedule 30 IDs/s; they do not acquire or display 30 native frames/s.
Python encoder/decoder wall time in the HC21 result is actual host component
work with all competing patch modes paid, not target throughput.

## Reproduction

Use the project Python environment with NumPy/Pillow/PyAV for regeneration.
Retained verification needs NumPy/Pillow and local source/objects, not video files.

```sh
python -m unittest -v test_model.py
python verify.py
```

`benchmark.py` regenerates the ten pair fixtures and calculations only after the
HUD-cache component is frozen. It pins its local helpers and dependency sources.
`verify.py` independently replays all pairs and recomputes every budget row.
