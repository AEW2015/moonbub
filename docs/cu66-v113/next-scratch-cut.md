# Next control cut after the V113 100-MHz route

Status: **design proposal only; no implementation or timing qualification**.
The terminal 100-MHz route changes the priority: global operational fault/
readiness/ingress control is first; the prefetch/continuation proposal below
remains a secondary conditional study. No frozen source, tooling or oracle was
changed, and this review launched no job.

## Terminal routed priority

The [independent final audit](spatial-100-final.md) confirms WNS −1.686 ns and
8,220 setup failures at the actual 10-ns clock. Its primary path is
`transform/fault_pending_o_reg/C` → synchronous ingress
`fetch_index_reg[2]/CE`: 12 logic levels, 11.433 ns, with 9.489 ns (82.996%)
routed interconnect. Forty-five of the 50 retained worst paths start at this
fault register and end in ingress fetch/prepared-request or admission enables.
Those 50 paths are a sample, not the complete endpoint population.

The first fault-pending net has **fanout one**. Blind MAX_FANOUT constraints or
duplicating that register are not evidence-backed fixes. Inspect each physical
segment and the source dependencies through `base_abort`, base readiness,
accepted-start qualification, local running/refill state, queue eligibility and
ingress fetch controls. Review locality across those boundaries; do not infer
a cause solely from the separate 7,141-load clear or 2,359-load reset nets.

The next primary architectural experiment is a reserved admission/registered
command boundary and tagged local kill/flush ownership, so remote fault status
no longer qualifies every private ingress register. Preserve a small immediate
public revocation mask on both outgoing valid and returned ready. External
reset/abort suppresses transfers at that edge; a sequentially detected fault
must suppress the next eligible edge according to the explicit owner contract.
A plain registered abort that permits an extra public transfer is unsafe.
A delayed sample of today's `start_ready` is also insufficient: reserve the
child/cache/queue resources before issuing a credit. Keep accepted scratch and
reference operations in their real ledgers until matching physical completion;
private flush ACKs cannot authorize reuse while those operations remain.

The complete production PCTL1 supervisor/session protocol is **not implemented**
by V113. Its registered-owner proposal needs a new contract and independent
oracle for command/kill/credit, held data/EOF, stale fault/ACK, retry and reset
with pending physical requests. Preserve the current frozen checks. Only a
future measured full-component route can establish that a control or locality
change helps. The following prefetch design addresses the historical synthesis
cone and must not be described as the terminal route's primary diagnosis.

The V113 100-MHz **synthesized, pre-route** report lists
`coefficients/child/scratch/output_block_reg[2]/C` →
`coefficients/child/scratch/return_state_reg[0]/CE`, WNS **−0.946 ns**, 14 logic
levels and 10.660-ns data delay. It lists 4.829 ns logic and 5.831 ns estimated
interconnect; the intermediate nets are explicitly unplaced. These numbers
are not routed delays, a 100-MHz qualification or a comparison of terminal
WNS. The exact report examined is
`/home/lori/gamebub-build/cu66-v69/v113-spatial-100-20261108T213507992002Z-40531d/results/synth-setup-paths.rpt`,
SHA-256 `945a8d136bb34b10c73f74d2e5e3fa21c152de6138c1da262d1611bc3c6a48fe`.

## Source-backed diagnosis

The path traverses next-address carry chains, `candidate_valid*`, candidate
segment selection, mapped `dbg_prefetch_launch` logic and state/return-state
enables. Mapped cell names are evidence of that cone, not invented RTL owners.
The actual [scratch source](../../fpga/experiments/cu66-v113-scratch/packed_scratch_v91g2.sv)
is SHA-256 `efc3e61ac94d6c336164026c2865b70dee832c53a328bce720278719f6693f0f`.
Its candidate logic computes:

- Nonraw next-block DC address: `32 + (uint32(output_block)+1)*2`, then AC
  addresses `starts[b] + cursors[b]*4`, with DC before bands 1, 2, 3.
- Raw next-word address: `32 + (uint32(output_block)*64 + output_index + 1)*2`.
- Cache-line misses and remaining-count/bounds predicates, followed by the
  priority winner. A line is aligned in the 32-bit domain before projection
  to the 18-bit request address.

`prefetch_launch=candidate_valid` immediately feeds the sequential prefetch
capture. It also feeds the same-edge `EMIT/RAW_EXTRACT` choice between direct
continuation and `PREFETCH_DRAIN`, which writes `return_state`. Thus speculative
geometry and candidate selection qualify a general controller continuation
register. The proposed cut targets this prefetch-planning cone; the report
does not identify the AC cache-word validation predicate as this path's cause.

The current shared `transfer_address/request_epoch` and single `outstanding`
flag also service ordinary `READ_REQ/READ_WAIT`, descriptor reads and writes.
`return_state` carries demand returns, write continuations and prefetch-drain
continuations. Merely delaying `prefetch_launch` would let the original FSM
advance while a delayed request can still overwrite that shared context.

## Proposed owned registered plan

Introduce one finite prefetch-plan command, per-segment prepared candidates,
and one held issue tuple. Reserve this capacity explicitly. Capture a complete
coherent command, compute addresses/cache eligibility in a registered stage,
then select/register the priority winner or an explicit NO_PREFETCH result.
The public request must come from its held issue tuple. Controller drain and
continuation decisions must use registered ownership/resolution bits rather
than live geometry or the current combinational launch expression.

A concrete proposed schedule is command capture at E, per-segment preparation
at E+1, and selected issue tuple or NO_PREFETCH registration at E+2. The first
public request transfer can occur at E+3 with an available service. These are
new functional edges to verify, not evidence that either stage meets timing.
Planning may begin during a held output, but neither the first EMIT edge nor
RAW_EXTRACT may assume spare preparation cycles. Compared with capture/issue
on the current launch edge, this can delay a request and stall a raw/demand
continuation. Declare a new latency/debug contract and measure that tradeoff;
do not shift or relax the frozen V113 exact scratch checker.

The command must carry, directly or through a held immutable owner record:

| Required coherent field | Purpose |
| --- | --- |
| Private reset generation + scratch admission sequence; supplied active epoch | Reject old local plans; retain the actual external response tag |
| Request kind and requester; full raw/prefetch/tile mode snapshot | Distinguish raw next-word, next-block DC, AC lookahead, demand, descriptor and write obligations |
| Full output block/index frontier, next-coordinate intent and sequence | Prevent an advanced emitter from reinterpreting an old plan |
| Blocks, relevant starts/counts/cursors and their versions | Preserve full-width arithmetic, count bounds and AC ordinal meaning |
| Relevant cache-valid/line identity/version per candidate | Bind hit/miss eligibility to the same snapshot as its address |
| Selected segment, full uint32 word/line address, offset and projected address | Preserve alignment, range, wrap/truncation and bank placement |
| Explicit resume kind and complete coordinate/owner context | Resume RAW_FETCH, CLEAR_TILE or a demand extraction without reading a later shared return state |

Do not copy all live arrays into an unversioned slot or revalidate a held plan
against changing `output_block`, cursors or cache payload. Either reserve the
referenced frontier until plan resolution, or check compact registered owner/
version keys and discard/rebuild a stale **unissued** plan. Preserve the
original deterministic DC/band priority within each coherent snapshot. Never
retarget an offered request while `mem_req_ready` is low.

Separate a demand-read return context from the emitter's prefetch-barrier
continuation. An accepted dense word may advance its public ordinal only once;
if its continuation must wait, retain that complete next-coordinate obligation
in a finite local slot. Reserve continuation capacity before exposing a new
dense offer; once exposed, retain its valid and complete tuple through normal
backpressure. Mirror every public acceptance to the internal source exactly
once. A full continuation slot must backpressure the next unoffered item,
not withdraw a held valid or permit a hidden internal transfer. Revocation
masks both public valid and returned internal ready. A newly available request
slot is a reserved local credit, not a delayed sample of old `!outstanding`. Unresolved plans, held issues and outstanding physical
requests must prevent a conflicting demand issue from reusing shared fields.
NO_PREFETCH resolves planning; it does not fabricate a memory completion.

## Request, cancellation and drain contract

On actual `mem_req_valid && mem_req_ready`, transfer the complete issue owner,
request kind/segment/address/epoch and resume context into the single physical
ledger. Count that accepted operation once. A producer-side pop, private flush
or cleared offer cannot retire it. Until a matching response, hold every
required physical owner field; cache publication uses the ledger's captured
segment and line, never live read/frontier pins. Prefetch planning, issue and
completion must not advance AC cursors or consume heads; the owned record
validation/consumption path advances those obligations exactly once.

External reset or a matching abort before an edge suppresses new memory and
dense transfers at that edge. A stale-epoch abort must retain the active offer,
payload and owner. Invalidate unaccepted plans/issues and local continuations
on cancellation; an already accepted operation remains in DRAIN with response
acceptance operational. A wrong-tag response may fault the logical owner but
must not retire the real pending request. A matching error response retires
that physical obligation and publishes no cache data. A matching success for a
revoked owner retires/discards it without publishing a new owner's cache.
Never wait for dense readiness to accept the physical completion.

`begin_ready` and parent restart eligibility must require all local plan/issue/
continuation slots empty **and** the real physical ledger drained. With an
unbounded response delay, readiness may remain low indefinitely. Final done
joins the final accepted dense word with resolved planning and every genuine
physical completion; there is no bounded fake ACK or early bank publication.
Preserve error priority, including the parent's packet-error-before-store-error
choice for simultaneously visible causes, and test any changed fault latency
explicitly rather than silently changing the terminal code.

The existing memory response carries epoch only. A private generation or
request sequence cannot distinguish two external replies with the same tag.
Keeping this interface therefore requires the service's ordered, exactly-once
single-outstanding completion contract and a real drained session boundary
before epoch reuse. If arbitrary duplicate/late replies must be tolerated,
extend a unique transaction/session tag through the physical adapter and
response; internal tags alone are insufficient.

The actual parent
[br88_pipeline_v91h](../../fpga/experiments/cu66-v108-capacity/br88_pipeline_v91h.sv),
SHA-256 `cb440ed9c12c6fa3eac579aea99f2c03716e33b97ce50822ab00b93de08a4360`,
keeps `busy=running||store_busy`, asserts draining when only the store remains
busy, masks outgoing dense valid, and masks ready returned to scratch on
reset/start/abort/error. Retain those semantics. A private plan flush is not
permission for the enclosing coefficient pipeline to admit a new owner before
its accepted scratch/reference work drains.

## Required proof and measurements

Keep the existing focused original/candidate proof unchanged on frozen V113.
Build a separate accepted-event oracle for the new latency contract: independent
packed/dense goldens, held tuples, output ordinals and a physical request ledger
created only from actual external handshakes. Candidate plan/flush/busy bits
cannot delete oracle obligations. Retain the original full-component coefficient,
DQ, residual, pixel, error and matching scratch/reference drain checks.

The directed campaign must cover:

- First EMIT edge with immediate ready; held output; samples 62/63; final block;
  RAW indices 0/7/8/63 and line/block transitions; all prefetch/overlap/tile-mode
  combinations, including tile mode where this prefetch path is disabled.
- DC miss versus each AC-band miss; simultaneous candidates and exact priority;
  zero/exhausted counts; all banks/offsets; full32 starts/cursors, alignment,
  truncation/wrap and last legal line. Compare every used prepared address and
  decision with independent original scalar geometry.
- Cache fill or cursor/version change at command capture, preparation, winner
  capture and issue; stale unissued plan discard; held issued tuple immutability;
  simultaneous demand intent, write-slot ownership and speculative intent.
- Abort/reset/restart at every new stage; stale abort; request acceptance coincident
  with semantic failure; matching success/error, wrong tag then real response,
  repeated reply under the declared service contract, and cancellation with a
  genuine completion withheld. New starts must remain blocked until actual drain.
- Final dense word with unresolved/no-op/issued prefetch; held ACK; simultaneous
  response and slot replacement; packet CRC/store fault coincidence; clean retries
  with repeated supplied metadata; owner/generation wrap and explicit quiescence.

Retain the nine historical accepted-write/drain hazards, all-bank/all-offset
cache checks, corrupt/read-owner tests and the full canonical bench's accepted
write/reference reset/abort checks. Report accepted, issued, canceled-before-
issue, completed and discarded-after-kill counts separately. Fixed readiness
service tests may measure bounded latency; the unbounded-delay case proves
retention only. Request sequence/timing changes need an explicit contract and
new evidence, not relabeled exact-cycle PASS. A fresh complete-component route
and any required positive repeat remain necessary before claiming a benefit.
