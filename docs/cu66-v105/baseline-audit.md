# V105 baseline audit

This read-only audit fixes the V105 comparison point at commit
`afc073e36f813cbcedaec9b21b61cda239453a5b`. The V104 source selection chooses
`baseline`, which retains the V102 combined memory-template and reconstruction
predicate sources. Both selected source files match the V104 selection SHA-256
pins, their working-tree SHA-256 values, and their Git blobs at the V105 task
baseline.

## Frozen profile and retained evidence

The workload remains 720×480 with a 49,152-byte packet cap. The retained V104
source audit reports **22/22 checks passing** and its native evidence audit
reports **4/4 checks passing**, with three measured variants and no pending
variants. These audits record V104 provenance and component evidence; this
baseline audit does not rerun the V104 simulations or native flows.

## Selected V102 routed footprint

The selected V102 native receipt is
`experiments/python-gamebub-v102/native/20261107T213234207776Z/receipt.json`,
for `cs88_pipeline_v91k` on `xc7a100tcsg324-1` at a 10 ns comparison clock.
The route completed with signoff still open. Routed setup WNS is **−13.976 ns**.
The worst path runs from `reconstruction/tile_reg[10]/C` to
`reconstruction/residual_reg[1082]/CE`, with a 23.687 ns data path (8.572 ns
logic, 15.115 ns route; 29 logic levels). This is the measured routed path,
not an inferred source-level bottleneck.

| Hierarchy | Total LUTs | Logic LUTs | LUTRAMs | FFs | RAMB36 | RAMB18 | DSPs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Top | 48,522 | 45,804 | 2,718 | 34,795 | 32 | 0 | 28 |
| Coefficients | 31,378 | 29,814 | 1,564 | 22,869 | 32 | 0 | 4 |
| Admission | 18,138 | 16,614 | 1,524 | 9,161 | 16 | 0 | 1 |
| Child pipeline | 12,724 | 12,692 | 32 | 12,684 | 16 | 0 | 3 |
| Reconstruction | 4,640 | 4,640 | 0 | 3,754 | 0 | 0 | 0 |
| Transform | 12,156 | 11,002 | 1,154 | 8,170 | 0 | 0 | 24 |
| Dequant | 3,471 | 3,471 | 0 | 2,351 | 0 | 0 | 8 |
| IDCT inverse | 6,200 | 6,200 | 0 | 5,132 | 0 | 0 | 16 |

The routed RAM configuration ledger contains 32 RAMB36E1 primitives: 16 under
`coefficients/admission` and 16 under
`coefficients/child/packet_decoder/synchronous.ingress`. All are reported as
TDP with one-bit read/write widths on both ports, port A `READ_FIRST`, port B
`WRITE_FIRST`, output registers disabled, and `DELAYED_WRITE` collision
configuration. The routed utilization report separately records 2,718 LUTRAMs:
1,524 in admission, 32 in child, and 1,154 in transform. Hierarchy totals
overlap parent/child rows and should not be added together.

These are implementation mappings from the selected routed reports, not a
source-bit-count estimate. The two 16-RAMB36 groups are grouped by implemented
hierarchy; the report does not by itself prove a one-to-one correspondence to
source arrays or establish the mapping of a future write-port-only candidate.
Memory probes establish bounded memory behavior and collision observations;
they do not prove the complete packet-admission protocol or board service.

## Evidence scope

The machine-readable audit records source/report hashes and primitive rows in
[`baseline-audit.json`](../../experiments/python-gamebub-v105/baseline-audit.json).
`PASS_EVIDENCE` means the selected-source pins and retained audits agree. It is
not a full formal state-space proof, board-service proof, parent-clock/I/O
signoff, hardware 30 fps qualification, or under-10-ms decode proof. No V105
RTL or native build was run for this baseline inventory.
