# V107 extracted threshold-unit native mapping

The exact frozen arithmetic wrapper synthesizes successfully in Vivado 2026.1. This is **measured extraction mapping with open DSP-pipelining findings**, not routed timing closure or whole-ingress/decoder qualification. No production, wrapper, mapper or exception was changed for this run.

The [raw receipt](../../experiments/python-gamebub-v107/count-threshold/native-unit/20261108T072036746798Z/receipt.json) records exit 0 in about 31 seconds. It binds all four production sources, the actual unit wrapper, literal extraction, Tcl, XDC, tool settings, reports and hashes. The separate [portable audit](../../experiments/python-gamebub-v107/count-threshold/native-unit/audit.json) and [evidence index](../../experiments/python-gamebub-v107/count-threshold/native-unit/evidence-index.json) preserve the raw result and add qualified connectivity attribution. Rice's behavioral aggregate pointer is untouched.

## Exact source and setup

The wrapper is `fpga/experiments/cu66-v107-count-threshold/verification/threshold_math_probe.sv`, SHA-256 `70022c313ad91332a49e36daa3034cf055fad26c299d076feeb8e4a59d6cece4`. Its literal generate block matches the production synchronous ingress, extracted block SHA-256 `6b48c5e641280970ca660f393c0a1995985f5d4c6d8aad079ba76677c8cbd066`. The snapshot includes the four production hashes `079381…`, `2c4a0a…`, `a5d8a8…`, `f0bab2…`; all remain unchanged after the run.

Setup: `xc7a100tcsg324-1`, out-of-context synthesis, rebuilt hierarchy, Default directive, `SYNTHESIS` define, two threads, fixed **synthetic 10 ns unit clock loaded before synthesis**, 8 GiB/two CPU limits and a 300-second tool cap. Host available-memory/PSI launch and live-stop gates were active. Existing Vivado tools and legitimate license were mounted read-only. No I/O delays, timing exceptions, board clock locations, PLL/MMCM changes or hardware actions were invented. The `settings.tsv` field labeled `top` records Vivado's internal design name `design_1`; the actual RTL top is explicitly `threshold_math_probe` in the synthesis command and netlist.

## Actual primitives and DSP registers

The synthesized extraction has **399 LUTs, 485 FFs, 124 SRL16Es, 16 DSP48E1s and five control sets**, with no RAMB primitives. The source has 18 multiplication sites, but that is not an expected physical DSP count. Intra-pipe products may share where reciprocal high/low halves match. The synthetic wrapper also broadcasts the same numerator to all three forwarded words every clock, allowing cross-pipe CSE/delay sharing that is unavailable when the full ingress has different cached lower bytes. These resource counts do not predict full production resources.

Actual [DSP register properties](../../experiments/python-gamebub-v107/count-threshold/native-unit/20261108T072036746798Z/reports/dsp-registers.tsv):

| AREG | BREG | MREG | PREG | DSP count |
|---:|---:|---:|---:|---:|
| 1 | 0 | 0 | 0 | 2 |
| 1 | 0 | 0 | 1 | 3 |
| 1 | 0 | 1 | 1 | 8 |
| 0 | 0 | 0 | 1 | 1 |
| 0 | 0 | 1 | 1 | 1 |
| 2 | 2 | 1 | 1 | 1 |

Thus **14 DSPs have PREG=1**. `partial_product_return` and `partial_product1_return` retain **AREG=1, BREG=0, MREG=0, PREG=0**. Registering an RTL arithmetic result does not guarantee a physical output register; synthesis can absorb/commute stages and share operators. This residual mapping is reported, not waived or described as an all-DSP-register success. All **160 DSP reset pins** are connected to GND. DSP CE pins are constants: 44 VCC and 164 GND, including unused internal paths; no external reset/accept control reaches them in this extraction.

## Fabric payload versus generated reset-mask control

The raw receipt deliberately preserves its initial name-based role heuristic. That heuristic labeled seven generated `threshold_pipes_r*` reset-bearing FDREs as data because their names do not contain `valid_pipe`. It is not evidence that arithmetic payload reset remains, nor permission to silently ignore those cells.

The separate [qualified attribution](../../experiments/python-gamebub-v107/count-threshold/native-unit/connectivity-attribution.json) proves their actual connectivity from the retained mapped Verilog:

1. `threshold_pipes_r` has D=1, CE=1 and R=`reset`.
2. Six more resettable FDREs form an unconditional fill chain; each intermediate Q drives only the next D.
3. The terminal Q drives only three LUT2 AND gates (`INIT=4'h8`). Each AND combines the reset-fill mask with its valid-delay signal and drives that pipe's `valid_pipe_reg[7]/D`.

These seven registers implement a shared validity reset mask around inferred SRLs. They are control, not numerator/quotient/remainder payload. The graph proof is nonempty and explicit; no classification is based only on a name.

After that qualified classification, the actual mapping contains **469 data FFs and 16 control FFs**. Every one of the 469 data reset pins is GND. Of their CE pins, 377 are VCC; the remaining 32, 31 and 29 are driven by the corresponding registered `valid_pipe[7]` Q for the three cached ceilings. None has external-port CE fanin. These are actual retained pin/driver/fanin rows, with constant pins checked directly rather than interpreting empty `get_ports -of_objects` output.

Of 124 SRL16Es, three belong to reset-masked validity pipelines and 121 to data delays; all SRL CEs are VCC. Reset elimination does not mean operational validity no longer resets. The source still flushes valid/live control, and an old valid cache write on a flush edge remains private/unowned. Source behavioral ownership and actual E0–E8 cycle checks are separate from this synthesis/connectivity evidence.

## Actual synthesis timing, with limits

The untouched [synthesis timing report](../../experiments/python-gamebub-v107/count-threshold/native-unit/20261108T072036746798Z/reports/timing.rpt) reports internal WNS **+4.871 ns**, WHS **+0.207 ns**, and pulse slack **+4.020 ns**. Its worst setup path is one of the PREG=0 DSPs:

`partial_product_return/CLK` → `threshold_pipes[0].cross_s1_reg/C[0]`

Data delay is **4.812 ns**: **4.009 ns** DSP clock-to-P logic and **0.803 ns estimated unplaced routing**, with zero fabric logic levels. This is the unit's worst reported registered path, not merely an unused arithmetic tail. The second PREG=0 DSP has no separately printed worst-path detail in this report; no exact per-source slack is invented.

These positive values are **post-synthesis estimates only**. There is no placement, routing, full-ingress timing, board I/O qualification, bitstream or hardware run. The synthetic byte plumbing and shared data path also differ from production. Neither the positive unit slack nor the E0–E8 RTL schedule proves decoder 100 MHz closure. No mapped UNISIM/SDF cycle simulation was run as part of this native query.

## Retained warnings and constraint gaps

| Actual report | Finding |
|---|---|
| DRC | CFGBVS-1: 1; DPIP-1 input pipelining: 5; DPOP-1 PREG pipelining: 2; DPOP-2 MREG pipelining: 6 |
| Methodology | 139 TIMING-18 missing I/O-delay checks |
| `check_timing` | 36 missing input delays, 99 missing output delays; zero unclocked registers, zero unconstrained internal endpoints, zero loops |
| Timing | `HD.CLK_SRC` is unset in OOC mode; no parent buffer location is guessed |
| Synthesis | Removed/merged sequential elements and constant output bits, retained verbatim in the log |
| Other | Flat-netlist floorplanning advisory and OOC incomplete-connectivity DRC notices |

No warning was suppressed or waived. DRC's PREG/MREG/input-pipeline recommendations remain open mapping findings. Configuration voltage/CFGBVS and physical clock-source settings belong to the actual parent/board context, not this synthetic arithmetic unit.

## Portable evidence and reproduction

All small reports, the complete functional mapped netlist, source snapshots, query Tcl and XDC are retained and indexed with SHA-256. The external synthesis DCP is retained by path/hash/size only; it is not required for the portable audit. The original raw receipt and raw heuristic rows are unchanged.

```sh
python3 scripts/cu66-v107/count_threshold_native_audit.py
# Exported evidence folder, without the original source tree or Vivado:
python3 audit_native.py --retained-only --area /path/to/native-unit
```

A fresh `python3 scripts/cu66-v107/count_threshold_native.py` requires a scheduled heavy-job slot. It synthesizes the untouched frozen wrapper and records a separate receipt; it does not select a decoder variant or modify Rice's proof pointer.
