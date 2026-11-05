# V42 checkpoint: exact HUD planning and packed construction

V42 accelerates the host HX32→HX33 HUD stage while preserving the frozen
syntax, byte decisions, and selected packets. It plans Huffman and Rice costs,
then materializes only winning patch and channel streams with vectorized bit
packing. This is an exact host component optimization; it shows no compression
gain and does not establish whole-chain or physical frame rate.

## Paired results

The campaign uses 24 already-encoded HU25 inputs from the first six frames of
four qualified Mass Effect clips. For every frame, three paired repetitions
alternate slow/fast order. The combined reported mean of per-frame paired
medians is 137.602950 ms for the frozen stage and 34.351526 ms for the fast
stage: 4.006×, or 75.04% less time at this component boundary.

| Clip | Frozen HX32→HX33 | Fast HX32→HX33 | Ratio |
| --- | ---: | ---: | ---: |
| Mass Effect 10000 | 187.722238 ms | 46.712712 ms | 4.019× |
| Mass Effect 4500 | 135.584970 ms | 22.446594 ms | 6.040× |
| Mass Effect 1600 | 19.493715 ms | 6.542234 ms | 2.980× |
| Mass Effect combat | 207.610876 ms | 61.704564 ms | 3.365× |
| All 24, mean per-frame paired medians | 137.602950 ms | 34.351526 ms | 4.006× |

HU25 generation, source patch selection and motion search are excluded from both
paired timings. The timed path includes HX32 semantic decode and validation,
HX32 encoding, HX33 validation of HU25 and the supplied HX32, recipe and channel
planning, all Rice k trials, selected payload construction and packet sealing.
Source reads, archive work, final assertions, additional output decode,
transport and display are also excluded. Thus 34.35 ms is not whole-chain sender
service or a 30-fps result.

## Exactness and scope

Independent replay verifies all 24 HU25 inputs, 24 byte-identical HX32 outputs,
24 byte-identical selected HX33 outputs, 506,880 exact HUD words, four accepted
reference chains, 568 recipe plans, 2,556 channel/scheme plans and 1,295 source
pins. The six producer tests and six independent tests pass. Three paired timing
repetitions per input and their alternating order are checked independently.

Across these frames, fast planning records 3,222 successful Huffman plans and
25,560 Rice-k trials, while constructing 299 Huffman streams and 210 Rice
streams. Plans retain per-call owned input data; there is no prepared cache or
frozen-global monkeypatch. Existing HU25 generation and the shared exact HUD
optimization benefit both native and custom hybrid paths. The study does not
claim lower video bytes, an FPGA/ESP32 fit, or an optimal native implementation.

## Whole-chain diagnostic

A separate cProfile run covers selector, HU25 motion generation and fast HX32 /
HX33 for 24 frames, matching all qualified packets. Its README reports 3.163 s
instrumented total and identifies RLE, Rice decode, motion search, row token
construction and Huffman decode as possible follow-up hotspots. This run is a
profile diagnostic, not a paired performance result or comparison with the
paired stage timings. HU25 generation is included in this diagnostic even
though it is excluded from the paired stage.

The profile summary is affected by the same pstats aggregation caveat found in
V41: the root `generate` cumulative time (3.172660 s) exceeds the reported total
instrumented time (3.163314 s) by about 9.35 ms. The profile script builds rows
from `pstats.Stats.stats`, whose filename/line/function keys can collapse
separate code aliases. Treat its total and per-function ranking as qualitative
diagnostic evidence until raw profiler entries are aggregated without key
collisions. No optimization or speed claim relies on this profile.
