# V101 methodology resolution status

The initial Vivado 2025.2 query returns zero exact target and zero Series-7
parts. A subsequent isolated 2026.1 runtime successfully accepts the legitimate
existing Basic license and finds the exact target. Actual baseline synthesis
now succeeds and produces a checkpoint and native reports. Placement is
blocked by three UTLZ-1 memory-resource errors before the placer runs. This
file summarizes native evidence; it is not a completed closure workflow.

| Evidence | Before | After | Status |
| --- | --- | --- | --- |
| Vendor methodology findings | Not available initially | 2,451 reported | SYNTH-5 378; SYNTH-6 8; TIMING-16 1,000; TIMING-18 1,000; ULMTCS-2 1; RTGT-1 64; no exhaustive-count claim |
| Vendor DRC findings | Not available initially | 95 reported, including three errors | UTLZ-1 3; CFGBVS-1 1; DPIP-1 51; DPOP-1 27; DPOP-2 13 |
| Vendor CDC report | Not available initially | All analyzed paths safely timed | Single-clock OOC; undelayed input ports skipped, not whole-board signoff |
| Historical timing source modifications | None | None | Original constraints/build flows retained byte-for-byte |
| New OOC clock-loading order | V100 loads clock after synthesis | V101 recipe loads the same 10-ns clock before synthesis | Source/recipe check only; not a measured closure result |
| New external timing assumptions | None | None | Unknown contracts remain open |
| New waivers or exceptions | None | None | No `create_waiver`, false-path, multicycle or asynchronous clock-group addition |

The exact target requires 22,286 memory LUTs against 19,000 compatible sites;
RAMD64E demand alone is 19,956 against 19,000. No resource error was disabled.
The synthesized total is 74,340 LUTs against 63,400, with only 16/135 block RAM
tiles occupied. Memory port/latency-aware RTL mapping is required before
placement can be evaluated.

At the unchanged 10-ns component target, synthesis WNS is -16.629 ns and TNS
is -73,220.930 ns. The first setup path has 49 logic levels. TIMING-16's
clock/path review supports an architectural investigation; the audit does not
invent a false path or relax the target. TIMING-18 remains open because actual
external interface timing requirements are missing. No source assertions,
public counters or metadata validation were removed to clear a report.

Native methodology, check_timing, CDC, DRC, exceptions, clocks, unconstrained
and min/max synthesis reports are retained under the selected build attempt.
For actual reported rule IDs, apply the AMD skill's supported-rule guidance
using the violation properties, preserve before/after constraints and generate
the requested constraint diff. No rule was waived or declared resolved here.
