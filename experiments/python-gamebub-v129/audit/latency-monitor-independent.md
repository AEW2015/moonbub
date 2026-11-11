# Independent review of V129 latency monitor

The monitor is an opt-in, simulation-only observer. The reviewed run covers **one** row-write configuration, stalled finite-service profile 1, seed 116702, epoch 2. It does not qualify the other three cases of the full V129 parent suite, physical memory, hardware throughput, or decode latency. Its overlapping observations do not establish a stall cause or an additive speedup.

## Evidence and scope

- Monitored [receipt](../latency-monitor/full-parent/attempts/20261111T004718819050Z/receipt.json): SHA-256 `f94ac37c4dd47d63c8f64b2e5cece02baaef9e2d575ad0fbd69ef4829aa47888`; status `PASS_V129_MONITOR_ONLY_SELECTED_COMPONENT_ROW_ACK_C2_HUD_ABSTRACT_PUBLICATION`.
- [Monitor](../../../fpga/experiments/cu66-v129-observe/monitor.hpp): SHA-256 `b0ef3d0cf30fc1fed4e12af487f84c3190686e8ce4a09b088cc73d2a3878f7a8`.
- [Instrumented bench](../../../fpga/experiments/cu66-v129-observe/tb_keyframe.cpp): SHA-256 `6dc67e745ff57b40298f575c108a271f3006be0b1d3fb1a5329f4740563ef895`.
- [Monitor runner](../../../scripts/cu66-v129/latency-monitor/run_parent.py): SHA-256 `525eb17658b38389dc1425f0e96c35b71069a513fd727a99492033bacae1a7d6`.
- [V129 uninstrumented parent selector](../integrated-study/live-guard/results.json): SHA-256 `d042090fce73f3d0e44e45ca37dc023459db7aa41b022263b4c6226064932d62`.

All **98** receipt source hashes and **91** receipt artifact hashes matched the retained files. The selector's receipt hash matched; the single emitted monitor JSON record equaled the receipt's `monitor_record`. The generated bench differs from the frozen V117 bench by the monitor include, storage/reset, sampling, and reporting additions; no original bench guard was removed. The derived runner preserves the existing checks for its selected case but intentionally reduces execution to the single row/profile/seed above. Its retained checks include canonical and accepted byte comparisons, digest and seal validation, ownership and wrong-ACK drain/retry checks, and comparison to the pinned V128 case.

For an additional comparison, the monitored run's six terminal dictionaries (`live_case`, `fences`, `service`, `verdict`, `spatial_pipeline`, and `parent_guard`) matched the corresponding **uninstrumented V129** parent case. Decompressed event, accepted-output, and hash streams matched that case byte for byte. This is evidence that the monitor did not change the checked trace for this run; it does not establish equivalence for untested cases.

## Signal and window review

The actual `cs88_live_v91l.producer` instance is the selected `cs88_pipeline_v91k` RTL. Its hierarchical `staged_valid` and `staged_ready` connect the coefficient elastic output to the inverse input. Coefficient, residual, canonical-output, write/hash-delivery, candidate-request, and candidate-response pairs use the corresponding live-parent ports. The C++ bench samples after combinational evaluation and before the rising edge.

The monitor starts when parent `start && start_ready` is observed, excludes sampled edges with the bench's reset/abort/error kill condition, and stops sampling after the bench has observed commit. The reviewed output has **1,601,560 sampled pre-edges**. The separate start-to-commit timestamp subtraction is **1,601,561 cycles** (`1,807,172 - 205,611`); these are distinct boundary conventions. The last-outer-input-to-commit measurement is **1,553,197 cycles** for this simulated case.

The request/response signals and `candidate_pending` refer to the bench's **candidate-write finite-service model**. They do not include refill or reference-read traffic and are not measurements of a physical SDRAM controller. `candidate_pending` includes an outstanding write even when its response is valid. The seven-bit mask records stalls on the first six channels plus `candidate_pending`; response-channel stalls remain in the response handshake counts and are not a mask bit.

## Independently recomputed accounting

Each channel's `no valid`, `valid and not ready`, and `valid and ready` bins sum to 1,601,560. Every per-channel mask-bit marginal equals its independently reported held-valid count. The 128 mask bins and eight priority bins each sum to the same total; recomputing priority as the lowest set mask bit (or the empty-mask bin) reproduces every priority count. This priority is a reporting convention, not a causal ranking.

| Channel | No valid | Held valid | Accepted |
| --- | ---: | ---: | ---: |
| Coefficient | 460,297 | 641,679 | 499,584 |
| Staged inverse input | 460,297 | 641,679 | 499,584 |
| Residual | 484,635 | 617,341 | 499,584 |
| Canonical output | 429,159 | 654,001 | 518,400 |
| Write/hash delivery | 877,141 | 163,779 | 560,640 |
| Candidate-write request | 1,508,353 | 23,127 | 70,080 |
| Candidate-write response | 1,531,480 | 0 | 70,080 |

Summing the retained mask bins gives 1,120,705 samples with `candidate_pending`; 569,509 also have coefficient held valid, and 542,508 also have canonical output held valid. These overlaps are simultaneous observations, not proof that the candidate-write service caused either stall. No changes were made to the monitor, its receipt, or its recorded artifacts during this review.
