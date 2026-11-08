# FSM encoding: read-only follow-up assessment

Do not spend a global one-hot methodology trial on the current P6/P8 evidence. The requested option is supported, but the only reported sequential extracted FSM is the inverse arithmetic controller, whereas the worst measured paths are in ingress/context arithmetic and distributed control. Count's actual final result remains a separate gate; this review makes no prediction about it and changes no flow, policy or source.

AMD documents `synth_design -fsm_extraction one_hot`; the default `auto` selects encodings for identified FSMs independently. This changes an encoding option, not the Default synthesis directive, and does not mean every register named state becomes a recognized FSM. One-hot generally trades one register per state for simpler decode. AMD's generic speed guidance is not a routed-clock guarantee. [UG835 2026.1](https://docs.amd.com/r/en-US/ug835-vivado-tcl-commands/synth_design), [UG901 one-hot encoding](https://docs.amd.com/r/en-US/ug901-vivado-synthesis/One-Hot-State-Encoding).

Both actual final synthesis logs report exactly the same two inferred/encoded FSMs:

| Extracted register | States | Actual encoding | Nominal one-hot change |
| --- | ---: | --- | --- |
| `cu66_dequant.state` | 3 | one-hot, 3 bits | none |
| `cu66_inverse_stream_v91j.math_state` | 5 | sequential, 3 bits | 5 bits: +2 internal state FFs before optimization |

The second log explicitly maps M_IDLE/DQ_SEND/DQ_WAIT/IDCT_WAIT/EMIT to sequential codes; it is not merely using the original RTL constants. The inverse's reset/start/cancel branch and fail task all restore M_IDLE; its bank/token ownership and immediate kill/output fences remain integral to the controller. The dequant reset/abort returns IDLE and already has the proposed encoding. Recoding can alter output re-encoding, replication, control sets and routing, so +2 FFs is only a nominal storage calculation, not a full utilization prediction.

No extraction/encoding message is reported for context (10 states), synchronous ingress (14 plus saved `fetch_return`), scratch (30 plus saved `return_state`), producer (17), reconstruction (11), Rice (4), admission (33 plus saved returns), or IDCT (10). The source inventory and hashes are in the companion analysis. The legacy ingress is pruned by actual SYNC_STAGING=1. Wrapper/top, elastic/refill and small mode/scale/reconstruct helpers add no other reported extracted FSMs. A global option cannot be assumed to recode this entire inventory.

The actual worst-path evidence is distinct:

- P6 Default: WNS −1.199 ns, band→live address/bounds→ingress state, 15 levels, 11.072 ns data delay: 3.241 logic and 7.831 route (70.728% routing). Thirty-six of 50 reported paths launch from band.
- P8 composed Default: WNS −1.365 ns, band→context product/count validation→done, 12 levels, 11.358 ns data delay: 5.944 logic and 5.414 route. The DSP arc alone is 3.656 ns and three carry stages follow. Eight of 50 paths launch from band.

Neither report contains a math_state launch or named math_state cell. P8 does contain five math_bank→dequant paths; a different inverse state encoding could affect shared enables there, but the report does not establish a decode-depth saving. The 50-path sample cannot prove every inverse path passes or exclude all indirect state influence. Recoding the unrelated reported FSM does not directly remove the P6 address arithmetic, P8 DSP/count check, or the required cancel/drain fences. Reduced decode depth, if any, can be offset by changed placement/fanout/routing.

The P6 hierarchical utilization report records 35,089 LUTs, 35,369 FFs and 42 DSPs; P8 records 35,114 LUTs, 35,405 FFs and 42 DSPs, with the same 32 RAMB36/12 RAMB18. These are different source compositions, not measurements of an encoding option. No synthesis-time, memory, LUT or clock gain for one-hot has been measured.

The OOC interface exposes many numerical state/return/debug views and state-indexed counters. Ingress and scratch also assign state from saved return registers. These are plausible recognition/optimization constraints, not proven reasons for Vivado's choice. Reset availability alone is insufficient: the sources already specify reset or power-up states as AMD requires. Conversely, inverse math is publicly observable yet extracted, and IDCT lacks a raw-state port yet was not extracted. The evidence does not justify blaming debug exposure alone. [UG901 FSM registers](https://docs.amd.com/r/en-US/ug901-vivado-synthesis/FSM-Registers), [auto encoding](https://docs.amd.com/r/en-US/ug901-vivado-synthesis/Auto-State-Encoding).

Production-wrapper versus complete-parent observability classification remains open. Do not remove required operational/public debug, return or counter ports merely to induce extraction or claim clock closure. Per root's decision, finish the actual Count route and use its final source-bound path to guide a registered-control/latency contract if still needed. There is no approved one-hot trial or new budget in this note.

`experiments/python-gamebub-v110/fsm-method-analysis.json` pins both final receipts/logs, full paths, utilization reports and inspected sources. All 18 actual/current/snapshot sources for each route were checked. No DCP, Vivado, simulation or heavy job was run by this assessment.
