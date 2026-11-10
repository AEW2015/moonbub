# V122 routed bounds inspection

`scripts/cu66-v122/inspect_bounds.tcl` prepares supplemental read-only queries
against an existing routed component checkpoint. It does not run Vivado during
preparation and does not change any focused-test input, RTL, constraint or
implementation recipe. The parent owns checkpoint selection and dispatch.

The Tcl takes exactly two arguments: `ROUTE_DCP OUTPUT_DIRECTORY`. Bind both
the chosen checkpoint and Tcl read-only, with a fresh writable output directory.
The command tail for the retained Vivado installation is:

```text
/opt/amd-tools/2026.1/Vivado/bin/vivado -mode batch -nojournal -nolog -notrace \
  -source /diagnostic/inspect_bounds.tcl \
  -tclargs /input/route.dcp /output
```

Use the native receipt's existing tool/image/license setup, host launch and
stop gates, and two-CPU/eight-GiB memory-plus-swap cap without extra swap. The
parent wrapper must bind the input native receipt/hash, checkpoint content hash
before and after, script hash, exact command, raw stdout and output hashes in a
separate inspection receipt. The retained Vivado image content ID is
`sha256:dd51b5dd44148c23bb0059b929697243797022172d5efb01ffdd8b8dd7a89742`.
Each inspection needs an available execution slot. No inspection is dispatched
by these files.

The script validates the checkpoint's existing part as `xc7a100tcsg324-1` and
requires exactly one existing `component_clk`, period 8 ns and waveform 0/4 ns.
It reports existing clocks and route status. It never creates a clock, applies
constraints, changes settings, synthesizes, optimizes, places, routes, writes a
checkpoint or generates a bitstream. The checkpoint hash binding belongs to
the parent wrapper; Tcl part/clock checks alone do not identify its source.

The eight admission source families are selected through hierarchical
`NAME` patterns and mapped `FD*` primitives, retaining replica names:

| Family | Source RTL declaration width |
| --- | ---: |
| `cursor` | 32 |
| `word_acc` | 24 |
| `bounds_cursor_base` | 64 |
| `bounds_word_base` | 64 |
| `bounds_length_total` | 64 |
| `bounds_number_plus12` | 32 |
| `prepared_number_outside` | 1 |
| `prepared_length_invalid` | 1 |

Every source family is queried to all timed endpoints, and separately to the
admission state `FDRE` D/CE pins, word-accumulator D/CE pins, and each of the six
new payload/predicate D/CE families. This explicit cross product includes both
successive pipeline stages and shared state/enable cones. Each nonempty query
returns at most 50 maximum-delay paths, one worst path per endpoint, with a
full-clock-expanded report. There are at most 72 admission reports. Actual
start/end pins, slack, data delay and logic levels are also tabulated.

The separate unchanged-request group inventories V121 refill
`prepared_req_addr`, `issued` and `offset`, each declared uint32. It queries
each family to all endpoints and specifically to admission packet-memory
`RAMB*` `ENARDEN`/`ENBWREN` pins. The packet-memory selection is the retained
`*admission/memory_reg*` family; lookup RAMs are excluded. These at most six
additional reports allow the parent to compare V121's local request-path
closure while assessing the new admission result. Missing optimized `offset`
registers remain an explicit observation gap.

`register-inventory.tsv` lists every matched mapped cell's exact hierarchical
name, primitive, location, Q-pin count, declaration width and parsed RTL bit
index. `register-width-summary.tsv` distinguishes physical cell count from
unique named bit indices, reports the greatest observed index plus one,
unparsed names, the observed index list and unmatched declared indices.
Replicas can increase cell count without increasing unique named bits.
Missing upper bits can reflect constant trimming, merging or naming changes.
A full64 source declaration does not imply that 64 physical flip-flops remain;
neither fewer flip-flops nor indexed names prove arithmetic semantics.

`inspection.tsv` records selections/counts, `targeted-paths.tsv` records timing
rows, and `query-gaps.tsv` distinguishes missing cells, missing source or
endpoint pins, unparsed register indices, declaration/physical count
differences and nonempty selections returning no timed path. Empty selections
never become unrestricted timing queries. No missing family or zero-path pair
is reported as eliminated logic or successful timing closure.

For interpretation, compare the original admission cursor-to-state cone with
the cursor-to-first-stage, stage-to-stage, final-sum-to-predicate and
predicate-to-state reports. Check the actual carry and LUT cells and retained
register bits in the mapped reports. Read all-endpoint reports to detect a
path moving to another destination. The unchanged request-to-packet-RAM-enable
family remains a separate local comparison. These targeted reports do not
replace the complete routed setup/hold summary or its global worst paths.

The exact completion marker is
`V122_BOUNDS_READONLY_INSPECTION_COMPLETE`. It denotes script completion with
existing part/clock validation and explicit gaps; it does not denote a timing
PASS. A parent wrapper should require that marker as a literal status line,
normal tool termination and unchanged checkpoint hash. This is observation of
one existing implementation, not a new physical trial, positive repeat or
qualification of the board, frame rate, decode latency or hardware behavior.
