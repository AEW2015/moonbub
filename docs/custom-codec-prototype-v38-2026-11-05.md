# V38 checkpoint: direct CS37, adaptive coefficient coding and spatial modes

This is the first checkpoint in the six-hour Python research run that began
2026-11-05 at 07:14:21 UTC. It establishes an exact direct CS37 sender and an
11.00% / 10.41% complete-byte reduction from adaptive binary coefficient coding
on two 12-frame prefixes. A separate spatial predictor improves source MSE but
regresses compression because mode signaling costs more than residual savings.
None establishes HEVC/AV1 superiority or physical 30 fps.

Resolution stays 720×480 coded / 720×405 active, with 21,120 exact RGB565 HUD words
and a 49,152-byte complete frame cap. These are reused short Mass Effect clips;
synthetic and directed-motion tests are labeled separately. No firmware,
bitstream or physical hardware changes are made. JPEG/v20 remain unchanged.

## Integrated direct CS37 sender

[Integrated implementation](../experiments/python-game-integrated-v38-study/README.md)
combines the fast fixed-zero analyzer, preserved original quantization/global
RDO reversion decisions, direct coefficient selection and CS37 implicit grammar.
It computes full-grid and compact costs but constructs only the three winning
plane components. No intermediate CN36 packet, coefficient parse or transcoder
is used. One final reconstruction, normalization and CS37 wrapper are paid;
inverse work required inside RDO remains paid separately in the same timer.

| 48-frame window | Equivalent fast-CN36 + transcode sender | Direct CS37 | Time reduction |
| --- | ---: | ---: | ---: |
| Primary | 66.013235ms | 52.330068ms | 20.7279% |
| Complex | 94.977235ms | 65.397145ms | 31.1444% |

Every frame has three alternating paired repetitions. Both clocks include fresh
fixed-policy analysis, quantization, RDO, global legacy-size decisions, entropy,
reconstruction, normalization and one output wrapper. Source/HUD fixtures or
generation, verification, archives, receiver/network/display are excluded.
Do not compare the new grammar timing with v37's CN36-only output task or
multiply component speedups from separate campaigns. Both means exceed 33.33 ms.

All 96 main and six directed fractional-motion packets are byte-identical to
v37 CS37: 434,875 / 1,057,390 bytes on the main windows and 109,308 on the probe.
Independent replay rederives original RDO/reversion decisions at all 102 actual
references and checks 612 full-grid/compact alternatives, ties and fallback,
whole references, coefficients, HUD and quality. Four producer and three
independent tests pass, including forced global reversion and winner-only
construction. The source still has no generalized searched-motion integration.

## AB38: exact adaptive binary coefficient coding

[AB38/CS38 study](../experiments/python-game-binary-v38-study/README.md) preserves
the selected quantized coefficients and codes their DC/run/level events with a
bounded binary arithmetic machine. Four independent streams use a 16-bit interval,
8-bit adaptive probability and shift-only adaptation. Each binary decision uses
one 17×8 unsigned probability product. 352 bytes describes logical packed
probability contexts, not measured Python memory, BRAM allocation, DSP count,
clock, initiation interval or resource fit.

New AB38 component headers include geometry, stream lengths, counts, parameters,
exact bit lengths, termination, padding and CRC. Rice parameters minimize uncoded
Rice lengths, not arithmetic-coded cost. Full-grid and implicit-hidden arithmetic
payloads compete with the unchanged old plane. The old representation wins ties;
actual complete packets cannot grow. New CS38/GS38 profile tags and plane
dispatch 5/6 are required; installed receivers do not support them.

| First 12 causal frames | Old CS37 bytes | Actual CS38 bytes | Saving | Source active MSE, unchanged |
| --- | ---: | ---: | ---: | ---: |
| Primary | 129,084 | 114,889 | 10.9967% | 14.362737 |
| Complex | 302,953 | 271,410 | 10.4118% | 26.378421 |

All 72 selected planes use arithmetic: 9 full-grid and 63 implicit-hidden. Both
actual alternatives are archived for every plane:144 component packets. All 24
frame packets preserve full causal normalized references, quantized coefficients,
exact HUD and displayed pixels. This is a 12-frame-prefix result, not a 48-frame
stream or a broad held-out test; keyframe weighting differs from older tables.

Three component tests and three independent frame-corruption tests pass. The
independent arithmetic decoder imports no encoder. The frame proof decodes the
new coefficients, re-encodes frozen coefficient syntax and invokes the frozen
CS37 receiver to validate tags/reconstruction. It stages full arrays/packets and
is explicitly a proof adapter, not a native streaming-decoder architecture.
All 144 alternatives and frame winners replay. 3,580,304 probability products and
2,792,258 renormalization steps cover all paid alternatives, not just selected
payloads; these are operation counts, not FPGA cycles.

Actual binary candidate encoding costs total 55.10 / 116.91 ms per source frame
for six candidates. Already encoded CS37 input is externally paid. These clocks
exclude input parsing, validation/decode, fixture/HUD generation and archive I/O;
they are not a complete sender speed claim. Arithmetic-state and throughput
qualification, direct integration, full 48-frame testing and held-out scenes
remain to be done.

## Spatial SP38 pilot: lower error at higher byte cost

[Spatial study](../experiments/python-game-spatial-v38-study/README.md) defines
independent 2×2-block tiles per plane. Four modes predict an 8×8 block from the
temporal base or already reconstructed top/left residual edges, including a DC
mean. Tile boundaries provide no external spatial edge. Fully hidden blocks
commit 128 immediately so later neighboring predictions see the canonical value.

Both mode0 control and spatial policies use their own accepted causal histories,
the same ROI 8/background 16 quantizers and no old global RDO. This control is not
the v37 searched/RDO codec. The host chooses modes using actual Q14 quantization,
inverse source-SSE and an exact isolated-CP02 byte proxy; the full mode map and
actual chosen plane entropy are then serialized and charged.

| 12-frame window | Control bytes / MSE | Spatial bytes / MSE | Byte change | Spatial mode bytes |
| --- | ---: | ---: | ---: | ---: |
| Primary | 134,817 / 14.354870 | 155,885 / 13.890415 | +15.6271% | 19,827 |
| Complex | 309,308 / 26.365446 | 331,421 / 25.651026 | +7.1492% | 23,457 |

Source MSE improves 3.24% / 2.71%, but signaling overwhelms residual savings.
The mode0 control costs only 36 mode bytes in each window. These are actual
complete-packet regressions, not successful compression improvements. Flat,
directional and low-amplitude-noise synthetics are separately retained. The
byte-rounded local proxy sometimes hides a real sub-byte DC saving; it is not
a global entropy or mode-context rate model.

All 54 packets fit the cap. Four producer and six independent tests pass. Replay
recomputes 1,053,810 candidate blocks' prediction/Q14 quantization/inverse/SSE,
exact CP02 proxy and winner decisions, plus actual mode grammar, coefficients,
causal references, HUD and quality. 22,978 nonzero modes are checked. The next
experiment codes an index among decoder-derived distinct clipped predictors:
at a tile's top-left all predictors are identical and need no choice bits.
This hypothesis is not included in the v38 results.

## Fresh retained-native prefix comparison

[Comparison evidence](prototype-v38-comparison.json) freshly redecodes 48 retained
original-input native AUs across four matching 12-frame prefixes. There is no
fresh native encode. PTS/DTS, key 0, immediate outputs, exact HUD, output hashes,
original-source metrics, payload lengths and once-only extradata are checked.
Every budget charges the same 80 binding bytes per frame and actual HX33.
Native binding is modeled accounting, not native CS38/SP38 wire support.

| 12-frame window / codec | Complete budget bytes | Active MSE |
| --- | ---: | ---: |
| Primary CS38 | 114,889 | 14.362737 |
| Primary HEVC q32 | 70,401 | 11.601327 |
| Primary AV1 q48 | 64,376 | 12.308815 |
| Complex CS38 | 271,410 | 26.378421 |
| Complex HEVC q28 | 190,072 | 20.656737 |
| Complex AV1 q38 | 186,911 | 18.927560 |

All four native points remain smaller at lower MSE than binary or spatial custom
points. This is not matched-quality BD-rate, perceptual equivalence, optimal
standards encoding or equal hardware resources. Same-input exactness prevents
the new binary gain being attributed to source preprocessing or quality loss.

## Next work during the six-hour run

1. Test distinct-predictor mode ranks with actual syntax and unchanged SP38
   reconstruction before changing selection. Then add signaling-aware tile/frame
   decisions and measure whether spatial prediction can pay for its metadata.
2. Extend AB38 beyond short prefixes, including held-out windows. Quantify
   operation/tail distributions and investigate context/parameter choices without
   overfitting these two windows or hiding transmitted state.
3. Integrate arithmetic emission directly with the coefficient sender and build
   a direct independent receiver instead of the re-encoding proof adapter. Keep
   exactness, malformed syntax and state publication tests.
4. Target broader bounded temporal/spatial prediction for larger rate gains;
   preserve actual mode/vector/header costs and original-source temporal quality.
5. Qualify complete host service and model/measure FPGA memory/compute plus
   actual ESP32 transport separately before claiming physical 30 fps.

[Prediction inventory](v38-prediction-inventory.md) records previously tried
methods and negative evidence so the next experiments do not repeat old claims.

## Reproduction and checkpoint scope

```sh
python experiments/verify_prototype_v38.py
```

The inventory freezes v37 dependencies except mutable indexes, new source pins,
actual packets/candidate data, test logs, independent replay and fresh native
prefix comparison. There are 23 focused passing tests, 180 archived custom frame
cases (102 integrated + 24 binary + 54 spatial), and 48 native AU redecodes. These are
reused source contents and separate policies, not 180 independently captured
images. Recorded timings are not remeasured speed guarantees during replay.
The six-hour goal remains active after this checkpoint.
