# V130 active-prefetch synthesis independent review

## Scope and pins

Read-only review of the completed active-prefetch synthesis receipt and analysis, including the preflight/audit chain, frozen RTL and recipe inputs, raw Vivado reports, active-cell inventory, and retained V130 speculative-read baseline. No synthesis or implementation flow was run for this review.

- Candidate receipt: `experiments/python-gamebub-v130/active-prefetch/synth-only/native/20261111T034257038885Z/receipt.json`, SHA-256 `8f8bc22848fc84227d9a21814d06dc98cb03efd6bc4f2bfd93f6d89a456a8369`, status `SYNTH_COMPLETE_EXPLORATORY`.
- Preflight: `experiments/python-gamebub-v130/active-prefetch/synth-only/prepared/v130-active-synth-125-20261111T034039076177Z-ca79de/preflight.json`, SHA-256 `1c05e06475b3052b8f80b64ad8631097ac98f4fa9ab201bc8966a205f4e303eb`; its static audit has status `PASS_ACTIVE_SYNTH_PREFLIGHT_AUDIT` and pins that preflight SHA.
- Analysis: `experiments/python-gamebub-v130/active-prefetch/synth-only/analysis.json`, SHA-256 `9ab03e07fc0a06b47a761f4eb5907bb784bd4d50a6afc2ed451c8f2958e098bc`.
- Retained baseline: `experiments/python-gamebub-v130/spec-read/native/20261111T024750249700Z/receipt.json`, SHA-256 `f7af8110cf6883175c144f02a26549862c1f95e9c919b091997b8a2a1d306273`.

The candidate receipt’s 54 retained artifact hashes and 18 source snapshot hashes all matched their files. The baseline’s 110 retained artifact hashes also matched. Analysis pins both receipts and the parser source; the parser hash matched. Candidate and baseline use the same ordered source aliases and differ at exactly one origin, admission: baseline V130 speculative-read source versus `fpga/experiments/cu66-v130-active-prefetch/cs88_admission_v91i2a.sv` (SHA-256 `fdc98933ca4f0becc19d9a3b5b6eca156ca9d335a210ba79020b1e405cfe52c2`). The positive and negative paired-RTL receipts are pinned in the preflight and were independently reviewed in `active-scan-independent.md`.

## Command and constraints

Vivado logged exactly one `synth_design` command: OOC top `cs88_pipeline_v91k`, part `xc7a100tcsg324-1`, flattened hierarchy. The receipt and logs report `SYNTH_COMPLETE`, an 8.000 ns `component_clk`, two threads, and no route or checkpoint read. The launcher takes the frozen V120 recipe prefix only through the point immediately before `OPT_DESIGN`; it writes synthesis reports/checkpoint, adds a read-only active-cell mapping inventory, and terminates. The component XDC and report Tcl are hash-pinned to the baseline versions. No placement, physical optimization, route, timing exceptions, or constraint edits appear in the executed prefix. This is source-bound OOC synthesis, not a routed run.

## Raw report comparison

I checked the analysis values against the candidate and retained baseline raw `synth-capacity.rpt` and `synth-timing-summary.rpt` files. Candidate versus V130 speculative-read baseline:

| Synthesis estimate | Candidate | Baseline | Delta |
| --- | ---: | ---: | ---: |
| Slice LUTs | 34,016 | 33,697 | +319 |
| Slice registers | 43,166 | 43,131 | +35 |
| Block RAM tiles | 38 | 38 | 0 |
| DSPs | 42 | 42 | 0 |
| WNS | -1.760 ns | -1.764 ns | +0.004 ns |
| TNS | -313.121 ns | -445.728 ns | +132.607 ns |
| Setup failing endpoints | 547 | 1,081 | -534 |

The WNS delta is correctly computed as candidate minus baseline. Both synthesis estimates still have negative WNS and setup failures at the fixed 8 ns target; the small WNS improvement is not timing closure or a routed timing result.

## Inventory interpretation and limitations

The retained `active-cell-inventory.tsv` has 6,229 `cell` rows and 1,401 separate `fanin` startpoint rows. The cell rows comprise 1,351 FDRE, 4,615 LUTs, and 263 MUXF7/MUXF8 cells. They include 1,350 `active_cell` register cells and one `active_scan_value` register cell; the active scan read logic appears as LUT/MUX fabric. There are no RAMB or RAMD primitive rows in this explicitly name-filtered inventory. The whole-design capacity report separately reports 38 BRAM tiles and 180 RAMD32 primitives; those totals are design-wide and cannot be attributed to the active-map inventory.

One analysis presentation issue: `active_mapping_primitive_counts` sums both the `cell` rows and the separate `fanin` rows. Its 2,752 FDRE value therefore combines 1,351 named cell rows with 1,401 fan-in rows and is not a unique-cell count. Keep the `kind` distinction when interpreting that inventory. Also, the analysis parser’s memory-prefix check omits `RAMD*`; the inspected inventory itself contains no RAMD rows, but the empty `named_memory_primitives` summary alone is not a general proof about memory inference. The analysis explicitly cautions that absent named primitives do not prove absence of memory inference.

The original analysis and script reviewed above are retained in
`active-prefetch/synth-only/analysis-history/combined-inventory-counts/`.
The current `analysis.json` was subsequently regenerated with separate cell
and fan-in counts and with `RAMD`/`RAMS` included in the memory-name filter.
The synthesis receipts and raw reports were not changed.

The receipt and analysis correctly limit the result to estimated OOC synthesis evidence. They make no routed timing, full-parent functional, hardware, 30 fps, or under-10-ms claim. The external invalid-cycle bus consumer contract remains unverified, and the paired RTL test qualifies replay/stage data only while their response-valid signals are asserted.

## Follow-up verification of corrected analysis

The analysis was revised after this review. I independently checked the current `analysis.json` (schema `v130-active-synth-analysis-v2`, SHA-256 `aef4fd79c9432e369c3a6a222c98b39c0c77c168bc15906fd43da1e201813954`) against the raw inventory and reports. The revised analysis now separates the 6,229 named cell rows from the 1,401 fan-in startpoint rows. Its cell-only primitive counts exactly match the raw inventory: 1,351 FDRE, 4,615 LUTs, and 263 MUXF7/MUXF8; the fan-in count is separately 1,401 FDRE. The expanded memory-prefix check includes RAMB, RAMD, RAMS, RAM32, RAM64, RAM128, and RAM256; the selected inventory has no such named cell rows. The device-wide capacity report still separately shows 180 RAMD32 primitives and 38 BRAM tiles, without assigning them to the active-cell name-filtered inventory.

The corrected candidate/baseline resource values and deltas still match the respective raw capacity reports: 34,016/33,697 LUTs (+319), 43,166/43,131 registers (+35), 38/38 BRAM tiles, and 42/42 DSPs. The timing values still match raw synthesis timing summaries: candidate WNS -1.760 ns versus baseline -1.764 ns (+0.004 ns), candidate TNS -313.121 ns versus -445.728 ns, and 547 versus 1,081 setup-failing endpoints. Both WNS values remain negative at 8 ns; this does not qualify physical timing. The revised analysis continues to bind the same candidate and baseline receipt hashes and parser hash. The inventory-count issue identified above is corrected in the current analysis; the prior caveat describes the superseded combined-count version.
