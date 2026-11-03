# Hypothetical 60 Hz LCD timing sensitivity

This experiment changes only the pixel-clock half-period in the existing behavioral QSPI-to-LCD testbench, from `17.029 ns` to `18.470 ns`. With the unchanged 541 × 834 modeled raster, the latter produces approximately **59.998 Hz**, versus approximately 65.08 Hz in the baseline. The same 300 distinct JPEG fixtures, arrivals, decoder, memory model and test logic are used. The fixtures are sampled at 29 Hz from a near-29.88-fps precompressed gameplay clip and replayed at 30 Hz, about 3.45% faster than source time; see [gameplay-study](../gameplay-study/README.md). All input and per-frame framebuffer hashes match between the two timing runs.

| Model pixel timing | Strict 10 s window | First-to-last FPS (299 intervals) | Arrival-to-swap p95 / p99 / max | Frames above 1/30 s age |
| --- | --- | ---: | --- | ---: |
| Baseline ~65.08 Hz | 300 / 300 presented | 29.98086 | 36.16168 / 36.85783 / 37.27471 ms | 71 |
| Hypothetical ~59.998 Hz | 300 / 300 presented | 29.99921 | 30.05083 / 30.06139 / 30.06402 ms | 0 |

Both completed the exact strict 10-second simulated window with zero model-reported underruns, and all framebuffer RGB565 pixels matched the related C model. This is a meaningful **phase/timing sensitivity result for this one fixture sequence and starting phase**, not a physical display or 60-second result. Other phase offsets, clock drift, network/ESP32 delays, panel electrical limits, and target clock generation are untested. A scanout-swap timestamp is not input-to-photon latency. The C model shares decoder algorithms with the RTL. `verified.jsonl`, `summary.json` and `latency-analysis.json` preserve the hypothetical run. The baseline artifacts are `../gameplay-study/*-300-unique.*`.

The ILI9806E controller documentation is compatible with the candidate clock at a high level, but exact panel/module limits, board implementation and physical polarity are not established. See [panel timing evidence](../cadence-study/PANEL-TIMING-EVIDENCE.md); do not apply this simulation timing to hardware without validating those details.

Run `run.sh` with `FIXTURE_DIR` pointing to the local 300-frame fixture set, `BUILD_DIR` a new empty directory, and Verilator, Python/Pillow and C++ available. `FRAMES` and `TIMEOUT_SECONDS` can be changed; `strict=1` is enforced. The wrapper compiles the modified behavioral testbench and checks every resulting frame against the related C decoder. The source video and JPEGs are not redistributed.
