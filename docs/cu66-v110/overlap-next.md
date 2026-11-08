# Next latency experiment: overlap inverse math and residual emission

This is an unimplemented architecture proposal derived from the qualified
[transform-event analysis](transform-budget.md). It does not change the fixed
codec, establish timing, or predict measured hardware FPS/latency.

Both frozen seeds join 63,412 complete transform identities each, without
orphan or incomplete stage events. Every residual burst contains 64 consecutive
samples. The next launched transform begins no earlier than two cycles after
the previous burst's final sample. Coefficient prefill already overlaps math;
the launched transform's dequant/IDCT and residual emission remain serialized.
Stage response intervals include readiness delays and must not be presented as
pure arithmetic execution time.

## Proposed storage and scheduling

Separate arithmetic ownership from residual-output ownership. Introduce two
complete result slots, each holding the 64 signed residuals and their complete
frame/child/token/plane/tile/qcell/qscale identity. Reserve a free result slot
before starting arithmetic. Transfer the completed result to that reserved slot
before releasing its arithmetic owner. Emit an older ready slot while the next
tile computes. Preserve the existing coefficient assembly banks and their
independent ownership.

Choose register versus striped dual-port RAM storage from actual inference and
timing reports. Count all result payload, tags, ready/valid state, read latency,
ports and arbitration; do not assume a free BRAM port or instantaneous vector
copy. If moving 64 results needs several edges, model that transfer explicitly.
Prevent slot reuse until the final residual handshake retires it. A full queue
must stop new arithmetic admission rather than overwrite or drop a tile.

This changes scheduling and public cycles. Develop it in a new namespace with
an explicit versioned latency contract. Keep the V110 exact-cycle checker and
sources as the unchanged control; do not weaken its comparisons or shift its
expected traces to claim equivalence.

## Cancellation and completion

Retain immediate public revocation on abort or owned fault. Tag every result
reservation and queued tile with the same admission owner as its arithmetic
job. A canceled computation cannot mark a slot ready for another generation.
Suppress and eventually retire canceled results while preserving accepted
physical-memory obligations and matching response drains.

Join producer EOF, arithmetic completion, both empty result slots, the final
residual acceptance, reconstruction's final accepted pixel, and all matching
physical drains before success/retry. A private math-done bit is insufficient.
Cover reset with one computing job, one held result, and a stalled final output;
old tags and delayed completions must not authorize new work.

## Required proof and measurements

Use an independent event-driven scoreboard for ordered coefficient/residual
identities, values, pixels, references, HUD and hashes. Reuse immutable packet,
transform and canonical goldens. Account for accepted, emitted and canceled
tiles separately, including full-queue pop/push, output stall, simultaneous
abort/completion, late failure, final EOF and retry. Preserve partial/error
publication fences. Compare intended content and explicit ownership bounds
under the new contract, rather than demanding old cycles or discarding invalid
observations without documenting their changed meaning.

Instrument producer waiting, coefficient-bank ownership, arithmetic phases,
result reservations, queue occupancy and residual-ready stalls. Match these
counters against external accepted events. Re-run both fixed workload seeds
and service profiles, recording changes in actual fences and maximum queues.
Do not add overlapping stage spans as if they were serial costs.

Only then implement and route the complete source composition at the fixed
10-ns target, including mapped memory/DSP/control costs. A shorter simulation
schedule with worse timing may be a regression. Production service bounds and
calibrated validated-frame publication measurements remain necessary for the
strict under-10-ms goal; the slow zero-residual case already demonstrates a
service-limited cost that extra arithmetic overlap alone cannot remove.

Close the current timing prerequisite first. If its remaining scratch/admission
control needs registered boundaries, use the separately versioned
[admission/kill/drain contract](control-contract.md) and combine only after each
change has an independently checked ownership model.
