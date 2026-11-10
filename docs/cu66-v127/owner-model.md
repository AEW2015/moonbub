# V127 owner-selection algebra model

The model compares the frozen V126 owner expression with the proposed three-lane Boolean factorization. The old expression selects one of two full-width tile-bank comparisons using `dbg_tile_mode` and `dbg_emit_bank`, or compares the selected non-tile scalar epoch/block against the parent's current epoch and expected block. The proposed expression computes bank 0, bank 1, and scalar comparisons independently, then selects one bit.

The script binds to the exact V126 producer and scratch source hashes at runtime and checks their relevant equations before running. It exhaustively enumerates the lane-result, tile-mode, emit-bank, raw-mode, ready, and valid Boolean context; tests full 32-bit epoch and 16-bit block boundary values; and runs 50,000 deterministic full-width vectors, including duplicates, opposite-bank mismatches, and coherent foreign-parent cases. Readiness, child validity, and raw-mode are context flags; none is treated as proof of ownership.

Run from the repository root:

```sh
python3 scripts/cu66-v127/owner_model.py
```

The output is `experiments/python-gamebub-v127/python-model/owner-model.json`. This is finite Python algebra and boundary sampling only. It is not sequential RTL execution, formal equivalence, synthesis, routed timing, throughput, FPS, or hardware qualification. The random and boundary samples do not exhaust the full tag space. No production source or proof input is changed.
