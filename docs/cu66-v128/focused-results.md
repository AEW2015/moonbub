# V128 focused verification results

The revision-2 raw-validation and header-padding focused suites passed with assertions enabled and strict Verilator/C++ warnings. The independent focused audit passed. These are simulation results; they do not establish routed timing, hardware throughput, or a complete Sunshine/ESP32/FPGA stream.

| Proof | Actual run | Result |
| --- | --- | --- |
| Raw full-tuple algebra | Seeds 128501, 128502; 196,608 cases and 1,572,864 phase checks per seed | PASS |
| Paired real scratch modules | Seeds 128601, 128602; 74 cases per seed; 1,221 / 1,220 clock edges; 81 requests and 81 ACKs each | PASS; public cycle delta 0 |
| Source-extracted owned padding kernel | Seeds 128701, 128702; 7,268 completed headers per seed; 1,072,456 / 1,072,334 clock edges | PASS; public cycle delta 0 |

The raw algebra intentionally tests arbitrary metadata, all eight phase encodings, independently selected raw/context tuples, and independent stored-format bits. It performs **zero DUT clocks** and does not claim naturally reachable packets. It includes 180,224 arbitrary rank-mask cases and 16,384 coherent literal-order checks per seed. The separate clocked scratch pair uses actual public begin and memory handshakes, covering epoch-versus-format error priority, cancel/retry, wrong ACKs, pending faults, and unready offers without forcing private state or results.

The padding proof extracts the actual source writer, cache consumer, ordered error chain, and ownership checks. It is **not the complete admission FSM**. Each seed checks all 12 padding positions × 256 byte values, 4,096 randomized headers, 84 canceled prefixes, 12 incomplete prefixes, 558 nonwriter holds, six nonpadding writer holds, and two last-byte forwarding cases. Natural callers and the five changed origins together require the separate full-composition spatial/peer/parent suites.

The aggregate binds the four raw-validation origins and one padding origin explicitly. It combines two separately compiled focused models; it does not describe them as one whole-composition binary. Production source hashes and original assertion blocks were preserved, and compilation input copies were checked against their recorded hashes.

## Receipts

- [Raw revision-2 receipt](../../experiments/python-gamebub-v128/raw/attempts/20261110T205241614705Z/receipt.json), SHA-256 `ffe8e97d8af707982c303c90ed86a410c532aafbbcc93876480ee5cdb5251e91`.
- [Padding revision-2 receipt](../../experiments/python-gamebub-v128/padding/attempts/20261110T205028675118Z/receipt.json), SHA-256 `8856bb3bd578bbeeb9edd1cf2572057ea73ee4fa889ab378ada0b6a39dd395d9`.
- [Focused aggregate](../../experiments/python-gamebub-v128/focused/attempts/20261110T205329510285Z/receipt.json), SHA-256 `9573b1de6b7e582247bb4d9d5b3e55ae08ca872443b1657937848821235b8f9e`.
- [Independent focused audit](../../experiments/python-gamebub-v128/audit/focused-independent.json), SHA-256 `71be571a3bd5972fe64ede1aeb2452a02e8eb229454755c78d6dbfbda67d09b2`.

## Retained first attempts and repairs

The first raw attempt passed both algebra seeds, then stopped on the authored driver’s stale combinational `begin_ready` observation after clearing abort/reset. The approved repair adds an evaluation/check without advancing a DUT clock. The entire model and all four seeds were rebuilt and rerun.

- [First raw failure](../../experiments/python-gamebub-v128/raw/attempts/20261110T203905162052Z/receipt.json).
- [Raw driver repair and archived inputs](../../experiments/python-gamebub-v128/raw/repair-history/20261110T204235617984Z-drain-settle/repair.json).

The first padding attempt stopped at strict compilation on three BLKSEQ warnings in the verification kernel projection. The repair expresses the source temporary combinationally and retains the clocked observed view. No production RTL or warning policy changed.

- [First padding failure](../../experiments/python-gamebub-v128/padding/attempts/20261110T203914447394Z/receipt.json).
- [Padding projection repair and archived inputs](../../experiments/python-gamebub-v128/padding/repair-history/20261110T204309401260Z-BLKSEQ-projection/repair.json).

The [initial freeze](../../experiments/python-gamebub-v128/audit/functional-tooling-freeze.json) remains intact. The reviewed repairs were bound by the [revision-2 freeze](../../experiments/python-gamebub-v128/audit/functional-tooling-freeze-revision2.json) before the fresh qualification runs.

## Subsequent full-composition qualification

The actual five-origin composition subsequently passed all four spatial, two peer and four parent exact stream comparisons. The independent full audit passed with public cycle delta zero. See [functional results](functional-results.md) for the full-model receipts, actual admission-FSM scope, retained compile/resource stops, and the limits of the 30-fps/10-ms evidence. The focused models and their successful receipts above were unchanged and were not relabeled as full-composition runs.
