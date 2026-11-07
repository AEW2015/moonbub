# V95: exact pixel palettes for the Game Bub codec

V95a–c now have a bounded software implementation and retained-corpus evidence.
The rate policy keeps the previous control on every tested frame. Two optional
byte-budget policies can bypass some residual blocks at higher traffic cost;
they remain research candidates. No palette decoder has been promoted to RTL.
See [results and decision](results.md), [contract audit](audit-notes.md), and
[qualified summary](../../experiments/python-gamebub-v95/summary.json).

## What was implemented

CS95 version 1 retains 720×480 canonical Y/U/V pixels, COPY/hidden CONST128
semantics, quantizer maps, HUD composition, RGB565, content roots, seals and
atomic accepted-reference publication. Its explicit profile separates it from
CS92/CS94: older receivers must reject the new magic. Palettes represent exact
reconstructed **pixel samples**, not transform coefficients. Palette tiles
write directly into the existing candidate image and bypass residual decoding,
dequantization, IDCT and reference prediction. Coefficient fallback tiles retain
exact original active coefficients. Original-coefficient equality is not a claim
for tiles represented as pixels.

Each canonical 8×8 plane tile can use an own palette of one through eight sorted,
unique U8 entries, packed indices, TOP/LEFT prediction with literal runs, indexed
escapes, or RAW. Reuse references only the preceding palette in the same plane;
RAW clears it, and each plane/frame starts empty. A skipped encoder candidate
cannot teach the dictionary. There is no cross-frame dictionary negotiation.
The bounded record grammar and its 138-byte maximum are in the
[audit](audit-notes.md) and independent [Python reader](../../experiments/python-gamebub-v95/python/codec.py).

A plane serializes big-endian `pal_count:u32`, then sorted entries
`tile_position:u16, record_length:u16, record`, then
`residual_blocks:u32, entropy_length:u32, EC92_bytes`. The complement of the
palette positions is actually re-encoded with EC92; subtraction from an old
entropy stream is never used as a byte estimate. With no palette, its twelve
fixed bytes match the old plane directory cost. No per-record checksum is added:
the outer CRC plus semantic roots cover complete frames.

The host prepares six variants per plane: control, P2/P4/P8, E8 and W8. Entry
caps are 2/4/8, and complete per-record admission thresholds, including the
four-byte directory entry, are 16/24/40/40/64 bytes. E8 and W8 allow escapes.
A shortest-byte run search is bounded to 65 positions and runs of at most 64
samples. Complete-frame selection enumerates 216 plane-profile tuples;
it does not globally optimize every possible subset of the 8,100 frame tiles.
The minimum-byte selector and work5/work15 use a strict 49,152-byte receiver.
Uniform diagnostic palette profiles use an explicitly separate 2-MiB research
receiver and never demonstrate normal-cap admission by that fact alone.

## Reproduction

From the repository root, use Python 3 and the existing
`gamebub-cu66-v69-build` container with GCC 13.3. Retained V82/V85/V88/V92 data
and their verified indices are required; they are inherited from the baseline.
These are software experiments; no board, Renode model or Vivado license is
needed for the V95 tests below.

```sh
# Compare the two retained native qualification attempts:
python3 experiments/python-gamebub-v95/native/verify_repeat.py \
  "$PWD/experiments/python-gamebub-v95/native/attempts/20261107T061743203157Z-8eab340c/results.json" \
  "$PWD/experiments/python-gamebub-v95/native/attempts/20261107T062130291445Z-c7b8e637/results.json"
python3 scripts/cu66-v95/test_python.py
python3 scripts/cu66-v95/audit_corpus.py --index experiments/python-gamebub-v95/native/attempts/20261107T061743203157Z-8eab340c/results.json
python3 scripts/cu66-v95/run_wire.py --native-index experiments/python-gamebub-v95/native/attempts/20261107T061743203157Z-8eab340c/results.json
python3 scripts/cu66-v95/test_wire.py
python3 scripts/cu66-v95/test_selection.py
python3 scripts/cu66-v95/summarize.py
python3 scripts/cu66-v95/bundle_manifest.py
```

To regenerate native candidates, run `python3 scripts/cu66-v95/collect_palettes.py`
twice and pass those two immutable report paths to repeat verification. Update
the dependent campaign input paths to the first new report. The command block
above reuses the two retained native attempts. Qualification receipts pin immutable inputs, so rerunning a collector
creates new attempts rather than rewriting qualified evidence. Re-run dependent
campaigns if selected input reports change. The checked-in full-wire campaign
pins the first native report; the second is byte-identical and both are retained.
Reports and copied sources bind executed binaries and artifacts, and unsuccessful
attempts remain available rather than being relabeled as successful.

## Next decision

Retain the rate control. V96 should measure actual COPY/prediction/constant
traffic, memory ownership and stalls in the complete decoder path. Only promote
palette work if calibrated full-path cost demonstrates a useful benefit after
its extra bytes, pixel writes and packet parsing. Add broader raw captures before
claiming a gameplay-wide gain. Lossy clustering, global palette dictionaries,
variable tile shapes, palette RTL and a production host encoder are deferred.
V91l, V92d and V94's remaining full-path gates stay open; V100–V110 retain the
planned 7-series placement, routing and timing focus. Sustained hardware 30 fps
and validated complete decoding below 10 ms remain unproven.
