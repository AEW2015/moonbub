# V117 reconstruction wordbank and C peer independent review

Review result: **PASS for the recorded behavioral simulation evidence**. The reviewer `/root/v117_ac` did not author the reconstruction wordbank candidate or peer adapter. This review used source inspection, reversible edit reconstruction, SHA-256 checks and independent parsing of existing terminal logs/canonical payloads; it launched no heavy job and did not modify any pinned source or proof input.

The machine-readable review contains 62 passed checks: [wordbank-and-peer-c-terminal.json](../../experiments/python-gamebub-v117/audit/wordbank-and-peer-c-terminal.json). Its SHA-256 is `51d49f9f7819f334c68bd6f327ae9bdbe1952488669f18148a47a622c20149bc`.

## Reconstruction source and exact-cycle proof

The final production source `fpga/experiments/cu66-v117-reconstruct-wordbank/cu66_reconstruct_stream_v91k.sv` hashes to `6bef0bea8d721bc9550dd0a3c7af73e8aa6e793b8b44c683bef42897a5e25bc4`. Applying its seven ordered recipe edits to the literal R5b production source (`5b12193073a8410ad0d05d251c061f7379cd9dba5a9677e5f8f20da4c581be06`) reproduces the entire candidate; reversing every edit reproduces the entire baseline. Every old assertion block remains a literal contiguous body. The focused C++ bench is byte-identical to R5b. The probe ports/assignment/module rename reverse losslessly to production, and the independent V103 geometry oracle is retained literally.

The residual insertion loop covers all 64 constant 24-bit destinations and selects exactly the original six-bit `fill_index`; it remains under the original accepted-tuple checks. Reset/start/cancel and MODE_WAIT residual/reference clears are unchanged. The recipe does not change clocking, attributes, ports, public transfer masks or error priorities.

Physical canonical writes now use two registered bank CE strobes predicted at the existing successful MATH_WAIT→COPY transition. The strobes default to zero on every central FSM edge. Their new assertions compare them against the unchanged preedge predicates `storage_copy && !owner_tail` and `storage_copy && owner_tail`, and reject simultaneous banks. The private physical write still occurs on the existing COPY edge, including an external kill asserted on that edge; the logical `owner_copy=running&&state==COPY&&!kill` and output masks still prevent publication. All old complete-response, held-head, kill-at-COPY, owner-count and reference-debt assertions remain intact. This is a timing hypothesis, not evidence of achieved timing.

The [final focused receipt](../../experiments/python-gamebub-v117/reconstruct-wordbank/attempts/20261109T125304434518Z/receipt.json) is actual RTL PASS, SHA-256 `d10f17366a149f9fc6748359de25ef843d08eb820f009f0a803eb83ed7959424`. Its 42 source pins, all corresponding snapshots and 47 artifact pins independently match. The [R5b receipt](../../experiments/python-gamebub-v117/throughput/reconstruct/attempts/20261109T111821839417Z/receipt.json) also passes all 14 source and 20 artifact checks. Both raw terminal logs were parsed and their **entire dictionaries** compared between old and new for each seed:

| Seed | Clock edges, old = new | Key-frame cycles | Inter-frame cycles | Geometry cases | Full frames |
| --- | ---: | ---: | ---: | ---: | ---: |
| 117311 | 1,948,079 | 557,496 | 685,259 | 32,768 | 3 |
| 117312 | 1,948,093 | 557,496 | 685,493 | 32,768 | 3 |

Every other terminal field also matches, including all 46 directed checks, both private-copy cancellation cases, full owner cycles, held tuples, canonical bytes, residual handshakes, overlap edges and fixture reference drains. The candidate adds no measured cycle or throughput improvement in this focused comparison.

The [first attempt](../../experiments/python-gamebub-v117/reconstruct-wordbank/attempts/20261109T124955603501Z/receipt.json) remains preserved as FAIL with `actual_RTL_run=false`, `simulation_started=false`, no runs and a nonzero strict compilation exit. Its frozen source contains `endcount_residuals<=count_residuals+1;`—the exact token is **endcount_residuals**, not endcount_output_stall. Inserting only the missing newline/indentation yields the final source exactly; removing whitespace from both sources produces identical strings. The parser's downstream errors, snapshots and failure-history receipt hash remain intact. The failed parse is not presented as an RTL simulation failure or pass.

## C peer adapter and terminal proof

The C peer bench `fpga/experiments/cu66-v117-peer-wordbank/tb_peer.cpp` hashes to `a3587961a1ca412b08513cf536b637f67d02494e43e1fb01a7811df349ce887e`. All five ordered derivation edits apply uniquely to the literal V115 bench and reverse exactly; its independent base header is byte-identical to V115 (`e56c4eb4a7a479c123baae06a7ad137b7c90e637735ccb6890c62f2df87c59dc`). Every old `need(...)` statement remains present. The injection body and actual inverse/reconstruction `fail(reason)` task literals match their contract hashes.

The two additional prepared reconstruction clears set `storage_copy_bank0` and `storage_copy_bank1` to zero. This reproduces the **actual whole fail-edge central defaults**, which run in addition to the task, without another DUT clock edge. It does not change production logic or assign physical reference/scratch ledgers. The adapter also preserves the previously required complete inverse acceptance/reservation flush and reconstruction logical-owner release. These are verification-only complete poststates; the campaign does not claim that these child faults arose naturally from malformed packets.

The [C peer terminal receipt](../../experiments/python-gamebub-v117/repair-study/control-peer/attempts/20261109T130008825351Z/receipt.json) is actual RTL PASS, SHA-256 `7e68faf2f7e386ed94124b2ec27dc6bb3a6e9c63250c61cc78cf35a27f491415`. Its selector matches the complete raw receipt plus the selected-report path/hash. All 63 current source pins, corresponding snapshots and 61 artifact pins match. All 18 RTL source origins match their pinned selected files, including final R6bef, the V117 inverse, selected AC, bytecount ingress, and unchanged old caller. Admission's three compile fragments reconstruct its full original bytes exactly; this packaging does not remove any module or assertion.

For seeds 115501 and 115502, raw terminal verdicts match the receipt. Each seed exercises eight prepared peer cases (two accepted writes, four accepted reads and two queued replays), 14 prepared child fault injections, and six real parent abort/reset cases across all three scratch preparation boundaries. All old owner/debt/first-cause/private cancellation checks remain. Each seed completes 14 canonical retries: eight peer retries plus six parent retries.

The reviewer independently decompressed both canonical TSVs and compared every pixel hex string to the independent `actual_001` canonical golden. All **28 records × 518,400 sample bytes = 14,515,200 sample bytes** match exactly. Both expanded TSVs hash to `d3934726e53914526600e93552dd207631b702d4815b2963abcd35072ada604d`. All 28 raw case rows report zero error, the full sample count and no pending drain; all 12 raw parent-case rows cover the expected reset/stage pairs and preserve the read-only parent abort tag.

All audited successful compilation commands retain `--assert -Wall`, C++ `-Wall -Wextra -Werror`, `-j 1`, bounded timeouts and 2-CPU/8-GiB containers with no extra swap. No command used `-Wno-fatal`, stopped on resource pressure or exited nonzero. Both runners persist actual-RTL flags before launching the runtime command.

## Remaining signoff

These results support functional retention for the selected standalone reconstruction and full-top peer campaigns. They do not close the separate full component/transport/LIVE gates or the new native composition route. They do not establish 125-MHz timing closure, sustained physical hardware 30 fps, ESP32 link performance or validated under-10-ms hardware decoding. Those claims require their own terminal evidence.
