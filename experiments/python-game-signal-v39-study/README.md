# V39: finer coefficient-bit and raw rank-signaling proxies

This pilot fixes one specific defect in SP38's mode-choice proxy: rounding each
isolated CP02 candidate to bytes can hide a real DC-bit difference. It combines
an **unrounded coefficient-bit proxy** with the raw truncated-unary rank decision
count, and evaluates lambda 1/4/16 on separate causal histories. Actual packets
use the unchanged RP39 decoder grammar. There is no free mode signaling.

The harder retained prefix has promising aggregate results; neither policy is
uniformly better, and simple synthetic fixtures expose remaining global-rate
model failure. No default promotion or HEVC/AV1 advantage follows.

| Twelve-frame window | Policy | Complete bytes | Active MSE | Byte change vs control | MSE change |
| --- | --- | ---: | ---: | ---: | ---: |
| Primary | Mode0 control | 134,817 | 14.354870 | — | — |
| Primary | lambda1 | 139,005 | 13.828465 | +3.1064% | −3.6671% |
| Primary | lambda4 | 137,135 | 13.846928 | +1.7194% | −3.5385% |
| Primary | lambda16 | 135,918 | 13.962322 | +0.8167% | −2.7346% |
| Complex | Mode0 control | 309,308 | 26.365446 | — | — |
| Complex | lambda1 | 312,455 | 25.650186 | +1.0174% | −2.7129% |
| Complex | lambda4 | 308,839 | 25.657229 | −0.1516% | −2.6862% |
| Complex | lambda16 | 305,345 | 25.865307 | −1.2812% | −1.8970% |

Every complete frame fits 49,152 bytes. Complex lambda16's maximum packet is 39,829
versus control 39,354, despite its lower aggregate byte budget. Its peak MSE is
26.398723 versus control 26.986409. Aggregate improvements are not per-frame
quality/rate guarantees; the policies have independent visible reference history.

## Proxy and decoder semantics

All SP38 predictor rules remain unchanged: fixed-zero temporal base, independent
2×2-block tiles per plane, four clipped 8×8 predictor arrays from already decoded
residual edges, exact Q14 transforms/quantization, and immediate hidden-block 128
commit. Mode0 control forces temporal prediction. Each candidate policy chooses
the lowest score among stable first representatives of distinct clipped arrays:

```text
source_YUV_SSE + lambda * (coefficient_bit_proxy + raw_rank_decisions)
```

The coefficient proxy is:

```text
min(1024 raw bits,
    32 parameter bits + minimum DC Rice bits
    + exact AC run/EOB syntax bits + per-band minimum Rice bits)
```

It uses frozen CP02 Rice lengths and syntax. It deliberately omits the separate
DC/AC byte ceilings and constant packet header/CRC. A test shows DC=−29 and
DC=0 have identical isolated packet-byte costs but different fine proxies:
41 versus 35 bits. The proxy therefore sees a difference the previous byte-rounded
decision could not see. Raw rank cost is 0 for singleton menus, otherwise
`min(rank+1,N-1)` decisions for the same truncated-unary grammar. Duplicate clipped
predictors are excluded from argmin; lowest canonical mode wins ties.

This is still a proxy: it does not model whole-plane DC/context coupling,
adaptive arithmetic probabilities, mode fallback/headers/termination or true
marginal full-frame cost. Source YUV SSE is not the eventual RGB565 metric.
Actual packet bytes and original-source RGB565 quality are measured separately.

All four candidate transforms, quantizations, reconstructions, source SSEs,
fine-bit costs, rank counts and canonical flags are paid and archived **even for
the forced control**, as a research oracle. Cost tensors are int64 `[blocks,4,4]`
with fields SSE/coefficientBits/rawRankDecisions/canonicalFirst. Hidden entries
are zero. Unselected aliases and losing candidates are retained rather than
silently discarded from evidence. Neither policy uses residual RDO/pruning.

## Actual paid packets and own reference chains

The proof sender constructs a complete SP38 packet and then runs frozen RP39
rank transcoding, including its parsing, menu derivation, arithmetic trials,
fallback comparisons, reconstruction and repacking. Both actual intermediate
and final packets are retained, along with every winning/losing rank trial and
menu/rank arrays. The unchanged RP39 receiver independently decodes the actual
packet before it supplies the next causal reference.

The exact source/HUD/ROI 8/background 16 configuration matches the previous pilot.
All 27 mode0 control packets reproduce the prior RP39 control packets byte for
byte. The new policies change mode choices and visible reconstruction; they are
not lossless substitutes for the old spatial history. Mode and coefficient bytes
remain explicit in every summary. For example, complex lambda16 pays 5,528 mode
bytes plus 151,977 coefficient bytes, versus control 36 and 161,432 respectively.

There are 108 actual packets: two 12-frame retained gameplay prefixes × four
policies, plus three single-frame synthetic inputs × four policies. Each policy
has its own accepted decoded reference chain. All policies, including losing
trade-offs, are retained.

## Synthetic counterexamples

| One-frame fixture | Control bytes / MSE | lambda1 | lambda4 | lambda16 |
| --- | --- | --- | --- | --- |
| Flat | 3,095 / 0 | 5,189 / 0 | 5,189 / 0 | 5,189 / 0 |
| Directional constant tiles | 4,930 / 0 | 5,243 / 0 | 5,243 / 0 | 5,243 / 0 |
| Low-amplitude noise | 5,136 / 25.147523 | 5,368 / 25.094739 | 5,230 / 25.131118 | 5,192 / 25.138384 |

Fine bits make flat/directional fixtures select spatial modes, so the intended
byte-rounding defect is fixed. However, **flat complete bytes increase 67.66%** at
identical zero error. Its coefficient component grows 1,144→3,212 bytes, even
though the isolated proxy favored the local coefficient changes; the compact
rank map is only 29 bytes. Directional bytes rise 6.35%. This directly disproves
the idea that a finer isolated proxy alone establishes a global compression win.

## Verification and scope

Four producer tests qualify the DC byte-tie/fine-bit distinction, independent
scalar Rice/syntax calculation, stable duplicate ranks, hidden immediate commit,
flat-predictor selection and source ownership. Independent replay imports no new
encoder and recomputes source candidate prediction, Q14 forward/quant/inverse,
SSE, unrounded bit cost, rank decision count, canonical eligibility and the exact
lambda argmin using each policy's actual decoded neighbors/reference. It checks
actual RP39 decoding, intermediate packets, bytes, source/HUD, candidate arrays,
rank alternatives, summaries and the 27 control goldens.
Final replay passes all 108 actual RP39 frames and independently recomputes
3,372,192 candidate blocks and 324 rank trials. Three independent tests pass;
all 1,301 producer/source pins match. No new signal encoder is imported by replay.

Encoder means are roughly 195–216 ms/frame for the retained gameplay on this host.
They include all four candidate evaluations, both proof serialization paths and
duplicate reconstruction. Source/HUD loading or generation, archive/hash/metric
I/O, independent receiver, transport and display are excluded. These are single
clock samples, not paired speed measurements, optimized sender costs or 30 fps.

The next gate is actual whole-packet rate/quality selection, with own-history
controls and explicit global-rate counterexamples. A local source guard must not
be confused with quality against an independent control history. Retain the flat
fixture as a negative regression when introducing frame/tile guards or richer
entropy models. The source windows are reused, not held-out gameplay; there are
no fresh HEVC/AV1 encodes, native endpoints or fitted hardware claims here.

```sh
cd experiments/python-game-signal-v39-study
python -m unittest -v test_model
python -m unittest -v test_verify
python verify.py
```
