# V45 exact mirrored-output Q14 inverse

This Python prototype exploits a symmetry already present in the frozen integer
basis: `Q[k,7-x] = (-1)^k Q[k,x]`. It forms even and odd sums for each mirrored
output pair, then rounds `(even+odd+8192)>>14` and `(even-odd+8192)>>14` separately.
The first pass still rounds before the second pass. No intermediate-rounding
fusion or floating transform approximation is allowed.

All **1,731 full-grid AB38 payloads** from v38/v39/v40 were independently decoded
and dequantized with their actual packet qmaps. The new inverse matches the frozen
matrix inverse on **4,673,700 actual blocks**. Scalar sparse/shortcut execution is
also checked on 5,193 actual tiles. Five focused tests cover signed impulse basis
extremes, random full-domain blocks, both rounding boundaries, zero/DC shortcuts,
integer interval bounds and invalid domains. Independent replay recomputes actual
qmaps, all transform outputs and multiply counts.

## Logical DSP work, with equal shortcuts

| Model on these blocks | Multiply operations |
| --- | ---: |
| Dense direct two-pass matrix | 4,785,868,800 |
| Dense mirrored pairs | 2,392,934,400 |
| Sparse direct, equal zero/DC shortcuts | 275,542,196 |
| Sparse mirrored pairs, equal zero/DC shortcuts | 138,052,328 |

Both sparse models skip zero products. Both give zero blocks zero products and
DC-only blocks the same exact two-product shortcut. There are 3,073,322 zero,
281,230 DC-only and 1,319,148 complex blocks. With equal shortcuts, modeled
multiplies fall 49.8979%; the benefit is not obtained by charging shortcuts to only
one side. Mirroring adds even/odd recombination and changes scheduling; halving
multiply count does not prove halved cycles or latency.

The vectorized NumPy implementation still executes dense matmuls. Its zero-skip
operation counts are a proposed sparse MAC implementation model, explicitly
separate from executed Python timings. The scalar function actually skips zero
multiplications and executes the zero/DC cases, validating logical accounting on
the selected actual tiles and directed fixtures. No DSP lane synthesis is run.

## Integer widths and component boundaries

The full accepted coefficient/quantizer domain is ±2048 ×255 =±522,240, requiring
20 signed input bits. Basis constants require 14 signed bits. Conservative
absolute-value interval sums bound first-pass accumulation at 22,604,644,352
(36 signed bits), rounded intermediates at 1,379,678 (22 signed bits), and
second-pass accumulation at 59,717,990,744 (37 signed bits). These conservative
bounds cover the advertised domain, not just observed small gameplay values.
The observed maximum dequantized magnitude is 1,792 and intermediate magnitude
674; they must not be used to narrow the normative decoder domain.

A target implementation must preserve signed extension, both +8192 shifts,
accumulator width, zero/DC handling and memory ownership. Operand widths may
require different DSP arrangements on different FPGA families. No fit, resource
count, memory arbitration, initiation interval, routed clock or complete decoder
frame rate follows from this Python proof. Compressed packets, coefficients,
references, display pixels and application quality are unchanged.

The model uses int64 arrays as host proof storage. One-block transform buffering
and the v44 four-stream coefficient iterator are separate components until an
integrated pipeline proves backpressure, late errors and atomic frame publication.
No RTL, firmware, Sunshine installation or hardware is modified.

```sh
python -m unittest -v test_model
python benchmark.py
python verify.py
```
