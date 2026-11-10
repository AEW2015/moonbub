# V128 padding-cache routed observations

The [frozen query method](padding-inspection.md) was run on the existing V127
and V128 routed checkpoints. Both read-only queries completed successfully and
their input checkpoint hashes were unchanged. Neither query is a new implementation
or a timing qualification by itself.

| Measured family | V127 | V128 |
| --- | ---: | ---: |
| Named admission header Q to all timed endpoints | −1.165 ns | −0.630 ns |
| Any timed startpoint to new padding-cache D | Not present | +2.369 ns |
| New padding-cache Q to all timed endpoints | Not present | +0.494 ns |

Family minima can refer to different physical endpoints. In V128, the cache
clock-enable query and the cache/header Q to tile-R queries returned **no timed
paths** despite nonempty pin selections. This is a measurement gap; it does not
prove that a path was eliminated. The new cache has two direct Q loads and 402
reported transitive timing endpoints; the printed endpoint list is capped at 256.
Physical header bit counts differ from the 1,024 declared bits and may reflect
pruning, replication or renaming; they do not prove a source-width reduction.

The [baseline receipt](../../experiments/python-gamebub-v128/padding-inspection/baseline-v127-20261110T215424460066Z/receipt.json),
[candidate receipt](../../experiments/python-gamebub-v128/padding-inspection/candidate-20261110T222722130673Z/receipt.json)
and [pre-query freeze](../../experiments/python-gamebub-v128/orchestration/padding-query-tooling-freeze.json)
bind the query scripts and artifacts. The method document is the retained
pre-query snapshot; this page records the later observations.
