# V124 read-only owner-path comparison

The matched baseline/candidate query opens an existing source-bound routed
checkpoint at its existing component 8 ns clock on xc7a100tcsg324-1. It never
changes a constraint/property, runs implementation or writes a checkpoint.
The bounded wrapper checks unchanged DCP content hashes, captures command,
runner/Tcl/output hashes and keeps empty selections explicit.

Source families include scratch emit-bank, bank-ready and both raw bank epochs/
blocks, producer current-child-epoch and expected-block, plus unchanged RAW and
rank-mask sources. Each is queried to all timed endpoints and to scratch busy,
scratch state and producer state D/CE/R/S pins, at most 50 worst paths per family.
The two-dimensional bank field selector separately matches bank and bit indices;
it does not mistake bank index for register width. Physical replicas are counted
separately from unique logical bit indices.

The query observes the combinational tile_owner_match/child_owner_match nets
and their KEEP property when names survive mapping. An absent name remains a
gap, not evidence of logic removal, successful timing or comparator placement.
The source's intentionally kept two scalar lane results add no flip-flops;
only actual mapped reports can establish the implementation topology.

Admission cursor/state and all-endpoint queries, and refill issued/prepared
address all/RAM-enable subsets, stay visible. A local owner-path gain does not
close unqueried paths or the global component timing gate.

```bash
python3 scripts/cu66-v124/inspect_owner.py \
  --receipt RECEIPT_JSON --label candidate --license-file LICENSE_PATH
```

Use `--label baseline-v123` for the immutable V123125 control. The source clock
must already be 8 ns with 0/4 ns waveform; the script does not create or relax it.
The normal two-CPU/eight-GiB, available-RAM/PSI/combined-memory guards and finite
watchdogs apply. Query completion is read-only observation, not a fresh native
route, positive repeat, physical board qualification or a throughput result.
