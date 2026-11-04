# Bounded half-pixel prediction, v26

This Python-only study isolates fractional prediction while retaining frozen
GM25 coefficient entropy, transform, quantization, ROI and inverse arithmetic.
`model.py` has the GM25 component API, with `motion_precision='coarse'`,
`'integer'`, or `'half'` on `analyze_planes` / `encode_planes`. `motion_mode`
remains zero/global/block; block size16 or32. There is no mutation of imported
module globals. [SCHEMA.md](SCHEMA.md) defines the new standalone GM26 frame.

Nonzero search first pays the frozen81-candidate even-pixel ±8 search. It then
pays9 integer or25 half-pixel candidate maps centered on that winner, within
±1pixel per axis. Maximum displacement is9pixels; it does not exhaustively
search every fine vector in the range. Coarse/global policy first chooses one
coarse global winner. Block policy refines each coarse block winner locally.
Tie order prefers the coarse center, then short local adjustments. SAD includes
luma and twice chroma. A SAD winner is only an encoder proposal, not a bit-rate
claim or a fallback selection rule.

`work.search.candidate_vectors` counts tested full candidate maps. Multiply it
by the macroblock count for block-cost evaluations; every map compares all
518400 YUV samples at720×480. `sad_sample_operations` counts these comparisons;
`reference_sample_fetches` additionally charges four taps per refinement sample.
Decoder reference fetches charge four per sample for every P frame, including
integer and zero vectors, matching the actual generic implementation. Motion
metadata bytes and coefficient bytes are separately reported. No physical
cache/burst behavior is inferred from these logical costs.

The benchmark uses the first12 retained frames per scene. Every matched trial
reads the exact reconstructed frozen `capped_key_zero_rdo1` GM25 reference bank.
Every closed-loop policy instead reads its own last decoded GM26 frame. Both
use the exact selected GM25 quantizer map and lambda1. All key RDO stays disabled
by the unchanged arithmetic. All packets are retained, decoded, and compared to
the encoder reconstruction. Metrics compare the same retained original RGB565
source to RGB565 reconstruction over active rows37:442, with exact original HUD
rectangles overlaid. HUD transport is excluded from base byte totals; no complete
stream cap or joint admission follows from this component study.

Run with `/home/lori/gamebub-streaming-prototype/.venv/bin/python`:

```
python -m unittest discover -s experiments/python-game-prediction-v26-study -v
python experiments/python-game-prediction-v26-study/benchmark.py
python experiments/python-game-prediction-v26-study/verify.py
```

These are offline measurements on two reused game windows. Nominal30fps rate
projections are not measured physical throughput, resource fit, or native FPGA /
ESP32 execution evidence. Scalar-oracle tests cover negative fractions, integer
rounding, luma/chroma edges, partial macroblocks,16/32 blocks; packet tests cover
zero/global/block syntax, canonical maps, unknown residual modes, exact tags,
reference identity, CRC and coarse parity. Retained goldens include decoded YUV
and exact-HUD RGB565 for frames0/1 of each case.

The current model is GM26 header **version2**, with actual minimum choice among
12bits/vector packing, causal left/median component Rice deltas and the earlier
map grammars. All losing representations and28 axis/k trials are paid. Their
costs are under `work.analysis.motion_map`. Search block-cost evaluations are
also explicit. The main campaign includes half32 as a narrow control for map
cost against prediction granularity. `early-results.json`, `early-sourcepins.json`,
`model_early_probe.py`, `benchmark_early_probe.py`, `early_test_probe.py` and
`early-run.log` preserve the precompact144-packet version1 probe unchanged.
`early-archive.json` resolves original execution paths to exact source snapshots
for verification after replacement by version2. `verify.py` checks both cohorts.

The192-packet compact probe passes full replay, alongside144 early packets.
Matched-reference half16 reduces base bytes by8.94% /4.93% against zero on the
2600/7200 windows, with lower active MSE. Half32 reduces bytes further, but its
own first12-frame closed-loop aggregate quality slightly misses zero in both
scenes. This is why a source-only causal quality gate is required for that tool.

`full_benchmark.py` runs48frames per scene with actual zero-vs-half32 byte/SSE
selection on the same accepted reference, all losing attempts paid. It adds
actual distinct CP2F packets and JA2F acknowledgements, not a projected CP25
binding. See [FULL-SCHEMA.md](FULL-SCHEMA.md). `full_results.json`,
`full_sourcepins.json`, `full_run.log`, `full_tests.log` and `full_verify.py`
retain and verify the complete campaign without changing the frozen probe
model/sourcepins. The exact fast RDO counter is an isolated adapter and preserves
the frozen residual grammar. Every selected complete packet is capped at49152B.

The full48-frame causal CP2F result is:

| Scene | Complete bytes | Nominal Mb/s at30 | Active MSE | Frozen v25 MSE | Byte reduction |
|---|---:|---:|---:|---:|---:|
| mass-effect-2600 |580970|2.90485|14.04092|14.38366|8.087%|
| mass-effect-7200 |1289119|6.44560|26.42170|26.89721|6.107%|

All96 accepted packets fit49152bytes (maximum48686), all HUD words match, and
both scenes improve aggregate quality against the frozen v25 stream. Half32
wins43frames per scene; zero wins5 including the two keys. The causal quality
gate rejects four half32 candidates across the two windows. All189 actual base /
pair candidate packets and188 analyses are paid and retained; one fine key
attempt overflows the complete cap and retries the coarse map. The selected
CP2F/JA2F timeline has96 real ACKs. Host analysis+all candidate encoding takes
about0.65–0.68seconds per source frame in this run, before receive/verification;
this is explicitly not physical30fps or a native implementation result.
