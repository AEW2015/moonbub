# Native Common17-1257 investigation

Full exact-source replay gives a verified workaround, not an identified internal
root cause. The design/clock/IO Tcl body and every RTL/header byte were preserved.

| Working directory | Child TEMP/TMP | Full flow |
|---|---|---|
| Original long | Original long | Common17-1257; process0 is not clean evidence |
| Short unique | Short unique | Clean completion and all required reports |
| Original-length long | Short unique | Clean completion and all required reports |
| Short unique | Long | Common17-1257; completion still not a clean gate |

Use a new short private child TEMP/TMP for the next build, while preserving all
source/clock/constraint gates and requiring no native ERROR in its fresh complete
transcript. Do not change user/machine environment, mutate active runs, or waive
the prior errors. Output artifacts may remain at their long source-bound paths;
the long-working-directory/short-temp replay completed cleanly.

The message names failed directory `C`. The exact intended internal artifact is
unknown. A read-only Tcl file-mkdir trace sees the successful synthesis realtime
tmp directory, but does not expose the failing native call. Eight startup-only
probes were clean, including the exact prior temp path and full CLI shape. Thus
no general startup-only failure, slash-only bug or MAX_PATH threshold is claimed.

The first metadata record queried a mixed-case key on plain `dict(os.environ)`;
Windows keys there are uppercase. Its null/false NoDefault metadata was wrong.
The child environment was copied without removing that key; later direct native
prints show NoDefaultCurrentDirectoryInExePath1. No global environment changed.

`environment-review-v001/report.json` hashes the failed/clean full runs and
minimal probes. The image gate remains blocked for affected error-bearing runs;
the next complete clean implementation must independently pass timing, route,
DRC, CDC, source binding and physical qualification.
