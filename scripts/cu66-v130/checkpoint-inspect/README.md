# Read-only targeted checkpoint inspection

This optional observation asks Vivado to open the already-routed V129 and
V130 component checkpoints read-only and query paths from physical
`base_kill_valid_reg*` FD Q pins to physical admission `memory_reg*` RAMB
ENBWREN pins. It does not run synthesis, placement, routing, modify timing
constraints, write a checkpoint, or access hardware. The original clock and
checkpoint bytes are checked. V130 remains exploratory and its invalid-data
consumer contract remains unknown.

The current source-bound preflight is
`experiments/python-gamebub-v130/spec-read/checkpoint-inspect/prepared/20261111T031711951719Z/preflight.json`.
The two earlier prepared cards were superseded as the comparison script was
hardened and intentionally fail the script-hash gate. After independent review,
the command to inspect both designs sequentially is:

```
python3 scripts/cu66-v130/checkpoint-inspect/checkpoint_inspect.py run \
  --preflight experiments/python-gamebub-v130/spec-read/checkpoint-inspect/prepared/20261111T031711951719Z/preflight.json \
  --license-file /path/to/license.lic
python3 scripts/cu66-v130/checkpoint-inspect/checkpoint_inspect.py compare
```

Each checkpoint and source provenance, existing post-route audit and fixed
recipe is rechecked before execution. Each container uses at most two CPUs,
8 GiB RAM including swap, and a 900-second watchdog, with the agreed RAM/PSI
launch and stop thresholds. The mounted Vivado installation is separate from
the pinned container image. Each inspection produces a source/destination
inventory, an exhaustive Cartesian pair query, and explicit `PATH`,
`NO_TIMED_PATH` or `QUERY_ERROR` records. Empty or zero-comparable selections
are `QUERY_INCOMPLETE`. The comparison computes deltas only for exact matching
physical pin names with paths in both designs. Lists of source and destination
names present in only one checkpoint are retained. A renamed, unmatched or
untimed endpoint is never treated as timing zero, improvement, or closure.

A matched physical pin name does not prove logical equivalence or that the
path is representative of whole-design timing. Reading a checkpoint and
obtaining a path is not hardware, full-parent or timing signoff. A preflight alone does not show that an inspection has executed.

The comparator does not itself enforce matching preflight identifiers between
its two selected inspection receipts. Before interpreting a comparison,
independently verify that both receipts have the same `preflight` and
`preflight_sha256`, and that this hash matches the reviewed preflight. Treat a
mismatch as invalid evidence, even if the comparator emitted a result.
