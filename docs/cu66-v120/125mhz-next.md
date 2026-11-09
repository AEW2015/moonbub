# Continuing the 125 MHz implementation

The [2026-11-09 spatial literature review and proposed V121–V125 roadmap](../gamebub-v121-v125-spatial-literature-review.md)
connects these measured paths to elastic request stages, local memory banking,
validation overlap and ESP32 Wi-Fi/QSPI integration. Its reproducible analytical
budgets retain the strict latency and physical frame-rate gates; it does not
promote a new source composition or modify the qualified 100 MHz handoff.

Keep the remote 100 MHz handoff pinned while experimenting on a separate source composition. V120 A125 failed at −1.847 ns, initially dominated by admission validation. The completed B125 route improves that to −1.517 ns but still fails; its [independent mapping audit](B-native-initial-mapping.md) identifies refill address generation and admission replay readiness as the new global worst. Component timing closure, complete-parent timing, sustained hardware frame rate and validated decode latency are separate gates.

## Current bounded repair

Source B combines Source A's range prefix with the [admission header-total equality preparation](admission-match.md). It changes the measured header-total comparison cone while keeping every ordinary public cycle and first-fault priority. The address-writer and context-terminal prototypes are not selected into B.

Require the fresh focused proof, actual complete-component/transport decode, physical-debt/cancellation/retry proof and guarded byte/row parent before routing B at 8 ns. Keep the original recipe and clock-before-synthesis method. Compare WNS, TNS, failing endpoints, hold/pulse margins, internal coverage and routing, plus the actual retained equality register/carry path. A moved worst path or fewer carry cells is useful diagnostic evidence, not a timing pass. A positive result needs a separate fresh repeat of exactly that source/tool/core recipe.

All four functional proof stages passed. B's first 100 MHz route passed at +0.174 ns setup and +0.028 ns hold; its positive fresh repeat is a separate qualification gate. B125 finished at −1.517 ns setup, −3,931.934 ns TNS and 10,524 failing setup endpoints. Versus A125, TNS improves by 4,813.769 ns and failing endpoints decrease by 7,750. One predicate FDRE and three writer CARRY4 cells survive routing; the complete carry count remains 4,198. The old total and new predicate are absent only from the retained top-200 path samples, not proved absent from every failing path.

The next source experiment must remain separate from Source B: its 18 selected files are byte-identical to the hardware team's pinned `69c0f145` checkpoint. Qualification evidence and the eventual manifest do not require a decoder RTL change.

## Next changes, selected from the next actual route

1. **Refill address and replay readiness.** B125's worst path runs from queue `issued[1]` through `req_addr = offset + issued`, then the admission `replay_addr < size_bytes` check, to RAM `ENBWREN`. The 8.990 ns data path has five address-addition CARRY4 stages plus two readiness-comparison CARRY4 stages. Prototype an owned, prepared request address and bounds decision on existing ownership/accepted-request edges. Preserve literal full32 arithmetic, original caller eligibility/assertions, qualified addresses, first-fault behavior and immediate cancellation. Retain accepted read debt until its real response drains. Prove all request tuples and credit conservation against an independent scoreboard before selecting any timing trial; keeping an unqualified debug value unchanged must not leave its old adder in the physical request-control cone.
2. **RAW mode and scratch preparation.** B125's RAW-mode source-family worst is −1.462 ns, and B100's global worst is scratch `emit_bank` to scratch state through raw/prefetch control. Use the actual next routed cone to prepare local format/phase decisions or read-address ownership. Keep original coefficient-range, ordering, held-transfer and physical-cache checks. Do not infer that changing ingress bounds eliminated independent scratch validation.
3. **Context and kill controls.** B125's emitted and kill source-family worst slacks are −1.386/−1.357 ns. Revisit first-RUN position selection/parser arithmetic and kill-to-storage enables where causal reports support it. The unselected terminal-bit prototype addresses a narrower trailing-event subset. Keep immediate logical cancellation separate from accepted physical work that must drain; prepare phase-local payloads without resetting them unnecessarily. Further header caching or tile/active-cell write-port work needs a retained causal path before promotion. Preserve memory read-during-write semantics, coordinate/reference identity and single-write/drain ownership.
4. **Registered diagnostics and explicit pipeline stages.** Keep wide OOC debug buses internal in the production parent and snapshot diagnostic-only counters coherently with their epoch. Avoid feeding a large combinational status mux back into a live datapath. Functional error/revocation and ownership signals keep their required latency. If existing edges are insufficient, a separately declared next composition may add registered control or memory stages and a revised latency contract. Preserve accepted values/order, error priority, backpressure and cancellation with independent scoreboards. Keep the old exact-cycle control as a control; add and verify an explicit new latency model rather than silently weakening it. A small added pipeline delay may be preferable to retaining a failing 8 ns combinational cone.
5. **Complete-top measurement.** After component closure, route the actual board parent with clocks, CDC/reset, QSPI, SDRAM and scanout. Attach calibrated per-frame logs from the remote system before claiming hardware frequency, 30 fps or sub-10-ms decoding.

## Frame and latency budgets

The existing row fixtures require 1,145,104 fast and 1,553,197 bounded-stall cycles from final input byte to validated commit. Their public schedule is unchanged by the current timing repairs:

| Assumed complete-parent clock | Fast fixture | Bounded-stall fixture | Strict under-10-ms cycle limit |
| --- | ---: | ---: | ---: |
| 100 MHz | 11.45104 ms | 15.53197 ms | fewer than 1,000,000 |
| 125 MHz | 9.160832 ms | 12.425576 ms | fewer than 1,250,000 |

At 125 MHz, the fast fixture fits the arithmetic latency budget, but the stalled fixture still needs at least 303,198 fewer cycles to be strictly below 10 ms. At 100 MHz those reductions are at least 145,105 and 553,198 cycles. Clock closure alone cannot remove these service/cycle costs. Optimize measured memory stalls, row joining, validation overlap and reconstruction throughput while retaining finite ownership and complete validation.

These are conditional calculations. The complete parent has not been routed at either clock, physical service is not calibrated, and these recovery fixtures are not sustained distinct gameplay frames. A 30 fps source leaves 33.333 ms per frame for the complete real pipeline, including work outside this measurement fence.
