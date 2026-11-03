# Bounded Q14 arithmetic and DSP operand-width experiment

This Python-only study preserves the frozen Q14 transform's exact rounding and
full legal coefficient domain. It tests whether narrower host intermediates
help and records arithmetic widths for a future FPGA implementation. It does
not generate RTL, assign DSPs, validate memory service or establish FPGA timing.

## Bounds and exactness

`bounded_math.py` computes conservative absolute bounds using the largest
matrix row L1 norm for forward transforms and column L1 norm for inverse
transforms. Both rounding biases are included. A safe transform uses int32
NumPy matrix operations and converts its return to the reference int64 dtype;
a wider legal inverse uses the original int64 implementation. Bounds are
checked before narrowing, including signed-min and unsigned integer inputs.

| Domain | Input | First accumulator | Rounded intermediate | Second accumulator |
| --- | ---: | ---: | ---: | ---: |
| Residual forward, ±255 |9 signed bits|25|11|26|
| Full inverse syntax, ±522,240 dequantized |20|36|22|37|

The Q14 matrix constants need 14 signed bits. Forward intermediates fit int32.
The inverse int32 cutoff is conservatively **18,779** in absolute dequantized
input. The complete accepted ±2,048 coefficient syntax times a quantizer up to
255 does **not** fit int32; silently narrowing all decoder inputs would be wrong.
The fallback is deliberately retained even though sampled host keys use much
smaller values (maximum dequantized magnitude 1,024 in this benchmark).

AMD documents a signed 25×18 multiplier and 48-bit accumulator in the 7-series
DSP48E1. These arithmetic domains fit those operand/accumulator widths: the
inverse's 20/22-bit data can use the wider multiplier port with 14-bit constants.
This is a **width-compatibility inference**, not a one-DSP decoder, initiation
interval, resource count or routing/clock result. See the primary
[DSP48E1 guide, UG479](https://docs.amd.com/api/khub/documents/gu4oRPFEh_Pm2uaAlfY6Kg/content).

The conservative bounds are 11,825,912 and 33,422,216 for the two forward
accumulators; the full inverse bounds are 22,604,644,352 and 59,717,990,744.
Signed arithmetic, each pass's rounding and final clipping must be preserved
in any future RTL/native implementation. Reducing a host workspace width does
not reduce the external reference/framebuffer memory requirement.

## Actual paired result

`benchmark.py` exercises four native input frames from each 4-second source
window, two quantizers (8/32), and three alternating-order repetitions:
48 checks from eight source capture IDs. It compares residual coefficients,
reconstructed YUV, complete key bytes against the fast-key encoder, and the
frozen packet decoder's RGB. Source/frame/PTS and executed-code hashes bind the
run. Content may repeat; this is not 48 independent images or native30fps input.

| Transform + inverse stage | Wide mean | Bounded mean | Change |
| --- | ---: | ---: | ---: |
| Combat |17.17 ms|17.04 ms|0.8% lower|
| Second clip |18.50 ms|18.16 ms|1.9% lower|

The inverse stage alone gets slightly **slower**:5.69→5.85 ms and6.25→6.53 ms.
Range checks, casts and returning the original int64 dtype offset most of the
small forward improvement. Host load is uncontrolled; these small differences
are not compelling throughput evidence. This remains an exactness/width study,
not a selected host optimization or an integrated encoder scheduling result.
Color conversion, entropy, packet/state work, source scaling, network, receiver
and presentation are excluded from these timings. No full-key or30fps gain is
inferred by adding/subtracting timings from another benchmark run.

Eleven tests cover seeded/extreme values, the exact conservative dispatch
boundary, full-syntax int64 fallback, malformed/out-of-domain input, odd block
geometry, key/P residuals, independently constructed Python-int bounds and
DSP operand-width arithmetic. These are finite numerical checks plus analytic
bounds, not formal equivalence of every complete codec packet or a hardware test.

## Reproduce

From this directory with the common pinned environment and media layout:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v
/home/lori/gamebub-streaming-prototype/.venv/bin/python benchmark.py
```

`results.json`, `run.log` and `tests.log` preserve the measured run. Retain the
frozen codec as the golden. Optimize native arithmetic only with identical
rounding and valid wide-input fallback; measure whole-key/P service separately.
