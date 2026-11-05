# AR03 double-bank transpose read-index component export

This portable package isolates the selected `ar03_yuv_transpose` double-bank component and its cycle-equivalence baseline. It does not include a complete CP23 receiver or claim that the selected leaf has been integrated into the separate CP23 composite-scanout experiment.

## Bound functional evidence

All three runs were executed in the source experiment with the exact selected RTL, shadow baseline, testbench, parent modules, and vector files included here. The retained source logs/results and their snapshots are under `evidence/`.

| Profile | Result |
| --- | --- |
| `directed` | 14 jobs, 20 checks, 193,587 equivalence cycles; ownership, cancellation, reset, identity, and geometry-bound cases. |
| `full` | 259,200 accepted/output words and physical writes, matching column data/guards, 923,310 equivalence cycles, 23,040-byte high-water; same completion schedule as the shadow. |
| `end-abort` | Same 259,200 physically accepted words drain; success is suppressed after abort during final flush; 923,310 equivalence cycles. |

The directed result records 193,587 compared equivalence cycles; the bench reaches its finish point at 193,595 cycles. Full and end-abort finish at 923,318 cycles after 923,310 compared cycles. These are simulation counts, not throughput or hardware measurements.

## Selected RTL and scope

The selected top is `rtl/ar03_yuv_transpose.sv`, which selects the two-bank path by default; `rtl/ar03_yuv_transpose_double.sv` contains the selected read-index and registered diagnostic-peak implementation. `rtl/ar03_yuv_transpose_baseline.sv` and `rtl/ar03_yuv_transpose_double_baseline.sv` preserve the original comparison path. The testbench compares observable outputs cycle by cycle, except for the documented one-cycle diagnostic high-water delay and its settled peak equivalence. Address checks compare each registered read address against the original arithmetic address.

These files remain an isolated transpose component. No ACK, publication, CP23 profile, board system, display integration, or physical write path is implied. This package does not establish that the optimized leaf is used by the CP23 composite-scanout sources.

## Reproduce the three simulations

Prerequisites: Python 3, Icarus Verilog (`iverilog` and `vvp`, 2012/SystemVerilog support), and a fresh writable evidence directory outside this package. The Windows source run used the MSYS2 UCRT64 Icarus tools. Set `IVERILOG` and `VVP` if those programs are not on `PATH`. The helper prepends the selected executables? directories to the child process `PATH`, so Windows runtime DLLs beside the tools can be loaded.

```powershell
python verify_source.py
python run.py --profile directed --evidence C:/ar03-ri-directed
python run.py --profile full --evidence C:/ar03-ri-full
python run.py --profile end-abort --evidence C:/ar03-ri-end-abort
```

`run.py` verifies the included manifest, copies only the bound compile inputs to the new evidence directory, compiles and runs the selected profile, checks the expected completion marker and rechecks the export. It does not invoke any external parent verifier, resource parser, Vivado, programmer, or hardware interface. It never writes into this source package.

## OOC synthesis and routed component evidence

The source experiment used Vivado 2025.2, `xc7a100tcsg324-1`, and the unchanged single 100 MHz component clock constraint in `ooc/ooc-clock.xdc`. The exported scripts and full reports are bound alongside the DCPs.

| OOC gate | Recorded result |
| --- | --- |
| Synthesis estimate | WNS +1.102 ns, WHS +0.260 ns, WPWS +4.500 ns; 852 LUT, 703 FF, 16 RAMB36 tiles, 2 DSP. |
| OOC routed component | WNS +0.169 ns, WHS +0.134 ns, WPWS +4.500 ns; all 1,546 routable nets routed, zero routing errors. Routed utilization reports 839 LUT, 703 FF, 16 RAMB36 tiles, 2 DSP after physical optimization. |

The route is **out-of-context component evidence, not board timing closure**. It has no board pin/I/O delay budget; Vivado retained missing `HD.PARTPIN_LOCS`/`HD.CLK_SRC` and external timing coverage warnings. The routed DRC report has configuration-property and DSP input-pipelining warnings. No BIT or board image was generated.

For a synthesis-only replay, invoke the Tcl script from a fresh external working directory so generated files stay outside the export:

```powershell
vivado -mode batch -source C:/path/to/export/ooc/synth-constrained.tcl -tclargs 2
```

The included route script consumes `ooc/bank2-constrained/synthesized.dcp`, relative to the route script, and writes output reports/checkpoint into its current working directory. To reroute the included checkpoint, use a fresh external working directory:

```powershell
Push-Location C:/ooc-route-replay
vivado -mode batch -source C:/path/to/export/ooc/route-component.tcl
Pop-Location
```

For a fresh synthesis followed by route, use a scratch copy of the export. Run synthesis with that copy's `ooc/bank2-constrained` directory as the current working directory, then run its `route-component.tcl` from a separate fresh output directory. Existing OOC reports and DCPs are evidence, not a replacement for rerunning a requested gate against an altered source.

## Preserved license notices

The export includes the complete GPLv3 text and the complete CERN-OHL-S-2.0 text, both unmodified. `licenses/ORIGINAL-NOTICES.md` preserves the upstream scope and trademark notice. The applicable license for each file remains governed by that file's original notice; bundling these texts does not change or extend any file's terms. File integrity and exact source bindings are in `manifest.json`, `source-bindings.json`, and `verify_source.py`.
