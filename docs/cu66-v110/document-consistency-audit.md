# V110 documentation consistency audit

Static review of 41 V110 leaf Markdown files found 114 local relative links and no unresolved targets (source-line suffixes were normalized for filesystem checks). External primary URLs were not refetched. Root README and shared central plans were left untouched for root's final update after Default terminates.

## Claims matched to retained evidence

All six actual canonical compositions passed with 44 candidate case profiles and 42 directed checks each (22/21 per seed). Each reused the hash-bound actual V109 FETCH baseline; none recompiled or reran it.

| Composition | Receipt status | Candidate cases / directed checks | Seeds |
| --- | --- | ---: | ---: |
| busy | PASS_EXACT_V110_CANONICAL | 44/42 | 2 |
| fault | PASS_EXACT_V110_CANONICAL | 44/42 | 2 |
| combined | PASS_EXACT_V110_CANONICAL | 44/42 | 2 |
| dequant | PASS_EXACT_V110_CANONICAL | 44/42 | 2 |
| ready-rice | PASS_EXACT_V110_CANONICAL | 44/42 | 2 |
| prefix | PASS_EXACT_V110_CANONICAL | 44/42 | 2 |

The target remains 720×480 CS88 q16/all-BR88 with a 49,152-byte cap. The five original RuntimeOptimized fresh-RTL native routes are terminal and WNS-negative:

| Trial | WNS ns | TNS ns | Setup failures |
| --- | ---: | ---: | ---: |
| v110-combined-initial | -1.700 | -6860.993 | 12,612/88,660 |
| v110-combined-dequant | -4.845 | -23128.131 | 23,412/89,110 |
| v110-combined-ready-rice | -2.871 | -10185.816 | 16,322/89,672 |
| v110-fault-initial | -2.578 | -8838.627 | 13,862/87,829 |
| v110-combined-prefix | -1.654 | -3716.410 | 8,328/89,709 |

All five have zero routing errors, nonnegative hold/pulse slack and zero hold/pulse failures. Hardware 30 fps, complete validated decode below 10 ms, and full-custom-top qualification remain false in every receipt. The product gates separately require 1,800 distinct frames/60 s, then 18,000/600 s, and every qualified complete-decode latency strictly below 10 ms. Production integration remains open.

[`overlap-next.md`](overlap-next.md) is explicitly an unimplemented proposal and does not predict measured hardware FPS or latency.

## Items for root's final rewrite

- [`gamebub-v91-v110-development-plan.md`](../gamebub-v91-v110-development-plan.md) has a stale V110 checkpoint: it lists only three completed routes and says prefix/fault route outcomes are pending, though all five original RuntimeOptimized routes now have terminal receipts.
- [`default-method.md`](default-method.md) says no Default preflight/build/tool launch exists and preparation has not been invoked; parent coordination reports the Default build active.
- [`README.md`](README.md) has the current five-route Runtime table but describes Default as prepared/result pending. Refresh lifecycle status and the final comparison after the active Default trial terminates.
- Root README and shared central plans were intentionally not edited. The Default result is excluded from the five RuntimeOptimized route count until its receipt is terminal.

Machine-readable evidence pins: [`document-consistency.json`](../../experiments/python-gamebub-v110/audit/document-consistency.json).
