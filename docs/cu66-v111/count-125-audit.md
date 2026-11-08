# V111 Count-125 native route audit

Status: **PASS_V111_NATIVE_FINAL_AUDIT** for independent receipt and report consistency. The design result is a **125 MHz timing failure**, not a timing pass.

- Receipt: `experiments/python-gamebub-v111/native/20261108T183002986106Z/receipt.json` (SHA-256 `4844575267375152b0f91fa194589dfbcabec615b1d08961c089cb36f909822d`).
- The prepared Count source set is unchanged from the V110 Count control and was freshly synthesized from RTL, out of context, at 8 ns (125 MHz). The run used Vivado 2026.1, default synthesis by CLI omission, two threads/CPUs, 8 GiB memory and swap limits, and the 3600 s timeout.
- All 72 external report artifacts and 97 retained files rehashed successfully. All 18 prepared source snapshots, four recipe files, and five tool/driver pins match their recorded digests. The dispatch receipt and static preflight are pinned.
- Route completed; all 66,271 routable nets routed and zero routing errors. Timing report independently parses to WNS **−3.264 ns**, TNS **−40607.203 ns**, and **34,864 / 89,161** setup endpoints failing. Hold WHS is +0.080 ns with zero failures; pulse width WPWS is +2.750 ns with zero failures.
- Worst setup path: `coefficients/child/scratch/read_segment_reg[1]/C` → `coefficients/child/scratch/busy_owned_reg/D`, 11.211 ns data delay over 15 logic levels.
- The actual 100 MHz control was not remeasured. This is only a component out-of-context route; it does not qualify full custom-top I/O timing, bitstream, board hardware, or 30 FPS operation.

Machine-readable checks and selected report hashes: `experiments/python-gamebub-v111/audit/count-125-final.json`.
