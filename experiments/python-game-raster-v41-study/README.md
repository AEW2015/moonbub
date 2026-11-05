# V41: global raster spatial context with exact-output guarding

RR41 removes SP38's 2×2-block predictor resets. Available top/left residual edges
now cross every prior block boundary in global raster order. The first pilot
has a genuine lossless synthetic witness: **flat 3095→2683 bytes (−13.3118%)**,
with zero error and exact control reference. Gameplay candidates still lose.

| Input | Control bytes | Candidate bytes | Selected bytes | Accepted candidate frames |
| --- | ---: | ---: | ---: | ---: |
| Primary, 12 frames | 134,817 | 138,677 | 134,817 | 0/12 |
| Complex, 12 frames | 309,308 | 313,076 | 309,308 | 0/12 |
| Flat | 3,095 | 2,683 | 2,683 | 1/1 |
| Directional tiles | 4,930 | 5,298 | 4,930 | 0/1 |
| Low-amplitude noise | 5,136 | 5,155 | 5,136 | 0/1 |

Every candidate reconstructs the complete mode0 YUV reference exactly. The actual
complete-packet guard chooses a candidate only if strictly smaller; ties retain
control. All packets fit 49,152 bytes. There are 63,699 eligible nonzero alternatives
and 20,862 proposed nonzero block modes. The flat candidate uses 5,143 nonzero modes
among 5,144 visible luma blocks, rather than being forced to start every 2×2 tile
with temporal prediction. This confirms the reset-island hypothesis on that
fixture, not a compression gain on the two gameplay windows.

## New causal decoder profile

The four predictor formulas remain temporal base, top residual vector, left
residual vector and DC mean of available residual edges. The temporal base is 128
on a key frame or the exact previous canonical reference on a P frame. What
changes is availability: top iff `block_row>0`, left iff `block_column>0`.
Prediction is clipped to 0..255, DC uses signed floor half-up rounding and hidden
safe 8×8 blocks commit 128 immediately before any later global neighbor reads.

The decoder processes block rows/columns in global raster order. It never uses a
future neighbor, the original source image or a precomputed control frame. Its
distinct clipped-predictor menu and selected rank are derived from its already
reconstructed prefix. The new header/profile is **RR41/GR41**, with the same
80-byte outer and 84-byte inner-header-plus-CRC structures as RP39. Coefficient,
quant-map and exact HUD grammars are frozen; there is no old spatial decoder
compatibility claim across the new profile.

Mode components retain dense 2-bit/RLE/all-zero fallback and dispatch 3 arithmetic
ranks, choosing the actual complete-payload winner. Ranks follow global raster,
and the frozen bounded AB38 context uses edge availability rather than parity:

```text
position = 2*(block_row>0) + (block_column>0)
context  = position*12 + (distinct_menu_size-2)*3 + decision_index   # <=44
```

Singleton menus emit no decisions. Other ranks use truncated unary and the
frozen 16-bit interval/8-bit probability/shift 5 adaptive coder. Every rank trial,
header, termination/guard bit, padding and checksum is charged; old full mode
payload wins byte ties. No coefficient or mode signaling is free.

## Host-only control oracle and exactness proof

The host first computes the complete mode0 quantized reconstruction once. It
then constructs all global predictor arrays from top/left positions of that
known control image and vectorizes candidate transforms across blocks. Mode0
coefficients/output are reused; modes 1–3 do new forward/quant/inverse work.

This optimization is permitted in the **encoder**, which has the source. A mode
is eligible only if every reconstructed 8×8 YUV sample equals the mode0 target,
and it is the first representative of its distinct clipped predictor. Therefore
each accepted output block supplies the same neighbor samples to the next block;
the decoder discovers those samples causally rather than receiving an oracle.
The complete committed reference also equals control, preserving future temporal
predictions. Selection among eligible alternatives uses the fine coefficient-bit
plus raw-rank proxy; it is not a scalar-MSE guard.

Actual control/candidate packets are decoded on forks of the current selected
receiver state; only the selected receiver advances. The encoder's next state
and metric source are its owned mode0 oracle, with decoder equality asserted at
every frame. Independent replay compares that host oracle against a sentinel-
initialized causal frontier, raw top/left edge values and all four predictions.
Thus a hidden future-neighbor read cannot be credited as a decoder optimization.

Control coefficient payloads, quant-map bytes, HUD bytes, incoming/outgoing
reference tags and full YUV/RGB quality match all 27 previous RP39 mode0 controls.
The wire magic and profile tag differ, so this is **content/semantic equality,
not cross-profile packet byte identity**. Gameplay active MSE remains 14.354870 /
26.365446; flat/directional error stays zero and noise MSE 25.147523.

## Logical edge-cache sketch, not complete memory fit

Residual-edge history can be represented by a signed-int16 top row for each
plane: 720+360+360 samples = 2880 bytes, plus three 8-sample left edges = 48 bytes.
These 2928 logical bytes are **only the edge context**. Temporal/output reference
frames, coefficient/payload buffers, range state, predictor deduplication,
inverse-transform scratch, DMA and display/transport buffers are additional.
No SRAM/BRAM/DSP allocation, external-memory arbitration, routed clock or FPGA
fit is established by this sketch.

The flat candidate's actual smaller serialized packet exercises the accepted
candidate path absent in v40; the strict guard protects all 26 losing cases.
Directional tile boundaries and gameplay continue to expose the gap between a
local bit proxy and global mode/coefficient entropy. Do not generalize a flat
synthetic gain into a gameplay or HEVC/AV1 victory.

## Evidence and reproduction

The campaign retains 27 selected packets, 54 actual control/candidate packets,
all arithmetic rank trials, modes, full six-field candidate cost tensors,
eligibility masks, menus and rank options. Four producer tests cover crossing old
tile boundaries, DC/clipping, exact oracle eligibility, source ownership, hidden
canonical samples and strict byte ties/caps. Independent tests/replay validate
the new raster decoder, future-prefix sentinels, exact full-block eligibility,
coefficients, old control semantics, actual choices, references, source/HUD and
all summaries without importing the new sender.
Final independent replay passes 27 selected frames, 27 old control semantic
matches, 843,048 candidate recomputations, 218,700 causal frontiers and 162 rank
trials, including the one genuinely accepted candidate. Eight independent tests
pass, including original CRC validation before syntax adaptation and rejection
without corrupt reference publication. All 1,310 source pins match.

Single paid pair-clock means are 237.94 / 226.59 ms for the real prefixes. They pay
the host oracle, all proposals, both complete mode/coefficient/rank trials and
wrappers. Fixture/HUD reads or generation, archive/hash/metric work, independent
decoders, network and display are excluded. These are not paired speed results
or 30 fps. The 27 inputs are reused short prefixes/synthetics; no held-out gameplay,
fresh HEVC/AV1 encode, native endpoint or fitted hardware is qualified here.

```sh
cd experiments/python-game-raster-v41-study
python -m unittest -v test_model
python -m unittest -v test_verify
python verify.py
```
