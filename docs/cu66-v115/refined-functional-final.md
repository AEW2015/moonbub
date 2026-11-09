# V115 refined functional evidence audit

The selected refined V115 functional proofs pass the source, snapshot, artifact,
selector, and canonical-output checks recorded in the accompanying
[machine-readable audit](../../experiments/python-gamebub-v115/audit/refined-functional-final.json).
This read-only audit rehashed the archived receipts and evidence; it did not
rerun RTL. The earlier [`functional-final.md`](functional-final.md) remains the
prior cutoff report and is unchanged.

I rehashed 287 selected-proof source bindings against both the current files
and each receipt's saved source snapshot, plus 362 retained artifact bindings.
All match their receipts. The selected refined main and peer proofs carry the
same 18 source-origin paths. The initial inverse selection is rehashed and
retains its previous qualification; it was not rerun. Both initial and refined
LIVE selections are also rehashed and PASS.

## Canonical output

All 76 complete output rows match the frozen V113 reference bytes: 24 main
component rows, 24 custom-transport rows, and 28 peer retry rows. Each row
contains 518,400 samples, for 39,398,400 samples total. Main and transport
compressed outputs were streamed and compared with the corresponding V113
baseline output for each seed. Peer retry pixel payloads were compared directly
with the frozen V113 vector table. No rejected frame prefixes were counted as
complete outputs.

Across the two main seeds, the receipt records 44 candidate case profiles and
42 directed checks (22 and 21 per seed); 24 candidate arrays were emitted.
The separate custom transport exercised 24 successful profiles and four
abort/reset retries (12 and two per seed), producing 24 complete arrays. Peer
retries total 28 across seeds 115501 and 115502: each has eight local retries
and six parent retries.

## LIVE parent and JPEG endpoint

For each refined LIVE profile, the actual component-to-parent run records
560,640 write requests and acknowledgements, 1,025 hash jobs, and 518,400
canonical bytes. I recounted 1,025 hash-job lines and independently decoded the
three actual data rows (518,400 canonical bytes, 560,640 accepted bytes, and
1,350 qcache bytes). The actual C2/HUD seal validator and abstract publication
pass. Each profile observes one wrong ACK, drains the owned write, and completes
a clean retry without reset. These are simulation results for the selected
component and abstract publication path.

The separate JPEG-wire selection also passes: two phases, two good frames per
phase, 691,200 verified pixels per phase, one bad-CRC case, and one mid-receive
reset retry per phase. Its 1,382,400 total verified pixels use the recorded
RGB565 golden related to the existing C-model golden; this is not an independent
decoder oracle. This endpoint/CDC/JPEG result does not connect the custom CS88
transport to the JPEG parent.

## Retained failures and limits

Historical failures remain in the evidence. The archived live-parent attempts
include a compile-time UNOPTFLAT failure with no RTL runtime, a fast RTL pass
followed by a cumulative-conservation runner assertion, and a full attempt that
passed its first profile before the second profile's wrong-ACK fixture asserted
before the expected response. The earlier refined ingress failure records
parser runtime but a failed ingress-probe compile guard; its two scratch
predecessors record no qualified RTL runtime. Their original receipt,
snapshot, and artifact hashes remain valid. The selected passing receipts do
not erase or relabel those attempts.

The selected evidence supports custom component-to-C2/HUD validation and
abstract publication, plus a separate actual QSPI endpoint/CDC/JPEG test.
Custom-CS88-to-QSPI integration, ESP32 CPU/Rust execution, Sunshine host
serializer and negotiated-stream integration, physical SDRAM, RGB LCD,
sustained hardware 30 fps, and complete validated decode under 10 ms remain
open. No claim is made about every private-state fault.

I authored the earlier report-only refined-flow derivation and its documentation,
not production RTL, implementation logic, or test benches. The byte comparisons,
counts, and hash checks in this audit were recalculated independently from the
selected receipts and files.
