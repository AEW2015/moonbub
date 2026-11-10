# V125 matched admission-control preflight

Before candidate production edits, the same frozen read-only Tcl query inspected
the existing V123 and V124 routed checkpoints. Both runs returned
`PASS_READONLY_OBSERVATION` and verified unchanged checkpoint hashes, part
xc7a100tcsg324-1 and the existing 8 ns clock with 0/4 ns waveform. The
[baseline comparison](../../experiments/python-gamebub-v125/tile-baselines.json)
rehashes both query receipts and their artifacts. It contains 77 returned
timing-family comparisons plus inventories and explicit gaps.

| Worst returned setup slack, ns | V123 | V124 |
| --- | ---: | ---: |
| Tile → all timed endpoints | −0.498 | −1.170 |
| Tile → tile D/CE | −0.101 | −1.170 |
| Tile → coordinate D/CE | +0.022 | −1.057 |
| Tile → state D/CE | +0.396 | −0.300 |
| Tile → group-end D/CE | +0.478 | +0.558 |
| Tile → mode-RAM EN/WE | +0.457 | −0.010 |
| Tile → mode-RAM data/parity | +0.313 | −0.080 |
| Group-end → coordinate D/CE | −0.012 | −0.140 |
| Plane → all timed endpoints | +0.082 | +0.148 |

These are like-family observations of each independently routed composition,
not guaranteed identical physical path endpoints or a claim of semantic change
in unchanged admission RTL. RAM EN/WE selects both ports; DI* selects data and
parity pins. Exact selected pins are retained rather than assuming a write-port
mapping. Missing timed paths never broaden an empty selection to unrelated
paths or count as a positive timing result.

V124 inventory finds 33 physical tile register cells and all 32 unique tile bit
indices, two plane bits and 32 group-end bits. Physical replicas do not imply
wider logical state. The three proposed scalar predicate names are absent from
both baseline designs and recorded as gaps. The identical query already includes
their D/CE targets and Q sources for a later candidate measurement.

The original owner, RAW, rank, cursor and refill families remain in the query.
The clock, constraints, netlist properties and implementation are unchanged.
Query runs are observations, not new routes, positive repeats, board timing or
30-fps/under-10-ms qualification.

The first comparer invocation generated valid data but failed while printing
a relative output path. Its script/data and failure record are preserved under
`experiments/python-gamebub-v125/orchestration/comparer-history/`. Resolving the
output path before printing fixed that summary-only issue; no query or source
was changed. The corrected derivation and regenerated comparison are retained.
