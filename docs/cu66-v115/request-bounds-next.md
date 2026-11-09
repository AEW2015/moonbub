# Request-address/bounds contingency after refined routing

**Review only: no RTL was emitted, no frozen source changed and no new job was
launched.** Decide whether to implement this third composition only after the
current refined **ROUTE** reports confirm that the same address/bounds cone is
still limiting. Defer it if routing identifies a different limiting cone.

## Evidence and design understanding

The 125-MHz refined synthesis report for attempt `20261109T025651403152Z` shows
`fetch_index_reg[5] → prepared_request_in_bounds_reg/D`: −2.657 ns setup slack,
10.617 ns data delay, 19 levels including eight CARRY4s, under an actual 8.000-ns
clock. This is synthesized, unplaced evidence: its 6.452-ns routing contribution
is an estimate. It is not the final routed critical path or a timing verdict.

| Understanding | Assessment |
| --- | --- |
| Problem | Next-index selection, full address formation and two bounds comparisons occupy one existing WAIT update cone. Confidence: high from source and synthesis path. |
| Intent | Preserve the same current request and prepare the following request without a public bubble. Confidence: high. |
| Available boundary | An actual FETCH_REQ precedes FETCH_WAIT; index/base/kind/size and descriptor-last address remain owned and stable between its request and uncanceled reply. Confidence: high from the current state machine. |
| Proposed change | Use that existing request edge for address preparation, then the existing WAIT edge for bounds. Confidence: high on functional feasibility; routed benefit remains unmeasured. |
| Constraint policy | Retain the current clock, constraints, strategy and source-bound route budget. No false path, multicycle path, new timing exception, waiver or guessed I/O delay. |

Current source is
`fpga/experiments/cu66-v115-refined-ingress/br88_packet_ingress_sync_v91h.sv`,
SHA-256 `93b965d5d02d89e9f8b88b64340af7bd8f7c08568694e1dc0aaeb41c19bfcaf2`.
The synthesis report inspected is
`/home/lori/gamebub-build/cu66-v69/v115-integrated-125-20261109T024836651775Z-7eb017/results/synth-setup-paths.rpt`.
The inspected synthesis report SHA-256 is
`33a398c821cdc5920a37d51853b66bc8c5b6ea064b17bd0be89fb4e5389dfc48`.
Its native input card is the retained
`refined/native/20261109T025651403152Z/inputs.json` under the V115 evidence area.
This follows the AMD timing-methodology skill's report-first distinction between
observed constraints, source intent and a proposed fix; no new methodology run
was started during this review.

## Proposed reversible edit

Retain the entire existing `next_request_addr` combinational expression. Add one
private **32-bit** `next_address_at_request` payload register. At the edge of an
actual `stage_read_req`, capture the current `next_request_addr`. In the existing
`if(state==FETCH_WAIT)` block, use that register for both assignments:

```systemverilog
// Proposed only; not emitted into the frozen source.
if (stage_read_req)
    next_address_at_request <= next_request_addr;

// Existing FETCH_WAIT edge; no new FSM state or public wait cycle.
prepared_request_addr <= next_address_at_request;
prepared_request_in_bounds <=
    next_address_at_request < size_bytes &&
    next_address_at_request < 32'(MAX_PACKET_BYTES);
```

The comparison uses the same owned `size_bytes`, which is stable through the
request/reply interval. Keep `begin_fetch`'s initial address and initial bounds
assignments unchanged: they seed the first request and override unowned old
payload when a new fetch sequence starts. Keep the current request's separate
`expected_fetch_addr` capture unchanged; it must not be replaced with the
following request's address.

Preserve the original expression's order, casts, widths and modulo behavior:

- The current source explicitly declares a **six-bit** `next_request_index` and
  computes `fetch_index + 6'd1`. Preserve that exact index-wrap behavior, then
  preserve its existing 32-bit extension and address arithmetic. The new address
  register must never be six bits or truncate the 32-bit address result.
- Preserve the header CRC-tail jump at next index42:
  `size_bytes - 4 + 32'(next_request_index) - 42`.
- Preserve the descriptor last-byte substitution at next index6, using the
  existing full-width prepared `descriptor_last_addr`.
- Preserve both unsigned strict `<` bounds comparisons, full 32-bit wrapping
  address algebra, branch priority and all original assertions.

A new validity bit, if needed, is for verification/warm-up ownership only. It
must not add a public stall or replace the existing guards. Clear validity on
the original cancel/start/failure conditions; leave payload unreset. Snapshot
request epoch/index/base/kind/size for assertions if useful. Every active WAIT
must refer to its real preceding request, and a new start must never consume a
stale preceding packet's preparation.

## Verification before another native composition

Create a separate derived source and exact forward/reverse recipe; retain the
93b body, selected proofs and current native attempts unchanged. The smallest
focused proof should extend the existing original/refined pair and keep all
56 original public outputs checked every edge, including counters and invalid
payload. Preserve all parser checks, the 160 ingress profiles, old malformed
and cancel/retry coverage, and the refined header-overflow/cancel tests.

Add directed cases at current request indices0/5/6/41/42/45 and replay/raw
boundaries. Cancel, reset and replace start at the address-capture edge, while
waiting, and on the matching reply; retry without an extra reset. Check the
current read owner's tuple separately from the next prepared address. Compare
both backing-store read bytes and every delivered coefficient/metadata tuple
against the independent old vectors.

Add an explicitly labeled owned delayed-reply fixture that holds index, kind,
base, size and epoch while the accepted request waits; advance real clocks and
check the saved address/bounds remain exact. Such a fixture is not presented as
a naturally variable-latency response from the current one-cycle internal RAM.
A wrong-address/epoch response must retain the original assertion/first-cause
behavior in an expected-failure microtest; never disable that assertion to force
progress. New validity must not arm from an unaccepted request or stale reply.

Exercise full-width address arithmetic with base values near 0 and `2^32−1`,
index carry/wrap values and both bounds edges. Label prepared arithmetic-domain
fixtures separately from naturally reachable packet cases. Copying the exact
expression plus registered owner equality is essential; narrowed arithmetic
must not be justified by the ordinary 49,152-byte corpus alone.

Only after focused PASS should a fresh complete component/transport/peer proof
bind the third composition, followed by source-bound native trials within the
existing shared budget. Require unchanged accepted value/order/error/drain
behavior and zero added matched external cycles. The intended timing split is
address formation ending at the request-edge register, followed by bounds
comparison ending at the existing WAIT-edge register. Neither cone's clock
closure is assumed until actual reports confirm it.
