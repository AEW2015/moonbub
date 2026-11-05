# V39 checkpoint: full arithmetic histories and rate-aware spatial choices

This checkpoint extends exact adaptive coefficient coding to complete 48-frame
histories and cuts spatial mode signaling with decoder-derived predictor ranks.
A finer spatial bit-cost proxy finds one small rate/quality Pareto improvement,
but synthetic regressions show why actual whole-frame rate checks remain needed.
The six-hour run is ongoing; native codec superiority and physical 30 fps remain
unproved. No firmware, FPGA bitstream or hardware is modified.

## Exact arithmetic coding across both complete histories

[Full qualification](../experiments/python-game-binary-full-v39-study/README.md)
uses the frozen AB38/CS38 syntax, parameters and independent arithmetic decoder.
All 96 frames, including key 24, preserve original coefficients, normalized
references, exact HUD and displayed pixels. Both actual full/compact alternatives
are retained for each plane: 576 AB38 component packets, with an old-CS37 fallback.

| 48-frame window | CS37 complete bytes | CS38 complete bytes | Saving | Active MSE, unchanged |
| --- | ---: | ---: | ---: | ---: |
| Primary | 434,875 | 382,756 | 11.9848% | 14.383661 |
| Complex | 1,057,390 | 950,940 | 10.0672% | 26.544696 |

Complete maxima are 19,413 / 36,397 bytes. Nominal 30-decision rates are 1.913780 /
4.754700 Mbps, byte arithmetic rather than measured service. Against the matched
fixed-policy legacy histories, reductions reach 16.87% / 14.07% at identical pixels;
that is not a claim against the different searched v35 controller. These remain
the same two reused clips, not new held-out content.

Six inherited frozen AB38 tests qualify unchanged syntax. No additional unit
count is invented for extending a dataset. Independent replay checks all 576
alternatives and 96 causal frame packets. Candidate-only encode costs are 42.85 /
108.31 ms/frame; old source encoding is externally paid. The decoder proof adapter
still stages full arrays and re-encodes frozen syntax, so this is not native
sender/receiver timing or an FPGA streaming architecture.

## RP39: omit choices that the decoder can infer

[Rank grammar](../experiments/python-game-mode-rank-v39-study/README.md) preserves
SP38's already selected modes, coefficient payloads and reconstructed pixels.
Before reading a mode, the decoder builds the same four clipped predictors from
already reconstructed context and stably removes duplicates. The transmitted
symbol is a rank among the distinct predictors. A singleton menu emits no bit
decisions; tile top-left is a guaranteed example. Actual rank streams use the
bounded AB38 binary machine, with the old full-mode payload winning ties.

| 12-frame spatial stream | SP38 bytes | RP39 bytes | Saving | Mode bytes old→new |
| --- | ---: | ---: | ---: | ---: |
| Primary | 155,885 | 139,838 | 10.2941% | 19,827→3,780 |
| Complex | 331,421 | 313,848 | 5.3023% | 23,457→5,884 |

The images, modes, qmap bytes, coefficient payload bytes, HUD and whole causal
references are exact. Mode costs fall 80.94% / 74.92%, but the spatial streams
still exceed their mode0 controls by 3.7243% / 1.4678%, retaining their lower MSE.
The noise fixture shrinks 6,471→5,378 bytes; synthetics remain separately labeled.
No compression win over the matched mode0 control is claimed here.

Three producer and eight independent tests pass. Replay checks 54 frames, 162
rank trials, 73 selected rank planes, 283,626 singleton zero-decision blocks and
159,869 trial probability products, with dynamic menu construction, original
mode identity, exact termination, fallback and state publication. These are
logical work counts, not DSP cycles. The new RP39/TR39 contract needs a new
receiver. Paid-input transcoding averages 29.83 / 40.72 ms excluding old encoding;
there is no sender FPS claim.

## Fine bit proxy plus explicit rank cost

[Signal-aware pilot](../experiments/python-game-signal-v39-study/README.md) fixes
a concrete flaw in SP38's byte-rounded isolated-CP02 proxy. A zero residual and
DC=-29 can both occupy 32 packet bytes while their unrounded coefficient proxies
cost 35 and 41 bits. The improved selector uses source YUV SSE plus lambda times
unrounded DC/AC bits and actual truncated-unary rank decisions. It retains the
same RP39 decoding grammar, own causal histories and no old global RDO.

| 12-frame window / policy | Complete bytes | Active MSE |
| --- | ---: | ---: |
| Primary mode0 control | 134,817 | 14.354870 |
| Primary lambda1 | 139,005 | 13.828465 |
| Primary lambda4 | 137,135 | 13.846928 |
| Primary lambda16 | 135,918 | 13.962322 |
| Complex mode0 control | 309,308 | 26.365446 |
| Complex lambda1 | 312,455 | 25.650186 |
| Complex lambda4 | 308,839 | 25.657229 |
| Complex lambda16 | 305,345 | 25.865307 |

Complex lambda16 improves complete bytes 1.2812% and mean MSE 1.8970%; lambda4
also improves both slightly. Primary lambda16 spends 0.8167% more bytes for 2.7346%
lower MSE. These are actual complete packets and measured trade-offs, not a
matched-quality standards victory. This is a short calibration pilot; lambda16
must be fixed before additional-scene qualification, rather than selecting a
winner on the qualification data and calling it held out.

The flat fixture is a critical negative result: 3,095→5,189 bytes at zero MSE;
directional tiles likewise grow 4,930→5,243. Fine local bits still miss whole-plane
DC prediction and mode/entropy context. The proxy may select a locally cheaper
representation that makes the actual packet larger. It cannot substitute for
final serialization and admission.

Four producer and three independent tests pass. Replay checks 108 actual RP39
packets, 27 byte-identical frozen controls, 3,372,192 predictor/quantization/SSE/
fine-bit/rank/selection candidate blocks and 324 actual rank trials. All losing
rank streams, candidate costs, synthetic sources and intermediate packets are
retained. Encoding includes the proof intermediate and rank conversion; no
optimized sender or 30 fps is claimed.

## Standards comparison and remaining video gap

[Accounting](prototype-v39-comparison.json) reuses verified original-input native
anchors: full 48-frame points from v36 and prefix 12 points from v38. There is no
fresh native encode or decode in v39. Both receive the same common YUV source,
and budgets charge identical exact HUD, 80 binding bytes/frame and native
extradata once. Native binding is modeled cost, not custom-protocol support.

| 48-frame window / codec | Complete budget bytes | Active MSE |
| --- | ---: | ---: |
| Primary CS38 | 382,756 | 14.383661 |
| Primary HEVC q32 | 239,698 | 11.210939 |
| Primary AV1 q48 | 223,411 | 12.248229 |
| Complex CS38 | 950,940 | 26.544696 |
| Complex HEVC q28 | 607,492 | 22.161878 |
| Complex AV1 q38 | 602,347 | 19.767521 |

All native points remain smaller at lower mean MSE. After removing identical
HUD/bindings, custom video remainders are 179,350 / 484,580 bytes versus HEVC 36,292 /
141,132 and AV1 20,005 / 135,987: a 3.43–8.97× component gap. This is not matched-
quality BD-rate, an optimal standards encoder or equal FPGA resources. The
arithmetic gain is real but has not closed the larger prediction/residual gap.

## Next experiments in the active run

1. Gate spatial alternatives on **exact full-block reconstructed YUV equality**
   to mode0, then accept only a strictly smaller actual complete packet. This
   preserves future reference semantics and rejects local-proxy regressions.
   This exact-output experiment is underway separately, not included above.
2. Qualify fixed policies and arithmetic syntax on additional timestamp-defined
   scenes. [Source notes](v39-source-qualification-notes.md) specify exact BOX /
   RGB565/YUV formation, media hashes, source-cadence gaps and provenance limits.
   Additional windows are not new games or project-wide unseen source evidence.
3. Integrate and test arithmetic receive/emission directly, then measure full
   host service and bounded FPGA memory/compute separately from ESP32 transport.
   Tile-major predictor order versus coefficient order needs an explicit staging
   schedule; small packed context state alone does not qualify memory bandwidth.

JPEG/v20 and prior frozen studies remain unchanged. The six-hour run remains
active after this checkpoint.

## Reproduction

```sh
python experiments/verify_prototype_v39.py
```

The manifest binds frozen v38 dependencies, source snapshots, actual packets,
candidate data, focused tests and independent replay. There are 18 new focused
passing tests plus inherited AB38 coverage, 258 archived frame cases (54 rank,
108 signal, 96 full arithmetic), 576 arithmetic alternatives and 486 rank trials.
These policies reuse source content; they are not 258 independent captures.
