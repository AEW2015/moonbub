# Exact AR03 entropy traces and native lifecycle vectors

This study removes the v17 memory model's proportional entropy-byte apportionment
for **retained actual packets**. It walks CP02 tokens, records the selected
streams' exact per-block bit cursors and byte refills, and groups those records
into eight-row plane stripes. It retains full AR03/GF02/AF03 lifecycle bytes,
canonical reconstructed YUV banks, display RGB565 and exact source arrays.
No native/FPGA timing, physical 30 fps or fully streaming decoder is claimed.

## Results

- Three cohorts and **16 actual AR03 packets**: six native frames in GM, the same
  six in exact GM/SR selection, and four partial-geometry flat SR controls.
- Twelve native decisions are only **six related source acquisitions**, not
  twelve independent captures. They come from the previously used precompressed
  clip at four seconds, BOX-scaled to 720×405 inside 720×480.
- Each native cohort follows key0 → promotedP1 → P2 → independent refresh3 → P4
  → promotedP5, using epoch18 and actual content-bound AF03 feedback.
- All twelve native frames select all four UI regions: **253,440 original
  RGB565 words** checked exactly in aggregate. YUV reference state remains
  independent of display patches.
- **244 real GF02 datagrams**, reassembled in reverse chunk order during replay.
- **97,308 coefficient blocks** walked and checked exactly against the frozen
  coefficient decoder; actual selected GM01 and SR01 formats both occur.
- **53 malformed/binding operations** reject atomically in the declared positive
  preconditions, preserving bank identities/arrays, decoded ID and reader ownership.
- **215 content-addressed objects / 3,466,147 stored bytes**, plus the manifest.
  zlib packages fixture arrays/trace JSON offline; it is not video compression.
- **Eight tests pass**; **43 conservative source/dependency snapshots** match.
  Dependency discovery metadata are pinned too; pins are not an exclusive list
  of executed source code.

A concrete nonuniformity matters for future scheduling: native GM independent
refresh ID3 luma consumes **16,375 selected-token refill bytes** over 60 eight-row
stripes. Uniform block-count apportionment predicts 272.92 bytes/stripe, while the
actual peak is **2,470 bytes, 9.05× that mean**. This is logical decoder refill
demand, excluding header/parameters/CRC/preflight; it is not a measured SDRAM
burst or a 9× speedup. `stripe-demand.json` conserves the exact refill bytes for
all 48 plane traces and binds itself to the retained result and analyzer hashes.

## Parser and causal trace contract

Import `trace_codec.parse_packet(packet)` for a JSON-safe trace. The function
validates AR03 syntax/UI and records each plane's complete packet-relative payload
offset, selected format, coefficient hash and ordered eight-row stripe records.
It separately invokes the frozen full parser as a correctness oracle; that oracle
is not used to infer token boundaries. Header geometry determines expected block
counts. The exact walker derives each next bit position by consuming syntax.

`iter_cp02(packet,blocks,blocks_w)` yields one 8×8 coefficient block and record.
It supports actual RAW and Rice modes. The Rice walker has separate DC and AC
cursors/reservoirs, consumes row-reset DC deltas, EOB/ZRL/run prefixes, signed
values and bounded canonical escapes, then checks complete zero padding. A
byte-at-a-time refill needs no future coefficient search. Each reservoir is
asserted at most64 bits; the observed single-reservoir maximum is **21 bits**.
The two-reservoir bound is128 bits, not a whole-decoder storage claim. Per-block
zigzag/output work uses bounded block arrays; Python full output arrays and traces
are retained by convenience wrappers outside that bound.

Records retain logical bit ranges and actual byte-refill ranges relative to the
CP02 header. Rice parameters, CP02 header and CRC ranges are separate. A read can
bring up to seven not-yet-consumed bits into a reservoir; this bounded lookahead
is explicit, not future-state byte estimation. RAW mode records its exact128-byte
coefficient block range and uses no Rice reservoir. Exhaust the iterator to
validate terminal padding; a consumer stopping early has not validated the stream.

SR01 dense planes add their SP01 offset. Split planes preflight their two-bit
mode map/counts, then walk output block order with one cached map byte, signed
DC values and a compact CP02 stream for full blocks. Compact block IDs differ
from output IDs, so each full record retains both and its CP02 base offset.
Map preflight is a separate pass. No full future coefficient array chooses an
entropy length; selected formats' offsets and lengths come from actual headers
and actual token consumption.

See [SCHEMA.md](SCHEMA.md) for offset composition and fixture representation.

## Bounds and what is not proved

The complete compressed input packet is retained. CRC/header/UI/map preflight,
full frozen-parser oracle, decoded coefficient arrays, source/output arrays,
reference banks, metadata/JSON and fixture decompression are **outside** the
bounded-reservoir claim. These Python convenience functions are not a fully
bounded end-to-end decoder, an incremental wire/CRC machine, or a hardware memory
allocation proof. Physical cache transactions, burst alignment, parser stalls,
RAM ports, issue cycles and native CPU work are not measured. Full-frame CRC
preflight happens before the walker; a two-pass memory architecture must charge it.
Mode-map checks can rescan retained map bytes; the recorded refill ranges are the
semantic selected decode demand, not all Python memory/cache loads.

This is selected syntax only. It does not assign costs to unencoded candidate
modes or prove host encoder speed. Six related native frames do not establish
quality or throughput on broad gameplay. Input native material is already
precompressed; display equality is against the scaled input RGB565 words, not
an uncompressed original game render. No candidate/commit or gateway timing is
integrated here; those are separate parent studies.

## Reproduction and handoff

```sh
python verify.py
python analyze.py --check
python -m unittest -v test_trace.py
```

Use the project's NumPy/Pillow/PyAV environment. `verify.py` needs only retained
objects, not external video. It hashes every object used, reassembles actual
GF02, decodes the lifecycle, compares canonical arrays/tag identities/AF03 and
pixel hashes, and rederives every exact coefficient cursor trace. Negative
operations include truncated/bad outer CRC, false stored reconstruction tags and
wrong source-reference tags under resealed CRC. Parser guards additionally cover
noncanonical escapes, truncated unary, run/ZRL overrun, nonzero padding, RAW range,
partial geometry, dense/split SR and signed DC extremes.

`export.py` regenerates the native evidence and requires the media file. Sources
are pinned before export and checked after; `analyze.py` is an untimed supplemental
check. `failed-initial-verify.log` records an initially incorrect negative-fixture
header field index; it was corrected before the final fresh pins/export/replay.
No existing v17 source/result or other workspace was changed.

Next feed these **actual byte/bit demands** into a bounded coefficient-producer
and memory/compute schedule instead of proportional stripe bytes. Preserve exact
DC/AC stream offsets, header/CRC/preflight passes and output-private publication.
Then compare reconstructed integer pixels against these retained golden arrays
before native/RTL resource and timing work.
