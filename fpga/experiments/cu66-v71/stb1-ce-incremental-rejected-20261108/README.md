# CE incremental implementation option ? PREPARED / HOLD

No Vivado process or implementation was launched for this option. Root review and explicit approval are required after the current fresh flow and its exclusive cone/help query finish.

Use the SAME CE constrained.dcp (exact one-line source/function gates), then original opt_design, then:

`read_checkpoint -incremental -directive RuntimeOptimized C:/moon/builds/stb1-v001/routed.dcp`

The physical reference is the passing V001 checkpoint, not V003's replicated netlist or the fresh CE route. This applies reference physical data to matching current netlist objects; it does not substitute the old RTL/netlist for the CE candidate. Root's selected V028 image remains unchanged.

No force_incr, fixed-object list, source edit, clock/pin/exception relaxation or new reset is used. Original place/route/physopt/cleanup commands and all final reports remain. RuntimeOptimized is the documented default incremental directive and targets reference WNS. In actual incremental mode the tool may override ordinary place/route directive behavior; if it selects a full flow, those original directives remain the full-flow request. Report what the tool does, not just what this script requests.

Reuse reports are requested immediately after reference load, after placement and at final route, plus clocks/exceptions before and after reference load. Native matching/mode messages must be preserved. AMD2025.2 documentation says standard incremental normally needs >80% cell reuse and may select a full flow; one changed source file out of79 does NOT establish cell matching, placement reuse or net routing reuse. There is no forced fallback bypass. A full-flow fallback might consume the remaining window; root must choose whether to launch based on actual time available.

run.py is default-blocked by review-approval.json and pins current constrained DCP, source freeze, reference PASS DCP, scripts and actual source hashes. It checks no other Vivado process is active and requires the installed read_checkpoint/report_incremental_reuse help captured in the same authorized post-route read-only cone query. Until root reviews those local flags, the prepared report command options remain unqualified.

After root approval (including prepared_bindings_sha256), the concrete command is:

`python C:/moon/builds/stb1-ce-incremental-v001/run.py`

A negative HOLD test passed before any launch receipt. Python syntax is checked; no native incremental command has executed yet. No BIT/hardware or image identity is assigned. Positive WNS alone would not select a new image; all final timing/hold/pulse/DRC/routes/CDC/source/cone gates and root selection remain.

Primary references:

- [AMD2025.2 Incremental Mode](https://docs.amd.com/r/2025.2-English/ug904-vivado-implementation/Incremental-Mode)
- [AMD2025.2 read_checkpoint](https://docs.amd.com/r/2025.2-English/ug835-vivado-tcl-commands/read_checkpoint)

The supplied Running-Incremental-Place-and-Route URL and report_incremental_reuse reference page were unavailable through web retrieval; exact installed help will be the decisive option check. The current passing design is preserved regardless of this optional experiment.
