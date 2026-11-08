# V113 spatial content contract and actual custom transport chain

This harness composes the 18 source origins in the actual V112 100 MHz
component receipt, replacing only `br88_context.sv`,
`packed_scratch_v91g2.sv` and `cu66_inverse_stream_v91j.sv` with the frozen V113
geometry, phase validation and owned inverse candidates. All other production
bodies remain unchanged. It uses V112's byte-exact admission split packaging;
the reassembled fragments must equal the original admission file. V111's
header candidate is excluded. This is a new-latency content qualification under
[IV113.1](inverse.md), not an exact public-cycle comparison.

The first executable compiles the original 496-line
`fpga/experiments/cu66-v107-elastic/verification/bench.cpp` unchanged. Its
independent coefficient, dequant, residual, canonical pixel, metadata/order,
held tuple, counter, malformed-frame, reference matching and real accepted
memory/reference drain checks remain active. It runs the original two seeds,
107601 and 107602, each with 22 case/profile rows and 21 directed checks. The
candidate's canonical output TSV must match the frozen V112 accepted pixel
bytes exactly. Event timestamps, stdout and intermediate/private diagnostics
are not compared with frozen cycles; the old exact checker remains unchanged.

The second executable connects an independently compiled, unchanged actual
`fpga/experiments/cu66-v97-forward/v97_forward.sv` model to the same actual
CS88 component model. A synchronous C++ source adapter presents explicit
parallel DMA reservations and byte writes. The V97 sink's byte valid/data feed
CS88's real `in_valid/in_data`; sink ready is the actual CS88 `in_ready`.
Both models use the same rising edge. External reset/abort masks both sides of
the public transfer, and the helper checks equal accepted-transfer predicates.
There is no hidden transfer behind a masked valid. The final-byte marker is
derived from the independently counted drained-byte ordinal and the accepted
transport frame length. Epoch, generation and FID are checked for every sink
transfer, and every byte is compared with the selected actual custom packet.

The transport executable reuses the original oracle through an auditable
five-edit derivation: add the standard function header and two callback fields,
invoke one callback before edge observations and one after the edge, and rename
the original main function. These provide precisely two clock hooks. Every
original `need` check and oracle body is retained. The derivation is reversed
byte-for-byte to the frozen original and recorded in `derivation.json`. The
first executable uses the original file directly, independently of those hooks.
The component's module ports and private hierarchy are not renamed to insert
the transport.

A separate software ledger models the actual transport's finite FIFO and two
DMA descriptors from accepted external events. It records reserved lengths,
written bytes, descriptor tokens, FIFO order, sink bytes and ACK retirement.
Actual RTL occupancy, reservations, received/drained counts and held sink/ACK
tuples must agree after every edge. Wrong DMA tokens are driven into the real
RTL with an existing reservation and must accept zero bytes. The adapter
rejects a wrong software completion token without consuming the real held ACK;
V97 exposes no incoming ACK-token port, so this latter matching check belongs
to the explicit source adapter. The actual ACK remains held and stable until
the correct completion is supplied.

Each transport frame first reserves two 1,024-byte descriptors, filling the
2,048-byte credit budget. Those 2,048 actual packet bytes fill the actual FIFO
while the decoder awaits start; both descriptors and the first ACK remain
owned. After 17 more held-ACK edges, the decoder accepts its command and drains
that FIFO through its real readiness. Subsequent DMA lengths are at most 1,400
bytes. No padding byte enters the decoder. All selected frames are at most
49,152 bytes. The transport campaign runs all six successful actual/canonical
cases in both service profiles for each seed, followed by abort and warm-reset
prefix cancellation and clean canonical retries. The unchanged full-component
campaign separately retains its original malformed/late-CRC and genuine
memory/reference drain cancellation tests.

V97 ingress commit requires the independently matching whole packet, CRC,
empty FIFO and retired DMA ACKs. The helper records that actual commit pulse
separately from decoder done and requires commit to precede decoder completion.
Decoder done is checked only after all canonical pixels, coefficient/residual
EOF and real memory/reference obligations drain under the original oracle.
These are validated tentative candidate bytes. No C2 seal, final publication,
reference/display promotion, physical panel service or whole-parent PCTL1
supervisor is implemented by this harness.

The adapter is a synchronous parallel DMA test source. It supplies no QSPI,
ESP32 CPU, firmware, UDP/native Sunshine or hardware performance claim. V97's
retained FIFO and descriptors are actual RTL, while the host fixture/oracle
storage and DMA source adapter are outside the firmware RAM bound. The models
share a simulated edge; no board clocks or CDC have been qualified.

Prepare and run with:

```sh
python3 scripts/cu66-v113/spatial.py
python3 scripts/cu66-v113/spatial.py --run
```

The run explicitly uses Verilator from image
`sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf`,
assertions enabled, fatal `-Wall` warnings, one compiler worker, 2 CPUs and
8 GiB memory with the memory-swap limit also 8 GiB. Containers have no network.
Compile and simulation watchdogs and host memory/PSI stop gates are retained.
Owned C++ and SV warnings remain fatal, with no removed checks or old-cycle shifts. Each run
snapshots sources and the raw focused proof receipts, retains failed prefixes,
pins every artifact and serializes the final receipt. Full-component and
transport results are separate rows/scopes in that receipt; the 18-source
native component order excludes the extra transport RTL.

The familiar `PASS_V113_SPATIAL_CANONICAL` receipt schema requires both seed
verdicts, 44 full-component case/profile rows, 42 original directed checks,
exact canonical TSV bytes and both successful actual transport campaigns.
`results.json` equals the selected raw receipt plus its `selected_receipt`
pointer. Existing stall counters and per-case completion fences are observations
under the declared service profiles, not calibrated microseconds or an
unconditional decoder deadline. Fresh component implementation and the
prescribed independent repeat remain separate timing/fit gates.

DMA ACK retirement frees a descriptor after its bytes enter the FIFO; it does
not certify decoder acceptance. FIFO occupancy and the sink byte ledger retain
those bytes until the actual decoder handshake. Ingress commit joins both
obligations. Explicit prefix cancellation discards private FIFO/descriptors
under the externally driven kill; it cannot clear an independently accepted
scratch/reference request in the decoder oracle.


The initial attempt `20261108T210733724256Z` completed both full-component seeds
and exact canonical comparisons, then failed while the direct C++ adapter
compile diagnosed unused parameters inside Verilator runtime headers. The
adapter compile now treats those unmodified tool headers as system headers
using `-isystem`; owned C++ retains `-Wall -Wextra -Werror`, and the SV build
still retains fatal `-Wall` and all assertions. No runtime-header source is
patched. A subsequent adapter retry was intentionally interrupted to correct
provenance counts; its FAIL receipt is retained as well.

An adapter-only retry uses the explicit `--reuse-canonical <raw-receipt>` option.
It verifies the parent's artifacts, both actual seed verdicts, all 18 unchanged
component source hashes and the original oracle hash before copying canonical
streams/logs and the exact compiled component model. The prior whole-attempt
status remains FAIL; only its independently complete canonical certificates are
reused. The old runner is pinned through the parent's immutable source snapshot,
not with an obsolete hash at the changed live script path. The selected retry
records `canonical_qualified_case_profiles=44` and
`canonical_qualified_directed_checks=42`, but
`newly_executed_candidate_case_profiles=0` and
`newly_executed_candidate_directed_checks=0`. Its two transport campaigns are
newly executed and reported separately. This avoids claiming that reused tests
were run again.

The unchanged full-component oracle passed both seeds in the retained parent:
4,058,368 exact coefficient/assembly/dequant/residual samples per corresponding
stage in each seed, 63,412 complete transform tiles, all 22 original
case/profile rows and all 21 original directed checks. Both canonical TSV
hashes match frozen V112. Total campaign edges are 28,258,871 and 28,260,255,
versus V112's 29,845,741 and 29,837,683.

| Successful fast-profile case | V112 cycles | V113 cycles |
| --- | ---: | ---: |
| `actual_001` | 1,478,420 | 1,281,738 |
| `actual_006` | 1,196,953 | 1,021,013 |
| `actual_043` | 1,051,188 | 923,623 |
| `actual_031` | 1,726,035 | 1,392,053 |
| Structural zero residual | 650,593 | 650,593 |
| `actual_006_varied_qcache` | 1,196,953 | 1,021,013 |

These fast-profile values agree across both seeds. In stalled profile 1,
`actual_001` takes 2,315,467–2,315,535 V113 cycles and structural zero residual
takes 1,769,043–1,770,767. Those service costs remain, and one-million-cycle
completion is not established for the complete workload. Randomized service
sequences can diverge when the new schedule changes handshakes, so small
profile-1 differences are not evidence of an isolated arithmetic speedup.
The separate inverse-only benchmark's fast zero-tile regression also remains
part of the result; full structural zero residual launches no inverse jobs.

The frozen selected result is
`experiments/python-gamebub-v113/spatial/attempts/20261108T212355592057Z/receipt.json`,
with summary `experiments/python-gamebub-v113/spatial/results.json` and status
`PASS_V113_SPATIAL_CANONICAL`. Both newly executed transport seeds pass all
12 successful case/profile rows and both abort/reset canonical retries.
Each seed reaches actual FIFO/reservation/descriptor high-water marks of
2,048 bytes / 2,048 bytes / two slots, rejects 16 wrong DMA tokens and 16 wrong
completion tokens, checks 17,230 held-ACK cycles, and records 147,542 sink-stall
cycles. The 16 `source_stalls` are deliberately rejected wrong-token DMA
presentations; that counter is `data_valid && !data_ready`, not a DMA request
credit-wait counter. All successful transport canonical TSV bytes match the
same frozen V112 canonical artifact exactly.

The selected script is frozen at SHA-256
`d61b4e2b92a9056cc65d5881c83ef2ac187b66c6ee4555fa31f077bcdf9255a9`.
The selected retry command was:

```sh
python3 scripts/cu66-v113/spatial.py --run --reuse-canonical experiments/python-gamebub-v113/spatial/attempts/20261108T210733724256Z/receipt.json
```

The selected receipt and summary, every current source pin, every retained
artifact pin, decompressed artifact hashes and the explicit parent reuse pins
were independently re-read and verified after PASS. Source and selected
artifacts are frozen for native component binding. Both heavy slots were
released after the two successful transport campaigns. No achieved clock,
full-top physical qualification, hardware rate or under-10-ms result follows
from this content qualification.
