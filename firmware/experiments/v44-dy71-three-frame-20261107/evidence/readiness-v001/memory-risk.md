# V44 third-frame memory risk and selected repair

November 7, 2026. Offline model and actual native semantic tests only; not physical SRAM qualification.

## Historical baseline

The actual V43 serial readiness line reports free117524/largest37888 **after** native endpoint creation/socket setup. It is slightly different from the earlier117552 shorthand. Its final native live42408, arena peak92235, physical minimum16400 and final heap74828 are preserved historical observations, not guarantees for V44.

Original V44 host three-frame native peak was103484. The actual third HC70 wire is6034 bytes (not rounded6036); if these lifetimes coincide,117524-103484-6034 leaves8006, below the8192 reserve before allocator/SDK overhead. Simple peak addition alone would not prove coincidence, so an actual endpoint allocation-probe model was executed.

## Actual endpoint model

The isolated probe uses the real native endpoint and packets. Its free callback reports `baseline - native_arena_live - external_HC70_wire_bytes`, with the full wire counted during the native prepare call and dropped before later control calls. It preserves the8192 guard. It excludes malloc metadata/alignment, fragmentation, SDK traffic, Rust runtime/stack and target-vs-host container layout. Reported minimum is sampled by the native probe, not an exact physical or continuous post-allocation low-water measurement.

| Variant | Logical cap | Modeled baseline free | Result |
|---|---:|---:|---|
| Original native |106496|117524|Third frame cleanly refused; preparecode4, allocation failure1.|
| Original native control |106496|130000|Three prepares/commits;63360 words match independent HUD oracles; peak103484.|
| Selected repaired native |98304|117524|Three prepares/commits;63360 words match; peak92379; zero failures.|

The exact failure was HS33 patch3 mode9, requesting5760 bytes with live97724 and modeled free13766. Required free was13952 to preserve8192. This confirmed the risk was real within the stated host allocation model, rather than merely adding noncoincident peaks.

`decode_full_patch.reserve(pixels)`, reserving four Patch entries, and moving the unused `motion_prediction(mode1)` allocation after its early return did not remove this cohort's peak. Those changes were not selected or applied to production.

## Selected change and equality evidence

HS co-located/plain1 prediction (HS modes1/9) now borrows the immutable accepted reference words instead of making an identical prediction-vector copy. Accepted reference lifetime covers the whole decode; errors leave it retained. Motion plain2/3 still use the original owned prediction generation, and independent modes still do not read a prediction. Pixel/tag/transaction semantics and physical reserve remain unchanged.

Only this change was approved and applied to V44 `native/hud.hpp`; V43 is untouched. Before SHA6013fe8ef4506c419f291af12b268602b4f2acf066c537c3f8c99ba5a2c970e9; after SHAcd65e262b66efe5e5b70db685b8f6cc417d35c113cb34b902d23a49b6d77bd70. Parent restored the worker's original98304 cap after the exact-three-frame fit passed. Receipt: `native-fix-receipt.json`.

Fresh actual final native semantic regression decoded/committed **457 historical frames**, comparing **9,651,840 HUD words** against independent frozen per-frame hashes. It covers HS33 modes1/9,2/3/10/11, HS32 and HD25 variants. Three malformed HU header/body cases reject without candidate/accepted publication. This broader semantic test uses a1MiB host-only logical cap (maximum observed arena110730); it does **not** establish that all457 frames fit the target98304 budget.

The exact hardware trial remains the separately qualified original three packets. Final-source localhost `run02` exercised actual network_io, driver and native endpoint at98304, with3matching status2 replies,63360 actual words verified and allocator `[98304,42488,92379,15360,770,0]`. Fake-MMIO model ticks are not target CPU timing.

## Physical recommendation

The repair materially improves the fit model and allows the bounded three-frame trial to remain a useful controlled physical measurement. Keep114688/24576 admission and8192 per-allocation reserve unchanged. Fresh device heap/largest-block, stack high-water, native minimum-free, allocation failures and exact current images are still required. A clean reserve refusal must stop and retain ownership; never lower guards to force a success. No sustained streaming or120-second source capacity follows from this three-frame fit.

Evidence: `memory-model-results.json` with source pins/compile/run commands, `memory-{baseline,final}-*.log`, `native_corpus.cpp`, `native-corpus.tsv`, `native-corpus.log`, and final `run02/{RESULT.json,source-hashes.json,receiver.log,sender.jsonl}`.
