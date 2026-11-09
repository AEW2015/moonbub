# V120 unselected ingress payload-owner proposal

The proposal addresses the actual V119 125 MHz path from base-kill authorization through reset/ready eligibility into `prepared_request_addr` D. That path has 14 LUT levels and 10.052 ns data delay, including 7.798 ns routing. It does not delay cancellation or change the request protocol. Root must select a physical source composition only after inspecting the isolated range candidate's final routed reports.

Two private, already unreset fields change lifetime: `prepared_request_addr` and `prepared_request_in_bounds`. They are now prepared on every relevant phase edge, including an edge that is canceled or rejected. They are consumed only by the original live FETCH_REQ transaction. Logical kind/count/index/base/continuation, descriptor tail, all state transitions, errors, public masks and synchronous RAM ports remain unchanged. Extra writes grant no request, output or physical memory ownership.

## Exact four initial call sites

| Existing phase | Actual initial-fetch guard, below original cancellation/context-fault priority | Kind/count/continuation | Prepared full-width address |
| --- | --- | --- | --- |
| RECEIVE | Accepted last input byte with exact `in_last` agreement | Header / 46 / HEADER | 0 |
| DESCRIPTOR | Descriptor is not ready; length at least 6; cursor and remaining checks pass | Descriptor / 7 / DESCRIPTOR | `cursor` |
| CONTEXT_RUN | No context-word handshake; no held word; replay remains | Replay / ceil of the real 6-bit word width / CONTEXT_RUN | `active_offset + (replay_bits >> 3)` |
| RAW | No held raw coefficient | Raw / 2 / RAW | `42 + 2 * raw_position` |

All addresses and bounds retain 32-bit wrap semantics. Fetch index remains six bits. FETCH_WAIT retains the original speculative `next_address_at_request` update on its existing edge. The phase writer evaluates both initial and next-request bounds against the same captured `size_bytes` and MAX_PACKET_BYTES. `descriptor_last_addr` is not changed by this proposal.

For example, a held replay word can update the unowned preparation register while the context consumes the word. The FSM still suppresses the initial fetch on that edge. When the subsequent CONTEXT_RUN edge actually calls `begin_fetch`, the writer uses the newly advanced replay count and owns the exact next address. A rejected descriptor similarly may write its private cursor, but the unchanged controller enters FAILED and never consumes that value.

## Complete request ownership and physical debt

Verification-only certificates are captured from the actual `begin_fetch` arguments, rather than from a second guessed controller. A successful nonfinal matched physical response advances only the owned six-bit index/address. Every live FETCH_REQ and WAIT checks epoch, packet size, kind, count, base, index, continuation and band. Request consumption additionally checks address and bounds; descriptor requests check their unchanged full-width tail and selected length. WAIT checks the actual preceding request's captured address. These certificates add no synthesized state.

All original RTL assertion blocks remain byte-for-byte in the proposal. Public cancellation remains immediate. The physical byte RAM still has one write port and one synchronous read port, and its original request/response logic is unchanged. No RAM port, extra queue, tile buffer, request capacity or public cycle is added.

## The admitted private-contract change

This is **not all-private equivalence**. The inherited extent checker compared the two preparation fields even while unowned. The original equality remains unchanged in the frozen range-A control proof. In the derived candidate checker, exactly one two-field equality is replaced by complete independent one-edge writer oracles for both the original writer and the phase writer. Every write and hold is checked after each clock; no candidate readout is masked or forced. The third field in that old condition, `descriptor_last_addr`, remains exactly compared. Every other old private/public check and every original RTL assertion remains active.

The writer oracles observe unreset initial bits before the first transition, then check all subsequent transitions, including reset/start/abort, malformed extents, rejected descriptors, held words and context failures. Prepared predicate contexts remain labeled as prepared contexts. Natural packet, request, response, cancellation and retry ledgers remain distinct.

An independent next-address shadow is updated only by each actual accepted staging request. It computes the full modulo-32 next address from the preceding six-bit index, base, packet size, header-footer rule and independently selected descriptor length/tail rule. On owned WAIT, the real cached value must match that shadow, and both writer oracles use the shadow. No cached register is forced. Before any actual request, an unowned cache remains an explicitly unspecified prestate input; it is not called an independently owned mathematical address. The original RTL owned-address assertions remain active as a separate check.

The combined unit proof retains A's complete 65,536-value actual-DUT range test, 36 natural RAW boundary packets, 27 real prepared cancellations, 67 retries, all original packet/extent/bytecount suites and the current V119 caller pair. It adds 24 actual initial-call cancellations, 24 first-request/response cancellations, 32 natural malformed-context packets and 80 nonreset retries per seed. Error packets exercise missing DC bits, out-of-range DC value, first AC run overflow and final-symbol trailing bits. Complete writer coverage and all four initial call classes must be nonzero.

It also adds 11,424 explicitly prepared canceled-unowned RAW/replay contexts over complete 32-bit boundary values, including wrapping additions, variable packet bounds and reset/abort/start collisions. Those cases force coherent prestates in both models with cancellation already asserted, never force a cache or expected poststate, and require zero physical requests/responses/writes. The independent writer oracle checks every resulting payload transition. These are mathematical/lifetime fixtures, not natural packets. Held replay speculation and actual shadow-cache capture/WAIT coverage are required to be nonzero rather than merely reported.

## Files and dispatch

The address-only body is [the unselected proposal](../../fpga/experiments/cu66-v120-control-proposal/br88_packet_ingress_sync_v91h.sv), SHA256 `66f0a63d1c733558919b81ea550f0936ac9d0606409ed514aa893709d807c4eb`. The separately prepared [combined range/address body](../../fpga/experiments/cu66-v120-control-proposal/combined/br88_packet_ingress_sync_v91h.sv), SHA256 `a6a8191a8bd2ea7bcb451a88020641b0a4b6299b8a9dc73e94882a23cba7bd23`, applies the already isolated range edits after the reversible address edits. Neither is selected as source B by preparation.

Both recipes preserve the original source and reconstruct forward and backward exactly. The combined recipe names the explicit single private comparison edit and all adapter instrumentation. Its frozen A proof is control evidence only; the candidate ingress and caller models must compile fresh.

Root alone may dispatch, under the existing two-heavy-job/2-CPU/8-GiB/no-added-swap policy:

```bash
python3 scripts/cu66-v120/control_proposal/qualify.py --run \
  --root-grant ROOT_V120_CONTROL_PROPOSAL \
  --routed-cause ACTUAL_A125_RECEIPT_PATH
```

The preparation has not run Verilator, synthesis or routing. Passing a standalone unit proof would not select a source composition, close timing, establish a complete parent clock or demonstrate hardware 30 fps/under-10-ms decoding. If a context-terminal candidate later joins the selected composition, all affected composed proofs must be refreshed.

## Remaining parser and context families

The retained V119 top 50 also contain kill-to-parser reservoir, consumed-count and cached-remaining enables. These fields have promised reset/public-view behavior. Simply removing reset or relaxing incoming qualifiers can change public counters, responses or padding invariants after failure; that is outside the two-field contract and is not proposed here.

A separate small context candidate can capture the exact wrapped 32-bit `(emitted + 1) == target` predicate at an existing accepted DC/RUN/LEVEL request edge. Epoch, emitted and target remain stable through the corresponding WAIT/HELD consumption. One new owned payload FF can replace both the response error-7 terminal test and the accepted-output terminal branch without adding a public cycle. This addresses the emitted-to-error/BRAM-enable families, but requires its own full-domain/current-context/held/cancel/error-priority proof and actual A route justification. It is not yet included here and does not by itself remove the global parser-enable cone.
