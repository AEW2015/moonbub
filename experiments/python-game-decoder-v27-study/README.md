# GM27 bounded motion syntax decoder qualification

`model.py:unpack_vectors(data,mw,mh)` parses modes 0 global, 1 dense, 2 RLE,
3 sparse, 4 packed 12-bit, 5 row Rice, and 6 median Rice without invoking the
encoder or trying alternative representations. The integrated GM27 study imports
this function as its receiver default. `parse_frame` and `decode_frame` are a
standalone adapter with an explicit GM27/version1 default; no frozen globals are
modified. The integrated model owns its complete profile and protocol parser.

This changes accepted language and therefore requires a new negotiated profile.
It must not silently replace the normative GM26 parser. The explicitly named
`replay_parse_gm26`/`replay_decode_gm26` functions are qualification adapters only.
Archived GM26/version1 replay permits modes0..3; final GM26/version2 permits
modes0..6. The default frame adapter rejects GM26 packets.

The decoder preserves signed half-luma vector bounds -18..18, the original
1+2*n byte map bound, valid grid geometry, exact record and bitstream lengths,
zero trailing padding, canonical Rice escapes, bounded unary escape decoding,
reconstructed-vector bounds, positive complete RLE coverage, strictly increasing
sparse indices, and exclusion of sparse entries equal to their default. It drops
selection of the shortest representation, mode tie policy, optimal Rice k,
adjacent equal RLE run merging and sparse modal-default selection as encoder
policy. Under the retained map byte bound, any sparse default already occupies
a strict majority, so nonmodal sparse defaults cannot actually enter this profile.

`results.json` retains all 525 canonical packets: 192 main-probe frames, 144
archived early frames, and 189 full-policy attempted frames including losing
attempts. Each input is source pinned and digest checked. All 492 P-frame maps
have retained encoded-byte and decoded int8-vector controls; every frame has a
coefficient-array hash and output tag. Qualification compares all metadata,
quantizer maps, motion vectors and coefficient arrays bit for bit against the
correct frozen version. This proves the frame parser yields identical inputs to
reconstruction on canonical packets. A separate key/P decode test checks output
identity and exact reference-ID rejection. It does not repeat complete HUD/ACK
presentation qualification, which belongs to the integrated study.

Six retained nonminimal forms (dense global, split RLE, sparse global, packed
global, nonoptimal row-Rice k and nonoptimal median-Rice k) are accepted by GM27
syntax and rejected by the strict GM26 oracle. Thirty-one retained malformed
vectors cover mode, length, range, runs, sparse ordering, escape, truncation and
padding rejection. Seven tests also check geometry/types, profile separation,
canonical equivalence, output decode and that production code has no encoder
search calls.

Timing uses five cyclically rotated map rounds and three rotated whole-frame
parse rounds. Decoder order alternates at each input and round. Per-input samples
are retained. Group summaries aggregate each input's median, rather than treating
repeat trials as new corpus frames. Whole-frame parse includes CRC, quantizer map
and coefficient entropy parsing; it excludes prediction, reconstruction, HUD,
transport, reference ownership and publication. Maps already globally constant
avoid Rice search in the frozen encoder too. For other canonical v2 maps, removal
eliminates 28 Rice-axis trials and 28*n Rice-value trial encodes per parse, as well
as construction and comparison of six candidate representations. These are
algorithmic operation counts, not processor instruction or native DSP clocks.

Map bytes and decoded vector bytes describe the MV component only. They do not
represent total receiver memory or complete RF traffic. Python timing does not
establish native DSP/FPGA fit, clock rate or physical 30 FPS.

Reproduce from this directory with
`/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v test_model`,
then `python benchmark.py`, then `python verify.py` using the same interpreter.
`benchmark.py` writes retained controls, source pins, per-input trials and summary
results; `verify.py` independently replays those controls and grammar vectors.

Observed host results (milliseconds; median across per-input medians):

| Retained group | Frames / P maps | Frozen MV parse | Syntax MV parse | Frozen frame parse | Syntax frame parse |
|---|---:|---:|---:|---:|---:|
| Main v2 probe | 192 / 176 | 24.368 | 1.681 | 30.206 | 12.871 |
| Archived early v1 | 144 / 132 | 3.133 | 0.007 | 13.352 | 10.690 |
| Full v2 attempts | 189 / 184 | 4.656 | 0.268 | 14.680 | 10.491 |

Across one pass through all retained P maps, encoded MV inputs total 397,101
bytes and decoded state comprises 435,060 vector pairs / 870,120 int8 bytes.
Removing v2 re-encoding eliminates 6,272 Rice-axis trials and 4,640,160 Rice-value
trial encodes over those retained inputs. Archived v1 has no Rice trials; its
improvement comes from removing its older representation re-encoding. Results
retain all individual samples, encoded maps, vector controls and input hashes.
