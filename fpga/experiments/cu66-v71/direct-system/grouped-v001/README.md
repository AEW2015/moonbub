# Isolated grouped-command scheduler

This candidate changes only the bridge scheduler in an archived copy of the qualified tile-major memory backend. Live/frozen memory, PHY, controller, map, codec and base display-owner files remain unchanged. Modules and ports retain their original names inside this isolated source selection; never compile both bridges together.

The nominal contended quota is eight accepted LCD commands followed by four accepted background commands, preserving a 2:1 command ratio. Background selection stays on its chosen client for the group when that client continues to supply requests; round-robin position advances so the next group can serve another background client. Canonical tile adapters can consequently issue their four BL8 operations without alternating physical rows after each operation.

Counters charge only `mem_req_valid && mem_req_ready`, including physical commands that subsequently drain after a client cancellation. Local invalid-request responses and scalar cache hits do not consume quota or refresh a reservation. Local responses retain the original per-port slots and cache-invalidation ordering; at most one local response precedes an eligible physical dispatch so an endless cache-hit/error stream cannot retain a background phase forever.

Group reservation bridges the actual client-completion gap with bounded grace: **18 clocks for LCD and four for background**. The prior bridge used a four-clock LCD lookahead. This grace increase is an explicit part of the grouping experiment; it can trade controller-idle cycles for fewer row switches. Missing requests, held responses and canceled clients let the reservation expire. There is no indefinite wait or physical-operation preemption. The accepted controller operation, refresh handling, masks, read assembly, actual write recovery fence and wrapper abort-drain paths are unchanged.

`qualification-components-v001.json` binds passing fast/slow actual pin-model component tests and a separate synthetic-controller fairness test. Each physical component passes 5,277 checks and 94 abort probes, including all 32 accepted read-beat and all 32 write-beat abort positions. The policy test passes 24,157 checks: exact continuous 8:4 physical sequences across all four clients, uncharged cache hits/errors, data/mask ownership and a held response that does not block other clients.

The first short component shows a real tradeoff, not a universal win: total cycles 81,301→82,200; its contended 480-word LCD transfer 2,256→1,976 clocks; worst LCD wait 39→76 and maximum auxiliary wait 83→563. The candidate records real IDLE-qualified reservation clocks. Its `*_expiry` registers count timer expiry with pending opponents even while another controller operation is busy; they must **not** be labeled actual idle-reservation expirations. No source is silently changed to correct that observer definition.

The first actual full KEY/P run passes complete canonical/HUD integrity, lost-COMMIT-ACK retry and actual LCD pixel scoring with **zero observed underruns or black lines**, versus the frozen base's 596. KEY cycles fall 2,093,762→2,049,238; P cycles rise 3,307,863→3,438,471 (about 3.95%). KEY ACT/PRE fall 21,346/21,652→8,493/8,800; P ACT/PRE fall 63,602/60,036→29,769/25,960. P serves more read bursts because it renders clean lines instead of skipping their data. Each frame still stores exactly 428,160 physical write beats; no RGB traffic is introduced.

Full-run reserved idle totals 449,276 clocks (300,693 LCD, 148,583 BG); maximum LCD/BG waits are 116/253 clocks. The P transaction is 34.38471 ms, not a 30-fps result. In addition, initial P work begins before the KEY's first vblank presentation, so it is not a steady-P throughput bound. Matched reference-copy and chronological KEY/P/P measurements must determine sustained usefulness. `qualification-full-v001.json` is a native functional fixture result, not physical cadence or hardware acceptance.

The matched chronological three-frame pair is now complete. Both runs retain the base display owner; the comparison asserts that the bridge is the only changed hardware module and the first two transactions reproduce the earlier runs.

| Transaction cycles | Base 2:1 interleaving | Grouped 8:4 |
|---|---:|---:|
| KEY | 2,093,762 | 2,049,238 |
| First P | 3,307,863 | 3,438,471 |
| Second P | 3,893,472 | 4,549,603 |
| Final underruns / black lines | 2,261 / 2,261 | 0 / 0 |

The grouped second P is approximately 16.85% longer, while it also performs more front read bursts (133,224 versus 110,904) and fewer ACT/PRE commands (45,304/39,405 versus 92,228/86,525). Zero missed lines has a real service cost, so the skipped-work baseline cannot be treated as equally useful throughput.

Both variants publish generations 1/2/3 at exactly the same native cycles: 3,073,366; 6,146,719; 10,756,748. Their first canvas pixels also match at 3,191,331; 6,264,684; 10,874,714. Thus this cohort has fresh-presentation intervals of 30.73353 ms and 46.10029 ms. The grouped run observes a complete clean 800-line raster for each generation; the base observes a clean raster only for the last generation after decoder load ends. These two P samples do not establish steady 30 fps. Stage-by-stage and complete-raster identity records are bound by `comparison-three-v001.json` and `qualification-three-v001.json`.

No hardware image, routed timing, CDC or physical playback is qualified by this directory. All original controls and failed attempts remain preserved.
