# V119 A125 checkpoint diagnostic results

The first actual read-only checkpoint inspection completed successfully in 20.04 seconds, with the checkpoint hash unchanged. Its connectivity query is **partial**: an empty segment query prevented collection of driver LUT equations and actual load counts. The tool completion marker is not a complete operand proof.

The immutable first [attempt receipt](../../experiments/python-gamebub-v119/checkpoint-diagnostic/attempts/20261109T174654192490Z/receipt.json), [raw operand table](../../experiments/python-gamebub-v119/checkpoint-diagnostic/attempts/20261109T174654192490Z/operands.tsv), and [expert audit](../../experiments/python-gamebub-v119/audit/checkpoint-diagnostic-results.json) retain the actual result. Thirteen execution/provenance checks pass. Both exact CARRY4 cells and all twelve exact cancellation-net aliases were found. All 36 CARRY pins and all 20 CARRY input logical-startpoint lists were recorded.

The actual startpoints narrow the CARRY family to the raw coefficient:

| Target carry | Input | Raw-coefficient bit dependencies |
| --- | --- | --- |
| `dbg_coef_valid_INST_0_i_11` | CYINIT | 0–1 |
| Same | DI/S lanes 0, 1, 2, 3 | 2–3, 4–5, 6–7, 8–9 |
| `dbg_coef_valid_INST_0_i_4` | CI | 0–9, through the preceding carry |
| Same | DI/S lanes 0, 1, 2 | 10–11, 12–13, 14–15 |

The remaining unused carry input lanes resolve to ground/startpoint aliases. No unrelated count, epoch, block or mode register appears in these operand startpoint lists. This supports investigating the actual ingress signed16 range predicate. The exact Boolean functions remain unresolved until their driver LUT INIT values and input wiring are available; a startpoint list alone does not establish a comparator equation or improved mapping.

The first Tcl used `get_nets -segments -of_objects` on an already named net object. Vivado returned an empty list without throwing an error for all 32 such queries. Downstream driver lists and twelve zero load counts therefore describe a query gap, not absent physical drivers or zero fanout. In particular, the original native report’s large downstream fanouts remain authoritative. The first executed Tcl, wrapper, prepared manifest and attempt remain unchanged.

A separate direct-net diagnostic is prepared in `inspect-direct.tcl` and `run_direct.py`, with a distinct [prepared manifest](../../experiments/python-gamebub-v119/checkpoint-diagnostic/prepared-direct.json) and `attempts-direct`/`results-direct.json` namespace. Its [static preflight audit](../../experiments/python-gamebub-v119/audit/checkpoint-diagnostic-direct-preflight.json) passes sixteen checks, including preservation of all original diagnostic artifacts. It explicitly records empty segment expansion, falls back to the direct net, checks driver/LUT INIT/load coverage, and reports unresolved connectivity rather than interpreting empty queries as zero logic. Root dispatches the job; no second execution is claimed here yet.

Both diagnostics read the same final A125 checkpoint and are distinct from native physical trials or positive repeats. No RTL, constraints, source composition, consumed native recipe or hardware was changed. Any exact signed-range prefix remains a proposed source experiment until RTL equivalence and fresh physical mapping are measured.

## Direct-net result: specific carry equations resolved

The separate direct-net inspection [finished in 20.04 seconds](../../experiments/python-gamebub-v119/checkpoint-diagnostic/attempts-direct/20261109T175003955021Z/receipt.json), with exit code 0 and the same DCP unchanged. Its overall receipt remains `PARTIAL_CONNECTIVITY_QUERY`: nine repeated unresolved rows concern only three reset/abort hierarchical aliases with no local leaf driver. These aliases are outside both target CARRY operand cones. No additional query is needed to interpret those two cones.

The [raw direct operand table](../../experiments/python-gamebub-v119/checkpoint-diagnostic/attempts-direct/20261109T175003955021Z/operands.tsv) contains 196 nonempty driver-query rows, 76 LUT INIT rows, and nonzero actual load counts for all twelve selected control nets. Those are query-row counts, including repeated observations, rather than counts of unique cells. All 217 empty segment expansions explicitly record their direct-net fallback.

The specific carry result is stronger than the first startpoint hypothesis:

- Lower `dbg_coef_valid_INST_0_i_11/CO[3]` is exactly `OR(raw_coefficient[9:0])`. Its initialization and data lanes use pairwise OR LUT2 INIT `4'hE`, while select lanes use NOR INIT `4'h1`.
- Upper `dbg_coef_valid_INST_0_i_4/CO[2]` is exactly **`signed16(raw_coefficient) > 2048`**. Its bit-10/11, bit-12/13 and sign-prefix wiring plus INIT values are fully present. These two CARRY4s implement the positive upper-bound rejection predicate, not the complete signed-range validity check.

The new [data interpreter](../../scripts/cu66-v119/diagnostic/interpret_direct.py) reconstructs all fifteen actual LUT2 functions, their recorded input order, both CARRY4s and ground connections from the raw table. It uses the installed vendor `LUT2.v` INIT indexing and `CARRY4.v` carry-mux equations, retaining their SHA256 pins. It exhaustively evaluates every 16-bit input: **65,536 values, zero mismatches** for the lower ten-bit OR and upper signed greater-than predicate. The upper output is true for exactly 30,719 values. This is actual netlist Boolean interpretation, not an RTL timing simulation.

The complete proposed validity prefix—`raw[15:11] == 0 || raw[15:11] == 31 || raw == 16'h0800`—is separately checked against signed −2048 through +2048 inclusive over the same 65,536 values with zero mismatches. That demonstrates a valid replacement expression to prototype. It does not show what Vivado would map or route, and it does not prove all downstream qualification/error chronology for a modified design. The corresponding [machine audit](../../experiments/python-gamebub-v119/audit/checkpoint-diagnostic-direct-results.json) is `PASS_SPECIFIC_CARRY_EQUATIONS_GENERAL_CONNECTIVITY_PARTIAL` and retains exact operand expressions, INIT values, bit dependencies, all boundary outcomes and the unresolved scope.

The actual control-net leaf load counts reproduce the native path report:

| Named path net | Actual leaf loads |
| --- | ---: |
| `mode_store/state_reg[0]_1` | 2 |
| `parser/base_abort` | 33 |
| `parser/reset_8` | 368 |
| `scratch/running_reg_29` | 259 |
| `scratch/packet_abort` | 10 |
| `parser/limit0_2[0]` | 1,031 |
| `scratch/start0` | 207 |
| `parser/sel_rep__0` | 76 |
| `parser/parser_in_ready` | 2 |
| `parser/stage_word_ready` | 2 |
| `parser/prepared_request_addr1104_out` | 6 |
| `parser/prepared_request_addr[15]_i_16_n_0` | 32 |

The remaining unmatched aliases are `mode_store/abort_packet`, `parser/reset` and `scratch/reset`. The report preserves all nine occurrences and does not infer their complete cross-hierarchy drivers. They do not invalidate the independently complete carry-input network or the twelve directly observed control load counts. Native RTL, constraints, source composition and consumed recipes remain frozen. No candidate B, physical reroute, positive repeat or hardware claim is introduced by this interpretation.

AMD’s [CARRY4 primitive documentation](https://docs.amd.com/r/en-US/ug953-vivado-7series-libraries/CARRY4) describes the carry-mux primitive; the interpreter pins the actual installed 2026.1 vendor model used for the exact Boolean equations.

A separate [verified interpreter](../../scripts/cu66-v119/diagnostic/interpret_direct_verified.py) and [verified audit](../../experiments/python-gamebub-v119/audit/checkpoint-diagnostic-direct-verified.json) additionally check all installed vendor carry input assignments and the exact `CO_fb = {CO[2:0], CI_in || CYINIT_in}` relation, not only the final CO mux equation. The same 65,536-value checks pass. The original executed interpreter and its audit are preserved byte-for-byte; their hashes are retained in the new audit.
