# Optional 8-row RGB strip candidate

`cu70_painter_strip.sv` has the same external interface as the frozen direct
`cu70_painter.sv`. It computes the same identity-filter/native-rounded color
and exact HUD pixels, but stages eight coded rows in 5,760 RGB565 words
(11,520 bytes). Draining the transposed strip writes eight contiguous words
per physical portrait row. Final memory is byte-for-byte identical.

Total logical cache data becomes 13,696 bytes, excluding registers/state and
physical RAM implementation overhead. Neither that count nor the source RAM
attributes establish mapped BRAM fit or port/timing feasibility.

## Retained comparison

Run `python3 fpga/experiments/cu66-v70/display/run_strip_comparison.py`.
The same new comparison bench is compiled against each DUT. Each has ideal
and seeded scalar-service runs, with eight actual key/P packets, four edge
patterns and a recovery. This adds 52 complete native-checked rasters,
19,968,000 RGB565 word comparisons and ten seeded fault probes. The original
40 baseline files are SHA-checked unchanged before and after the comparison.

| Measured quantity per complete frame | Direct | 8-row strip |
|---|---:|---:|
| Canonical/HUD logical read words | 280,320 | 280,320 |
| RGB logical write words | 384,000 | 384,000 |
| Contiguous active-canvas address runs | 345,600 | 43,200 |
| Aligned exactly-eight-word active runs | 0 | 43,200 |
| Changes of 512-word address row (including borders) | 324,105 | 40,577 |
| Ideal scalar-service clocks | 2,084,889 | 2,430,489 |
| Seed7001 mean scalar-service clocks | 5,295,213.38 | 5,641,576.54 |

These address runs and row changes are observed on accepted RTL memory
requests. They are not measured ACT/PRE counts or evidence of BL8 writes.
The scalar interface still issues one write word per acknowledged operation.
An actual controller/arbiter test must determine whether improved locality
outweighs the extra strip-drain control clocks and RAM cost. The candidate is
slower in the independent scalar-service model, which does not charge row
activation/precharge costs. No 30fps or physical-throughput result is claimed.

`run_strip_control.py` adds the same targeted test in Icarus and Verilator:
abort with 123 dirty RGB words in the strip and verify that no active-canvas
writes occurred; restart with a different Y bias; fill a complete new strip;
check the first eight contiguous words match fresh data; abort and drain the
accepted write. This checks that stale strip contents cannot escape after
abort. The broader comparison also tests aborts during strip draining and
accepted read/write completion failures.

The checked-in `strip-results.json` and `strip-control-results.json` pin
sources, commands and actual logs. `verify_display.py` checks these records
and the separate baseline result without silently repinning changes.
