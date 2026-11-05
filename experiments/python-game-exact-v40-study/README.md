# V40 exact-output eligibility and actual byte guard: safe, no pilot gain

This pilot strengthens spatial mode qualification from scalar error comparisons
to **exact equality of every reconstructed 8×8 YUV block**. It then constructs
both actual RP39 packets and accepts the candidate only when its complete packet
is strictly smaller. Ties keep control. The design preserves complete canonical
references and future predictions, not just current RGB565 or equal source MSE.

The guard rejects every candidate in the initial 27-frame pilot. This is a useful
negative result: the exactness and guard mechanisms work, but this mode-selection
proxy provides **zero compression gain** on these inputs.

| Input | Control bytes | Candidate bytes | Selected bytes | Candidate frames accepted |
| --- | ---: | ---: | ---: | ---: |
| Primary, 12 frames | 134,817 | 138,638 | 134,817 | 0/12 |
| Complex, 12 frames | 309,308 | 313,141 | 309,308 | 0/12 |
| Flat | 3,095 | 5,189 | 3,095 | 0/1 |
| Directional tiles | 4,930 | 5,243 | 4,930 | 0/1 |
| Low-amplitude noise | 5,136 | 5,156 | 5,136 | 0/1 |

All actual candidates and controls fit 49,152 bytes. There are 34,695 eligible
nonzero-mode alternatives, and the candidate packets choose 16,143 nonzero modes.
Thus this is not an empty mode search: exact alternatives exist, but their
combined mode/coefficient entropy is worse. The guard prevents the flat fixture's
known proxy regression from reaching the selected stream.

## Exact block condition and causal invariant

Every candidate uses the frozen SP38 four clipped prediction arrays, Q14
quantization/inverse, ROI 8/background 16, immediate hidden-block 128 commit and
RP39 mode grammar. At each visible block the encoder computes all four actual
reconstructions on the current causal reference and already-decoded neighbors.
An alternative is eligible only if:

1. It is the stable first representative of its distinct clipped predictor.
2. All 64 reconstructed samples equal the current mode0 reconstruction exactly.

Mode0 is always eligible. Among eligible candidates, the encoder minimizes the
frozen fine coefficient-bit plus raw rank-decision proxy. Scalar source SSE is
retained as evidence, but it does not establish eligibility or relax equality.
There is no lambda quality trade because all eligible outputs are identical.

Each chosen block therefore supplies exactly the same neighbor samples as mode0
to the next tile position. Hidden blocks also commit exactly 128 immediately.
By induction, all current planes match mode0, and the committed whole reference
supplies exactly the same future temporal base. The entire candidate frame must
match the separately encoded control before the packet byte guard executes.
This avoids the equal-error-but-different-reference failure of earlier local
source-SSE guards.

Actual serialized control and candidate packets are decoded on independent forks
of the current selected receiver state. The trial decodes do not advance the
selected history. Only the chosen packet is received by the persistent selected
receiver, and all resulting planes/HUD must match both trial decodes and model
outputs. Every control packet reproduces the prior RP39 mode0 golden byte for
byte, and selected quality/reference/display hashes match those controls.

## Real byte choice and archived losing evidence

The candidate still uses an approximate local rate model, not actual marginal
full-plane entropy. This experiment does not hide that model behind a forced
win. It constructs actual SP38/RP39 proof packets for control and candidate,
retains every losing packet, and applies:

```text
candidate if candidate_complete_bytes < control_complete_bytes
             and candidate_complete_bytes <= 49152
else control
```

Complete byte counts include actual mode/coefficient components, quant map,
HUD, frame headers, rank termination/padding and checksums. No new decoder wire
profile is introduced. The selected branch keeps old control on all 27 actual
frames; the strictly-smaller branch is separately covered by the pure guard unit
test but has no accepted candidate packet witness in this pilot.

All 54 actual trial packets, their SP38 intermediates, rank trial payloads and
mode arrays are retained. The candidate also archives uint8 eligibility masks
and int64 `[blocks,4,6]` cost tensors:

```text
sourceYUVSSE, fineCoefficientBits, rawRankDecisions,
canonicalFirst, exactMode0Pixels, eligible
```

Hidden entries are zero under the fixed profile. Eligibility is the conjunction
of the last two conditions; all four candidate outputs/costs are paid. Control
oracle costs are retained separately. There is no residual RDO/pruning in either
variant, and no quality comparison to the different CS37 controller is inferred.

## Qualification and limitations

Four producer tests cover an equal-SSE/different-pixel counterexample, duplicate
predictor exclusion, strict byte ties/caps and invalid guard inputs, directional
flat exactness, immediate hidden commit and source ownership. Independent replay
imports no new encoder, recomputes all candidate predictions/transforms/proxies,
checks full-block eligibility and exact argmin, then checks all actual packet
decodes, forks, references, source/HUD metrics, guard decisions and old goldens.
Final independent replay passes 27 selected/reference frames, 27 control goldens,
1,686,096 candidate block recomputations and 162 actual rank trials. Three
independent tests pass; all 1,306 source pins match. Zero actual candidates pass
the complete-byte guard, as independently confirmed from serialized lengths.

Pair encoder clocks average 395.61 / 427.40 ms on the two gameplay prefixes. They
pay both complete proof paths, all candidate evaluations, rank trials and model
consistency checks. Fixture/HUD loading, archive/hash/metric work, independent
receive trials, network and display are outside the clock. These are single
samples for a redundant research proof, not an optimized sender or 30 fps result.

The 27 inputs are reused short gameplay prefixes and synthetics. There is no
compression improvement to deploy from this pilot, no improved control quality,
new HEVC/AV1 result, held-out corpus, native endpoint or FPGA timing proof. The
next useful test must change whole-plane/tile rate decisions or entropy context
modeling while keeping this exact reconstruction and real-byte guard as a safety
oracle; merely admitting more exact local alternatives is insufficient here.

```sh
cd experiments/python-game-exact-v40-study
python -m unittest -v test_model
python -m unittest -v test_verify
python verify.py
```
