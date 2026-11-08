# Producer lookup-address cache

The completed CLOSURE route exposes `coefficients/tile_cursor_reg[8]` →
`coefficients/admission/lookup_scale_reg[1]/D`: WNS −3.438 ns, data delay
13.429 ns, with 14 logic levels. The
[pinned report](../../experiments/python-gamebub-v106/native/20261108T013032873883Z/reports/route-setup-paths.rpt)
has SHA-256 `4da106d91e7cb99b7ba84d83252621f3489fb7e1fd9663d2fd20bb234b4953bd`.
The candidate separates coordinate evaluation from the existing registered
scale-table read by maintaining a private quantization-cell cache alongside
the producer's existing plane/tile registers.

Both actual producer modules retain their public headers, original state
transitions, guards, error priority, counters and plane/tile assignments.
Eleven exact edits per module declare the cache, mirror every original plane
or tile change, use it for lookup/mapped metadata, and assert the invariant
`producer_cell_cache == quant_cell(plane,tile_cursor)`. There is no added
public cycle or speculative memory access. The table still has its original
write/read/collision behavior; this change does not claim BRAM inference.

The inductive argument is explicit: reset/abort establishes `cache=f(0,0)`;
every one of the four plane assignments and five tile assignments has a
matching cache update for the new pair; other branches hold all three.
Entropy admission can reset the plane while retaining the tile, and advancing
a plane can retain the old tile until the next preparation edge. Both cases
are mirrored, including binary 2-bit plane and 13-bit tile wrap.

[Model results](../../experiments/python-gamebub-v106/producer-cache/results.json)
reconstruct all 704 original LUT constants and compare all 32,768 binary
plane/tile values to an independent quotient/remainder formula. All 262,144
model transitions across eight update roles pass. Exact recipes recover both
production files, preserve original assignment streams and public headers,
and leave the already tested helper bytes unchanged.

This is a **Python transition model and exact source/induction argument**.
It is not a standalone simulation of the complete controller or a claim that
all prepared states are reachable. The new paired pipeline lanes must pass
the live RTL invariant and actual public cycle/event/canonical goldens before
selection. Native timing, four-state/formal equivalence, board 30 fps and
complete validated decoding below 10 ms remain separate qualifications.

Reproduce the frozen model and recipes without changing production files:

```sh
python3 scripts/cu66-v106/producer_cache.py --verify
```
