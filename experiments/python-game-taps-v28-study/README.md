# GM27 tap-aware prediction qualification

`model.py` exposes `predict(reference, vectors, block_size=16)`,
`predict_with_info(...) -> (planes, work)`, and the GM27
`decode(packet, reference=None, *, expected_epoch=None,
expected_reference_id=None) -> (planes, metadata)` receive adapter.
The adapter calls the frozen unified-v27 parser, frozen Q14 reconstruction,
and frozen reference/output tag checks. It never assigns into imported modules.
Keys retain the constant-128 prediction.

Prediction shares the frozen reference and vector validators exactly. Luma
uses denominator 2 and chroma denominator 4; signed components remain half-luma
units with the same ±18 check. Coordinates use floor division, each tap clamps
independently, and the weighted sum receives one half-up rounding. The 16/32
block grids and partially populated last blocks retain the original behavior.
Tests also preserve unusual uint64 conversion behavior of the existing vector
validator; this optimization does not change its acceptance language.

The implementation gathers the top-left tap for every output sample, then
gathers top-right only for fractional x, bottom-left only for fractional y,
and bottom-right only when both axes are fractional. This gives 1/2/4 logical
sample fetches. Clamped duplicate coordinates are fetched again and counted
again. A whole-map-zero path copies each reference plane and counts one source
fetch per copied sample; output arrays do not alias the references. Integer
planes skip interpolation. Array arithmetic uses integer NumPy operations.

The retained run checks all 192 accepted base packets from the two v27 scenes
and both policies against the frozen decoder. Every plane and reconstructed
tag agrees. Timings use all 92 P inputs from the 96-frame `unified_causal`
cohort, including every accepted reference history and motion map. Keys are
excluded from predictor timing. Five rounds rotate the input order by 17,
reverse alternate rounds, and alternate old/new invocation order. Inputs are
warmed once. Validation is included in each timed predictor call.

| Predictor | Mean | Median | p95 |
| --- | ---: | ---: | ---: |
| Frozen eager four taps | 22.562 ms | 22.883 ms | 23.439 ms |
| Tap-aware masked gathers | 9.165 ms | 9.141 ms | 10.563 ms |

The measured mean speedup is 2.462× on this host/run. Logical reference gathers
across one pass through the 92 P inputs fall from 190,771,200 to 94,971,648
(50.22% reduction). This counts executed sample gathers, not DRAM transactions,
cache misses, unique addresses, validation scans, or the motion search. Timings
are predictor measurements; they do not establish the whole receiver speedup.

`results.json` retains the frozen source hashes, exact packet descriptors,
previous accepted reference packet descriptors and plane hashes, map shape and
int8 bytes, per-input counts, and every timing observation. The entire v27
results file is pinned, so reference chains can be rebuilt from key packets.
It reuses existing immutable compressed objects rather than duplicating them.

The 49,152-byte cap applies to a complete compressed CP27 packet. One 720×480
YUV420 reference or prediction occupies 1,036,800 bytes as full int16 Python
planes (518,400 samples). Multiple full planes and temporary arrays are still
allocated. Frozen prediction constructs two full int64 coordinate grids, a
full two-component int32 vector map, four full int32 quotient/remainder arrays,
four full int64 clamped coordinate arrays, and arithmetic temporaries. The new
implementation instead uses two expanded int32 component maps, four int32
quotient/remainder arrays, up to four int32 clamped coordinate arrays, up to
three boolean masks, an int32 accumulator, and gathered/arithmetic temporaries.
Expanded maps include padded last-block columns/rows before cropping.
`predict_with_info` names these arrays but does not claim a measured peak heap
size. No fitted FPGA line buffers, DSP resource fit, native FPS, or physical
link throughput are established by this host model.

Reproduce with the repository virtual environment:

```sh
cd experiments/python-game-taps-v28-study
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py --rounds 5
/home/lori/gamebub-streaming-prototype/.venv/bin/python verify.py
```
