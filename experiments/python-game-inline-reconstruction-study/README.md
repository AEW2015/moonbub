# Inline canonical tagging from actual reconstruction — v20

This hardware-development prototype removes a separate reference-bank tag reread.
It preserves the experimental AR03/AF03 contract, 720×480 coded geometry and exact
compact YUV8 reconstruction. It does not provide an installed decoder or a fitted
FPGA, native-clock or physical 30 fps qualification.

`model.py` validates the complete actual AR03 packet, dequantizes one coefficient
stripe, runs the frozen exact sparse Q14 inverse, adds the prediction tile and
clips to 0…255. It pushes each **newly generated** compact tile into `StripeTagger`
**before** writing that tile to the external output-bank oracle. A sentinel check
proves that the tag input did not come from the already reconstructed output bank.
Full completed planes are never traversed as tag input.

One uint8 stripe reorders 8×8 block output into raster rows. One little-endian
int16 row expands those compact values for SHA-256, preserving the canonical
`<HH` width/height prefix followed by Y, Cb and Cr rows. The private tag is the
first 16 digest bytes. The stream includes cropped valid edge samples, not padded
coefficient-block samples. Display-only exact RGB565 patches never enter this tag
or the YUV prediction bank.

A tag becomes available only after explicit all-plane completion and expected-tag
comparison. Only KEY/PROMOTE-eligible decisions may expose `publication_tag` after
validated packet completion. Ordinary P tags in this proof are private diagnostic
checks; they do not publish a reference and their hash work is not charged as a
required target operation in the timing model. Actual bank ownership, atomic bank
publication, AF03 generation and stale epoch handling belong to the receiver
controller; this standalone tagger does not replace those gates.

The functional proof checks **16 actual packet decisions, 97,308 blocks,
6,227,712 residual samples, 6,224,472 reconstructed YUV samples and 253,440 selected
original RGB565 words** against the frozen vectors. Twelve native decisions reuse
six source acquisitions across GM/exact cohorts; four flat controls exercise SR
and cropped geometry. The 15 tests include corrupt AR03 rejection before output,
reordering/duplication/truncation, failed expected tags, stalls, abort, ordinary-P
publication suppression, a generated partial-geometry fixture, and a conditional
case where inline copy work loses against fast bank memory.

## Service results and explicit costs

`results.json` retains five matched conditional schedules derived from the actual
v19 stripe demands. Hash/expansion assumptions are equal in each serial and inline
comparison. Reconstruction stripes remain owned until **both** compact writes and
copy/expansion/hash drain. Hash backpressure can therefore stall inverse and entropy
prefetch. Copy work, canonical expansion, SHA throughput, cache fill/preflight,
reference reads, compact writes, SHA final padding/compression service, color/output
and the average scanout reserve are
paid; no free hash stage or unmodeled SDRAM read port is assumed. Both matched
models include SHA-256 final padding/compression service; the final stripe and
publication permission wait for that digest-ready point.

| Profile | Serial mean ms | Inline mean ms | Conditional saving |
| --- | ---: | ---: | ---: |
| Hash 100 MB/s, default memory | 67.6298 | 62.8622 | 7.05% |
| Hash 25 MB/s, default memory | 88.3671 | 83.5994 | 5.40% |
| Hash 400 MB/s, default memory | 62.4455 | 57.6779 | 7.63% |
| Hash 100 MB/s, effective memory 240 MB/s | 53.4540 | 52.4816 | 1.82% |
| Hash 100 MB/s, one coefficient stripe | 67.9010 | 63.1335 | 7.02% |

The native published decisions eliminate **4,147,200 physical compact-bank reread
bytes** across twelve related decisions. Canonical hashed bytes are unchanged;
streaming avoids the physical reread, not SHA work. All native decisions in all
five profiles still miss the declared 33.33-ms single-frame budget. This conservative
serial schedule is not a target throughput upper bound or a full multi-frame
pipeline simulation. More overlap or a measured hardware implementation needs
separate proof. A fast-memory test demonstrates that additional inline copy work
can outweigh the removed reread; the gain is not universal.

At 720-wide geometry, the tagger's measured ndarray allocation is **7,200 bytes**:
5,760-byte compact stripe plus 1,440-byte canonical row. The conditional local plan
conservatively adds those bytes and **128 bytes SHA state + 64 bytes control state
as assumptions** to the v19 decoder plan, reaching **107,504 bytes** with two
coefficient stripes, or 95,984 bytes with one. It does not claim buffer alias reuse.
Python/hashlib control heap, full parsed packet/coefficients, stripe NumPy inverse
temporaries, external prediction/output banks, fixture arrays and export buffers
are outside the tagger ndarray claim. Parser/control implementation state remains
outside the complete decoder fit claim. No BRAM/DSP/resource mapping is supplied.

The inherited planning assumptions remain: 100 MHz, hypothetical wide arithmetic
slots, 140 MB/s effective SDRAM before an average 800×480×60 RGB565 reserve,
20 MB/s QSPI, a full 49,152-byte compressed cache and four full-packet preflight
planning passes. The 240-MB/s row is a sensitivity assumption. Physical 480×800
scan order/line deadlines, FPGA arbitration/Fmax and ESP32 ISA/heap/RF are not
calibrated. Reference-tag-ready, earliest compact-bank-publication and display-ready
instants are retained separately; a hash result alone does not authorize display.

## Hardware-development fixtures

[SCHEMA.md](SCHEMA.md) defines the small `IT20` generated-tile file format. Sixteen
frame decisions reference **nine content-addressed compressed streams** (identical
outputs deduplicate), totaling less than 600 KiB compressed. Each contains exact
ordered cropped uint8 reconstruction tiles, suitable for a SHA/tagger RTL testbench.
The manifest carries packet identity, expected tag, publication eligibility and
reconstructed/display hashes. IT20 is a **golden-file format**, not a negotiated
network packet or a replacement for the AR03 parser.

For integration, feed the receiver's newly generated compact tiles in the declared
plane/stripe/block order. On stalls, retain the current tile and ownership until
accepted; do not advance coordinates. On CRC/order/tag failure, abort the private
candidate and emit no bank-publication event. On success, the controller must also
confirm actual external-bank writes and its epoch/frame/body/owner identity before
publishing AF03. Keep RGB/front-buffer completion as a separate permission.

## Reproduce

The retained verifier requires Python 3.10+, NumPy and the inherited Python codec
dependencies; the repository environment includes NumPy, Pillow and PyAV. It needs
no external source video: all packet, coefficient and output fixtures are pinned.
From this directory:

```sh
python -m unittest -v test_model.py
python verify.py
python analyze.py --check
```

`benchmark.py` regenerates output objects and results, snapshots conservative
relative source/object hashes before and after, and records Python wall execution
time separately from conditional service. Do not change pinned source during a
run. `verify.py` independently regenerates actual tile outputs, replays all IT20
objects and reconciles every schedule without regenerating timings. The study
changes no older source, firmware or bitstream.
