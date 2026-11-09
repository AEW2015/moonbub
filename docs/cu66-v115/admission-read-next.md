# Admission packet-RAM enable: placement hypothesis

The final 125 MHz **fully placed, not routed** report has worst setup −2.678 ns from `base_kill_authorized_reg` to `coefficients/admission/memory_reg_0_6/ENBWREN`: 10.151 ns data, 11 LUT levels, no CARRY, and 81.46% estimated wire delay. The 100 MHz placed report was reported as −0.045 ns for the same family. These are placement estimates, not final timing. No candidate, flow, timing claim or budget extension is selected here.

The report path `/home/lori/gamebub-build/cu66-v69/v115-integrated-125-20261109T035613295775Z-79cccd/results/place-setup-paths.rpt` has SHA256 `4a382449ee19e5de5934907a5dd38974ee052d9ea6dc683ad817fd414e9a6397`. Its `place-ram-config.tsv` has SHA256 `da0de0ecf83d49a4b355a3ae8aae960ad76de3a3baec6eefb0acd320987828bb`.

## What the RAM port actually does

In frozen `cs88_admission_v91i2a.sv:294–320`:

- Packet writes occur only under `stage_write=in_valid&&in_ready`, with `in_ready` restricted to RX and original reset/start/abort guards. The only backing-array write is `memory[received[15:0]]<=in_data`.
- The synchronous read assignment is `if(memory_read_enable) ram_data<=memory[memory_read_address]`.
- `memory_read_enable=stage_read_req || (replay_req&&replay_ready)`; parser stage requests have priority in the address mux.
- Parser reads are FETCH_REQ→FETCH_WAIT. Replay requests are accepted only in FINISHED, with the original full-width `replay_addr<size_bytes` bound and reset/start/abort guards.
- `replay_rsp_valid` and address/epoch are registered on that exact accepted request edge. Both `replay_data` and public `stage_read_data` directly expose `ram_data`, including outside valid. The last accepted read data therefore holds until another accepted read, and it is not reset.

The reported final net is explicitly `memory_read_enable` before its inferred BRAM enable gate. This source and path identify a read-enable dependency, despite the primitive pin's combined ENBWREN name. The RAM configuration reports TDP, one-bit bank slices, READ_FIRST/WRITE_FIRST modes, and both write-width properties set to one; width properties alone cannot prove port B never writes. Any implementation must also inspect mapped write-enable connectivity to confirm the inferred source read port before changing a primitive enable. Do not generalize this result to scratch-memory/SDRAM writes.

## Causal chain from actual sources

`base_kill_authorized` qualifies the existing private producer abort pulse. The placed path passes through child cancellation and `child_in_ready`, then refill `frame_read_req`/`queue_req_valid`, then admission `memory_read_enable`.

`byte_refill_queue_v91i2b` computes:

```
pop_event = out_valid && out_ready;
owned_after_pop = fifo_count + pending - pop_event;
req_valid = active && issued<length && owned_after_pop<2
            && !blocked && !response_fault;
```

Its `out_ready` is actual child input readiness. This same-edge pop look-through intentionally allows a request into the credit freed by consumption. It also connects downstream ready/cancel logic combinationally to the upstream BRAM enable. The one-edge response/tag checker means simply adding a request register is not transparent: `pending` currently expects the matching response on the next edge.

## First bounded cut if actual routing confirms it

Use a **local queue capacity grant without same-edge pop look-through**. Compute eligibility from registered queue ownership (`fifo_count+pending<2`), or a registered local capacity certificate with equivalent conservative credit accounting. Do not include child-ready-derived pop in the request-enable arm. Keep original reset/start/cancel/error masks, full-width request address/epoch/span checks, actual admission request grant, memory address priority, data register and one-edge response timing.

This may introduce a recovery bubble when both local credits are owned and one is consumed. Declare and measure it. Empty/one-owned operation can still overlap request/response/consumption; do not promise unchanged throughput. It cuts the long ready arm but retains shorter direct cancellation/response-fault gates. Final routing can expose another endpoint.

Proof must show `queued bytes + pending response <=2` on every edge with unchanged response ownership. Retain all old queue assertions, full canonical bytes/order/last checks, cancellation accounting, wrong/extra/missing-response rejection and no-reset retry tests. Add exhaustive occupancy×push×pop×issue combinations, full→pop recovery, pending response plus pop, last-byte/final-offer fences and cancel/reset coincident with each edge. Preserve all original checkers; scheduling differences get an explicit new queue contract, not a broad assertion waiver. Since this option leaves the RAM read assignment and logical grant unchanged, `stage_read_data`/replay data hold semantics stay exact for each accepted read sequence.

## Alternative: local registered read grant or speculative private read

Only consider this after the conservative queue cut and actual routing. Two different contracts must not be confused:

1. **Registered request grant.** Capture a complete bounded replay request tuple before driving the RAM. This can make read enable local but adds request/response latency. Update the queue's exact pending-response contract explicitly, retain the old checker, and independently prove accepted-request→one matching response with the new latency. Keep logical/public requests, ready/backpressure and cancel/drain ownership coherent; do not claim the old one-edge API still holds.
2. **Speculative private BRAM read while preserving the public API.** Decouple physical BRAM Q from the existing logical read-data view. The private read can ignore a late cancellation only if it cannot write, cannot publish a response, and cannot alter public data/tags without the original logical grant. Retain original grant/response-valid/tag edges. A forwarding/hold view can expose physical Q following a real accepted read and otherwise retain the last logically visible value, including reset/abort edges. It needs an explicit prior-grant/hold register proof analogous to a forwarded write slot: before overwriting physical Q, retire the previously visible value into the hold view. Merely gating response_valid is insufficient because public `stage_read_data` is visible outside valid.

Unconditionally reading on every FINISHED edge is rejected as the first proposal: FINISHED can last indefinitely, so it creates unbounded speculative activity and changes Q continuously. A feasible speculative design needs a finite reservation/certificate: at most one private read attempt per named next-byte owner, complete address/epoch identity, no repeat until that attempt is consumed or discarded, and explicit rearm on a new reservation. Charging that attempt must not consume a queue credit twice. If constructing the certificate requires the same late ready chain, no cone was cut; move its birth to an actual earlier owned request/preparation edge and prove the new schedule. Do not silently restrict arbitrary external replay requests to friendly traces.

For either alternative:

- Charge accepted logical reads and extra physical attempts separately. Bound outstanding physical/logical owners, discard count and retry reuse. No speculative DRAM or BRAM writes.
- Preserve FETCH_REQ versus replay arbitration, full address bound, truncation rules and read-first semantics. Check RX writes versus speculative reads, equal-address collisions, reset/new-start transitions and invalid/out-of-range replay addresses; do not read unwritten/out-of-range entries and claim equivalence from unspecified RAM contents.
- Keep exact raw `stage_read_data`, replay_data, response address/epoch and held request views on every edge, not just asserted-valid cycles. Use distinct initial/unowned cases and compare only where the original initialized data contract permits.
- Preserve receipt/admission state, parser byte use in FETCH_WAIT and all cancel/error/reset priorities. Any accepted memory/reference write debt elsewhere remains subject to original physical drain; local packet-BRAM speculation supplies no permission to release it.
- Record RAM inference/mapped enable and write-enable roles, grant/tag/response traces, private-attempt counts, FIFO occupancy and full-frame stalls before measuring a later authorized native result.

The next decision waits for final actual routed path families. No RTL or flow changes were made for this analysis.
