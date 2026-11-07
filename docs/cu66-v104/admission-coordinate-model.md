# V104 admission-coordinate recurrence model

**PASS: Python coordinate arithmetic only.** This model prepares an isolated
future admission recurrence experiment; it changes no admission RTL, measured
V104 source, source width, parser state or native timing contract.

The published admission `cell_index` accepts a full unsigned 32-bit tile. The
model exhausts a **conditional bounded domain**: planes 0–2, valid Y/chroma tiles
plus their end sentinels, and every delta 0–16 that does not pass plane end.
It compares a finite-width cached-coordinate update with the original full-width
integer quotient/remainder formula. This is not a proof that arbitrary real
admission histories stay in that bounded domain.

| Modeled evidence | Count |
| --- | ---: |
| One-step tile/delta transitions | 137,343 |
| Holds | 8,103 |
| Y row crossings | 8,040 |
| End-sentinel results | 51 |
| Chained trajectory steps | 10,085 |
| Proposed owner-event sequences | 84 |
| Owner-rule assertions | 516 |

For Y, cache column `tile%90`, row parity and `45*floor(tile/180)`. Adding a
bounded delta crosses at most one 90-column row: wrap column if needed, toggle
parity, and increment pair base by 45 only when the old row was odd. Cell is
pair base plus half-column. Chroma cell is tile. Observed maxima are column sum
105, column 89, pair base 1350, cell 1350
and tile 5400; all declared 7/1/11/13-bit arithmetic bounds hold.

The tile5400 Y and tile1350 chroma sentinels have cell1350. They are **not**
residual cells and must never mark `active_cell`. The model checks sentinel
holds/mark rejection, all group-size deltas, every row/plane end, hidden-region
crossings and multi-step held/variable-group trajectories. The sentinel-to-next-
plane transition resets geometry; it is distinct from advancing past the end.

The owner model deliberately retains stale tile/plane coordinates on reset,
start, abort or failed entry, but invalidates their ownership. A qualified new
header establishes plane0/tile0 under a fresh opaque owner; queued old-owner
marks remain rejected. These are proposed safety rules, **not actual admission
FSM execution or a proof of its reachability**. Future RTL must establish the
entry invariant, cover every real assignment/group jump and error path, enforce
write drain before active-cell scan, and preserve epoch/reset/abort priorities.
Current 32-bit admission semantics cannot be narrowed merely from this model.

```sh
python3 scripts/cu66-v104/admission_coordinates.py
```

The receipt stores source/script/input/result hashes and a finite20-second
watchdog. It writes no large expanded trace. No RTL simulation, formal proof,
placed/routed improvement, full decoder integration, hardware30fps or complete
validated under10ms decoding follows from this conditional arithmetic result.
