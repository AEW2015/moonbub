# WV32 sparse wide-motion escapes

This isolated Python feasibility probe serializes the retained wide vectors from
`../python-game-wide-motion-v32-study/`. It preserves those exact predictions,
coefficient payloads and reconstructed pixels. It changes the motion component's
byte accounting; it does not implement a complete wide-motion frame or receiver.
All 24 vector maps roundtrip through actual packets and the independent parser.

## Component syntax

The 16-byte little-endian header is `<4sHHHHI>`: magic `WV32`, motion-grid width,
height, narrow-map length, escape count, CRC32. CRC covers the first 12 header
bytes followed by the complete body. The CRC field itself is excluded.

For a wide component outside ±18 half-luma units, both components of its narrow
base entry are zero. That base is compressed by the unchanged frozen GM27 motion
encoder. Then sorted, unique `<Hbb>` entries carry block index, dx and dy. An
escape must exceed the narrow bound in at least one component, stay within ±68
in both components, address a zero base entry, and lie inside the declared grid.
The syntax-only decoder calls the frozen bounded GM27 narrow parser, never the
encoder. It rejects CRC errors, extra/truncated bytes, duplicate/reordered/outside
indices, incorrect domains and nonzero escaped base entries. No raw fallback was
needed for this bounded experiment.

## Results

The same 12 actual source frames per scene, 720×480, use the same accepted v30
strict reconstructed reference input as the original probe. Trial outputs do not
become references: this remains a noncausal matched-reference experiment.

| 12-source scene | Narrow original body budget | Wide raw-MV body budget | Wide WV32 prospective body budget | Improvement vs narrow |
|---|---:|---:|---:|---:|
| Mass Effect 2600 | 152,292 B | 157,686 B | 151,790 B | 0.330% |
| Mass Effect 7200 | 355,962 B | 358,571 B | 353,896 B | 0.580% |

The unchanged original raw-vector negative baseline is retained in each row.
Across 11 P frames per scene, raw motion's 7,601 B becomes 1,705 B / 2,926 B of
actual WV32 packets, including every 16-byte component header and 114 / 153
escape entries. Key-frame maps are also serialized and verified as artifacts,
but are charged zero motion bytes, consistent with both original frame budgets.

The prospective body is exactly **80 reserved frame-header bytes + qmap + actual
WV32 component + actual residual planes + current HU25 bytes + 60 binding
bytes**. No full body was serialized or CRC/reference bound together. Residual
planes and HUD bytes come unchanged from the pinned parent experiment. These
are hypothetical complete-profile sizes, not valid GM27 wire packets.

The original wider search reduced residual plane bytes by 1.04% / 1.47%, and
P-frame source YUV prediction SSE by 1.50% / 25.01%, with 3.00% / 4.03% of P-block
vectors outside the old range. Sparse escapes preserve those gains and remove
the raw-MV penalty. The resulting complete-body gain remains below 1% here.
This does not explain or close the much larger HEVC/AV1 compression gap.

`results.json` records actual WV32 pack time, including the frozen narrow
encoder's full candidate search, and separately records syntax decode time. Pack
time is added to the original fully paid baseline-plus-wide search work; original
costs were approximately 254 / 412 ms per source before that addition. This is an
unoptimized Python research pipeline, not a 30 fps/native throughput proof.
Acquisition, archival compression and validation replays are outside encode time.

## Reproduce

Use Python 3 with NumPy and the existing study virtual environment. From this
folder:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v test_model
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python verify.py
```

Eight focused tests pass, including missing/extra/reordered scene and row rejection. The verifier validates pinned sources, all 24 actual
packet artifacts and vectors, an additional direct narrow-base/escape-entry
reconstruction, complete budget sums, inherited metrics and paid encoder totals.
Retained `objects/*.zlib` contain actual WV32 component bytes, not size estimates.
`results.json` pins dependencies; `sourcepins.json` also pins final own artifacts.
The verifier requires exactly the two ordered scenes and IDs 0–11 per scene,
checks row alignment against the original wide study, and requires 24 maps and
267 escapes. It also validates every final source pin, including its own code
and results. The audit amendment updates only verifier/test hashes in the results
metadata; all producer hashes and numerical cases are unchanged.

## Next gate

A negotiated new frame profile must declare the wider prediction bound, serialize
all lengths/CRC/reference identity, reject malformed frames atomically, and
implement a bounded decoder. Then compare full causal reconstructed histories
and quality/latency against the narrow controller. A broader rate-distortion
search could decline a costly wide block instead of always keeping a sampled-SAD
winner. Hardware memory/bandwidth/throughput and HEVC/AV1 comparisons still need
separate validation. Existing GM27 compatibility is deliberately not claimed.
