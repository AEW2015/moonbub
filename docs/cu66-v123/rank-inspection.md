# V123 read-only routed rank inspection

`inspect_rank.py` and `inspect_rank.tcl` inspect a source-bound existing routed
checkpoint, using the retained V122 wrapper's resource gates, immutable-checkpoint
hash checks and status-file completion marker. The script validates the existing
Artix-7 part, single component clock at8ns and0/4ns waveform. It changes no
constraint or setting and never implements or writes a checkpoint/bitstream.

The six source groups are ingress RAW-mode/RAW-position and scratch previous
position/rank-threshold-mask/record-view-bank/phase. For each group, inspect all
timed endpoints plus scratch state, mask, previous-position and bank D/CE/R/S
pins. Each family returns at most50 worst paths, one per endpoint. Empty groups
and groups with no timed path stay explicit gaps, never unrestricted queries.
Missing mask registers in the V122 control are expected observations.

The query also retains admission cursor/all/state and refill prepared-address
and issued/all/RAM-enable subsets. Improvements to the targeted RAW family do
not establish closure of those other families or the complete component.

The register inventory distinguishes declared widths, physical cells and unique
named bit indices, including replicas, scalar fields and missing/optimized bits.
Neither a missing register name nor a low FF count proves arithmetic correctness.
Full-width functional checks and the independent native evidence audit remain
separate. Netlist names alone do not identify every LUT's exact Boolean role.

Use a terminal native receipt and an existing legitimate license path:

```bash
python3 scripts/cu66-v123/inspect_rank.py \
  --receipt RECEIPT_JSON --label candidate --license-file LICENSE_PATH
```

The V122 control uses `--label baseline-v122`. Both the original and final DCP
hash must match the native receipt; runner/Tcl/command/output hashes are retained
in the separate query receipt. Tool completion is read-only observation, not a
new native route, positive repeat, clock qualification or hardware trial.
