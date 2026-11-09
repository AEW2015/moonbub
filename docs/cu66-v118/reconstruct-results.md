# V118 focused reconstruction results

The owned residual pipeline and four-beat canonical copy passed the established strict Verilator5.020 backend with two seeds,118311 and118312. This qualifies the standalone functional change; routed timing and full-parent performance are separate tests.

| Check | Seed118311 | Seed118312 |
| --- | ---: | ---: |
| Complete canonical frames |3|3|
| Exhaustive geometry inputs |32768|32768|
| Directed checks |56|56|
| Canonical bytes, including retry prefixes |1568063|1568063|
| Maximum logical tile owners |2|2|
| Held output tuple checks |264724|264497|
| Physical128-bit lane writes |98147|98160|
| Physical copied bits |12562816|12564480|
| Kill-at-copy cases, allfour beats × reset/cancel |8|8|
| Malformed residual pipeline cases |4|4|
| Deterministic unstalled key-frame cycles |596526|596526|
| Randomly stalled inter-frame cycles |714587|713755|

The independent bench checked every32-bit word of both512-bit canonical banks before and after every real edge: the armed128-bit lane must capture the engine's exact data and every other word must remain unchanged. The four lane counts sum exactly to physical write counts, and each write accounts for128 bits. Cancellation cases additionally retain an older stalled READY head, verify the selected private write on the kill edge, reject partial publication, and complete a clean retry.

Malformed owned tuples at indices0,7,61 and63 produced error4 on the third test edge, corresponding to acceptance E, validation E+1, fault/commit E+2. The committed-word count stopped at the invalid word's position, so malformed and younger accepted words did not commit. RTL assertions additionally checked ordered accepted/committed frontiers, final-word drain before math, and engine payload/ID stability during partial copying. The existing independent whole-grid pixel equations, reference tags/physical-debt conservation, mode/error priority, partial EOF, reset/cancel and held-head checks remain active.

The deterministic key-frame case took39030 more cycles than the V117 focused key-frame result557496, about7.0%. Random-stall inter-frame runs use different seeds and are not a controlled cycle comparison. The changed schedule is intentional: two-edge acceptance-to-commit latency and four physical copy edges replace immediate commit and atomic copy. No exact old-cycle equivalence or achieved MHz is claimed. These focused cycles exclude packet ingress, full inverse processing, parent memory/presentation fences, ESP32 and physical display behavior.

The first compile attempt failed before RTL execution because two new C++ `while` statements triggered `-Werror=misleading-indentation`. Braces/newlines fixed only that formatting; warning suppression was not added. Its snapshot remains under `attempts/20261109T143621716226Z`. A subsequent fresh compile and both simulations passed. A separate reviewer initially miscounted512-bit declarations by counting an input port; the corrected audit compares declarations directly to the unchanged V117 source and does not alter RTL or tests.

Selected receipt: `experiments/python-gamebub-v118/reconstruct/attempts/20261109T143735861575Z/receipt.json`. Independent221-check terminal/source/artifact audit: `experiments/python-gamebub-v118/audit/reconstruct-terminal.json`. All source and artifact hashes, strict compiler arguments, actual-run flags, raw logs and trace configuration phases were checked. The aggregate evidence represents six complete frames plus directed prefixes, not sustained hardware30fps or validated under10ms FPGA decoding.
