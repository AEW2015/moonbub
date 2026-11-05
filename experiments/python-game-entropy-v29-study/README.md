# V29 exact EC26 counter and guarded plane selection

`model.py` provides:

- `plan_coefficients(coefficients, blocks_w, layout=0)`: exact EC26 packet length, Rice parameters, padded stream lengths, raw fallback decision and counts. Validates the inherited bounded int16 coefficient domain. Counts include the EC26 header and CRC, and exclude the GM27 one-byte dispatch.
- `count_coefficients(...)`: integer length adapter. Both EC26 layouts are supported for counter verification.
- `encode_with(runtime28_module, prepared, scale_map, rdo_lambda=1)`: bounded encoder-only selection using that caller's owned Prepared type. No frozen globals are modified.
- `encode_prepared(...)`: adapter using this module's own runtime28 import.

The encoder first reproduces the incumbent v28 choice, then considers each unique original/pruned plane. It computes exact minimum legacy/EC26 bytes and reconstructs alternatives to require source YUV SSE no greater than the incumbent plane. It chooses minimum bytes among eligible candidates; incumbent wins ties. All reconstructions, counters, alternative comparisons and final packet construction execute inside its measured service time. GM27 layout0 syntax and decoder are unchanged. This per-plane YUV guard does **not** imply equal or better final RGB/perceptual error; the integrated controller must retain its measured RGB guard.

## Results

Twenty-four full-resolution retained source frames, twelve from each Mass Effect window, use the actual old accepted decoded reference. Alternative outputs are **not** substituted into the next reference in this matched-reference experiment.

| Scene | Baseline base bytes | Guarded bytes | Selected alternative planes | Baseline encode ms | Guarded encode ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2600 | 65,406 | 65,406 | 0 | 33.18 | 66.66 |
| 7200 | 163,759 | 163,759 | 0 | 43.22 | 79.44 |

All accepted packets fit the complete 49,152-byte cap after adding retained HUD bytes and the 60-byte CP27 binding. All output pixels and MSE are unchanged in this sample. **The guarded whole-plane policy adds work without improving this corpus and is not recommended as the default.** These host timings are small-sample wall measurements, not native throughput or hardware proof.

The exact counter was checked against actual EC26 serialization on all three accepted planes in both layouts: **144 equal lengths**. Mean counter versus actual construction cost was **0.914 vs 1.608 ms** in scene2600, and **1.089 vs 3.373 ms** in scene7200. These compare a length-only call to serialization of the same accepted coefficients; they do not represent a complete encoder speedup. The encoder still serializes the selected winning packet.

## Why this matters for an application-specific codec

The previous isolated CP02 proxy is not the actual EC26 marginal rate. This counter closes that correctness gap, but a correct counter alone cannot create better candidates. The next useful experiment is bounded block/band-context candidate generation: evaluate changes in sparse runs, Rice parameters, row-reset DC and byte padding, while protecting HUD/ROI detail and testing full causal source histories. The negative whole-plane result is a control against claiming a generic compression improvement from changing only the cost oracle.

## Verification

```sh
python -m unittest discover -s experiments/python-game-entropy-v29-study -v
python experiments/python-game-entropy-v29-study/verify.py
```

Five tests cover zeros, DC row resets/extremes, seeded sparse/dense arrays, long runs, both layouts, invalid bounded inputs, source guards, owned Prepared values, exact decoder reconstruction, and input immutability. The retained verifier repeats actual source/old-reference preparation and all policy decisions, checks candidate packets and hashes, all source SSE guards, exact lengths and complete capacity. Neither test count nor nominal rate projections establish ESP32 RF/QSPI service, FPGA resources, decoder clock closure or physical 30 fps.
