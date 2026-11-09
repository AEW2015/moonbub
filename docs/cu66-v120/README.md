# V120 decoder development and remote hardware handoff

Next research: [spatial architecture literature review and proposed V121–V125 plan](../gamebub-v121-v125-spatial-literature-review.md),
including 125 MHz control partitioning, latency/service budgets and the real
ESP32 Wi-Fi/QSPI endpoint work needed for 30 fps. These are proposed experiments;
the qualified Source B below remains unchanged.

Start with [remote hardware bring-up](remote-hardware-test.md). This is a source-and-evidence handoff for component integration on another Game Bub system; it is not a complete board bitstream or a production Sunshine/ESP32 update.

| Source | Change from V119 | Functional evidence | 100 MHz | 125 MHz |
| --- | --- | --- | --- | --- |
| A | Signed16 ingress range prefix | Focused, complete component/transport, peer and byte/row parent passed | Fails: −0.045 ns, one setup endpoint | Fails: −1.847 ns |
| B | A plus phase-local full35 admission total-equality bit | All four proof stages passed | Repeat-qualified: +0.174/+0.174 ns setup | Fails: -1.517 ns |
| V118 control | Previously published source | Published source-bound handoff | Repeat-qualified: +0.061 ns setup, +0.078 ns hold | Unqualified |

The [qualified 100 MHz handoff](handoff.md) supplies the manifest and exact export command. Its decoder RTL remains identical to `69c0f145`.

The machine-readable [results](../../experiments/python-gamebub-v120/results.json) retain measured source/clock identities and open milestones. A V120 handoff manifest is published only after the selected clock passes an initial fresh route and a separate fresh repeat. The [stable V118 handoff](../cu66-v118/handoff.md) remains available as a control; its qualification does not transfer to V120.

The [readiness explanation](hardware-test-readiness.md) distinguishes component qualification from board integration and sustained frame rate. The row-service fixtures still take 1,145,104/1,553,197 cycles from final input byte to validated commit, conditionally 11.45104/15.53197 ms at 100 MHz. Sustained hardware 30 fps and validated under-10-ms decoding remain open.

The separate [125 MHz work plan](125mhz-next.md) follows actual routed bottlenecks. Read the [A125 mapping](native125-mapping.md), [A100 mapping](native100-mapping.md) and [admission-repair results](admission-match-results.md) for supporting evidence. Address-writer and context-terminal prototypes remain unselected.

The [campaign plan](plan.md), [reproduction notes](reproduce.md) and [preserved failure index](../../experiments/python-gamebub-v120/orchestration/failures.json) describe the fixed method and its limits. No old source, assertion, timing constraint or negative result is replaced by a later positive result.
