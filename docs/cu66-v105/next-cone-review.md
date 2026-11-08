# V106 candidate review: placed coefficient-position validation cone

The V105 GEOMETRY **placed** worst path is a coefficient-position validation path into an inverse-transform coefficient RAM write enable. The immediate next experiment should target the still-original `quant_cell` evaluation and its guarded write-enable cone in the coefficient/inverse boundary. At the initial placed-stage review, this observation did not identify the final routed critical path. The retained GEOMETRY route update below now confirms the same class of cone for that variant; neither observation establishes a frequency or hardware throughput.

## Measured evidence and source binding

Report: `/home/lori/gamebub-build/cu66-v69/v105-geometry-20261107T235546691238Z-bc5cde/results/place-setup-paths.rpt`.
SHA-256: `6bf5e6bff66be3b8b3e4eee318c7ec7745c9f91461afb7c8ede7e0e07be2e23c`.
The report identifies Vivado 2026.1 build 6511674, `xc7a100tcsg324-1`, design `cs88_pipeline_v91k`, **Fully Placed**. Its 10 ns comparison clock supplies no board I/O timing relationship.

| Placed measurement | Value |
| --- | --- |
| Slack | −12.375 ns |
| Launch | `coefficients/mapped_tile_reg[2]/C` |
| Capture | `transform/coefficients_reg_0_1_408_408/DP/WE` |
| Data delay | 21.758 ns |
| Logic / interconnect contribution | 8.998 / 12.760 ns |
| Levels | 29, including 14 CARRY4 |

The first launch net has fanout 34. Intermediate net names include `quant_cell_return1[7]`, `quant_cell_return0[8]`, and `input_metadata_bad1`. The final write-control portion includes `transform/fill_bank_i_3_n_0` with fanout 74 and a write-enable net with fanout 32. Many reported endpoints are DP/SP write enables of neighboring coefficient words. These names support investigating positional validation and distributed write control. Synthesis can merge and rename logic, so they do not prove a one-to-one association between each carry and one source expression. Several interconnect entries are explicitly estimated at this stage.

The actual native hierarchy uses `cs88_coefficients_v91k`, not its earlier `cs88_pipeline_v91i2b` sibling. The relevant frozen files below match their external build snapshots byte-for-byte:

| Source | SHA-256 |
| --- | --- |
| `fpga/experiments/cu66-v91k/cs88_coefficients_v91k.sv` | `a394aaf3feda60919f082e6578170fa2b2490899b1e19eed650829b45c113fc7` |
| `fpga/experiments/cu66-v91k/cs88_pipeline_v91k.sv` | `a128717c65741aec03ef55adeddf86aed2149be20c45d1a85e1c9c1c301b42c3` |
| `fpga/experiments/cu66-v91j/cu66_inverse_stream_v91j.sv` | `277e4ea7018a9463c505be09112309de936e8b28b9aada7908994c087595dd08` |

The build's GEOMETRY override map changes admission to V105 and reconstruction to V104 control. It does not change these coefficient-producer or inverse-input validation functions. Earlier admission/reconstruction coordinate caches therefore do not eliminate this cone.

## Exact source semantics

In `cs88_coefficients_v91k.sv`:

- Lines 139–142 declare `tile_cursor`/`mapped_tile` as 13 bits, `mapped_cell` as 11 bits, scale as 2 bits, and `expected_block` as 16 bits. There is no 32-bit mapped-tile register to narrow.
- Lines 186–191 define plane counts and `quant_cell`. Its input tile is 13 bits but the Y expression explicitly promotes it to 32 bits before division/modulo by 90 and arithmetic.
- Lines 206–216 expose mapped tile/cell/scale and bind coefficient valid/ready to DISPATCH, matching child epoch and block ordinal. The lookup tile uses a global plane offset; lookup cell uses the local plane tile.
- Lines 225–238 arbitrate coefficient versus reconstruction lookups and retain the response owner. A cached coordinate must track the coefficient request, not a reconstruction response.
- Lines 312–324 clear mapped metadata on reset/abort. An accepted start resets cursor/plane/block/ownership but **retains mapped metadata until a later successful lookup**. Unqualified public outputs currently expose that retained value.
- Lines 339–356 validate entropy/child-epoch capacity, skip zero-residual planes, and initialize nonempty plane cursor/block ownership.
- Lines 369–376 bound the cursor before requesting metadata. On a qualified MAP_WAIT response, mode 2 captures tile/cell/scale and enters DISPATCH; every other mode increments the cursor and requests the next position.
- Lines 378–389 reject wrong child epoch/block, hold mapped metadata through all 64 coefficients and backpressure, advance only after the accepted index-63 coefficient, wait for child drain, and move to the next plane.

In `cs88_pipeline_v91k.sv`, lines 185–205 define accepted start and cross-block cancellation, and instantiate the inverse as `transform`. Lines 206–208 connect coefficient plane/tile/cell/block/index/value directly to inverse inputs. Lines 246–272 instantiate the producer as `coefficients` and bind its positional outputs. A sticky inverse error aborts the coefficient side once; a coefficient/reconstruction error cancels the inverse. Future metadata caches must follow these actual kill/accept signals.

In `cu66_inverse_stream_v91j.sv`:

- Lines 43–54 define two FREE/FILL/READY/ACTIVE coefficient banks, per-bank epoch/child/token/plane/scale/block/tile/cell, six-bit fill/emit indices, and a frame-local token counter.
- Lines 65–67 repeat the 13-bit-input, explicitly 32-bit Y `quant_cell` expression.
- Lines 73–82 define kill, input-ready, geometric validity, and immutable metadata during FILL. The geometric check is currently repeated on every accepted coefficient.
- Lines 83–91 establish error priority: partial-tile `input_done` (4), index order (1), metadata (2), scale/value bounds (3), then token overflow (7). Metadata is fault-relevant only when `in_valid && in_ready`.
- Lines 124–148 give reset/start/cancel priority, clear bank owners, and suppress normal assembly whenever `input_fault != 0`.
- Lines 150–163 write the selected coefficient only on an accepted, fault-free input, capture owner metadata/token on index 0, and close the bank at index 63. This same-cycle write protection is the reported endpoint obligation.
- Lines 165–189 independently manage the math bank, verify arithmetic response tokens, hold output through stalls, release ownership only after accepted output index 63, and declare completion only after all owners drain.

## V106 experiments and proof obligations

1. **Begin with a bounded combinational `quant_cell` candidate, not a new pipeline stage.** The actual input domain is only 13 bits. An independently proved 13-bit arithmetic implementation can retain the current function signature/result, fault priority, handshake, and RAM write timing. For all tile inputs 0…8191, `tile/90 <= 91`, the row-pair product is at most 2025, and the final pre-truncation sum is at most 2069; a 13-bit intermediate holds the entire original integer result before the existing 11-bit return truncation. This is a mathematical width bound, not evidence of a speedup. Measure inverse-only, producer-only, and both substitutions separately because synthesis may share the repeated evaluation.
2. **Treat owner-based reuse as a separate, conditional experiment.** Within a FILL bank, the first accepted coefficient has already passed geometry, and later beats must exactly match its stored tile/cell/plane and other owner metadata. This offers a potential repeated-check simplification, but it must preserve malformed-input rejection and error priority. The first-beat geometric check still exists and may remain the worst path. A producer-generated trusted flag or removing inverse validation would change the standalone inverse contract unless separately specified and proved; do not make that assumption.
3. **Consider a producer coordinate cache only with explicit request ownership.** Initialize it for a nonempty PREP_PLANE/ALLOCATE owner, advance it on both nonresidual MAP_WAIT skips and completed residual tiles, and hold it through lookup waits, refill stalls, all coefficient beats, and downstream backpressure. Reset/abort/accepted-start/error must invalidate its owner. Retained public mapped outputs must stay unchanged on invalid cycles. Prove the MAP_REQ boundary/sentinel behavior before using a narrowed value. Admission's cache is already invalidated at MODE_END and belongs to a different lifetime; it cannot supply this proof.
4. **Measure write-control locality after simplifying the evaluator.** The placed path has a larger estimated interconnect contribution than logic contribution and ends in a replicated RAM write-enable network. Local equivalent enables or structural bank partitioning may merit a later isolated experiment. Preserve both banks' state/metadata/data writes, fault-before-write behavior, simultaneous assembly/math ownership, RAM inference and counters. A registered enable or skid stage adds a timing boundary and changes cancellation/latency semantics; it requires an explicit new contract rather than an unannounced timing fix.

Do not narrow 13-bit public tile inputs, 16-bit block ordinals, epochs, tokens or parser state merely from nominal image dimensions. Arbitrary invalid inputs and sentinel/error behavior remain part of the current interface unless a revised boundary contract explicitly excludes them.

## Focused and integrated proof strategy

First exhaust the pure helper domain: all 4 plane values × all 8192 input tile values, comparing the unchanged 11-bit original return. If exploiting valid-input guards instead, prove the complete `input_metadata_bad` predicate, including plane 3 and out-of-range tiles, rather than claiming unrestricted function equivalence. Exercise matching and mismatching qcells, tile/row/pair boundaries, and sentinel tiles. Retain the full-width original function as a simulation oracle.

Next compare the complete original and candidate inverse modules under the same clocked stream. Existing `fpga/experiments/cu66-v91j/tb_inverse.cpp` supplies coefficient order, metadata mutation, partial completion, reset/cancel, arithmetic-token, two-bank/backpressure and retry checks, but its nominal geometry is largely tile 0; expand coverage before relying on it for this optimization. Cover all legal plane/tile cells, malformed tile/cell/plane values, every mutable owner field on every fill index, input/output stalls, simultaneous bank activities, `input_done` priority, overflow, and kill during each phase. Compare all outputs, error cycle, counters, bank writes, owner lifetimes and held tuples. A reachable-owner cache proof must be distinguished from an unrestricted combinational helper proof.

For producer changes, compare the complete `cs88_coefficients_v91k` and retained sibling behavior using real key/delta/hidden/copy/mixed packets, zero-residual planes, skipped positions, short/final planes, arbitration against reconstruction lookups, wrong/stale child epoch/block, reset/start/abort and all packet/refill/output stalls. Assert the local/global tile distinction, request/response owner, mapped-cell equality and stable output tuple through all 64 coefficients.

Then run fresh inverse and canonical reconstruction lanes with two identical baseline/candidate seeds, comparing coefficient traces, transformed residuals, canonical pixels, counters and exact cycle transcripts. Preserve V105's frozen source map while varying one targeted function/owner implementation at a time. Native comparison must retain the same part/tool/10 ns clock, source snapshots and phase-specific reports. Check RAM/DSP inference, capacity, methodology/DRC and full routed setup/hold/pulse/routing legality. Compare the **final routed** critical cone before selecting a V106 implementation; this placed report is a provisional direction only.

No RTL, constraints, recipes, receipts, builds or tests were changed or run for this review.


## Retained GEOMETRY final-route update

The [retained routed setup-path report](../../experiments/python-gamebub-v105/native/20261107T235546839098Z/reports/route-setup-paths.rpt) has SHA-256 `2ba4783898215eddddbe8fa662997171424f3889dc738c0cba320d9550239ae1`. It explicitly identifies **Design State: Routed** for the same GEOMETRY native build, part, tool and 10 ns comparison clock. Reading its first complete path confirms the same launch register and positional-validation/write-enable class of cone; its capture word differs from the placed report.

| Measurement | Placed | Routed GEOMETRY |
| --- | ---: | ---: |
| Slack | −12.375 ns | −13.124 ns |
| Data delay | 21.758 ns | 22.507 ns |
| Logic contribution | 8.998 ns | 8.977 ns |
| Interconnect contribution | 12.760 ns | 13.530 ns |
| Levels / CARRY4 | 29 / 14 | 30 / 14 |
| Capture coefficient word | `408_408/DP/WE` | `124_124/DP/WE` |

The routed path starts at `coefficients/mapped_tile_reg[2]/C` and ends at `transform/coefficients_reg_0_1_124_124/DP/WE`. It passes through named nets `quant_cell_return1[7]`, `quant_cell_return0[10]` and `input_metadata_bad1`, then the transform error/fill-bank logic and coefficient RAM write enable. Its launch, fill-bank and final WE nets retain fanouts 34, 74 and 32 respectively, now labeled routed. Interconnect accounts for 60.114% of the 22.507 ns data path. Relative to placement, the data path grows by 0.749 ns: logic decreases 0.021 ns and interconnect grows 0.770 ns. This strengthens the recommendation to measure both bounded metadata evaluation and write-control locality, with separate variants to attribute any change.

The [retained route-status report](../../experiments/python-gamebub-v105/native/20261107T235546839098Z/reports/route-status.rpt) records 69,998 routable nets, 69,998 fully routed nets and zero nets with routing errors. Completed routing is distinct from timing closure: the reported setup slack remains negative. It also does not establish board I/O timing, methodology/DRC/CDC signoff, FPS or complete decode latency.

This routed confirmation is specific to **V105 GEOMETRY**. COMBINED and LOCALITY were still running when this update was written; their changes can move the worst cone and must be assessed from their own final routed reports. The earlier placed evidence and source/owner obligations remain useful, but V106 selection should use all completed variant reports rather than treating GEOMETRY's path as universal.

## Completed joint-variant comparison

The final [stage-matched path analysis](../../experiments/python-gamebub-v105/path-analysis.json) also covers the completed COMBINED and LOCALITY routes. COMBINED's first/worst path runs from `coefficients/mapped_tile_reg[4]/C` to coefficient word `648_648/DP/WE`, with WNS −13.653 ns. LOCALITY's runs from `mapped_tile_reg[7]/C` to word `468_468/DP/WE`, with WNS −13.956 ns. Reading both first path blocks confirms the named `quant_cell_return` and `input_metadata_bad` cone before write control. The launch/capture bits and physical delays differ, while the same unchanged metadata-evaluation source remains relevant across these three measured variants.

GEOMETRY is the selected next-study point because it has the best routed setup slack of this matrix and lower total LUT/DSP use. The RAM template remains separately verified; compare GEOMETRY plus mode RAM without product prefetch before attributing its clock/area behavior to the full LOCALITY combination. This is a bounded single-run frontier, not exhaustive implementation or hardware qualification.
