# V113 synthesis warning review

The new `Synth 8-6901` for `phase_input_bad` is a declaration-order advisory in
the inspected SystemVerilog module, rather than evidence of a missing driver or
an implicit one-bit signal. Its use at [scratch line 260](../../fpga/experiments/cu66-v113-scratch/packed_scratch_v91g2.sv#L260)
selects an explicitly declared `logic [7:0]` at line 308 using a three-bit phase;
the following generate loop drives all eight bits. Module-scope declarations
can follow module processes. This differs from declaring a procedural local
after statements. The recipe reads these files with `read_verilog -sv`.

The three matching ingress warnings are retained from V112: `size_bytes` is
32 bits, `lengths` is four 32-bit words, and `band` is two bits, all explicitly
declared in the same module scope after their first uses at lines 71/73 of
[the frozen ingress source](../../fpga/experiments/cu66-v110-count-domain/br88_packet_ingress_sync_v91h.sv#L71).
No implicit-net, width-mismatch or multiple-driver diagnostic accompanies these
four messages in the captured prefix. A future source cleanup can move those
existing declarations before first use for portability/readability; frozen RTL
was not edited, and a changed source hash would need fresh qualification.

The [machine-readable audit](../../experiments/python-gamebub-v113/audit/synthesis-warning-review.json)
inventories every non-INFO Synth warning in the bounded native100 log prefix
observed at 21:43:26 UTC, through netlist translation: 174,703 bytes / 1,536
lines. It records the prefix hash rather than pinning a mutable whole log or a
RUNNING receipt. Synthesis reports **0 errors, 0 critical warnings and 55
warnings** under its summary counting. There are 269 printed warning rows,
including repeated instances; those counts are not interchangeable.

| Diagnostic | V113 printed rows | Frozen V112 rows | Review |
| --- | ---: | ---: | --- |
| 8-6901 declaration order | 4 | 3 | One new scratch declaration ordering message |
| 8-2898 ignored concurrent assertions | 100 | 100 | Both logs reach the tool's 100-message print cap |
| 8-6014 unused sequential state | 87 | 77 | Ten new diagnostic/verification fields removed |
| 8-4767 RAM implemented in registers | 8 | 8 | Retained multi-write IDCT intermediate array |
| 8-3936 register width trimmed | 2 | 2 | Retained scratch plan/read-position widths |
| 8-7129 no-load port bits | 13 | 13 | Retained `begin_prefix123[31:19]` |
| 8-3917 constant ports | 27 | 27 | Includes generated-helper port renaming |
| 8-13373 constant-propagated macros removed | 28 | 0 | New mapped context ROM candidates removed |

Ignored assertions are a verification/hardware distinction, not a waiver of
invariants. [Scratch lines 191/195](../../fpga/experiments/cu66-v113-scratch/packed_scratch_v91g2.sv#L191)
instantiate two bank-owner and 128 payload-stability properties; only 100
messages print before suppression. Synthesis does not implement those checks as
hardware monitors. The focused and full Verilator campaigns retain `--assert`.
Their PASS receipts remain the simulation evidence; the synthesis warning is
not hardware enforcement or evidence that simulation checks were disabled.

The ten additional removed fields comprise four internal inverse counters,
`expected_meta.token`, and five geometry validity/key diagnostics. The inverse
counters therefore describe simulation observations and cannot be assumed
available in the mapped component. Input coefficients carry no token port;
actual generated bank tokens, first-word token reservation and result/output
tokens remain operational. Geometry's removed valid/key fields feed simulation
coherence assertions. Its actual `prepared_geometry` and
`geometry_bytes_valid` still drive preparation/consumption. Correct use depends
on the separately checked Rice response-latency contract; a future parser or
handshake change must re-establish that relationship. Other retained removals
include assertion-only guards and unread header storage; their removal does
not establish additional validation of those header bytes.

The other families retain concrete risks. IDCT's simultaneous indexed writes
require real registers/muxes; the warnings do not imply free BRAM ports. The
scratch read-position high bits are explicitly zero, while the 19-bit plan
capture and unused prefix high bits rely on the existing coherent capacity
metadata/caller contract. Arbitrary inconsistent `begin_*` metadata is not
proven safe by this audit. Public constant error high bits agree with the
actual small reason encodings, and `mem_rsp_ready=1` agrees with the source's
always-accept response boundary; physical-owner matching/drain obligations
still apply.

The 28 removed `RAMB18E1` macros have generated names such as
`context_decoder/i_14/sel_rep`. Those are mapped names, not invented RTL owners.
The actual [geometry preparation and consumption](../../fpga/experiments/cu66-v113-geometry/br88_context.sv#L4043)
remain the source reference. Macro removal alone proves neither incorrect
geometry nor a free/absent memory implementation. Final mapped resources and
terminal paths need their own review; no synthesis-equivalence claim or timing
signoff is made here. This is a read-only review with no blanket warning waiver,
no source/selected-proof changes and no additional native/heavy run.
