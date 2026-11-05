# Dependencies and limits

## Simulation replay

- Python 3.8 or newer for `run.py` and `verify_source.py`.
- Icarus Verilog `iverilog` and `vvp`, with SystemVerilog 2012 support.
- Windows source evidence used MSYS2 UCRT64 Icarus. On another system, provide executable paths in `IVERILOG` and `VVP` or expose both tools on `PATH`.

## Out-of-context FPGA reproduction

- AMD Vivado 2025.2.
- Part `xc7a100tcsg324-1`.
- The included `ooc/ooc-clock.xdc` constrains only `clk` to 10 ns. The component has no board pin assignments, I/O delays, clock-source settings, or board-level constraints in this package.

The OOC evidence must not be represented as board timing closure, physical resource fit for the whole device image, or hardware qualification.
