# Fixed-reference hierarchical 32 → 16 motion probe

Five of 24 tested frames admit a smaller 16-pixel motion packet with no higher
current-source RGB error than the **actual accepted v32 `band_control` packet**.
Guarded selection saves **1,811 complete bytes (0.356%)**, with 0.108% lower
aggregate active RGB SSE. The added host work costs about **205 ms/frame** on
this run. This is a small offline compression opportunity with substantial
additional Python work.

The primary baseline is each retained accepted v32 packet, decoded against its
actual accepted previous reference. Its RGB metric is recomputed from source
pixels and checked against the retained evidence. A separately paid adaptive32
half-motion search and strict-band32 encode supplies the parent motion field.
That parent candidate is also archived and compared, but its admission result
does not establish a win over the full controller. Ten raw 16-pixel trials
qualify against accepted control (five distinct frames), versus sixteen trials
against the parent32 strict-band candidate (eight frames).

| Complete fixed-reference aggregate | Bytes | Active RGB SSE |
| --- | ---: | ---: |
| Actual accepted v32 control | 508,720 | 426,975,565 |
| All raw strict-band16 trials | 508,776 | 426,825,737 |
| Actual-control guarded selection | 506,909 | 426,515,821 |

The raw strict-band16 aggregate adds 56 bytes versus control, and individual raw
frames can regress quality. Every selected trial independently satisfies the
complete 49,152-byte cap, strictly fewer complete bytes, and source RGB SSE no
higher than that frame's actual accepted control baseline. Every trial,
including rejected trials and the full runtime16 incumbent, executes and is
retained. The selected frames are scene `mass-effect-7200`, IDs 5, 7, 8, 10, 11.

`model.seed16(parent_vectors, width, height)` repeats each bounded 32-pixel vector
over its child blocks, trimming the right/bottom partial parent blocks. At
720×480 it maps a 23×15 parent grid to 45×30 child blocks. `refine` scores zero
first at stride two using the exact frozen integer bilinear sampler, with
luma/chroma weights 1/2. Blocks whose weighted zero-vector sampled MAE is at
most two retain zero. Each active child tries all 25 offsets in
`{-2,-1,0,1,2}²` around its parent seed, clipped to ±18 half-luma units. Equal
costs retain the earlier candidate, so zero wins ties. No neighboring-parent
menu, search heuristic tuning or trial skipping is hidden in this probe.

`model.analyze16(module, adaptive, parent, reference)` builds an owned ordinary
GM27 Prepared object with `block_size=16`, a tap-aware full prediction, all
three actual forward transforms and actual vector-map serialization. Frozen
runtime28 incumbent and band30 strict encoders both run on it. Unchanged GM27
decoders reconstruct every trial exactly, and all 72 new baseline/trial CP27
packets pass the existing parser and complete cap. There is no decoder or wire
change.

Relative to the paid parent32 strict-band candidate, raw strict-band16 motion
bytes rise from 4,126 to 13,945, while residual bytes fall from 226,828 to
218,608. Thus the additional motion map outweighs that residual saving by
1,599 bytes before guarding. Relative to actual accepted control, motion bytes
are 2,616 versus 13,945 and residual bytes 229,881 versus 218,608. Per-packet
motion, qmap and residual plane lengths are retained. The summary's historical
`baseline_motion_bytes`/`baseline_residual_bytes` fields refer specifically to
the paid parent32 candidate; `control_baseline` rows contain the primary
accepted-control lengths.

The measured mean paid host work is **366.30 ms/frame**, including parent32
analysis/search, actual parent strict-band encode, child refinement/prediction/
transform/MV packing, both child encodes, RGB metrics and CP27 binding. The
additional child portion is **204.99 ms/frame**. Parent search scores 34,839,264
sample points and child refinement 19,466,400. Parent strict-band decoder
reference gathers total 15,220,480 versus 14,734,336 for all raw strict-band16
outputs; tap-aware encoder prediction counts agree with each corresponding
child decoder count. Counts include actual partial-edge block sizes. One
timing sample is retained per source frame; this is not a timing comparison
with a fully rerun v32 controller.

All 24 source inputs are the first twelve frames of each retained v32
`band_control` history, at its selected background map. Each probe reads the
actual previously accepted v32 reconstruction. Neither the parent candidate
nor a selected child changes the reference for the next frame. Same-frame
retained HUD bytes and the unchanged 60-byte CP27 binding are included in
complete packet comparisons. Retained-control decoding/metric extraction is
separately timed offline evidence and excluded from paid new-source work.
Fixture acquisition/conversion, preencoded HUD generation, debug decoding,
archives, transport, gateway and display are also excluded. There is no causal
campaign, full-controller integration, physical 30fps or combined-gain claim.

`results.json` retains 1,022 source pins, environment/parent identity, complete
paid work, every raw trial's metric and packet lengths, accepted baseline
packets, deterministic packet/output hashes and admission decisions.
`objects/` stores actual compressed GM27 and CP27 packets. Frozen <=v32 files
and the shared-v33 study remain unchanged.

```sh
PY=/home/lori/gamebub-streaming-prototype/.venv/bin/python
$PY -m unittest discover -s experiments/python-game-split-v33-study -p test_model.py -v
$PY experiments/python-game-split-v33-study/benchmark.py
$PY experiments/python-game-split-v33-study/verify.py
```

Three meaningful tests cover all 45×30 mapping positions, partial edge blocks,
invalid parent bounds, refinement bounds and quiet-zero behavior, independent
full-predictor sampled-cost equality, and actual key/P block16 encode/decode at
34×50 partial geometry. The independent verifier checks source pins, both
actual accepted reference histories, retained control metrics, every new
actual packet and output, complete binding and admission, then reruns the full
parent/refinement/three-encode probe. `--archives-only` explicitly skips
re-encoding while retaining archive, decode, metric and admission checks.
