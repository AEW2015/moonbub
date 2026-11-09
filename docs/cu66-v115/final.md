# V115 final route-driven composition

The third composition responds to the completed refined routed reports. It is
an RTL timing experiment; qualification and achieved clock are reported only in
[selected status](status.md).

The refined 125-MHz route has WNS −3.228 ns. Its worst path starts at
`owner_sequence` and crosses the wide private-kill comparison into parser
readiness. The request-index → prepared-request-bounds path is also in the
routed top 50, at −3.127 ns with 19 logic levels including eight CARRY4 cells.
The refined 100-MHz route fails at −0.777 ns on the owner cancellation cone.
Both routes have zero failing hold/pulse endpoints and zero routing errors.
See the [independent route audit](native-refined.md) and
[source-bound path groups](../../experiments/python-gamebub-v115/route-groups.json).

## Two causal cuts

The [new command top](../../fpga/experiments/cu66-v115-owner/cs88_pipeline_v91k.sv)
keeps the registered private valid/tag tuple, but captures a held authorization
bit atomically at either real kill birth. Reset or a new accepted command
revokes that authorization. A real cancellation therefore retains its original
edge without placing a 32-bit owner comparison in the child readiness cone.
The original stale-private-tag injection after a new command must still be
ignored. This is not protection against arbitrary simultaneous private-register
corruption. New birth, owner, consume and revocation assertions accompany the
unchanged original assertions.

The [new ingress](../../fpga/experiments/cu66-v115-final-ingress/br88_packet_ingress_sync_v91h.sv)
captures the full 32-bit future address at the existing real request edge. The
existing WAIT edge computes bounds from that registered value. The original
six-bit next-index expression, full-width address formula, initial fetch,
response ownership and public request/response edges remain unchanged. There
is no added protocol bubble or narrower-address assumption.

Relative to V114 there are six source aliases: the refined five plus the new
command top. The inverse pair, Rice parser and refined scratch payload slot are
unchanged. Each new body needs its own focused runtime proof; the actual
combined 18-source selection then needs fresh canonical, transport and peer
fault/drain proofs before native dispatch. The original global budget permits
only these three compositions, one route at each actual 100/125-MHz clock, and
one positive fresh repeat. No exceptions, guessed I/O delays, new attributes or
placement-strategy sweep are added.

## Remaining closure risks

The refined top-50 report also includes `owner_open` → publish/release counter
CE at −3.067 ns and scratch read-address selection at −3.013 ns. These are real
remaining risks; removing the two selected cones does not promise a timing
pass. The final routed report determines the result. A timing failure remains
a failure even if functional qualification passes.

Complete-parent validated decoding also needs the bounded overlapping write
join described in the [latency budget](validated-budget-next.md). The current
byte-write/ACK path alone has a 17.94-ms lower bound at an assumed 125 MHz.
Native component timing does not qualify physical SDRAM/LCD, ESP32 execution,
sustained hardware frame rate or the larger validation parent.

## Executed functional qualification

The [final focused ingress](../../experiments/python-gamebub-v115/final/ingress/results.json)
and [owner focus](../../experiments/python-gamebub-v115/owner-cut-focus/results.json)
pass with strict assertions/warnings. The actual 18-body
[component/transport selection](../../experiments/python-gamebub-v115/final/spatial/results.json)
passes 44 canonical profiles, 42 directed checks, 24 transport profiles and four
transport abort/reset retries. The separate
[peer selection](../../experiments/python-gamebub-v115/final/control-peer/results.json)
passes 28 complete canonical retries across two seeds. The
[cycle ledger](../../experiments/python-gamebub-v115/final/performance.json)
finds zero changed successful fence cycles across all 48 matched rows.

The actual final producer also passes the bounded
[ACK/C2/HUD/seal partition](../../experiments/python-gamebub-v115/final/live-parent/results.json)
with abstract memory/publication. See [LIVE scope](live-parent.md) for physical,
firmware and sustained-campaign exclusions. Native timing remains a separate
source-bound result in [status](status.md).
