# V123 sparse-rank algebra model

Run `python3 scripts/cu66-v123/rank_model.py` to regenerate
`experiments/python-gamebub-v123/python-model/rank-model.json`.

The model compares the frozen V119 full-width predicate
`(block * 64 + zigzag(raster)) <= previous_position` against a proposed
parallel form: if any previous-position bits above bit 21 are set, the
candidate is lower; otherwise compare the 16-bit block fields, then use a
64-entry prefix-threshold mask for `rank <= previous_rank` when blocks match.
For a 16-bit block and 6-bit rank, the candidate maximum is `0x3fffff`, so
every full32 previous position with bits 31:22 set is greater. Equality is
included, preserving the original `<=` behavior.

The V119 diagonal traversal is modeled directly in Python. A separate V91c
packet-oracle sort formula generates the 64-entry raster-to-rank table. The
report pins both source files and records SHA-256 of the rank table as 64 bytes
in raster-index order.

The finite checks cover all 64 indices; eight 16-bit block boundaries with
all ranks and previous-position equality ±1; full32 high-bit cases including
all ten high-bit patterns; 100,000 deterministic random comparisons; and 6,144
phase/raw format contexts across 6,144 Boolean gating combinations. Examples
cover sparse ordering, raw raster order, DC rules, bands, value/count bounds,
previous-position equality, and epoch-before-format error priority.

This is an independent algebraic model, not a Verilog equivalence proof. It
does not exhaustively evaluate `2^32 × 2^16` combinations, compile RTL, model
clocked backpressure, measure timing/throughput, or claim saved cycles or
hardware behavior. Full-frame events and cycles are required for any later
causal validation-overlap experiment; prior V122 aggregate counters cannot be
expanded into invented per-cycle savings.
