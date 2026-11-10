# Supplemental padding-cache routed inspection

The frozen broad V128 inspection queries the RAW validation families but does not name the new `prepared_header_padding_ok` register. This separate observation tool fills that measurement gap. It does not change the nine frozen native/query tools, production RTL, constraints, timing comparators, source maps, routed checkpoint, or qualification rules.

The [launcher](../../scripts/cu66-v128/inspect_padding.py) derives from the existing `inspect_pipeline.py` with only diagnostic description, script path, output directory, container label, receipt schema and completion markers changed. [Reversible derivation](../../scripts/cu66-v128/inspect-padding-derivation.json) records every literal edit and both old/new SHA pins. It retains the existing resource gates and stop monitors, two CPUs, 8 GiB combined RAM/swap, 240-second container limit and 270-second host watchdog.

Before the first candidate query, Root must review and freeze the launcher, [Tcl query](../../scripts/cu66-v128/inspect_padding.tcl), derivation and unchanged candidate padding-source SHA. This document records preparation; no EDA query has run from this tool yet.

The input is an already completed 8 ns native `route.dcp`, bound to its native receipt. The launcher checks the whole checkpoint SHA before and after execution, mounts it read-only and records hashes of all output artifacts. The Tcl additionally checks the existing `xc7a100tcsg324-1`, single `component_clk`, 8 ns period and 0/4 ns waveform. It opens the checkpoint and emits reports; it creates no clocks/constraints, performs no synthesis/placement/routing, and writes no checkpoint or bitstream.

Eight path families each retain at most 15 worst max-delay paths:

| Sources | Endpoints |
| --- | --- |
| All timed startpoints | Padding-cache D |
| All timed startpoints | Padding-cache CE |
| Padding-cache Q | All timed endpoints |
| Padding-cache Q | Admission tile R |
| All named admission header Q | All timed endpoints |
| All named admission header Q | Admission tile R |
| Full32 header-index Q | Padding-cache D |
| Full32 header-index Q | Padding-cache CE |

The declared cache is one bit, header index 32 bits and header array 128×8 bits. Header inventory parses byte and bit separately and records flattened `8*byte+bit` indices. Counts, unmatched declared bits, replicas and unknown names remain observations. An optimized or renamed register is a query gap, not proof that a path disappeared or a full-width comparison was removed. Empty selected sources or endpoints never silently broaden to a global query. The two intentional all-startpoint families are explicit; their source count is reported as scope rather than an invented count of one.

For at most 16 matching named cache FFs, the query records immediate Q load counts and timing-endpoint fanout. Printed load and endpoint lists are capped at 256 entries each while total counts and truncation gaps are retained. The positional source-object syntax follows [AMD UG835 2026.1 `all_fanout`](https://docs.amd.com/r/en-US/ug835-vivado-tcl-commands/all_fanout). Query errors are reported as gaps rather than silently treated as zero fanout.

Outputs include `targeted-paths.tsv`, family timing reports, register inventory/width tables, `cache-fanout.tsv`, query gaps, existing clock/route status reports and an observation receipt. A clean completion means the bounded read-only query finished and the input checkpoint SHA remained unchanged. It does not mean 125 MHz timing passed, a new physical repeat ran, hardware reached 30 fps, or decoding was validated below 10 ms.

After Root authorizes the query, use the same native receipt/license paths as the existing inspection launcher:

```bash
python3 scripts/cu66-v128/inspect_padding.py \
  --receipt PATH_TO_COMPLETED_NATIVE_RECEIPT \
  --label candidate \
  --license-file PATH_TO_EXISTING_LICENSE_FILE
```

If native work finishes before this supplemental tool is reviewed, retain the missing measurement as an explicit gap; do not block the native result or substitute this query for its timing evidence.
