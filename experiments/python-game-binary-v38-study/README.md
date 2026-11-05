# AB38 adaptive binary coefficient coding / CS38 packet pilot

This new Python research syntax preserves all existing quantized coefficients,
reconstructed references and displayed pixels. It replaces Rice event bit strings
with adaptive binary arithmetic coding, while retaining the actual CS37 plane
payload as a no-growth fallback. It is not installed firmware or an FPGA result.

| First12 causal frames | CS37 bytes | CS38 bytes | Complete-byte saving |
| --- | ---: | ---: | ---: |
| Primary | 129,084 | 114,889 | 10.9967% |
| Complex | 302,953 | 271,410 | 10.4118% |

All72 plane choices select arithmetic:9 full-grid and63 compact nonhidden-grid
payloads. Both alternatives are actually encoded and retained for each plane,
including losing choices:144 AB38 packets in total. Complete frames never grow
because the old representation wins ties. These are12-frame prefixes, not the
older full48-frame campaigns; keyframe weighting differs.

AB38 has a bounded header with geometry, four stream lengths, three nonzero
counts and whole-packet CRC. Each stream records its Rice parameters and exact
arithmetic bit count. DC uses row-reset deltas; three block-major sparse AC bands
carry run and mapped signed level events. Rice parameters minimize uncoded Rice
cost; this is not an arithmetic-optimal parameter search. A raw int16 fallback
bounds component length. All headers, stream metadata, termination and padding
are included in byte counts.

The arithmetic machine uses a16-bit interval,8-bit adaptive zero probability,
one17×8 unsigned probability product per binary event, shift-only adaptation and
E1/E2/E3 renormalization. Four independent streams each have88 probability
contexts. **352 bytes is logical packed probability state**, not measured Python
heap, FPGA BRAM use, a DSP count or fitted throughput. The decoder strictly checks
bit lengths, padding, termination, coefficient bounds, run bounds and CRC.
No division by a changing frequency total is required by the specified update.

New CS38/GS38 magic/profile identify plane dispatch5 (full arithmetic) and6
(implicit-hidden arithmetic); old dispatch0..4 remains a fallback. The80-byte
outer budget and exact HX33 are unchanged. Original source metrics are preserved:
active MSE14.362737 /26.378421 on these prefixes. Native anchors still outperform
these sampled custom points; see the v38 comparison report.

`decoder.py` imports no encoder. `frame_verify.py` independently decodes the new
payload, re-encodes decoded coefficients in frozen entropy and invokes the frozen
CS37 receiver to qualify tags, references, exact HUD and display. This adapter
stages full arrays/packets and is **not a native receive architecture**. No receiver
latency or FPGA streaming proof follows from it. Three component and three
independent frame-corruption tests pass; all24 causal frames and144 alternatives
replay. Probability products and renormalization totals are algorithmic work
counts, not cycles.

Both full and compact arithmetic candidates are paid. Their encode costs total
55.10 /116.91ms per source frame on this host, excluding the already-paid CS37
input encoding, input packet parsing, validation/decode, fixture/HUD generation
and archive I/O. These are candidate-component clocks, not a complete sender or
30fps claim. A direct sender needs a separate integration and measurement.

```sh
cd experiments/python-game-binary-v38-study
python -m unittest -v test_model test_verify
python verify.py
```

Inputs, actual candidate/frame packets, producer code and final independent
decoder/replay files are bound by the v38 provenance inventory. No held-out
gameplay, new native encoder, RTL, ESP32 transport or hardware is qualified here.
