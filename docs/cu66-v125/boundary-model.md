# V125 incremental boundary algebra model

This optional standard-library model checks whether the existing full-width
`hidden(plane, tile)` Boolean can be updated cheaply across an **owned same-plane
unit step**. It does not change the RTL, establish a timing improvement, or qualify
hardware.

For each inclusive hidden interval `[lo, hi]`, the model defines `ENTER` at
`tile == lo - 1` and `EXIT` at `tile == hi`. For 32-bit wrapped `next_tile`, it
checks:

```text
hidden(plane, next_tile) == ENTER(plane, tile)
                            || (hidden(plane, tile) && !EXIT(plane, tile))
```

It also checks the same-plane unit-step identity
`next_tile == tile_count(plane)` iff `tile == tile_count(plane) - 1`, where the
current source uses 5400 tiles for plane 0 and 1350 for planes 1, 2, and 3.

The model evaluates all four two-bit plane values, each range edge and nearby
values, high-bit values, uint32 wrap, and 25,000 deterministic random transitions
per plane. Its verification owner includes an abstract epoch, plane, and tile. It
exercises direct-function fallback cases for jumps and plane changes, and rejects
cached hidden witnesses with stale epochs or mismatched plane/tile keys.
These checks are finite samples over the 32-bit domain, not an exhaustive proof.

The source hashes for the current V125 admission module and frozen V122 bounds
parent are checked before running. The result records those hashes, the script
hash, counts, and scope. Reproduce with:

```sh
python3 scripts/cu66-v125/boundary_model.py
```

The result is in
[`experiments/python-gamebub-v125/boundary-model/results.json`](../../experiments/python-gamebub-v125/boundary-model/results.json).
The V122 source hash is
`54dc87ded7abf37a9dc6757a4dabe62d6530f8127989d0fef2a4fc0f723376cf`; the V125
source hash is `2f65ff770775404071e383890c75549ccb08ec9998993c86f1662cfed65d71eb`.

This remains an optional unimplemented candidate for a future routed comparison
if the current V125 implementation exposes a timing path involving the range
predicate. Synthesis may already refactor the original expression. Only a
source-bound routed experiment can establish whether this algebra changes timing
or resources; this model makes no FPGA, FPS, or hardware claim.
