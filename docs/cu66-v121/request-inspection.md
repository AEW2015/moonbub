# V121 routed request inspection

`scripts/cu66-v121/inspect_request.tcl` is a supplemental read-only analysis
of an already routed external `route.dcp`. It is prepared for the parent
dispatcher to execute after the fresh RTL implementation. Preparing this script
does not run Vivado, create timing evidence or change the fixed V120 recipe.

The script accepts exactly two Tcl arguments: the checkpoint and a fresh
output directory. For the existing pinned Vivado container setup, its command
tail is:

```text
/opt/amd-tools/2026.1/Vivado/bin/vivado -mode batch -nojournal -nolog -notrace \
  -source /diagnostic/inspect_request.tcl \
  -tclargs /input/route.dcp /output
```

Mount the chosen external checkpoint and this Tcl read-only, and mount a
separate output directory writable. Use the parent's resource gate, timeout,
license/tool/image setup and two-CPU/eight-GiB/no-extra-swap cap. Preserve raw
stdout, command, source script hash, input native receipt/hash, checkpoint hash
before/after and output hashes in the independent inspection receipt. The
expected image is the retained Vivado content ID
`sha256:dd51b5dd44148c23bb0059b929697243797022172d5efb01ffdd8b8dd7a89742`.
This execution is an inspection job and requires its own available heavy slot.

It rejects a missing checkpoint, an output directory already containing its
`status.txt`, any part other than `xc7a100tcsg324-1`, or anything other than one
existing `component_clk` with an 8 ns period and 0/4 ns waveform. It reports
the existing clocks and route status. It does not create clocks, apply
constraints, change settings, synthesize, optimize, place, route, write a
checkpoint or generate a bitstream.

The retained V120 `report.tcl` supplies the hierarchical `NAME`/`REF_NAME`
cell-selection and `REF_PIN_NAME == Q` conventions. Inspection inventories
mapped refill `prepared_req_addr`, `issued` and `offset` flip-flops, including
locations and Q-pin counts. It targets the packet `admission/memory_reg*`
RAMB cells, enumerating both `ENARDEN` and `ENBWREN`, plus address pins. Other
request endpoints cover cursor D/CE (including the new increment recurrence),
pending-address/last/valid and issued D/CE, and admission response-owner D/CE.
Each source family also gets its worst paths to all timed endpoints.

Each nonempty family query records up to 50 maximum-delay paths, one worst
path per endpoint, in a full-clock-expanded report and `targeted-paths.tsv`.
The table includes actual start/end pins, slack, data delay and logic levels.
`inspection.tsv` records selections and counts; `register-inventory.tsv`
records physical registers; `query-gaps.tsv` explicitly distinguishes missing
cells, missing pins and nonempty pin sets returning no timed path. Empty
selections never silently become unrestricted timing queries. Missing names
may reflect optimization, renaming or a hierarchy change and do not prove
path elimination.

Compare the cursor/issued-to-RAM-enable paths with B125's
`issued_reg[1] -> offset + issued -> replay_addr bounds -> ENBWREN` path.
Inspect the actual retained carry cells in the detailed reports. The expected
structural effect is replacing the serial address sum with a register source;
the cursor increment and admission bound/ready/enable cones remain. Offset
register disappearance is plausible because its remaining references are
assertions excluded from synthesis, but it is an observation to check.

The completion marker is
`V121_REQUEST_READONLY_INSPECTION_COMPLETE`. It indicates successful script
completion and existing part/clock validation, including explicit query gaps;
it does not mean timing passes. Only the parent fresh-RTL native receipt can
establish that trial's physical result. This inspection is neither a new
implementation trial nor a separate positive repeat, and does not qualify
the complete board, physical frame rate or decode latency.
