# V121 baseline audit

The starting point is V120 Source B, with its selected RTL pinned to `69c0f145d1e3969f5418645a79647634b312214b`. All 18 files in the V120 handoff source manifest were re-hashed in this checkout and match both the manifest hashes and the pinned source revision. The machine-readable per-file record is in [baseline.json](../../experiments/python-gamebub-v121/audit/baseline.json).

## Existing timing results

| Trial | Clock | WNS | TNS | Setup failures | Hold slack / failures | Pulse slack / failures | Routing errors |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| B100 initial | 100 MHz | +0.174 ns | 0 ns | 0 | +0.028 ns / 0 | +3.750 ns / 0 | 0 |
| B100 fresh repeat | 100 MHz | +0.174 ns | 0 ns | 0 | +0.028 ns / 0 | +3.750 ns / 0 | 0 |
| B125 initial | 125 MHz | −1.517 ns | −3,931.934 ns | 10,524 | +0.082 ns / 0 | +2.750 ns / 0 | 0 |

The 100 MHz repeat is the qualified internal OOC component timing baseline. The 125 MHz result is a failed internal setup result. Neither establishes full-board timing, a board bitstream, sustained hardware 30 fps, or validated hardware decoding below 10 ms.

## Frozen implementation recipe

The V120 component uses `xc7a100tcsg324-1`, top `cs88_pipeline_v91k`, the frozen Vivado image `sha256:dd51b5dd44148c23bb0059b929697243797022172d5efb01ffdd8b8dd7a89742`, fresh RTL start, and the original V120 core Tcl. Its `read_xdc $constraint_file` occurs before `synth_design`; the XDC defines only `component_clk` at the requested 10 ns or 8 ns period. Synthesis uses the default directive by omission. The recipe adds no retiming, false paths, multicycle paths, clock groups, or guessed I/O delays. The flow’s placement, optimization, and route directives remain those pinned in the V120 recipe.

## Reused native runner and limits

The exact existing native runner is `scripts/cu66-v120/admission_repair/native.py` (precedent hash `ad0545d3…15f29`). Its launch gate requires at least 8 GiB MemAvailable, full-memory PSI `avg10 < 1`, combined memory-plus-swap use below 85%, and fewer than two active `gamebub-v*` containers. The job is capped at 2 CPUs/threads, 8 GiB RAM and 8 GiB RAM-plus-swap, 2,048 PIDs, and 3,600 seconds. During execution it samples memory every 30 seconds and stops for MemAvailable below 4 GiB, full PSI `avg10 >= 5` twice consecutively, combined memory-plus-swap use at or above 90%, or the 3,645-second wall guard. The license and tool mounts are read-only; the runner does not print license contents.

## Protected untracked marker files

Both marker-recovery files remain untracked and match the prior V120 audit exactly: size, SHA-256, and `mtime_ns` are unchanged. Their exact values are preserved in the JSON audit. No files outside the two assigned V121 audit artifacts were changed by this audit.
