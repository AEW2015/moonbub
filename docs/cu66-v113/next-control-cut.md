# Next bounded control cut after V113

This is an unimplemented follow-up proposal. Frozen V113 sources, oracles and
receipts remain unchanged; neither timing closure nor a cycle improvement is
claimed. The terminal evidence is in the [125 MHz audit](spatial-125-final.md).

The placed 8 ns run had WNS −3.244 ns and 32,572 failing setup endpoints, with
`transform/result_state_reg[1][1]` → ingress `prepared_request_addr[16]/CE` as
its worst path. Terminal routing instead has WNS −3.303 ns and 44,277 failing
endpoints, starting at `transform/accept_state_reg[0]` and ending at that same
CE: 11 levels, 11.013 ns, 83.5% routing delay. Forty-two of its first 50 paths
start at this accept-state register. The 100 MHz route independently starts
at inverse fault-pending and reaches ingress `fetch_index` CE through the same
control family. This supports an ownership/control distribution diagnosis,
rather than choosing wider DSP arithmetic as the first response.

The actual source dependencies are:

1. [Inverse busy](../../fpga/experiments/cu66-v113-inverse/cu66_inverse_stream_v91j.sv#L969)
   includes pending intake and result occupancy, as well as running, banks and
   math. Its `in_ready` also joins local slot phase, the commit-forwarded bank
   frontier and kill/start qualification.
2. [Top admission](../../fpga/experiments/cu66-v110-fault/cs88_pipeline_v91k.sv#L197)
   joins inverse/reconstruction busy and coefficient-slot occupancy into
   `start_ready`, then forms a combinational `accepted_start`. That event also
   qualifies peer cancellation and reaches the producer as its start input.
3. [Producer controls](../../fpga/experiments/cu66-v110-ready/cs88_coefficients_v91k.sv#L1048)
   recompute accepted start from child/cache ownership. Start/abort/failed-state
   joins reach the refill queue's blocked/pop controls and child ingress.
4. [Ingress preparation](../../fpga/experiments/cu66-v110-count-domain/br88_packet_ingress_sync_v91h.sv#L270)
   writes prepared address, kind, base, index and continuation from `begin_fetch`.
   One caller is the final accepted input byte; other callers are descriptor,
   replay and raw fetch decisions. Thus ingress CEs can inherit the distant
   readiness/cancel/input chain even though their address payload is local.

The path report confirms the busy, coefficient-ready, accepted-start, refill
pop/stage-write and ingress-enable LUT family. Intermediate names such as
`next_token_reg`, `frame_epoch[...]` and `sel_rep` are mapped net/cell labels;
they do not identify additional source registers or an independently proven
frontier path. The published path is to CE, not an address arithmetic D input.
Do not cut it with a false path or assume runtime `start=0` removes its timing
obligation.

The smallest useful control-plane experiment is a **reserved one-command
intake with registered admission credit and local command delivery**. Each
participating stage provides a held, tagged empty/drained acknowledgment and
reserves that availability until consumed or explicitly revoked. The credit
register must represent those reservations, not yesterday's `!busy` sample.
A start accepted at E consumes one credit and captures the complete command:
packet size, supplied epoch, reference/cache validity and identity, mode/profile
and all four scheduling controls. Registered local commands reach children at
E+1; data eligibility waits for matching local start acknowledgments. This
breaks inverse slot state → global ready → start → child CE propagation.
A partial cache preload has its own reservation; it prevents frame credit and
cannot race between the availability sample and accepted start. Keep existing
start-over-cache priority and suppress both sides of unaccepted cache transfers.
The inverse must acknowledge empty only after pending coefficients, both banks,
math and both result/final-offer slots retire—not merely when math is idle.

A scoped companion is **two locally reserved coefficient-intake entries with
registered credits**. Separate the accepted frontier from the committed bank
frontier. Every accepted tuple reserves a bank/word and carries complete
metadata, expected position, token reservation and owner. Advance the accepted
frontier only on acceptance; validate registered operands and commit through a
local registered pulse. The bank cannot become READY or launch math until its
actual word-63 commit. A bank rollover cannot advertise credits for an occupied
next bank. If ready is registered, reserve capacity for every beat that can
still arrive under an already advertised credit. Do not recreate a combinational
`commit → ready → parent` bypass. Two entries may support an accept/validate/
commit pipeline if local write service and reservation accounting prove it;
**II=1 is not established by this proposal**. The current II=2 fast-zero
regression remains a mandatory comparison case.

If the remaining measured cone still crosses refill/ingress, add a real
registered handoff there: two byte entries carrying byte, last, address and
complete owner, with held registered credits. The existing queue already owns
up to two queued/pending bytes, so this implementation owns up to four combined
bytes unless those credits are deliberately repartitioned. Count that storage
and latency. A one-entry alternative without pop/push bypass is bounded but
can halve intake; a bare delayed ready is unsafe. Keep upstream enqueue and
actual child acceptance separate in the ledger and counters, and retain final
EOF until the held last byte actually transfers.

A remaining local fetch CE can then use a one-entry owned fetch descriptor
(kind/count/base/continuation, bounds operands and owner), followed by local
preparation and a matching request launch. This adds an explicit preparation
edge. Merely moving the old global expression onto that descriptor's valid D
pin is not a successful cut: its producer must already be local/registered.
Private speculative payload may update after revocation only under an explicit
new lifetime contract; it must not issue a RAM request, commit a coefficient or
escape under another owner.

Across every cut, retain a small **immediate public revocation mask**. External
abort/reset present before E suppresses transfers at E; a current-owner
sequential fault observed at E suppresses transfers at E+1. Mask both outgoing
valid and returned internal ready so no hidden transfer is counted. Tagged
registered local kills may invalidate private payload afterward. Already
accepted scratch/reference requests remain in their real ledgers until matching
physical completion; wrong-tag replies cannot retire them. Retain the first
current-owner cause and simultaneous reconstruction/inverse/coefficient
priority. Old faults/ACKs cannot revoke a new owner or create credit. Unique
owner/session handling and any external tag-alias quiescence requirements must
be explicit; this proposal does not claim the full PCTL1 supervisor is built.

Qualification must independently count accepted, validated, committed, queued,
retired and canceled tuples, using immutable coefficient/residual/pixel goldens.
Cover full FIFO pop/push, rollover metadata forwarding, all reservation/ACK
orders, pending last byte/coefficient/residual EOF, stalled final outputs,
reset/abort with queued commands and genuine physical requests outstanding,
wrong/duplicate/old ACKs, current/retired/simultaneous faults and clean retry.
Keep the frozen exact checkers unchanged. Re-run the same zero/AC throughput
cases and full service profiles; report added command/preparation latency and
occupancy. Only a new full operational composition route and an eligible
independent positive repeat can establish a clock result. Both V113 initial
trials are negative, so no further trial or positive repeat is authorized by
this proposal.
