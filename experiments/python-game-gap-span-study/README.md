# HD22: exact HUD deltas with minimum-cost gap packing

This Python component optimizes the v21 exact RGB565 display-patch experiment.
It is independent of YUV prediction and does not change video resolution,
quantization or base reference histories. HD22 is a new incompatible wire magic;
existing HD21/HC21 endpoints do not decode it. No native endpoint or RTL changes
are supplied here.

## Byte-optimal row partition

A span costs six header bytes plus two bytes per transmitted XOR word. Adjacent
changed runs separated by g unchanged words can be represented separately or
merged. Merging removes exactly one six-byte header and adds exactly 2*g zero
bytes. Each gap decision is independent, so merging gaps of one or two words
is globally minimum among ordered row-local spans. A gap of three words is a
tie and is canonically split; larger gaps split. A contiguous changed run stays
one span. This is a linear scan, not a search over gameplay futures.

This proof applies only to the declared fixed-header per-row XOR grammar. It
does not establish global entropy optimality, transform/motion-codec optimality,
or a general video coding bound. RAW and COPY remain alternatives; RAW wins
ties against a span payload. Parsing rejects redundant endpoints, short gaps
between records and long internal zero gaps to enforce the canonical partition.

HD22 keeps the v21 46-byte header and four-byte CRC, with geometry and exact
reference/current SHA256[:16] tags. Maximum geometry is720×480 and21,120 words
per patch. A packet is bounded by42,290 bytes. All results allocate fresh bounded
outputs and never mutate source/reference arrays on error. CRC/tags provide
consistency checking, not authentication or reset/rekey negotiation.

## Actual retained-sequence comparison

The campaign reuses all132 v21 HUD updates:96 native-source regression frames
from two48-frame Mass Effect windows, and36 separate static/sparse/noise controls.
Their528 current patches are original exact RGB565 fixture words. References
advance from actual selected decoded output, with immediate reliable ACK delivery
assumed. There is no transport schedule, loss/recovery or whole-video controller
in this independent optimization component.

Each patch pays the existing adaptive full HP01/HR01 encoder (including its
bounded exact-word cache), the old HD21 candidate and the new HD22 candidate.
Both comparisons independently choose the smaller complete patch against the
same actual legacy bytes, with legacy winning ties. All selected patches decode
exactly. Pure HD21/HD22 candidate gains must not be confused with final fallback
gains: a shorter delta still has no wire effect if legacy remains smaller.

| Case | Old HC21 HUD bytes | Proposed same-overhead bytes | HUD saving vs v21 |
| --- | ---: | ---: | ---: |
| Mass Effect2600,48updates |442,450 |427,966 |3.274% |
| Mass Effect7200,48updates |1,023,067 |981,385 |4.074% |
| Synthetic static,12updates |3,940 |3,940 |0% |
| Synthetic small change,12updates |4,928 |4,928 |0% |
| Synthetic noise,12updates |509,220 |509,220 |0% |

All528 HD22 candidates are no larger than their HD21 counterpart and independently
reconstruct2,787,840 exact words. Final selected native span patches increase
53→64 and64→88, displacing legacy full patches only where actually smaller.
Pure candidate bytes fall692,996→620,354 and1,186,222→1,090,826, but final sidecar
savings are smaller because legacy already wins many patches. Ten tests pass;
seven portable sampled goldens reconstruct26,880 words with seven CRC negatives.
Native and synthetic rows reuse prior fixtures; they are not new source captures.

Per-case results retain every candidate size/mode/span count, merged zero words,
changed words, SHA256 and measured stage work. Complete HUD numbers project the
same83-byte HC21 framing with a future new dispatch/profile; they are not an
existing HC21 packet. No base-video bytes or frame-binding/control bytes are
claimed eliminated by that arithmetic projection.

Fixture RGB565-to-RGB canvas reconstruction is performed only to run the actual
legacy compressor on the exact fixture words. This preparation, correctness
oracles and object export are excluded from paid encoder stage clocks; no claim
is made about capture or full host/target CPU cost. Python timings do not prove
ESP32/DSP/FPGA throughput or physical30fps. Peak NumPy/interpreter allocation,
native heap, QSPI/RF, SRAM/BRAM mapping and scanout deadlines remain unmeasured.

## Evidence and reproduction

The test suite exhaustively compares the partition cost with every partition of
every nonempty binary mask through ten pixels (2,036 masks), plus canonical ties,
seeded roundtrips, RAW/COPY/noise, endian/noncontiguous inputs and malformed packets.
The retained verifier independently scalar-decodes all528 HD22 candidates and
re-evaluates actual legacy/old/new selection on every source sequence. Sampled
goldens retain current/reference words and actual HD22 packets.

```sh
python -m unittest -v test_model.py
python benchmark.py
python verify.py
```

Use the existing project environment with NumPy/Pillow. The source fixture objects
are local and hash-pinned; no external gameplay video download is required.
`results.json` separates native and synthetic outcomes, including cases with no
improvement. Preserve frozen earlier studies when regenerating results.
