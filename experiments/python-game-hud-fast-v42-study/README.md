# V42: exact HUD32/HUD33 planning and vectorized bit packing

The optimized host HUD stage produces **exactly the same HX32 and selected HX33
bytes**, including all fallback/tie decisions, while avoiding per-symbol Python
format strings and materializing only winning patch/channel streams. Across 24
HU25 inputs from four qualified clips, the combined stage falls 137.603→34.352 ms
on this host: **4.006×**, or 75.04% less time at this component boundary.

| Six-frame clip | Frozen HX32→HX33 stage | Fast stage | Paired ratio |
| --- | ---: | ---: | ---: |
| Mass Effect 10000 | 187.722238 ms | 46.712712 ms | 4.019× |
| Mass Effect 4500 | 135.584970 ms | 22.446594 ms | 6.040× |
| Mass Effect 1600 | 19.493715 ms | 6.542234 ms | 2.980× |
| Mass Effect combat | 207.610876 ms | 61.704564 ms | 3.365× |
| All 24, mean per-frame paired medians | 137.602950 ms | 34.351526 ms | 4.006× |

Every frame has **three paired repetitions**, alternating order by frame and
repetition. The two outputs, all per-patch recipe/channel sizes, Huffman depth
rejections, scheme/k choices, stable ties and selected modes match the frozen
implementation and qualified archives. There is no changed syntax or compression
gain, and this shared exact HUD optimization benefits native and custom hybrid
pipelines equally.

## What is actually timed

Both paired paths start with the same already-encoded immutable HU25 packet and
same previously accepted HUD reference. The timed stage performs HX32 encoding,
then HX33 encoding using that actual HX32 output. It includes:

- Full HU25 semantic decode/validation inside HX32.
- Full HU25 and supplied-HX32 semantic decode/identity/word validation inside HX33.
- Every source/motion/row-delta recipe, Huffman tree/code/depth decision, channel
  scheme and all Rice k0..14 cost trials.
- Actual selected entropy construction, patch headers/CRCs, final HUD wrapping
  and original full-payload fallback/tie rules.

HU25 generation, motion search and source patch selection are **externally paid
and excluded**. Source reads/decompression, archive I/O, byte/decision assertions,
additional output semantic decode, transport and display are also excluded. Thus
34.35 ms is not whole-chain sender service or evidence of physical 30 fps. A quiet
HUD frame's speed is not representative of the combat sample.

Incoming references are the actual last accepted frozen HX33 words. The 24 inputs
are the first six frames of each qualified additional scene, not arbitrary saved
references or source frames substituted for reconstructed HUD state.

## Exact planning and construction

The Huffman plan retains the frozen deterministic length builder and canonical
code assignment, including constant-stream syntax, sorted tables and maximum
depth 16. Histogram counts determine exact coded bit/byte sizes before packing.
Only winning streams create a vectorized variable-length code lookup/mask and
`np.packbits(..., bitorder='big')` output. No source-symbol `format()` call exists.

The Rice plan pays all 15 k costs and preserves lowest-k ties. Packing allocates
the chosen bit array, sets unary delimiters at vectorized prefix-sum positions,
fills remainder bits with shifts/masks and packs MSB-first. Empty, all-zero and
padding behavior remain identical to the original bitstring implementation.

HUD32 plans every patch recipe but emits only its actual winner. HUD33 plans
all three channel schemes for every recipe, computes exact complete component
sizes including channel headers/Huffman tables/Rice padding, and emits only the
winning recipe's selected channel schemes. The existing HU25/HX32 candidate stays
first on byte ties; final HUD fallback stays strict as before.

Across the 24 frames, 3,222 successful Huffman plans produce only 299 actual Huffman
stream materializations. All 25,560 Rice-k trials remain paid, with 210 selected
Rice materializations. Rejected-depth plans and losing recipes remain in the
stored decision metadata. Constant scheme streams may require no symbol bits;
their real header/table bytes are still counted.

There is **no persistent prepared cache** and no frozen-global monkeypatch.
Plans own per-call input temporaries; a caller changing its original array cannot
change a retained private plan. Baseline32 validation is not skipped merely
because the fast pipeline just generated it. Public APIs are:

```python
encode_hud32(HU25, reference=None, *, expected_reference_id=None)
encode_hud33(HU25, provided_HX32, reference=None, *, expected_reference_id=None)
huff_encode(values)
rice_encode(nonnegative_bounded_runs)
```

All old non-clock public decision metadata is preserved, with additional explicit
validation/counter fields. Private NumPy code/mask/bit arrays are host allocations,
not a fitted FPGA memory layout, ESP32 buffer requirement or native port.

## Evidence and limits

Actual HU25/HX32/HX33 packets, source hashes, accepted-reference tags, all slow and
fast decision records and every paired clock sample are retained. Six producer
tests qualify constant/random Huffman packets, an explicit legal depth 16 table,
over-depth rejection, Rice empty/boundary/run cases, all channel schemes, a real
HUD pipeline and invalid supplied-baseline rejection, frozen-function identity
and owned plan input. They behaviorally forbid per-symbol `format()` in the
packing primitives.

Independent replay imports no fast encoder. It uses frozen semantic HUD decoding,
checks actual packet identity against qualified archives, accepted previous HUD
state, source/pins, complete decision parity, construction counters and the
three-pair timing arithmetic. The evidence establishes an exact host component
speedup on this sample, not an optimal native implementation, compression
advantage, hardware fit or end-to-end frame rate.
Final independent replay passes all 24 HU25 inputs and 48 exact HX32/HX33 outputs,
506,880 HUD words, four accepted-reference chains, 568 recipe plans and 2,556
channel/scheme plans. Six independent tests pass and all 1,295 source pins match.

## Diagnostic next hotspot

`whole_chain_profile.py` regenerates selector/HU25 motion encoding and fast
HX32/HX33 for the same 24 source canvases, matching every qualified packet.
`whole-chain-profile.json` records 3.163 instrumented seconds. Leading self times
are HU25 `rle_encode` 0.479 s (994 calls), bounded `_rice_decode` 0.382 s (60 calls),
motion search 0.200 s, row token construction 0.194 s and frozen Huffman decode
0.187 s. This points to exact HU25 RLE/row-token construction and repeated Rice
decode as subsequent targets. These profile times include instrumentation and
must not be used as paired speed measurements or compared directly with old
profiles on different samples/scopes. Source I/O and final semantic assertions
are outside this diagnostic; no new HU25 optimization is claimed here.

```sh
cd experiments/python-game-hud-fast-v42-study
python -m unittest -v test_model
python -m unittest -v test_verify
python verify.py
```
