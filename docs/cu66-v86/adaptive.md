# V86 rate-only host selector

This separate experiment chooses the shortest complete CS86 packet for each source frame. It constructs all six qualified candidates: COPY with the old V2 map, COPY with the new group map, and all-visible residuals, each with 256-block and whole-plane chunk caps. Ties use the frozen `CONFIGS` order. No new decoder opcode, coefficient change, image-quality change, or original CU66 fallback is introduced.

Run `python3 scripts/cu66-v86/prototype_adaptive.py`. The experiment binds every candidate's actual packet SHA, byte count, map method, and component accounting to the previously qualified 2,742-packet run. The selected bytes pass through the same qualified native CS86 receiver in one mixed-variant history, followed immediately by an exact replay. Expected responses include complete coefficient, canonical, HUD, display, content-root and C2-seal parity. The 914 responses represent 457 new source frames and 457 idempotent replays, not 914 independent content frames.

Artifacts are retained under `experiments/python-gamebub-v86/adaptive/attempts/`, with `adaptive/results.json` identifying the selected run. Per-frame rows retain all six candidate hashes and sizes, selected responses, and replay responses. The report records configuration transitions and representative packet fixtures, source hashes and archive, qualified binary hash, commands, native stderr, and byte comparisons against each fixed CS86 configuration and original CU66.

The selected run `20261106T140824748437Z-23b07c06` passed all 2,742 candidate packet bindings and 457 new-packet plus 457 exact-replay native responses, including 72 configuration transitions. It chose the whole-plane cap for every source: 20 tied key frames used the first V2 configuration, 406 frames used the group map with COPY, and 31 used all-visible residuals. The selected total is **7,929,974 bytes** (maximum 44,833 bytes); all 457 packets fit the 49,152-byte compatibility limit.

| Fixed reference | Total bytes | Selector saves |
| --- | ---: | ---: |
| COPY group, whole-plane cap | 7,930,953 | 979 (0.01234%) |
| All-visible, whole-plane cap | 8,008,725 | 78,751 (0.98332%) |
| COPY group, cap 256 | 8,410,466 | 480,492 (5.71302%) |
| Original CU66 | 7,946,811 | 16,837 (0.21187%) |

The selector ties or improves every fixed CS86 configuration on every frame. Choosing all-visible residuals for 31 frames removes the fixed group profile's 31 per-frame regressions against the matched whole-plane all-visible control. The additional rate gain over the fixed group whole-plane configuration is small: only 979 bytes over this 457-frame corpus. Candidate construction and native verification took 17.7 seconds on the study host; that elapsed time is campaign bookkeeping, not real-time throughput or decoder latency.

This is a rate-only offline prototype. Every candidate packet is actually constructed, but its residual components were already encoded offline. This is not a live host-encoding benchmark, and an implementation would pay for candidate encoding and selection. The all-visible alternatives are outside the COPY-only standalone context model. No ESP32 transport, FPGA fit, clock, memory behavior, physical 30 fps, or validated integrated under-10-ms decode result follows from this experiment.
