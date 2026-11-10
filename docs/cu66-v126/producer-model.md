# V126 producer successor model

The standalone Python model checks the proposed producer lookup schedule using the frozen V124 producer source and V125 next timing proposal. It extracts the entire `quant_cell` function’s 64 banks × 11 LUT truth words, independently decodes the 13-bit tile address, and models the successor-address/cell ownership across the existing MAP request, MAP wait, dispatch, and plane transitions.

Run it from the repository root:

```sh
python3 scripts/cu66-v126/producer_model.py
```

The run writes `experiments/python-gamebub-v126/python-model/producer-model.json`. The output binds the source, proposal, plan, extracted-table digest, and script SHA-256. It checks all 32,768 plane/tile pairs (four planes and 8,192 tile values), including successor and t+2 arithmetic and uint13 wrap. Its transition examples cover accepted and blocked starts, MAP_WAIT skip and mode2, dispatch holds and consumption, terminal and empty-plane behavior, next-plane cache recomputation, reset/abort invalidation, stale ownership rejection, and error priority.

This is a finite Python algebra/transition model, not RTL execution, formal equivalence, synthesis, timing, resource, FPS, image-quality, or hardware qualification. The truth table is extracted from the pinned source, rather than an external independent image oracle. Wrap contexts are checked algebraically; the modeled MAP request rejects out-of-range tiles. The model is bound to the frozen V124/V125 inputs and does not establish that every real controller transaction reaches the proposed existing-edge schedule. Full functional regressions and candidate-source qualification remain required.
