# V39: lossless ranks among decoder-derived distinct spatial predictors

RP39 reduces the mode-map overhead exposed by SP38 without changing any chosen
predictor, coefficient, reference or displayed pixel. It codes a rank among the
**distinct clipped prediction arrays that the decoder can derive itself**. Every
plane retains its old SP38 mode payload as a complete-byte fallback, winning ties.

| Twelve-frame spatial policy | SP38 complete bytes | RP39 complete bytes | Saving | Unchanged active MSE |
| --- | ---: | ---: | ---: | ---: |
| Primary | 155,885 | 139,838 | 10.2941% | 13.890415 |
| Complex | 331,421 | 313,848 | 5.3023% | 25.651026 |

Primary mode payloads fall 19,827→3,780 bytes (**80.94%**); complex falls 23,457→5,884
(**74.92%**). All 54 old pilot packets have actual RP39 packets. Every complete
packet is no larger than its SP38 input, including both unchanged-size headers,
new rank dispatch/bit count, arithmetic termination, padding and checksums.

The mode0 controls remain 134,817 / 309,308 bytes. RP39 spatial is still 3.7243% /
1.4678% larger than those controls while preserving SP38's lower MSE. Thus this
is a useful lossless signaling improvement **within the spatial profile**, not
proof that spatial prediction now beats the mode0 baseline or HEVC/AV1.

## Distinct menus are derived from reconstructed context

Each plane keeps SP38's independent 2×2-block tiles. Within tile-major order
`ty,tx,(0,0),(0,1),(1,0),(1,1)`, the decoder derives the same four 8×8 predictors:
temporal, vertical residual edge, horizontal residual edge and DC available-edge
mean, with final predictor clipping to 0..255. Their residual edges come only from
already reconstructed neighbors within the tile. Hidden safe blocks commit 128
immediately and produce no rank event.

The four predictor arrays are deduplicated **after clipping**, in stable mode 0,
mode 1, mode 2, mode 3 order. If there are N distinct arrays, the selected predictor
is represented by its rank 0..N−1. The top-left block has N=1, rank 0 and no coded
decision. Other blocks also frequently have N=1 because decoded residual edges
are zero or clipping makes predictors identical.

The old SP38 producer's stable lowest-mode argmin picks the first of identical
predictors. This transcoder checks that property and rejects a nonfirst duplicate
input instead of silently changing its mode identity. This is qualification of
the actual 54 retained packets, not a claim to accept every semantically legal
arbitrary SP38 stream from another encoder.

There are 421,524 visible-block menu events across all policies/fixtures;
283,626 have N=1 and require no arithmetic decision. The chosen coefficient
components, quant map and exact HUD payload bytes remain unchanged.

## Real bounded binary arithmetic syntax

New outer magic `RP39` and inner magic `TR39` keep SP38's 80-byte outer and 84-byte
inner-header-plus-CRC structures. A new profile digest binds the menu derivation,
tile-major order, truncated-unary ranks and context rule. Old mode dispatch 0..2
remains a per-plane fallback; new dispatch 3 is:

```text
u8 dispatch=3 | u32LE arithmetic_bit_count | packed arithmetic bits
```

For N>1, truncated unary emits `(rank>i)` for i=0..N−2, stopping on zero. N=1
emits no decisions. The maximum is three decisions per block. Context index is:

```text
position = 2*(block_row&1) + (block_column&1)
context  = position*12 + (N-2)*3 + decision_index   # maximum 44
```

The coder reuses frozen AB38 binary arithmetic: 16-bit interval, 8-bit adaptive
probability, one 17×8 probability product per binary decision, initial 128 and
shift 5 adaptation. It resets per plane. Bit counts include 18 termination/guard
bits; unused final low bits are zero. Inner and outer CRCs are charged. The
complete rank payload must be strictly shorter than the old actual mode payload;
otherwise the old mode component is copied unchanged.

The inherited primitive allocates 88 probability entries (88 logical 8-bit bytes
for a sequential plane coder); used context IDs and actual counts are retained.
Pending/interval/bit-buffer storage and Python object memory are separate. This
is logical arithmetic/state accounting, not fitted FPGA memory, DSP allocation,
routed timing, power or throughput. Deriving distinct predictors also adds decode
work; the rank stream is not a free reduction in signaling.

Across all paid trials there are 159,869 probability products. Selected rank
streams contain 82,987 products; trials that lose to old-mode fallback remain paid
producer work. Exactly 73 plane payloads select ranks (36 primary spatial,
36 complex spatial and one synthetic-noise luma plane).

## Synthetic and timing evidence

Flat and directional-tile packets remain 3,095 / 4,930 bytes, with zero MSE. Their
one-byte all-zero maps beat rank payloads and are retained. Noise spatial drops
6,471→5,378 bytes (**16.8907%**) with exactly unchanged MSE 25.094989; it remains
larger than the 5,136-byte mode0 noise control at MSE 25.147523.

Each of the 54 frames has **one paid transcoder timing sample**, not repeated
paired sender timing. Primary/complex spatial means are 29.83 / 40.72 ms. The clock
includes SP38 parsing, derived menus, reconstruction, every arithmetic trial,
fallback comparison and repacking. The original SP38 encode is already paid
outside this clock. Fixture/archive I/O, equality metrics, independent receive,
network and display are excluded. It is not an encoder speedup or 30 fps result.

## Verification and next gate

Three producer tests cover stable deduplication and nonfirst-duplicate rejection,
all N/rank arithmetic cases with independent frozen decoding, zero-decision N=1,
invalid ranks, tile-local reconstruction and immediate hidden blocks. The
independent decoder imports no new rank encoder. It derives menus from its own
current decoded samples, checks actual rank/fallback syntax, coefficient-byte
identity, selected modes, causal references, exact HUD and unchanged output.
Actual losing rank packets, menu/rank arrays, arithmetic work, source pins and
logs are retained for all 54 frames.
Final independent replay passes all 54 causal frames and 162 rank trials, with
73 selected rank components, 283,626 singleton blocks and 159,869 traced
probability products. Eight independent tests pass, including resealed rank
guard, profile, mode, output and prior-reference corruption without publication,
and rejection of a nonfirst duplicate predictor. All 1,295 source pins match.

The next step is to integrate the rank-cost estimate into mode selection and
measure whole tile/group decisions rather than choosing from an isolated
packet-byte proxy. Preserve this lossless transcode as a regression oracle;
changing predictor choice creates new reference histories and needs separate
quality qualification. The original 54 frames are reused short prefixes and
synthetics, not held-out gameplay. No native endpoint or hardware 30 fps is proved.

```sh
cd experiments/python-game-mode-rank-v39-study
python -m unittest -v test_model
python -m unittest -v test_verify
python verify.py
```
