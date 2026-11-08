# V106 measured implementation and source comparison

The fixed **100 MHz internal OOC timing target remains unmet**: selected routed setup WNS is **-4.034 ns**.

The selected next-study source is **closure**, with routed WNS **-4.034 ns**, a **+9.090 ns** change from the selected V105 geometry control. Selection requires paired functional parity, completed legal routing and target resource fit, clocked/constrained internal endpoints, no loops, nonnegative hold/pulse slack and zero hold/pulse failures; among eligible routes it prefers setup WNS, then LUT/DSP counts. Negative setup WNS remains a failure of the fixed 10 ns target. One route per measured variant is an experimental comparison, not robustness or achieved-Fmax evidence.

A separate, **unselected post-route diagnostic** reopened the original closure route and ran AggressiveExplore once: WNS changed from -4.034 to -3.777 ns (+0.257 ns), with 44,630 setup endpoints still failing. It is outside the six Default-flow source trials and does not replace the selected source or meet 100 MHz. [Diagnostic details](postroute-probe.md) and the [portable report audit](../../experiments/python-gamebub-v106/postroute/report-audit.json) retain its separate strategy, reports and scope.

**guarded-suffix-idct-cache: tool/build failure**, exit 1, 688.902 s; no placement/routing result was retained. Synthesis WNS -3.581 ns is an estimate only. The attempt remains in the [native audit](../../experiments/python-gamebub-v106/native-audit.json), without routed target qualification.

**local-guards-scratch-area: watchdog timeout**, exit 124, 1800.722 s; no placement/routing result was retained. Synthesis WNS -3.205 ns is an estimate only. The attempt remains in the [native audit](../../experiments/python-gamebub-v106/native-audit.json), without routed target qualification.


## Matched isolated IDCT synthesis screen

The independently pinned [unit comparison](../../experiments/python-gamebub-v106/idct-area/unit-synthesis-comparison.json) uses the same part, 10 ns clock, tool/settings and rebuilt original/first-prefetch/shared-selector sources. These are **unit synthesis** values, distinct from complete-top hierarchy or routed metrics.

| IDCT unit | Slice LUTs | Registers | DSPs | Estimated setup slack (ns) |
| --- | ---: | ---: | ---: | ---: |
| original | 7,690 | 5,149 | 17 | +0.796 |
| prefetch | 16,256 | 5,176 | 19 | -0.700 |
| shared | 7,772 | 5,129 | 17 | +2.920 |

The shared selector changes unit LUTs by +82 versus original and -8,484 versus the first prefetch. This supports the area-repair preflight; it does not establish whole-top fit, placed/routed timing, parent input arrival or hardware latency/FPS. The failed fifth full-top placement remains retained separately.

## Measured stages

All native attempts use Vivado 2026.1 build 6511674, `xc7a100tcsg324-1`, the retained 17-file canonical decoder closure, a 10 ns clock loaded before synthesis, Default directives and two threads. Native containers retain two CPUs, 8 GiB and a 1,800-second timeout. Synthesis, placement and routing values are separate stages; compare like stages. Failed placement attempts retain synthesis evidence only and supply no routed WNS, physical-locality result or target pass.

| Variant | Stage | LUTs | LUTRAMs | FFs | RAMB36 / RAMB18 | DSPs | WNS (ns) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| V105 geometry control | synth | 46,691 | 3,854 | 34,721 | 32 / 0 | 27 | -11.593 |
| V105 geometry control | place | 46,115 | 2,718 | 34,760 | 32 / 0 | 27 | -12.375 |
| V105 geometry control | route | 46,115 | 2,718 | 34,760 | 32 / 0 | 27 | -13.124 |
| closure | synth | 45,560 | 1,806 | 36,881 | 32 / 10 | 27 | -3.461 |
| closure | place | 46,062 | 1,694 | 36,919 | 32 / 10 | 27 | -3.369 |
| closure | route | 46,062 | 1,694 | 36,919 | 32 / 10 | 27 | -4.034 |
| closure-prefix-telemetry | synth | 44,726 | 1,806 | 36,739 | 32 / 10 | 27 | -3.897 |
| closure-prefix-telemetry | place | 45,230 | 1,694 | 36,795 | 32 / 10 | 27 | -4.800 |
| closure-prefix-telemetry | route | 45,230 | 1,694 | 36,795 | 32 / 10 | 27 | -4.700 |
| guarded-suffix-idct-cache | synth | 59,047 | 1,806 | 36,836 | 32 / 10 | 30 | -3.581 |
| local-guards-scratch-area | synth | 47,352 | 1,825 | 36,984 | 32 / 10 | 28 | -3.205 |
| lut | synth | 49,805 | 3,726 | 34,774 | 32 / 0 | 27 | -5.303 |
| lut | place | 49,263 | 2,590 | 34,838 | 32 / 0 | 27 | -6.246 |
| lut | route | 49,263 | 2,590 | 34,838 | 32 / 0 | 27 | -7.130 |
| lut-storage-plan | synth | 47,085 | 1,806 | 36,819 | 32 / 0 | 27 | -5.113 |
| lut-storage-plan | place | 47,594 | 1,694 | 36,879 | 32 / 0 | 27 | -4.777 |
| lut-storage-plan | route | 47,594 | 1,694 | 36,879 | 32 / 0 | 27 | -6.628 |

The V105 control is the published selected **geometry** route. The final selected route's same-stage resource deltas are:

| Resource | V105 route | Selected V106 route | Delta |
| --- | ---: | ---: | ---: |
| total_LUT | 46,115 | 46,062 | -53 |
| LUTRAM | 2,718 | 1,694 | -1,024 |
| FF | 34,760 | 36,919 | +2,159 |
| RAMB36 | 32 | 32 | +0 |
| RAMB18 | 0 | 10 | +10 |
| DSP | 27 | 27 | +0 |

All measured routed variants relative to that same V105 route:

| Variant | Δ LUT | Δ LUTRAM | Δ FF | Δ RAMB36 | Δ RAMB18 | Δ DSP | Δ WNS (ns) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| closure | -53 | -1,024 | +2,159 | +0 | +10 | +0 | +9.090 |
| closure-prefix-telemetry | -885 | -1,024 | +2,035 | +0 | +10 | +0 | +8.424 |
| lut | +3,148 | -128 | +78 | +0 | +0 | +0 | +5.994 |
| lut-storage-plan | +1,479 | -1,024 | +2,119 | +0 | +0 | +0 | +6.496 |

## Actual campaign versus deferred controls

First LUT synthesis exposed serial scratch-plan sums; first LUT routing exposed full32 context division and Rice remaining-bit paths. Prioritize those measured violations to meet the fixed target. The [campaign policy](../../scripts/cu66-v106/campaign.py) records its actual routed and synthesis evidence pins. Deferred variants retain functional verification; native resources/timing remain **unmeasured**, without interpolated values or inferred wins. This adaptive set is not an exhaustive factorial comparison.

| Variant | Functional status | Native outcome | Receipt |
| --- | --- | --- | --- |
| closure | fresh + canonical, paired PASS | COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN | [20261108T013032873883Z](../../experiments/python-gamebub-v106/native/20261108T013032873883Z/receipt.json) |
| closure-prefix-telemetry | fresh + canonical, paired PASS | COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN | [20261108T015540764948Z](../../experiments/python-gamebub-v106/native/20261108T015540764948Z/receipt.json) |
| guarded-suffix-idct-cache | **Excluded/rejected trial; required paired PASS absent** | TOOL_OR_BUILD_FAILED; **no completed route** | [20261108T021556317071Z](../../experiments/python-gamebub-v106/native/20261108T021556317071Z/receipt.json) |
| local-guards-scratch-area | fresh + canonical, paired PASS | TOOL_OR_BUILD_FAILED; **no completed route** | [20261108T025230842632Z](../../experiments/python-gamebub-v106/native/20261108T025230842632Z/receipt.json) |
| lut | fresh + canonical, paired PASS | COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN | [20261108T005012241750Z](../../experiments/python-gamebub-v106/native/20261108T005012241750Z/receipt.json) |
| lut-plan | fresh + canonical, paired PASS | **Unmeasured: native run deferred** | — |
| lut-storage | fresh + canonical, paired PASS | **Unmeasured: native run deferred** | — |
| lut-storage-memory | fresh + canonical, paired PASS | **Unmeasured: native run deferred** | — |
| lut-storage-plan | fresh + canonical, paired PASS | COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN | [20261108T010638248027Z](../../experiments/python-gamebub-v106/native/20261108T010638248027Z/receipt.json) |
| lut-storage-plan-context | fresh + canonical, paired PASS | **Unmeasured: native run deferred** | — |
| memory | fresh + canonical, paired PASS | **Unmeasured: native run deferred** | — |
| narrow | fresh + canonical, paired PASS | **Unmeasured: native run deferred** | — |
| storage | fresh + canonical, paired PASS | **Unmeasured: native run deferred** | — |

## Coefficient memory objects and storage tradeoffs

The retained distributed-RAM ledger includes both macro objects and their physical/logical subcell records. For example, 1,024 `RAM32X1D` objects plus 2,048 `RAMD32` SP/DP rows represent 1,024 parent memories, not 3,072 independent memories or LUTRAM sites. Use the utilization report's LUTRAM count for site accounting; do not add parent and subcell counts. The following table reports the actual named coefficient objects separately from full transform-hierarchy resources:

| Routed variant | Named coefficient objects by primitive | Transform LUTRAMs | Transform FFs |
| --- | --- | ---: | ---: |
| closure | 0 named coefficient RAM objects | 130 | 10,206 |
| closure-prefix-telemetry | 0 named coefficient RAM objects | 130 | 10,202 |
| lut | RAM32X1D × 1,024, RAMD32 × 2,048 | 1,154 | 8,175 |
| lut-storage-plan | 0 named coefficient RAM objects | 130 | 10,202 |

Static generated coefficient words can eliminate the tiny two-deep distributed memories while increasing FF use. Shared guards, CE/control-set fanout and other logic still require actual route evaluation. Full-component deltas include every composed edit and synthesis optimization; they are not isolated per-feature area costs. Mode-table BRAM inference is a separately qualified inherited building block and is not assumed present unless the measured variant's source map and RAM ledger contain it.

The [native audit](../../experiments/python-gamebub-v106/native-audit.json) retains primitive RAM/DSP settings, high-fanout, control-set, complexity, congestion, capacity, timing, DRC, methodology and routing-legality evidence, including every terminal failure/stop if present. The [setup-path analysis](../../experiments/python-gamebub-v106/path-analysis.json) records actual source/destination, logic/route delay and logic depth. The [quantitative physical-locality report](physical-locality.md) separates top-50 net samples, finite versus nonfinite slack, control-set/packing metrics and congestion-window thresholds. Report counts and observed settings do not by themselves establish mapped-netlist collision semantics or hardware service latency.

## Per-lane functional evidence

| Variant | Mode | Case/profile runs | Directed checks | Evidence |
| --- | --- | ---: | ---: | --- |
| closure | canonical | 88 | 84 | [PASS receipt](../../experiments/python-gamebub-v106/regression/closure/canonical/results.json) |
| closure | fresh | 24 | 52 | [PASS receipt](../../experiments/python-gamebub-v106/regression/closure/fresh/results.json) |
| closure-prefix-telemetry | canonical | 88 | 84 | [PASS receipt](../../experiments/python-gamebub-v106/regression/closure-prefix-telemetry/canonical/results.json) |
| closure-prefix-telemetry | fresh | 24 | 52 | [PASS receipt](../../experiments/python-gamebub-v106/regression/closure-prefix-telemetry/fresh/results.json) |
| local-guards-scratch-area | canonical | 88 | 84 | [PASS receipt](../../experiments/python-gamebub-v106/regression/local-guards-scratch-area/canonical/results.json) |
| local-guards-scratch-area | fresh | 24 | 52 | [PASS receipt](../../experiments/python-gamebub-v106/regression/local-guards-scratch-area/fresh/results.json) |
| lut | canonical | 88 | 84 | [PASS receipt](../../experiments/python-gamebub-v106/regression/lut/canonical/results.json) |
| lut | fresh | 24 | 52 | [PASS receipt](../../experiments/python-gamebub-v106/regression/lut/fresh/results.json) |
| lut-plan | canonical | 88 | 84 | [PASS receipt](../../experiments/python-gamebub-v106/regression/lut-plan/canonical/results.json) |
| lut-plan | fresh | 24 | 52 | [PASS receipt](../../experiments/python-gamebub-v106/regression/lut-plan/fresh/results.json) |
| lut-storage | canonical | 88 | 84 | [PASS receipt](../../experiments/python-gamebub-v106/regression/lut-storage/canonical/results.json) |
| lut-storage | fresh | 24 | 52 | [PASS receipt](../../experiments/python-gamebub-v106/regression/lut-storage/fresh/results.json) |
| lut-storage-memory | canonical | 88 | 84 | [PASS receipt](../../experiments/python-gamebub-v106/regression/lut-storage-memory/canonical/results.json) |
| lut-storage-memory | fresh | 24 | 52 | [PASS receipt](../../experiments/python-gamebub-v106/regression/lut-storage-memory/fresh/results.json) |
| lut-storage-plan | canonical | 88 | 84 | [PASS receipt](../../experiments/python-gamebub-v106/regression/lut-storage-plan/canonical/results.json) |
| lut-storage-plan | fresh | 24 | 52 | [PASS receipt](../../experiments/python-gamebub-v106/regression/lut-storage-plan/fresh/results.json) |
| lut-storage-plan-context | canonical | 88 | 84 | [PASS receipt](../../experiments/python-gamebub-v106/regression/lut-storage-plan-context/canonical/results.json) |
| lut-storage-plan-context | fresh | 24 | 52 | [PASS receipt](../../experiments/python-gamebub-v106/regression/lut-storage-plan-context/fresh/results.json) |
| memory | canonical | 88 | 84 | [PASS receipt](../../experiments/python-gamebub-v106/regression/memory/canonical/results.json) |
| memory | fresh | 24 | 52 | [PASS receipt](../../experiments/python-gamebub-v106/regression/memory/fresh/results.json) |
| narrow | canonical | 88 | 84 | [PASS receipt](../../experiments/python-gamebub-v106/regression/narrow/canonical/results.json) |
| narrow | fresh | 24 | 52 | [PASS receipt](../../experiments/python-gamebub-v106/regression/narrow/fresh/results.json) |
| storage | canonical | 88 | 84 | [PASS receipt](../../experiments/python-gamebub-v106/regression/storage/canonical/results.json) |
| storage | fresh | 24 | 52 | [PASS receipt](../../experiments/python-gamebub-v106/regression/storage/fresh/results.json) |

Counts include both implementations, both seeds and scheduled profiles/expected rejects; they are not frame counts. Golden data and cycle-exact equivalence have distinct scopes from routed frequency or complete-system service.

## Exact edit recipes

| Recipe | SHA-256 |
| --- | --- |
| [fpga/experiments/cu66-v106-context/edit-recipe.json](../../fpga/experiments/cu66-v106-context/edit-recipe.json) | `41a072399a86cf1a189af3b661946bc4a4ec70c7a277752a74a3dfbd4eee8e3f` |
| [fpga/experiments/cu66-v106-idct-area/edit-recipe.json](../../fpga/experiments/cu66-v106-idct-area/edit-recipe.json) | `3022274c92cc37c70cbc62e94fc7e9ee54be2039f396e3d539eb3431b69a4ebc` |
| [fpga/experiments/cu66-v106-idct/edit-recipe.json](../../fpga/experiments/cu66-v106-idct/edit-recipe.json) | `817bda21de9a29d3e91a0e6f44e9ec1765c8a02332cce95f7ca80041923b5574` |
| [fpga/experiments/cu66-v106-ingress/edit-recipe.json](../../fpga/experiments/cu66-v106-ingress/edit-recipe.json) | `7a85248baf1c8de6095b9d7225aafd04f5eb1045a646fe4423a37b88fc2981d2` |
| [fpga/experiments/cu66-v106-locality/edit-proof.json](../../fpga/experiments/cu66-v106-locality/edit-proof.json) | `62b7a8adddd02ef5d27d838fe2dd138c9867082ca8354e467d04121d5a62c0bd` |
| [fpga/experiments/cu66-v106-math/lut/cs88_coefficients_v91k.recipe.json](../../fpga/experiments/cu66-v106-math/lut/cs88_coefficients_v91k.recipe.json) | `f1e7dd853e86214ff3356f993b921f00f26ff75b448086323b37a01998043ffc` |
| [fpga/experiments/cu66-v106-math/lut/cs88_pipeline_v91i2b.recipe.json](../../fpga/experiments/cu66-v106-math/lut/cs88_pipeline_v91i2b.recipe.json) | `2eda2c95c6611abc6ff5611d389d88e9024b5e4f2a63b56ee0c0c85a93420237` |
| [fpga/experiments/cu66-v106-math/lut/cu66_inverse_stream_v91j.recipe.json](../../fpga/experiments/cu66-v106-math/lut/cu66_inverse_stream_v91j.recipe.json) | `35e0f7fa4897d82789d1871e2b0b662b9514f1fa783c15baa7b259819c36e541` |
| [fpga/experiments/cu66-v106-math/narrow/cs88_coefficients_v91k.recipe.json](../../fpga/experiments/cu66-v106-math/narrow/cs88_coefficients_v91k.recipe.json) | `f839781ac57fb717a9a184f5d99a6b19978ee33c7c058beaf8f0535f7f716962` |
| [fpga/experiments/cu66-v106-math/narrow/cs88_pipeline_v91i2b.recipe.json](../../fpga/experiments/cu66-v106-math/narrow/cs88_pipeline_v91i2b.recipe.json) | `bbccb8671194cc658fe332fe8b4f2fda7f77ab582ef2c77660d632a00da972c5` |
| [fpga/experiments/cu66-v106-math/narrow/cu66_inverse_stream_v91j.recipe.json](../../fpga/experiments/cu66-v106-math/narrow/cu66_inverse_stream_v91j.recipe.json) | `9bf327135be931bef66c95b38443672a876d368df7e1371ebe9d8c6b644bd7fb` |
| [fpga/experiments/cu66-v106-plan/edit-recipe.json](../../fpga/experiments/cu66-v106-plan/edit-recipe.json) | `bc27673675fa73250569f2811c3b06628832851e138e95745d6de69b9eb6515f` |
| [fpga/experiments/cu66-v106-prefix/edit-proof.json](../../fpga/experiments/cu66-v106-prefix/edit-proof.json) | `2eb2d9c06869ffa2d9c313f26406afb9a4874c428b4c4ff06e282eb2959abc51` |
| [fpga/experiments/cu66-v106-producer-cache/cs88_coefficients_v91k.recipe.json](../../fpga/experiments/cu66-v106-producer-cache/cs88_coefficients_v91k.recipe.json) | `455d1f6d5e0b70fd93b90ed6cf6a962b0b2eb3fe92bfbcf3fe4e7d2bd7d38d05` |
| [fpga/experiments/cu66-v106-producer-cache/cs88_pipeline_v91i2b.recipe.json](../../fpga/experiments/cu66-v106-producer-cache/cs88_pipeline_v91i2b.recipe.json) | `5b0c2703793bcec835ef3677b67487e253a4e688a782fbc42c1b9b443152f696` |
| [fpga/experiments/cu66-v106-rice/edit-proof.json](../../fpga/experiments/cu66-v106-rice/edit-proof.json) | `92238d4c6053dacb40ce3c02b358b9f144f6375112f2920547f5aa270a2e23ab` |
| [fpga/experiments/cu66-v106-scratch/edit-recipe.json](../../fpga/experiments/cu66-v106-scratch/edit-recipe.json) | `e63235fca7cb34360c75a8ae5b2532c2d335088df7029618a16ac0fb78cc6796` |
| [fpga/experiments/cu66-v106-suffix/edit-proof.json](../../fpga/experiments/cu66-v106-suffix/edit-proof.json) | `7962fdf91885521ead324cd0a361b1c0b49d0f90ae77190ccb27c3a7756e7662` |
| [fpga/experiments/cu66-v106-suffix24/edit-recipe.json](../../fpga/experiments/cu66-v106-suffix24/edit-recipe.json) | `290c32a3f136428c0a1d72c4fb93a014d61bef26d075e417425b7ef82af1cf97` |
| [fpga/experiments/cu66-v106-telemetry/edit-recipe.json](../../fpga/experiments/cu66-v106-telemetry/edit-recipe.json) | `dbb3df9555843c628424803243514922484f208b750e1c2c3bd61a5c16c2d01a` |

The [composition proof](../../experiments/python-gamebub-v106/composition.json) records exact both-order LUT-helper/storage composition. Other component recipes target distinct source modules. Module interfaces remain unchanged. Full recipe data includes each original/candidate hash and uniquely anchored exact replacement; use the machine manifests rather than copying snippets from prose.

## All variant source maps

Each row below is a replacement layered over the retained frozen source list. Inherited baseline replacements are included. Fresh-only producer mappings appear for reproducibility but are outside the filtered 17-file native canonical closure. Each replacement hash is verified against its audited paired-lane receipt when rendering.

| Variant | Original source key | Replacement | SHA-256 |
| --- | --- | --- | --- |
| closure | `fpga/experiments/cu66-v91/br88_rice_elastic.sv` | [fpga/experiments/cu66-v106-rice/br88_rice_elastic.sv](../../fpga/experiments/cu66-v106-rice/br88_rice_elastic.sv) | `5ad9997d61a74bd650999c96508c17fc03d17323ab5b1f3689ad991126b3fe5e` |
| closure | `fpga/experiments/cu66-v91b/br88_context.sv` | [fpga/experiments/cu66-v106-context/br88_context.sv](../../fpga/experiments/cu66-v106-context/br88_context.sv) | `9cb6337098d36adfbe4ef2dc073fc30a6dea17eaa4d57322fa4e725b8cce5277` |
| closure | `fpga/experiments/cu66-v91g2/packed_scratch_v91g2.sv` | [fpga/experiments/cu66-v106-plan/packed_scratch_v91g2.sv](../../fpga/experiments/cu66-v106-plan/packed_scratch_v91g2.sv) | `c46f01765b79bd35929183d8475287c2b71e93c289371f0e3f212b320b175e48` |
| closure | `fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv` | [fpga/experiments/cu66-v105-admission/cs88_admission_v91i2a.sv](../../fpga/experiments/cu66-v105-admission/cs88_admission_v91i2a.sv) | `a03a88ec25a1792b5ba5c970bb47cb66ae8b5277ec1f2680caba460e61af1d4a` |
| closure | `fpga/experiments/cu66-v91i2b/cs88_pipeline_v91i2b.sv` | [fpga/experiments/cu66-v106-math/lut/cs88_pipeline_v91i2b.sv](../../fpga/experiments/cu66-v106-math/lut/cs88_pipeline_v91i2b.sv) | `23dffb1f774049a18bc374e40b3ff36b8ac54e0d157646a3a865ce419cc2ddcf` |
| closure | `fpga/experiments/cu66-v91j/cu66_inverse_stream_v91j.sv` | [fpga/experiments/cu66-v106-composed/lut-storage/cu66_inverse_stream_v91j.sv](../../fpga/experiments/cu66-v106-composed/lut-storage/cu66_inverse_stream_v91j.sv) | `e013c3c132677c844ab02150e1477063e0ae59b89c978b20c20d68489447b326` |
| closure | `fpga/experiments/cu66-v91k/cs88_coefficients_v91k.sv` | [fpga/experiments/cu66-v106-math/lut/cs88_coefficients_v91k.sv](../../fpga/experiments/cu66-v106-math/lut/cs88_coefficients_v91k.sv) | `df0de544f56df7630850dbf20b388d4222291f885768761db7e989e9b7180f45` |
| closure | `fpga/experiments/cu66-v91k/cu66_reconstruct_stream_v91k.sv` | [fpga/experiments/cu66-v104-control/cu66_reconstruct_stream_v91k.sv](../../fpga/experiments/cu66-v104-control/cu66_reconstruct_stream_v91k.sv) | `445e1b96fc931cf1a8a6cabbf7f111a199197264eb8ab35f9dde871ab010ecb8` |
| closure-prefix-telemetry | `fpga/experiments/cu66-v91/br88_rice_elastic.sv` | [fpga/experiments/cu66-v106-prefix/br88_rice_elastic.sv](../../fpga/experiments/cu66-v106-prefix/br88_rice_elastic.sv) | `745a322dad262cbad732aea9af5d57ebfb940a961adc724b7d644b90baf25dbb` |
| closure-prefix-telemetry | `fpga/experiments/cu66-v91b/br88_context.sv` | [fpga/experiments/cu66-v106-context/br88_context.sv](../../fpga/experiments/cu66-v106-context/br88_context.sv) | `9cb6337098d36adfbe4ef2dc073fc30a6dea17eaa4d57322fa4e725b8cce5277` |
| closure-prefix-telemetry | `fpga/experiments/cu66-v91g2/packed_scratch_v91g2.sv` | [fpga/experiments/cu66-v106-plan/packed_scratch_v91g2.sv](../../fpga/experiments/cu66-v106-plan/packed_scratch_v91g2.sv) | `c46f01765b79bd35929183d8475287c2b71e93c289371f0e3f212b320b175e48` |
| closure-prefix-telemetry | `fpga/experiments/cu66-v91h/br88_pipeline_v91h.sv` | [fpga/experiments/cu66-v106-telemetry/br88_pipeline_v91h.sv](../../fpga/experiments/cu66-v106-telemetry/br88_pipeline_v91h.sv) | `c6f839570988768ac2a373302d8980ce9a6532ccbcf3c09415f9ca1c05959577` |
| closure-prefix-telemetry | `fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv` | [fpga/experiments/cu66-v105-admission/cs88_admission_v91i2a.sv](../../fpga/experiments/cu66-v105-admission/cs88_admission_v91i2a.sv) | `a03a88ec25a1792b5ba5c970bb47cb66ae8b5277ec1f2680caba460e61af1d4a` |
| closure-prefix-telemetry | `fpga/experiments/cu66-v91i2b/cs88_pipeline_v91i2b.sv` | [fpga/experiments/cu66-v106-math/lut/cs88_pipeline_v91i2b.sv](../../fpga/experiments/cu66-v106-math/lut/cs88_pipeline_v91i2b.sv) | `23dffb1f774049a18bc374e40b3ff36b8ac54e0d157646a3a865ce419cc2ddcf` |
| closure-prefix-telemetry | `fpga/experiments/cu66-v91j/cu66_inverse_stream_v91j.sv` | [fpga/experiments/cu66-v106-composed/lut-storage/cu66_inverse_stream_v91j.sv](../../fpga/experiments/cu66-v106-composed/lut-storage/cu66_inverse_stream_v91j.sv) | `e013c3c132677c844ab02150e1477063e0ae59b89c978b20c20d68489447b326` |
| closure-prefix-telemetry | `fpga/experiments/cu66-v91k/cs88_coefficients_v91k.sv` | [fpga/experiments/cu66-v106-math/lut/cs88_coefficients_v91k.sv](../../fpga/experiments/cu66-v106-math/lut/cs88_coefficients_v91k.sv) | `df0de544f56df7630850dbf20b388d4222291f885768761db7e989e9b7180f45` |
| closure-prefix-telemetry | `fpga/experiments/cu66-v91k/cu66_reconstruct_stream_v91k.sv` | [fpga/experiments/cu66-v104-control/cu66_reconstruct_stream_v91k.sv](../../fpga/experiments/cu66-v104-control/cu66_reconstruct_stream_v91k.sv) | `445e1b96fc931cf1a8a6cabbf7f111a199197264eb8ab35f9dde871ab010ecb8` |
| local-guards-scratch-area | `fpga/experiments/cu66-v69/inverse/cu66_idct8x8.sv` | [fpga/experiments/cu66-v106-idct-area/cu66_idct8x8.sv](../../fpga/experiments/cu66-v106-idct-area/cu66_idct8x8.sv) | `1ed49416dae06b727544ad1d2f96440f553cd99e5324dc895a0af5edbca5cc32` |
| local-guards-scratch-area | `fpga/experiments/cu66-v91/br88_rice_elastic.sv` | [fpga/experiments/cu66-v106-suffix24/br88_rice_elastic.sv](../../fpga/experiments/cu66-v106-suffix24/br88_rice_elastic.sv) | `d0e233eacb849476bac7c18157a6f29bd76228d378e07b2d7613db8a356cf919` |
| local-guards-scratch-area | `fpga/experiments/cu66-v91b/br88_context.sv` | [fpga/experiments/cu66-v106-context/br88_context.sv](../../fpga/experiments/cu66-v106-context/br88_context.sv) | `9cb6337098d36adfbe4ef2dc073fc30a6dea17eaa4d57322fa4e725b8cce5277` |
| local-guards-scratch-area | `fpga/experiments/cu66-v91g2/packed_scratch_v91g2.sv` | [fpga/experiments/cu66-v106-scratch/packed_scratch_v91g2.sv](../../fpga/experiments/cu66-v106-scratch/packed_scratch_v91g2.sv) | `0ee1196e2f0cafdf52742656d4c1a53604c79544c339b171989ad2785f051f8c` |
| local-guards-scratch-area | `fpga/experiments/cu66-v91h/br88_packet_ingress_sync_v91h.sv` | [fpga/experiments/cu66-v106-ingress/br88_packet_ingress_sync_v91h.sv](../../fpga/experiments/cu66-v106-ingress/br88_packet_ingress_sync_v91h.sv) | `4342972a6cf42cebf4f01a82841c0bc7c1850292ca23362817f7f071af126093` |
| local-guards-scratch-area | `fpga/experiments/cu66-v91h/br88_pipeline_v91h.sv` | [fpga/experiments/cu66-v106-telemetry/br88_pipeline_v91h.sv](../../fpga/experiments/cu66-v106-telemetry/br88_pipeline_v91h.sv) | `c6f839570988768ac2a373302d8980ce9a6532ccbcf3c09415f9ca1c05959577` |
| local-guards-scratch-area | `fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv` | [fpga/experiments/cu66-v105-admission/cs88_admission_v91i2a.sv](../../fpga/experiments/cu66-v105-admission/cs88_admission_v91i2a.sv) | `a03a88ec25a1792b5ba5c970bb47cb66ae8b5277ec1f2680caba460e61af1d4a` |
| local-guards-scratch-area | `fpga/experiments/cu66-v91i2b/cs88_pipeline_v91i2b.sv` | [fpga/experiments/cu66-v106-producer-cache/cs88_pipeline_v91i2b.sv](../../fpga/experiments/cu66-v106-producer-cache/cs88_pipeline_v91i2b.sv) | `d8fcac88930509d2cc92ff603be11204f362010cbecab4fd4a515ef18606e8a6` |
| local-guards-scratch-area | `fpga/experiments/cu66-v91j/cu66_inverse_stream_v91j.sv` | [fpga/experiments/cu66-v106-composed/lut-storage/cu66_inverse_stream_v91j.sv](../../fpga/experiments/cu66-v106-composed/lut-storage/cu66_inverse_stream_v91j.sv) | `e013c3c132677c844ab02150e1477063e0ae59b89c978b20c20d68489447b326` |
| local-guards-scratch-area | `fpga/experiments/cu66-v91k/cs88_coefficients_v91k.sv` | [fpga/experiments/cu66-v106-producer-cache/cs88_coefficients_v91k.sv](../../fpga/experiments/cu66-v106-producer-cache/cs88_coefficients_v91k.sv) | `396b0d9ac27a6bea6f1694252b18078ed5ac42351201b6c7e201c2091736061d` |
| local-guards-scratch-area | `fpga/experiments/cu66-v91k/cu66_reconstruct_stream_v91k.sv` | [fpga/experiments/cu66-v104-control/cu66_reconstruct_stream_v91k.sv](../../fpga/experiments/cu66-v104-control/cu66_reconstruct_stream_v91k.sv) | `445e1b96fc931cf1a8a6cabbf7f111a199197264eb8ab35f9dde871ab010ecb8` |
| lut | `fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv` | [fpga/experiments/cu66-v105-admission/cs88_admission_v91i2a.sv](../../fpga/experiments/cu66-v105-admission/cs88_admission_v91i2a.sv) | `a03a88ec25a1792b5ba5c970bb47cb66ae8b5277ec1f2680caba460e61af1d4a` |
| lut | `fpga/experiments/cu66-v91i2b/cs88_pipeline_v91i2b.sv` | [fpga/experiments/cu66-v106-math/lut/cs88_pipeline_v91i2b.sv](../../fpga/experiments/cu66-v106-math/lut/cs88_pipeline_v91i2b.sv) | `23dffb1f774049a18bc374e40b3ff36b8ac54e0d157646a3a865ce419cc2ddcf` |
| lut | `fpga/experiments/cu66-v91j/cu66_inverse_stream_v91j.sv` | [fpga/experiments/cu66-v106-math/lut/cu66_inverse_stream_v91j.sv](../../fpga/experiments/cu66-v106-math/lut/cu66_inverse_stream_v91j.sv) | `d8a3fc8b11cbbb61df864fc55ba44242c11094d50f27d33346cbb467bec2ffe2` |
| lut | `fpga/experiments/cu66-v91k/cs88_coefficients_v91k.sv` | [fpga/experiments/cu66-v106-math/lut/cs88_coefficients_v91k.sv](../../fpga/experiments/cu66-v106-math/lut/cs88_coefficients_v91k.sv) | `df0de544f56df7630850dbf20b388d4222291f885768761db7e989e9b7180f45` |
| lut | `fpga/experiments/cu66-v91k/cu66_reconstruct_stream_v91k.sv` | [fpga/experiments/cu66-v104-control/cu66_reconstruct_stream_v91k.sv](../../fpga/experiments/cu66-v104-control/cu66_reconstruct_stream_v91k.sv) | `445e1b96fc931cf1a8a6cabbf7f111a199197264eb8ab35f9dde871ab010ecb8` |
| lut-plan | `fpga/experiments/cu66-v91g2/packed_scratch_v91g2.sv` | [fpga/experiments/cu66-v106-plan/packed_scratch_v91g2.sv](../../fpga/experiments/cu66-v106-plan/packed_scratch_v91g2.sv) | `c46f01765b79bd35929183d8475287c2b71e93c289371f0e3f212b320b175e48` |
| lut-plan | `fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv` | [fpga/experiments/cu66-v105-admission/cs88_admission_v91i2a.sv](../../fpga/experiments/cu66-v105-admission/cs88_admission_v91i2a.sv) | `a03a88ec25a1792b5ba5c970bb47cb66ae8b5277ec1f2680caba460e61af1d4a` |
| lut-plan | `fpga/experiments/cu66-v91i2b/cs88_pipeline_v91i2b.sv` | [fpga/experiments/cu66-v106-math/lut/cs88_pipeline_v91i2b.sv](../../fpga/experiments/cu66-v106-math/lut/cs88_pipeline_v91i2b.sv) | `23dffb1f774049a18bc374e40b3ff36b8ac54e0d157646a3a865ce419cc2ddcf` |
| lut-plan | `fpga/experiments/cu66-v91j/cu66_inverse_stream_v91j.sv` | [fpga/experiments/cu66-v106-math/lut/cu66_inverse_stream_v91j.sv](../../fpga/experiments/cu66-v106-math/lut/cu66_inverse_stream_v91j.sv) | `d8a3fc8b11cbbb61df864fc55ba44242c11094d50f27d33346cbb467bec2ffe2` |
| lut-plan | `fpga/experiments/cu66-v91k/cs88_coefficients_v91k.sv` | [fpga/experiments/cu66-v106-math/lut/cs88_coefficients_v91k.sv](../../fpga/experiments/cu66-v106-math/lut/cs88_coefficients_v91k.sv) | `df0de544f56df7630850dbf20b388d4222291f885768761db7e989e9b7180f45` |
| lut-plan | `fpga/experiments/cu66-v91k/cu66_reconstruct_stream_v91k.sv` | [fpga/experiments/cu66-v104-control/cu66_reconstruct_stream_v91k.sv](../../fpga/experiments/cu66-v104-control/cu66_reconstruct_stream_v91k.sv) | `445e1b96fc931cf1a8a6cabbf7f111a199197264eb8ab35f9dde871ab010ecb8` |
| lut-storage | `fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv` | [fpga/experiments/cu66-v105-admission/cs88_admission_v91i2a.sv](../../fpga/experiments/cu66-v105-admission/cs88_admission_v91i2a.sv) | `a03a88ec25a1792b5ba5c970bb47cb66ae8b5277ec1f2680caba460e61af1d4a` |
| lut-storage | `fpga/experiments/cu66-v91i2b/cs88_pipeline_v91i2b.sv` | [fpga/experiments/cu66-v106-math/lut/cs88_pipeline_v91i2b.sv](../../fpga/experiments/cu66-v106-math/lut/cs88_pipeline_v91i2b.sv) | `23dffb1f774049a18bc374e40b3ff36b8ac54e0d157646a3a865ce419cc2ddcf` |
| lut-storage | `fpga/experiments/cu66-v91j/cu66_inverse_stream_v91j.sv` | [fpga/experiments/cu66-v106-composed/lut-storage/cu66_inverse_stream_v91j.sv](../../fpga/experiments/cu66-v106-composed/lut-storage/cu66_inverse_stream_v91j.sv) | `e013c3c132677c844ab02150e1477063e0ae59b89c978b20c20d68489447b326` |
| lut-storage | `fpga/experiments/cu66-v91k/cs88_coefficients_v91k.sv` | [fpga/experiments/cu66-v106-math/lut/cs88_coefficients_v91k.sv](../../fpga/experiments/cu66-v106-math/lut/cs88_coefficients_v91k.sv) | `df0de544f56df7630850dbf20b388d4222291f885768761db7e989e9b7180f45` |
| lut-storage | `fpga/experiments/cu66-v91k/cu66_reconstruct_stream_v91k.sv` | [fpga/experiments/cu66-v104-control/cu66_reconstruct_stream_v91k.sv](../../fpga/experiments/cu66-v104-control/cu66_reconstruct_stream_v91k.sv) | `445e1b96fc931cf1a8a6cabbf7f111a199197264eb8ab35f9dde871ab010ecb8` |
| lut-storage-memory | `fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv` | [fpga/experiments/cu66-v105-composed/cs88_admission_v91i2a.sv](../../fpga/experiments/cu66-v105-composed/cs88_admission_v91i2a.sv) | `dfc0784e7a61e92791391b2bf68323dcb459b11f3e1a69366fbaa9a96d575b0b` |
| lut-storage-memory | `fpga/experiments/cu66-v91i2b/cs88_pipeline_v91i2b.sv` | [fpga/experiments/cu66-v106-math/lut/cs88_pipeline_v91i2b.sv](../../fpga/experiments/cu66-v106-math/lut/cs88_pipeline_v91i2b.sv) | `23dffb1f774049a18bc374e40b3ff36b8ac54e0d157646a3a865ce419cc2ddcf` |
| lut-storage-memory | `fpga/experiments/cu66-v91j/cu66_inverse_stream_v91j.sv` | [fpga/experiments/cu66-v106-composed/lut-storage/cu66_inverse_stream_v91j.sv](../../fpga/experiments/cu66-v106-composed/lut-storage/cu66_inverse_stream_v91j.sv) | `e013c3c132677c844ab02150e1477063e0ae59b89c978b20c20d68489447b326` |
| lut-storage-memory | `fpga/experiments/cu66-v91k/cs88_coefficients_v91k.sv` | [fpga/experiments/cu66-v106-math/lut/cs88_coefficients_v91k.sv](../../fpga/experiments/cu66-v106-math/lut/cs88_coefficients_v91k.sv) | `df0de544f56df7630850dbf20b388d4222291f885768761db7e989e9b7180f45` |
| lut-storage-memory | `fpga/experiments/cu66-v91k/cu66_reconstruct_stream_v91k.sv` | [fpga/experiments/cu66-v104-control/cu66_reconstruct_stream_v91k.sv](../../fpga/experiments/cu66-v104-control/cu66_reconstruct_stream_v91k.sv) | `445e1b96fc931cf1a8a6cabbf7f111a199197264eb8ab35f9dde871ab010ecb8` |
| lut-storage-plan | `fpga/experiments/cu66-v91g2/packed_scratch_v91g2.sv` | [fpga/experiments/cu66-v106-plan/packed_scratch_v91g2.sv](../../fpga/experiments/cu66-v106-plan/packed_scratch_v91g2.sv) | `c46f01765b79bd35929183d8475287c2b71e93c289371f0e3f212b320b175e48` |
| lut-storage-plan | `fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv` | [fpga/experiments/cu66-v105-admission/cs88_admission_v91i2a.sv](../../fpga/experiments/cu66-v105-admission/cs88_admission_v91i2a.sv) | `a03a88ec25a1792b5ba5c970bb47cb66ae8b5277ec1f2680caba460e61af1d4a` |
| lut-storage-plan | `fpga/experiments/cu66-v91i2b/cs88_pipeline_v91i2b.sv` | [fpga/experiments/cu66-v106-math/lut/cs88_pipeline_v91i2b.sv](../../fpga/experiments/cu66-v106-math/lut/cs88_pipeline_v91i2b.sv) | `23dffb1f774049a18bc374e40b3ff36b8ac54e0d157646a3a865ce419cc2ddcf` |
| lut-storage-plan | `fpga/experiments/cu66-v91j/cu66_inverse_stream_v91j.sv` | [fpga/experiments/cu66-v106-composed/lut-storage/cu66_inverse_stream_v91j.sv](../../fpga/experiments/cu66-v106-composed/lut-storage/cu66_inverse_stream_v91j.sv) | `e013c3c132677c844ab02150e1477063e0ae59b89c978b20c20d68489447b326` |
| lut-storage-plan | `fpga/experiments/cu66-v91k/cs88_coefficients_v91k.sv` | [fpga/experiments/cu66-v106-math/lut/cs88_coefficients_v91k.sv](../../fpga/experiments/cu66-v106-math/lut/cs88_coefficients_v91k.sv) | `df0de544f56df7630850dbf20b388d4222291f885768761db7e989e9b7180f45` |
| lut-storage-plan | `fpga/experiments/cu66-v91k/cu66_reconstruct_stream_v91k.sv` | [fpga/experiments/cu66-v104-control/cu66_reconstruct_stream_v91k.sv](../../fpga/experiments/cu66-v104-control/cu66_reconstruct_stream_v91k.sv) | `445e1b96fc931cf1a8a6cabbf7f111a199197264eb8ab35f9dde871ab010ecb8` |
| lut-storage-plan-context | `fpga/experiments/cu66-v91b/br88_context.sv` | [fpga/experiments/cu66-v106-context/br88_context.sv](../../fpga/experiments/cu66-v106-context/br88_context.sv) | `9cb6337098d36adfbe4ef2dc073fc30a6dea17eaa4d57322fa4e725b8cce5277` |
| lut-storage-plan-context | `fpga/experiments/cu66-v91g2/packed_scratch_v91g2.sv` | [fpga/experiments/cu66-v106-plan/packed_scratch_v91g2.sv](../../fpga/experiments/cu66-v106-plan/packed_scratch_v91g2.sv) | `c46f01765b79bd35929183d8475287c2b71e93c289371f0e3f212b320b175e48` |
| lut-storage-plan-context | `fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv` | [fpga/experiments/cu66-v105-admission/cs88_admission_v91i2a.sv](../../fpga/experiments/cu66-v105-admission/cs88_admission_v91i2a.sv) | `a03a88ec25a1792b5ba5c970bb47cb66ae8b5277ec1f2680caba460e61af1d4a` |
| lut-storage-plan-context | `fpga/experiments/cu66-v91i2b/cs88_pipeline_v91i2b.sv` | [fpga/experiments/cu66-v106-math/lut/cs88_pipeline_v91i2b.sv](../../fpga/experiments/cu66-v106-math/lut/cs88_pipeline_v91i2b.sv) | `23dffb1f774049a18bc374e40b3ff36b8ac54e0d157646a3a865ce419cc2ddcf` |
| lut-storage-plan-context | `fpga/experiments/cu66-v91j/cu66_inverse_stream_v91j.sv` | [fpga/experiments/cu66-v106-composed/lut-storage/cu66_inverse_stream_v91j.sv](../../fpga/experiments/cu66-v106-composed/lut-storage/cu66_inverse_stream_v91j.sv) | `e013c3c132677c844ab02150e1477063e0ae59b89c978b20c20d68489447b326` |
| lut-storage-plan-context | `fpga/experiments/cu66-v91k/cs88_coefficients_v91k.sv` | [fpga/experiments/cu66-v106-math/lut/cs88_coefficients_v91k.sv](../../fpga/experiments/cu66-v106-math/lut/cs88_coefficients_v91k.sv) | `df0de544f56df7630850dbf20b388d4222291f885768761db7e989e9b7180f45` |
| lut-storage-plan-context | `fpga/experiments/cu66-v91k/cu66_reconstruct_stream_v91k.sv` | [fpga/experiments/cu66-v104-control/cu66_reconstruct_stream_v91k.sv](../../fpga/experiments/cu66-v104-control/cu66_reconstruct_stream_v91k.sv) | `445e1b96fc931cf1a8a6cabbf7f111a199197264eb8ab35f9dde871ab010ecb8` |
| memory | `fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv` | [fpga/experiments/cu66-v105-composed/cs88_admission_v91i2a.sv](../../fpga/experiments/cu66-v105-composed/cs88_admission_v91i2a.sv) | `dfc0784e7a61e92791391b2bf68323dcb459b11f3e1a69366fbaa9a96d575b0b` |
| memory | `fpga/experiments/cu66-v91k/cu66_reconstruct_stream_v91k.sv` | [fpga/experiments/cu66-v104-control/cu66_reconstruct_stream_v91k.sv](../../fpga/experiments/cu66-v104-control/cu66_reconstruct_stream_v91k.sv) | `445e1b96fc931cf1a8a6cabbf7f111a199197264eb8ab35f9dde871ab010ecb8` |
| narrow | `fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv` | [fpga/experiments/cu66-v105-admission/cs88_admission_v91i2a.sv](../../fpga/experiments/cu66-v105-admission/cs88_admission_v91i2a.sv) | `a03a88ec25a1792b5ba5c970bb47cb66ae8b5277ec1f2680caba460e61af1d4a` |
| narrow | `fpga/experiments/cu66-v91i2b/cs88_pipeline_v91i2b.sv` | [fpga/experiments/cu66-v106-math/narrow/cs88_pipeline_v91i2b.sv](../../fpga/experiments/cu66-v106-math/narrow/cs88_pipeline_v91i2b.sv) | `e1b364f4296cb697b08384846860a00cb1778103f145aa080a32087db66c6b32` |
| narrow | `fpga/experiments/cu66-v91j/cu66_inverse_stream_v91j.sv` | [fpga/experiments/cu66-v106-math/narrow/cu66_inverse_stream_v91j.sv](../../fpga/experiments/cu66-v106-math/narrow/cu66_inverse_stream_v91j.sv) | `4d765060d2764d7e230974ee0d57f34116514fd72ec853f3eb9e9a5ad175dcd8` |
| narrow | `fpga/experiments/cu66-v91k/cs88_coefficients_v91k.sv` | [fpga/experiments/cu66-v106-math/narrow/cs88_coefficients_v91k.sv](../../fpga/experiments/cu66-v106-math/narrow/cs88_coefficients_v91k.sv) | `41c44eda4021abbaf817d164fd5eb993607616ec177ef4bfeaccd2cb189d2029` |
| narrow | `fpga/experiments/cu66-v91k/cu66_reconstruct_stream_v91k.sv` | [fpga/experiments/cu66-v104-control/cu66_reconstruct_stream_v91k.sv](../../fpga/experiments/cu66-v104-control/cu66_reconstruct_stream_v91k.sv) | `445e1b96fc931cf1a8a6cabbf7f111a199197264eb8ab35f9dde871ab010ecb8` |
| storage | `fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv` | [fpga/experiments/cu66-v105-admission/cs88_admission_v91i2a.sv](../../fpga/experiments/cu66-v105-admission/cs88_admission_v91i2a.sv) | `a03a88ec25a1792b5ba5c970bb47cb66ae8b5277ec1f2680caba460e61af1d4a` |
| storage | `fpga/experiments/cu66-v91j/cu66_inverse_stream_v91j.sv` | [fpga/experiments/cu66-v106-locality/cu66_inverse_stream_v91j.sv](../../fpga/experiments/cu66-v106-locality/cu66_inverse_stream_v91j.sv) | `683e4fda539cd0149c6a88dbb2f33e941dde1269be1483cc2333e1ed9ef2f599` |
| storage | `fpga/experiments/cu66-v91k/cu66_reconstruct_stream_v91k.sv` | [fpga/experiments/cu66-v104-control/cu66_reconstruct_stream_v91k.sv](../../fpga/experiments/cu66-v104-control/cu66_reconstruct_stream_v91k.sv) | `445e1b96fc931cf1a8a6cabbf7f111a199197264eb8ab35f9dde871ab010ecb8` |

For integration, use only the selected override set in [selection.json](../../experiments/python-gamebub-v106/selection.json) and compile one production definition per module. Verification adapters are not integration sources. Parent clock/I/O/CDC constraints, actual external-memory arbitration, full-system integration, hardware 30 fps and complete under-10-ms decoding remain open; none follows from these OOC tables.
