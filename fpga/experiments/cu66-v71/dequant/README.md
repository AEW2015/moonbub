# CU71 pipelined dequant candidate

Integration module: `cu71_dequant_pipe`, drop-in ports for `cu66_dequant`.
The source is a successor; v69 RTL and all existing system bindings are untouched.

The original variable coefficient/quantizer selection, multiply and wide tile
write are split into selected operands, registered signed-25-bit products and
constant-slice output stores. Eight groups still issue on consecutive clocks;
the final result appears after ten work clocks instead of eight. Invalid and
all-zero requests retain their immediate-result path. There is one outstanding
tile, and output data/id/error remain stable until acceptance. Reset/abort gate
ready/valid immediately and synchronously clear visible data/id/error. Private
product payload registers need no reset because reset valid bits fence them.

Widths, coefficient range [-2048,+2048], scale mapping 8/16/32, invalid scale3,
quantizer rounding/clamp and signed20 result casts match the original module.

## Reproduction

From the repository root, with Python3.11/NumPy and isolated PyAV18.1.0:

```powershell
$env:PYTHONPATH='C:/mb70/fpga/experiments/cu66-v71/dequant/python-deps'
python scripts/cu66-v71/dequant/export_vectors.py
python scripts/cu66-v71/dequant/run.py --output <new-unique-path> --synth
```

`vectors.json` binds 123 imported source files and 16 original packet hashes.
The unchanged original v40/v43 packet parser supplies actual gameplay
coefficients and per-block quantization tables. A table must exactly match one
of the three normative FT01 tables; otherwise export fails. No replacement
parser or guessed qcode is used. All64 words of each sampled block are checked;
this is not exhaustive gameplay or native full-system coverage.

The three test campaigns use 1,536 existing pinned NumPy vectors, 3,441 sampled
actual gameplay vectors, and 2,104 directed full-tile/position/extreme/invalid
vectors. Each full result is checked against both the independent golden and
the original RTL. Busy input poisoning, up to257-cycle output stalls, and reset
and abort at thirteen pipeline/held-result phases are included. Each cancellation
is followed by a successful full golden replay. Simulation logs retain Icarus's
conservative `always_comb` sensitivity warnings.

The optional Vivado run is exact-device `xc7a100tcsg324-1` synthesis OOC at
100MHz with 1ns maximum/0ns minimum input and output delay budgets, matching the
earlier arithmetic diagnostic. It is an estimate, not routed full-board timing
closure. No clocks, I/O budgets or exceptions are relaxed to hide the old path.
No hardware is programmed by these scripts.

## Observed proof-synth01 result

All7,081 fixture transactions and78 cancellation/replay transactions passed.
Maximum nonzero work latency was10clocks. Exact-device synthesis used1,509LUTs,
2,369FFs and8DSPs. Setup WNS is+2.906ns, TNS0. The worst setup path is now the
input coefficient validation/zero fast path to visible output reset; the old
group-selection/multiplier/output-store path is split by registers.

The overall synthesized timing report **does not pass hold**: WHS−0.297ns,
1,063 failing hold endpoints. The shown worst hold path is `in_chroma` to
`chroma_reg/D` with0ns synthetic minimum input delay. Vivado also warns that
`HD.CLK_SRC` is unset. These are unplaced OOC estimates; physical setup/hold and
full-board integration remain mandatory gates. No constraints were relaxed.
Eight warnings trim unused product bits24:20, consistent with the retained
signed20 output cast; full-vector goldens verify the visible result. There are
zero synthesis errors/critical warnings. No hardware result is claimed.
