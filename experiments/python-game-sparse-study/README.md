# Exact zero/DC decoder bypass at 720×480

This Python receiver preserves complete GM01/HG01 packet syntax, reconstructed
YUV references and displayed RGB pixels. It caches the three quantization tables
for each plane type, skips the inverse transform for zero blocks, and evaluates
DC-only blocks with the frozen two-pass Q14 rounding. Mixed blocks use the frozen
inverse transform. This is a combined implementation optimization; the benchmark
does not isolate the benefit of cached tables from the benefit of bypass.

Five tests pass, including all 4,097 permitted signed DC values at each supported
quantization scale for luma and chroma, mixed/partial-block geometry, key/P/refresh
state, and atomic rejection. The paired benchmark uses identical packets in
alternating baseline/fast order. All RGB pixels and reconstructed YUV samples
match; selected UI RGB565 regions remain exact.

| 60-frame source | Whole GM01 receive, baseline → fast | Whole HG01 receive, baseline → fast | Inverse blocks bypassed |
| --- | ---: | ---: | ---: |
| Combat | 23.36 → 20.72 ms | 26.05 → 23.32 ms | 84.9% |
| Second sample | 23.86 → 21.63 ms | 26.64 → 24.45 ms | 69.3% |

Core reconstruction alone falls from 6.18 to 3.78 ms and from 5.55 to 3.39 ms.
Those core timers exclude parsing and prediction construction. The whole receive
timers include parsing, CRC, entropy decoding, prediction, color conversion and
UI processing. Hash verification is outside the timers. These are single-run
host measurements with alternating call order and uncontrolled system load.

The evidence contains 120 source IDs, 480 whole receiver calls and 240 separate
core reconstruction calls. There are only 92 distinct RGB images across the two
per-clip sets: 32 in the native 25 fps combat sample and 60 in the 29.88 fps second
sample. Both are related, already compressed footage, scaled to a 720×480 canvas
with 720×405 active content. They do not establish native 30 distinct fps capture.

No new coding mode or byte saving is claimed. Full host coefficient, residual and
output arrays remain allocated. This code does not prove FPGA resource fit,
SDRAM service, target decode throughput, finite feedback delivery or physical
30 fps. A native decoder can implement the same arithmetic bypass without
changing Sunshine/ESP32 packet framing, after matching these golden outputs.

Run from this directory using the study virtual environment:

```sh
python -m unittest -v test_fast_codec.py
python verify.py                       # checks retained results without rerunning
python benchmark.py                    # regenerates timings; requires external media
```

[results.json](results.json) pins the executed source and external media hashes.
The parent iteration manifest pins this README, verifier, tests and evidence.
