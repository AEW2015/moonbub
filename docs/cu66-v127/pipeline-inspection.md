# V127 matched mode/owner checkpoint queries

The V127 query retains all 129 previous families and adds scratch tile-overlap
mode, scratch raw mode, scalar active epoch and scalar output block sources.
All timing observations use actual sequential Q pins and explicit destination
groups, with a separate all-endpoint query. A failed cell/pin match never
broadens to all sources or all sinks. Empty, optimized or renamed objects and
width/replication differences remain explicit gaps.

The frozen query additionally observes named bank/scalar/selected owner nets.
For at most 32 named nets per group, `all_fanin -flat -startpoints_only` records
the complete returned timing startpoint list. AMD documents a sink net as a
valid positional object in [UG835 2026.1](https://docs.amd.com/r/en-US/ug835-vivado-tcl-commands/all_fanin).
Missing names, empty results, tool errors or larger groups retain a gap instead
of claiming physical lane isolation. This structural observation does not
replace functional proof or global timing signoff.

## Fresh V126 observation

The [baseline receipt](../../experiments/python-gamebub-v127/pipeline-inspection/baseline-v126-20261110T175334641526Z/receipt.json)
is `PASS_READONLY_OBSERVATION`, SHA-256
`fe403727e1a339f004cc59dba196b4864c26c4bc4c9a140d08fb8fa77790fa3f`.
It retains 154 artifacts and binds the existing V126 routed checkpoint, actual
native receipt, tool image and both query scripts. The checkpoint and tools
are read-only mounts; the sole existing clock is checked as `component_clk`
with period 8 ns and waveform 0/4 ns. No implementation command, new
constraint or checkpoint write is executed.

| Baseline family | Worst slack (ns) | Worst destination |
| --- | ---: | --- |
| Tile-overlap mode → all endpoints / scratch state | −1.867 | Scratch state D |
| Emit bank → scratch state | −1.813 | Scratch state D |
| Scalar active epoch → all endpoints | −1.751 | Scratch state D |
| Scalar output block → all endpoints | −1.380 | Scratch state D |
| Scratch raw mode → all endpoints | −1.457 | Scratch state D |
| Producer cursor → original cell cache | +0.246 | Cell cache D |

These reproduce the terminal V126 global failure and its local producer gain.
The later candidate must use the exact same frozen query and report both
improvements and regressions. A positive subset, a missing net name or a
successful read-only invocation does not establish a new implementation,
fresh positive repeat, qualified 125 MHz clock, board image, hardware FPS
or hardware decoding latency.

## Completed V127 observation

The [candidate receipt](../../experiments/python-gamebub-v127/pipeline-inspection/candidate-20261110T193258217290Z/receipt.json)
is `PASS_READONLY_OBSERVATION`, SHA-256
`589aada3a4181e1feeb52cd72a76785434f71d16571950eafdc29b49050cfe4a`.
It also retains 154 artifacts and verifies the existing routed checkpoint
unchanged. The [145-family comparison](../../experiments/python-gamebub-v127/pipeline-observations.json)
passes integrity checks. The independent [candidate review](../../experiments/python-gamebub-v127/audit/candidate-query-review.json)
passes all 12 checks, including raw TSV minima, artifact hashes and receipt/tool
bindings. This is a query result, not a new implementation or timing pass.

Tile-mode → all endpoints improves from −1.867 to +0.451 ns, while ingress
RAW mode → all endpoints regresses from −1.100 to −1.193 ns and becomes the
global worst. Scratch RAW mode is a different origin, improving to +0.127 ns.
The [timing report](timing-results.md) retains residual and adverse families,
including cursor/cache, prepared ROM, hidden-predicate and coordinate paths.

The bank-owner pattern matches 78 baseline and 110 candidate nets, exceeding
the 32-net bound. Those fan-in queries are not executed. Candidate scalar-owner
has one named intermediate whose raw fan-in lists 16 output-block and 16
expected-block FF startpoints. It does not expose the full epoch/block lane.
Candidate selected child-owner has no matched name. The raw `inspection.tsv`
retains OWNER_LANE_FANIN rows; the comparison's filtered owner-net list omits
that row kind. Source widths are not narrowed and complete physical lane
isolation is not claimed. Baseline/candidate gap counts are 131/163, including
repeated per-net cap rows; these are recorded omissions, not extra path failures.

The native route remains a global 125 MHz failure at −1.193 ns WNS. There was
one fresh initial implementation, no unchanged-source negative reroute, and
no positive-repeat qualification.
