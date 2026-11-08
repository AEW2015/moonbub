# Next local-control boundary after V112

Status: **design proposal; no implementation or timing result**. Use this only
if the measured V112 cuts leave the required clock open. The current V112
candidate retains the Count exact-cycle contract; the following changes need a
new version and independent event oracle. Preserve every frozen exact checker.
The governing future semantics are
[PCTL1](../cu66-v111/control-contract.md).

The concrete starting cones are scratch's routed
`read_segment → busy_owned/state` AC-validation family, admission's
`tile → group_visible` family, and the currently combinational readiness/cancel
network. In `cs88_pipeline_v91k`, `start_ready` joins base readiness, inverse
busy, reconstruction busy and coefficient-slot occupancy. `base_abort` joins
external abort with pending inverse/reconstruction faults; `inverse_cancel` and
`reconstruction_cancel` join remote sticky fault predicates with accepted-start
qualification. These expressions reach the producer, coefficient slot, inverse
and reconstruction. In `cs88_coefficients_v91k`, `start_ready/cache_ready` join
frame-running, child-busy, child-draining and partial-cache ownership;
`local_abort=abort_packet||(state==FAILED)` reaches the child/refill path.
These are source-level dependencies, not a new assertion that every such net
is a worst routed path.

The completed V112 100-MHz route now adds a concrete inverse-bank target:
`transform/fill_bank_reg/C` to
`transform/coefficient_banks[1].words[10].value_reg[12]/CE`, 10 logic levels,
10.745-ns data delay, WNS −1.034 ns. In the actual retained
`cu66-v110-fault/cu66_inverse_stream_v91j.sv`, `fill_bank` selects the bank
state and metadata used by `in_ready` and `input_metadata_bad`; those feed
`input_fault`, which qualifies every fixed coefficient-word payload enable.
The coefficient storage is already reset-free. Removing another payload reset
does not resolve this observed selector/validation/enable cone.

A concrete later experiment is an owned coefficient-accept slot containing the
complete tuple, selected bank/word, expected index, metadata owner and token
reservation. Validate its coherent registered operands, then issue a local
bank/word commit pulse. This intentionally separates public acceptance from
payload commit and needs PCTL1's reservation, fault-latency, final-offer/EOF and
flush semantics. The last accepted coefficient cannot make a bank READY or
advance EOF before validation and its actual write commit; a revoked owner
cannot write or launch math. Count accepted inputs and committed writes
separately in the new oracle. This proposal is not implemented or timed here.

The completed 125-MHz route has a different worst cone:
`context_decoder/sel_rep[1]/C` to `context_decoder/out_block_reg[15]/D`,
16 levels, 10.792-ns data delay, WNS −2.844 ns. `sel_rep` is a mapped name;
do not invent an RTL owner with that name. The actual Count `br88_context.sv`
computes `sparse_geometry(context_band, position, emitted[15:0])`
combinationally. `position_geometry` combines four byte quotient/remainder
tables, a remainder correction and quotient selection before `out_block` and
`out_index` are captured with a level response.

Test a private preparation of those byte contributions during the existing
run-to-level request interval. The consumer already registers the final
block/index. Before calling this an exact-cycle cut, prove the earliest legal
level-response edge from the actual Rice request/response RTL, including
zero-length/fast symbols, stalls, start/abort and generic band/DC defaults.
Do not assume an extra idle cycle. Preserve full uint32 quotient/remainder,
wrap/truncation and emitted-ordinal behavior; bind a prepared key to the
consumed context/band/position and assert equality with the original scalar
geometry at every consumption. If a complete preparation cannot be ready on
that edge, use an explicitly owned response slot under the latency-changing
contract instead. This is a source-backed next experiment, not new RTL or a
clock result.

The first implementation should move these operational joins into a supervisor
with reserved local stage ownership. A delayed sample of today's `start_ready`
is insufficient: a child or partial cache preload could consume a resource
between the sample and accepted start. Each stage must offer a held
`available_ack(reset_generation, reservation_id)` only when its data/EOF/offer
slots are empty and accepted physical operations have drained. It cannot
allocate those resources independently while the reservation is held. The
supervisor issues one registered admission credit after all matching ACKs.
`start && credit && !reset && !abort_packet` at edge E consumes that reservation
and snapshots the whole command: packet size, supplied epoch, reference/cache
identity and validity, all mode/profile flags and the four existing scheduling
controls (`serial_clear`, `write_overlap`, `read_prefetch`, `tile_overlap`).
Separate local command registers present this owned command at E+1. No input
beat is accepted until every participating stage acknowledges that command.
This adds a documented admission edge and removes live external command pins
from later child configuration decisions.

Cache preload has its own reservation. Preserve start-over-cache priority and
suppress `cache_ready` while `start` is asserted. A partial preload holds the
producer's resource reservation and prevents a frame credit until preload
completion or explicit cancellation. A failed or blocked start cannot reset
another owner's cache/preload. Admission credit is consumed once, and its
sequence advances even when the admitted command later fails.

| Actual boundary | Local owner and finite resources | Required ACK before reuse |
| --- | --- | --- |
| Producer admission and replay/refill | Registered command; packet RAM; one registered replay request and bounded refill queue; lookup response owner | Admission/parser flush, refill queue and pending-read retirement, lookup completion/discard |
| Ingress/context and scratch begin | Registered complete metadata command; context/Rice owner; scratch metadata-validation slot | Input/metadata EOF retirement plus scratch-start ACK with validated command identity |
| Scratch bank/read/write service | Two existing tile banks; cache line owners; assembler/write slot; one real outstanding memory ledger | Private bank/cache flush separately from physical read/write drain |
| Coefficient handoff and EOF | One full coefficient tuple, pending EOF and final offered coefficient owner | Empty data slot and EOF/final-offer retirement |
| Inverse arithmetic/emission | Fill-bank owners, arithmetic token, finite result/emission slots | Math result discarded/transferred, last held residual retired, private result-slot flush |
| Reconstruction/reference/publication | Residual owner, held output pixel, accepted reference-request ledger, provisional frame ownership | Residual EOF, held pixel retired/revoked, physical reference/write drain and validation |

The supervisor owns `(reset_generation:u32, admission_sequence:u32)`; child and
inverse tokens refine that owner, and supplied epoch/FID remain metadata.
Wrap disables new credit until an explicit drained session boundary. Every
command, slot, EOF, fault and flush ACK carries its private owner. A delayed
result/fault/ACK from an old owner cannot revoke a new owner or produce credit.
Diagnostic vectors and state observations get an owner/valid tag rather than
being reused as control oracles.

Keep a small immediate revocation mask at public operational boundaries. An
external abort/reset present before E suppresses request/pixel transfers at E.
A current-owner sequential fault detected at E suppresses transfers in the
interval after E and thus at E+1. A transfer accepted before E remains a real
obligation even when the frame later fails. Mask both the outgoing public valid
and the ready returned to the internal stage, so the stage cannot count a
hidden transfer. Scratch and reference response acceptance/matching remain
operational while the logical owner is revoked. Hold the first current-owner
terminal cause, with reconstruction/inverse/coefficient priority for
simultaneously visible faults, independently of stage-flush completion.

Broadcast a registered tagged kill to local owner controllers. Each controller
uses its own `owner_active`, `killed` and local error predicates for clock enables
and data acceptance; remote busy/sticky error no longer qualifies every payload
register write. For an external kill at E, invalidate private eligibility and
return matching `flush_ack` by E+1. For a sequential fault appearing after E,
capture kill at E+1 and return flush ACK by E+2. These are implementation
requirements to verify, not observed latency results. A local ACK certifies that
no private tuple can emerge for that owner. It does not acknowledge memory
completion. A stalled physical service can delay drain without a finite bound;
new credit stays low until the real completion arrives.

Warm reset increments supervisor generation and initiates that same logical
kill protocol. It must not clear accepted scratch/reference request records,
write-slot ownership or provisional framebuffer ownership. Physical completion
retires the recorded transaction exactly once. Wrong-tag and duplicate replies
do not retire it; an error on a matching reply retires the obligation and makes
the logical frame ineligible for publication. Current channels expose epoch
fields without a separately unique transaction/session response identity. The
new wrapper must either extend the channel tags through the service model or
require a proven channel-quiescence/session-reset handshake before those tags
can alias. Internal generation registers alone cannot distinguish two replies
that carry the same external tag. Cold configuration needs the same explicit
external-session condition before admission.

For the remaining scratch validation cone, put a one-entry owned read-result
slot between cache selection and `AC_EXTRACT` validation. A cache hit copies
word, decoded position, bank/offset/address, band, cursor ordinal, prior head
position, block limit and owner into that slot. A cache miss retains the request
owner and fills the same slot only from the actual matching response. Capture
all coherent operands together; live `read_band`, cache payload or cursor pins
must not change the interpretation of a held result. The next stage validates
the registered word and returns an owned valid/error result. Only that result
advances the scratch local state and busy/error owner. Release/update the
cursor/head exactly once after the validated result is consumed. Cancel before
consumption discards the logical slot while any accepted physical read remains
in the ledger. This intentionally adds a read-result edge and breaks the
selector-plus-validation cone; neither a specific delay improvement nor timing
closure follows without routing it.

Retain V112's prepared admission visibility unless its actual routed path
requires another cut. If it does, issue a complete registered geometry command
and return a registered mask/count response; `GROUP_BEGIN` waits for the matching
owner/key response. Preserve the generic 32-bit wrap function and all four
plane values on the command domain. A fixed 512×5 table is a different optional
specialization that still needs the caller-domain proof in PCTL1. It cannot
replace generic or malformed-state behavior silently.

The new coefficient/residual handoffs must treat data and EOF as separate owned
obligations. Full-slot simultaneous pop/push replaces the complete tagged tuple.
Producer done with a held final coefficient cannot advance coefficient EOF;
inverse done with a held final residual cannot advance residual EOF. An inverse
math completion releases arithmetic only after its reserved result slot accepts
the complete result. Emission owns the slot through residual 63 acceptance.
Success joins all final public outputs, EOFs, physical drains and validation;
private math-done or a cleared stage busy bit cannot authorize publication.

Build the new oracle from accepted external commands/bytes and independent
content goldens. It assigns private expected owners, queues ordered coefficient,
residual and pixel identities, records every actual accepted scratch/reference
request, and retires only independently matching responses. Candidate stage
busy/flush/done bits cannot delete those expectations. Compare accepted values
and order, retained offered values during stalls, and owner retirement; measure
latency against the explicitly versioned edge bounds. Keep the Count exact
checker unchanged on the frozen design and use its content outputs as fixtures,
not shifted candidate traces or relaxed cycle comparisons.

Required directed tests are start/cache/abort coincidence; all reservation/ACK
orders; final held coefficient/residual and simultaneous replacement; fault
before/at/after final pixel; late/current/retired/simultaneous faults; reset with
scratch write and reference read pending; wrong response followed by the real
response; duplicate ACK; delayed old math result; held output during kill;
repeated supplied FIDs/epochs; token/generation wrap; and retry while a genuine
physical drain is withheld. A bounded service campaign verifies latency under
its declared service bound; an unbounded-delay test verifies that readiness
stays low without inventing an ACK.

Qualify command, kill, credit and read-result stages first with their real
operational data/ready/valid/error/owner/drain ports. Fresh full-composition
synthesis/place/route and independent repeat remain required for a decoder
clock claim. A small control top that ties away a physical ledger or an
operational revocation input cannot qualify the complete pipeline. Keep actual
memory/panel clocks and CDC requirements separate from any decoder clock
experiment.
