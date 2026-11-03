# Selective exact UI patches over GM01

This new Python experiment admits only display patches that fit the **actual complete 49,152-byte frame cap**. It reuses frozen HP01/GH01 and GM01; it does not modify an installed Sunshine, ESP32 firmware, FPGA decoder, or existing GF01/MSV1/JPEG transport.

`select_frame(base_bytes, current_rgb, Config(...), spent_before_ms=base_preparation_cost)` is pure and state-free. The caller must supply GM01 and RGB from the same capture; syntax validation cannot prove that semantic correspondence. It validates the complete base, tries each declared rectangle once in priority order, and admits a patch using its actual encoded length, including the 22-byte GH01 header/CRC and each four-byte patch-length prefix. Up to four attempts are allowed. A rejected large patch does not prevent trying a later small priority. Selected HP01 bytes are validated and cached for wrapping, avoiding a second palette pass.

If no patch fits, output is the original GM01 byte string, without a wrapper. An over-cap base is explicitly rejected. Optional observed-work budgeting checks before and after attempted patches and after assembly. A late check falls back to GM01 but retains every attempted encode/validation/assembly cost. This is a cooperative fallback, **not a hard deadline**. `spent_before_ms` includes preceding base preparation, while final decoding and transport remain additional service.

`Decoder` dispatches capped GM01/GH01 packets through one frozen GM01 receiver. Every GH01 patch is validated before the stateful GM receive. Original RGB565 words overwrite only selected display rectangles; YUV reference planes remain the same as a plain GM01 stream. HR01 row coding from the separate study is deliberately not silently accepted through the frozen GH01 contract.

The two predeclared priority sets are:

- Broad: `(16,48,192,80)`, `(160,352,400,80)`; 47,360 pixels.
- Compact: `(22,54,160,24)`, `(22,82,160,24)`, `(168,360,320,24)`, `(168,390,240,24)`; 21,120 pixels, all within the broad set.

These are synthetic priorities, not verified locations of real game HUD text. The smaller set cannot fairly claim the broad set's lossless coverage. Results retain both selected/requested and selected/common-broad area fractions, plus a common broad ROI MSE denominator. Selected exactness is versus original RGB565; RGB888-to-RGB565 precision loss remains.

The campaign uses eight fixed native frame indices `(0,2,4,6,8,10,12,14)` beginning at four seconds from each of two related, precompressed Mass Effect clips; two seeded noisy HUD fixtures; and two separately labeled flat-color, 1-bit-glyph best cases. No interpolated or repeated frame is labeled independent gameplay evidence. Each source has the same ROI8/background16 GM01 key control and three selectors: broad, compact, and compact with a 35 ms observed preparation-work budget. Sources and helper versions are pinned by SHA-256 in `results.json`.

Full service charges GM01 preparation, complete selection including rejected patch work and duplicate frozen GH01 base validation, and receive/overlay. Same-frame GM01 preparation is measured once and charged to each independent policy. Source decoding/scaling, metrics, and reference-oracle checks are excluded. Uncontrolled host Python timing is not an ESP32/FPGA throughput measurement. Forward/reverse bytes are accounting only: packet + 59 bytes per 1,024-byte chunk and 52 reverse bytes per accepted frame.

A separate 12-native-frame functional sequence uses the frozen bounded GM01 base controller and explicitly disables patches every third frame. It checks mixed GH01/GM01 decoding and the unchanged YUV key anchor across subsequent P frames; it is not a paced loss/reorder simulation.

Run from the repository root with the prototype virtual environment:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest discover -s experiments/python-game-selective-study -v
/home/lori/gamebub-streaming-prototype/.venv/bin/python experiments/python-game-selective-study/benchmark.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python experiments/python-game-selective-study/verify.py
```

`tests.log`, `benchmark.log`, `results.json`, and `verify.log` preserve the run. No hardware/FPS proof or deployment claim follows from this experiment. Negotiated mixed-format support, bounded target resource use, and a target-specific deadline/drop policy are still required before integration.

## Recorded results

All 16 real inputs admit a valid complete frame under every policy. The independent noisy synthetic bases are about 95 KB and are explicitly rejected for all three policies, without palette work. The two flat best cases fit both declared sets. There are **54 admitted decisions and six base rejections** among the 60 same-source decisions; every admitted frame is at most 49,152 bytes.

| Policy on 16 real inputs | Mean complete bytes | Maximum bytes | Mean exact selected area | Common broad ROI MSE | Mean full service |
| --- | ---: | ---: | ---: | ---: | ---: |
| Same-frame GM01 control | 25,320 | 31,570 | 0 | 17.280 | 62.37 ms |
| Broad priorities, selective | 39,375 | 47,092 | 15,360 pixels / 32.43% broad | 16.964 | 117.18 ms |
| Compact priorities, selective | 40,048 | 41,511 | 21,120 pixels / 44.59% broad | 15.289 | 119.16 ms |
| Compact, observed 35 ms preparation budget | 25,320 | 31,570 | 0 | 17.280 | 90.63 ms |

Compact selects all four requested rectangles in all 16 real frames, with zero RGB565 word mismatches in those 21,120 pixels. Broad selects the first rectangle and pays for 16 rejected second-rectangle attempts. Pixels outside selected rectangles exactly match the same GM01 base in RGB565. The MSE column compares source RGB888 with RGB565-expanded output on the same active broad ROI; even an exact RGB565 patch can retain RGB888 quantization error.

The 35 ms observer admits the unchanged base on every cap-valid input, with no patches attempted: base preparation plus mandatory syntax validation already consumed that observed budget. Full service still averages 90.63 ms on real inputs because prior work and decoding are charged. **This experiment does not meet 30 fps in Python.** A byte cap and a cooperative fallback do not establish a processing deadline.

The 12-frame temporal functional sequence decodes **eight GH01 frames and four byte-identical GM01 fallbacks**, with exact selected words and the same immutable YUV key anchor through all P frames. Seven unit tests and the persisted-result verifier pass. `results.json` records each attempted palette cost, including rejected work, all source/packet hashes, full control/selector metrics, and the separately labeled artificial inputs.

Next, evaluate the parent study's explicit row-run patch contract against the same compact rectangles, then combine only after negotiated decoder dispatch and complete finite-service accounting exist. A bounded small priority set is useful; full broad lossless regions should remain optional. This result alone does not justify changing the hardware JPEG path.
