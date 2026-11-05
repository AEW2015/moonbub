# Generic v71 bridge elaboration

The final cut-through/grace `cu71_word_bridge` and frozen v70 scalar bridge both pass Yosys 0.33 hierarchy checks, process conversion, optimization and `check -assert` with zero structural problems. This is generic leaf elaboration and resource accounting. It does not include the controller, tile adapter, display, receiver, SDRAM pads or clock constraints.

```sh
python3 scripts/cu66-v71/run_elaboration.py
```

The runner uses the existing `gamebub-cu66-v69-build` container and records exact commands, source hashes and output hashes in `fpga/experiments/cu66-v71/memory/elaboration-results.json`. Per-version `.ys` files contain the exact Yosys command sequence: `read_verilog -sv`, `hierarchy -check`, `proc`, `opt`, `check -assert`, `stat -json` and `write_json`. Raw logs, JSON statistics and unmapped netlists are retained beside the results.

| Generic, unmapped statistic | V70 scalar bridge | V71 cut-through LCD bridge |
| --- | ---: | ---: |
| Cells after `proc; opt` | 225 | 826 |
| Generic memories | 2 | 4 |
| Retained memory bits | 298 | 852 |
| Retained dff-family cells | 15 | 26 |
| Sum of dff-family `WIDTH` parameters | 196 bits | 237 bits |
| Memory bits plus dff-family bits | 494 bits | 1,089 bits |

These cells have different widths and functions, so their count is not a LUT count or a meaningful silicon area ratio. The memory arrays remain generic Yosys memories in this flow. Their bits are reported separately from retained dff-family bits. The v71 storage covers the larger scalar cache and separate eight-word elastic LCD buffer plus tags/control state. Its eight individual physical-range checks also increase generic comparison logic; a later implementation can investigate a range-equivalent simplification while retaining all allocation/rejection tests.

No `synth_xilinx`, technology mapping, memory mapping, placement or routing was performed. These results establish neither Artix-7 fit nor actual LUT/FF/BRAM usage, device frequency, SDRAM electrical timing, sustained 30 fps or sub-10-ms decode latency. Functional behavior is supported separately by the component and integrated simulations.

`initial-buffered-elaboration.zip` and its manifest retain the earlier buffered implementation and its elaboration (801 cells, 852 memory bits and 228 dff-family bits) before the cut-through change. Current `elaboration-results.json` pins the final bridge source.

`elastic-no-grace-elaboration.zip` and its manifest preserve the intermediate cut-through leaf before the bounded-grace scheduler (815 generic cells, 852 memory bits and 236 dff-family bits). The final report has the extra finite grace state and pins the final source.
