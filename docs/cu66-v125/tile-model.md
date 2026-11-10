# V125 tile-predicate successor model

This standard-library Python model checks the exact full-width equations in the selected V122 admission source against the proposed registered-predicate successor contract. It is an algebraic two-state model, not RTL, timing analysis, or performance qualification.

## Frozen equation source

The model binds `fpga/experiments/cu66-v122-bounds/cs88_admission_v91i2a.sv` at SHA-256 `54dc87ded7abf37a9dc6757a4dabe62d6530f8127989d0fef2a4fc0f723376cf`. It independently expresses:

- `hidden(plane,tile)` for all four two-bit plane values. Plane 0 has nine inclusive ranges; planes 1, 2, and 3 use the inclusive range 1046–1064.
- `tile_count(plane)`: 5400 for plane 0 and 1350 for planes 1, 2, and 3.
- Terminal checks as exact equality. The model includes values above each count/end to distinguish `==` from `>=`.
- `GROUP_BEGIN` end as modulo-2^32 `tile+16`, then the literal `< tile_count ? plus16 : tile_count` selection.
- Modulo-2^32 tile increment and two-bit plane increment, including wrap boundaries.

## Registered successor contract modeled

The three scalar payloads are `prepared_tile_hidden`, `prepared_tile_terminal`, and `prepared_group_terminal`. Their verification-only owner keys are `(epoch,plane,tile)` and `(epoch,plane,tile,group_end)`, including plane coherence even though group equality itself is plane-independent. `epoch` is only an abstract fresh-parse identity token; it is not a claim that RTL has or increments an epoch register. The model does not add production owner state.

- Successful `HEADER_CHECK`, `KEY_TILE` increments/terminal transitions, and `GROUP_NEXT` plane clears prepare the hidden and tile-terminal predicates for the new plane/tile. Key-only branches invalidate group-terminal ownership.
- `GROUP_BEGIN` writes the clamped group end and invalidates group-terminal ownership.
- A completed `MODE_BIT` tag edge snapshots all three predicates for the current `(plane,tile,group_end)`. The hidden-only shortcut instead advances to `(plane,group_end,group_end)` before snapshotting.
- A mixed-bit tile increment and a `GROUP_TILE` increment snapshot all three predicates for successor `(plane,tile+1,group_end)`.
- `GROUP_TILE` checks group-terminal equality before mixed-count error 8 or hidden/tag stepping. `KEY_TILE` and `GROUP_NEXT` consume exact tile-terminal equality.
- Reset, start, and abort invalidate only verification owner keys; predicate payload remains unchanged. Hold cycles preserve both keys and payload. Wrong-plane group-owner keys are explicitly rejected.

These rules follow the independent V125 design contract supplied for the prepared predicate experiment. They do not claim reachability for the algebra-only high-bit fixtures.

## Finite coverage and run

The recorded run checks 58,904 key tuples across all four planes, including each hidden-range edge and adjacent value, terminal edges, high-bit values, deterministic random 32-bit tiles, and tile+1/tile+16 wrap cases. It applies each modeled writer/hold/cancel successor across those contexts. The output records per-transition counts, script/input hashes, and explicit model scope in `experiments/python-gamebub-v125/python-model/tile-model.json`.

Recompute with:

```sh
python3 scripts/cu66-v125/tile_model.py
```

This finite sample does not enumerate all 2^32 tile values or all possible parser histories. It does not establish four-state/X behavior, RTL equivalence, synthesis, placement, timing, latency, FPS, firmware behavior, or hardware qualification.
