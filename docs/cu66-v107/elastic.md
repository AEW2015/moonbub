# V107 registered coefficient boundary

This candidate adds one ready/valid register between the scratch coefficient producer and the inverse transform. It targets the actual resumed-sixth routed path from scratch `tile_emit_index_reg[0]` through tile-value selection and inverse validation to coefficient-bank word enable: 14.139 ns data delay, 3.018 ns logic /11.121 ns routing,12 logic levels, WNS −4.428 ns at10 ns. Root's subsequent Rice/quant/value-predicate implementation is a separate measured control.

The register carries the entire130-bit coefficient ownership tuple: epoch32, child_epoch32, plane2, qscale2, block16, tile13, qcell11, index6 and signed value16. It transports arbitrary bit patterns unchanged; inverse metadata, ordering, range and token checks stay in the inverse module with their original priority. Scratch payload generation is unchanged. The staged payload is registered independently of inverse ready/validation, cutting the scratch selector from inverse bank-write validation/enable.

There is a minimum one-clock latency from producer acceptance to inverse acceptance. When full and inverse-ready, the old token can retire while a new token replaces it, sustaining one coefficient per clock. Backpressure preserves the complete held tuple. Public raw coefficient payload/valid/done debug signals remain connected to their original producer; public coefficient_ready now reports stage capacity. Inverse counters describe downstream acceptance, while producer counters describe upstream acceptance, so their edges and related timestamps can differ by the declared stage occupancy. No exact-cycle old/new pipeline equivalence is claimed.

## End fence and cancellation

The inspected producer's coefficient_done is sticky: it follows the last coefficient acceptance, WAIT_DONE and NEXT_PLANE processing. Nevertheless the stage captures a pulse as well as a held done level, and publishes sticky output_done only after all accepted tokens retire. Done with a currently stalled final input offer remembers that offer's ownership and allows it to enter when capacity returns before closing input. Done with an accepted final offer closes input immediately after that acceptance. A done fence with no current offer closes input immediately; later offers belong to no accepted transaction and remain backpressured until a new start. Tests refer to done before/with/after final *delivery*, not to unannounced future tokens after an end fence.

Reset, accepted start and cancel discard the slot and fence. Reset/cancel override a simultaneous start, matching top-level accepted-start gating. The stage also flushes on inverse_error, because a failed inverse stops ready and a retained slot would otherwise block retry forever. The inverse-error flush is guarded by `!accepted_start` so a prior sticky fault does not cancel the newly accepted frame. Coefficient/reconstruction faults and abort follow the existing inverse_cancel priority.

Top busy includes an occupied slot/final offer; start/cache gating excludes it. A completed sticky done fence alone does not hold busy or prevent a new start. The inverse input_done receives only the drained staged fence; top combined done still requires raw coefficient_done, inverse_done, reconstruct_done and zero error. The inverse's first/last-word ownership and every original fault predicate remain unchanged, applied to the ordered registered stream.

## Source recipe and integration obligations

[edit-recipe.json](../../fpga/experiments/cu66-v107-elastic/edit-recipe.json) records exact reverse-offset edits against canonical `fpga/experiments/cu66-v91k/cs88_pipeline_v91k.sv`, unchanged public header identity, replacement top hash and the additional module/hash. The new RTL source `cu66_coefficient_elastic.sv` must be added explicitly: the historical17-file closure (16 RTL files plus one include header) becomes18 files (17 RTL files plus the header). Merely overriding the top without adding the stage is incomplete.

The parent may compose its existing independent inverse/Rice/quant overrides with this canonical top replacement. Parent integration must compare ordered accepted coefficient tuples, ordered residual/pixel payloads and final errors/receipts, with cancellation epochs and accepted-start ownership. Counter values must obey their local handshakes; cycle equality and identical inter-stage transient counts are not appropriate for this declared latency change. The source list and extra source must be retained in receipts and vendor inputs.

The unit harness is independent and latency-aware: an explicit one-token queue and per-frame transcript compare the complete tuple at output, enforce no bypass, conserve accepted/retired/discarded owners, check done after final delivery, hold behavior, occupancy and producer backpressure. It includes all seven reset/start/cancel masks across empty/full/stalled-final/done states, arbitrary full-width metadata/value bits (including invalid payloads), random stalls and same-edge replacement; zero/one/63/64/65/128-word boundaries; done pulse/sticky timing before/with/after final delivery; cancellation and recovery. Strict behavioral Verilator uses enabled assertions, no warning suppression, C++ `-Wall -Wextra -Werror`, bounded command and edge watchdogs.

## Actual unit result

**PASS**, Verilator5.020 with enabled assertions, strict `-Wall`, no warning suppression, C++ warnings as errors. The first compile and all three seeds passed.

| Seed | Clock edges | Accepted | Retired | Flushed accepted owners | Same-edge replacements | Held-output edges | Stalled final fences |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 107601 | 167,780 | 95,225 | 95,211 | 14 | 75,254 | 33,257 | 84 |
| 107602 | 168,990 | 95,641 | 95,627 | 14 | 75,615 | 34,039 | 76 |
| 107603 | 172,030 | 97,636 | 97,622 | 14 | 77,186 | 34,375 | 79 |

Total: **508,800 actual edges**,288,502 accepted tuples,288,460 retired tuples and42 explicitly discarded accepted owners. Every seed tests1,269 flush edges and retained done for9,696 edges. No token is lost, duplicated or reordered; cancellation discards are counted separately. Payload correctness uses the complete130-bit tuple and independently generated per-frame expected transcripts.

The [selection](../../experiments/python-gamebub-v107/elastic/results.json) pins [receipt](../../experiments/python-gamebub-v107/elastic/attempts/20261108T035430875362Z/receipt.json), SHA-256 `40544fe57834800d12db4fe7df29bfaae9f851585a846da09c10fb6a8e92fb30`. Source/tool/compile/binary snapshots and compressed handshake transcripts are retained. Stage SHA-256 is `28de630dc9266ff23302ecf96155e7b4135ee26b6140682483c219791b9b61e9`; canonical-top SHA-256 is `d9441f5a4600daf48cbb201cf731c42d724bf9f0c5609bf8b9249d683cf5e57d`. The [artifact audit](../../experiments/python-gamebub-v107/elastic/audit.json) checks all retained hashes, exact top recipe, unchanged header and accepted/retired/discarded conservation. Reproduce with `python3 scripts/cu66-v107/elastic/recipe.py`, serialized `python3 scripts/cu66-v107/elastic.py`, then `python3 scripts/cu66-v107/elastic/audit.py`.

For parent integration, observe `coefficient_boundary.full`, `done_pending`, `final_wait` and all `staged_*` wires. Count upstream accepts from raw coefficient_valid/ready, downstream accepts from staged_valid/ready, and discard exactly the old full bit on reset/accepted_start/coefficient_stage_cancel. The final_wait bit owns an unaccepted upstream offer, so it contributes no accepted-token discard. Per frame, upstream−downstream−discards equals full. On a successful completed frame, full=0 and upstream=downstream=inverse_count_inputs; preserve that equality. A bad token accepted downstream is still counted in inverse_count_inputs before fail; an extra queued token may be discarded by the resulting cancellation.

The same frozen stage/top now also pass the [actual complete canonical pipeline campaign](elastic-pipeline.md), including latency-aware tuple/fence/discard checks and both same-seed control comparisons. Physical route closure, CDC, hardware throughput and complete decode below10 ms remain separate gates.
