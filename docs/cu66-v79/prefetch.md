# V79 standalone two-slot reference prefetch prototype

This experiment implements a bounded reference-read walker in a new standalone RTL module. It does not change V78 HDL, the frozen V79 system harness/binary, or any running cohort campaign. It is not connected to the actual SDRAM controller, tile adapter, decoder, receiver, HUD, or LCD. Its passing result is `PASS_STANDALONE_LOGIC_SIMPLE_BACKEND`, separate from actual-system qualification and performance criteria.

Run the small independent Verilator experiment:

```sh
python3 scripts/cu66-v79/run_prefetch.py
```

The runner uses the existing `gamebub-cu66-v69-build` container, `-j 1`, and `/build/v79-prefetch`. Each attempt has bounded build/runtime timeouts, source SHA-256 pins, command/log digests, binary digest, wall times, and an explicit terminal marker. `fpga/experiments/cu66-v79/prefetch/results.json` identifies the latest result; `attemptN/results.json` and its logs retain each attempt. Attempts 3 onward also retain exact source bytes under `attemptN/source/`, verified against their recorded hashes. Attempts 1 and 2 retain logs and hashes but lack complete source snapshots; those historical attempts are not fully reproducible source archives.

## Interface and ownership contract

`cu79_reference_prefetch.sv` has one synchronous clock and synchronous reset. An epoch handshake supplies a nonzero 64-bit generation and reference bank 0, 1, or 2. Admitted generations must strictly increase across successful completion and abort; rejected epochs do not change the latest admitted generation. A joint reset clears that history. Generation rollover requires a joint reset rather than reuse. Invalid or stale epoch proposals are consumed and rejected with fault code 1 and never acquire a lease.

The caller supplies `lease_held` and keeps that reference bank immutable while `lease_busy` is high. `lease_busy` covers both active ownership and accepted physical-read drain. Lease loss faults the epoch; the block continues draining an accepted read before releasing its own ownership. This signal cannot enforce external memory immutability: the integrating owner must actually hold the bank lease. Keyframes bypass this block entirely; no epoch is submitted for a keyframe.

The walker allocates every canonical tile in order: Y indices 0–5,399, U 0–1,349, then V 0–1,349. A tile consumes 32 x16 words and four aligned BL8 reads. Frozen bank bases are `0x080000`, `0x480000`, and `0x880000`; plane word offsets are 0, 172,800, and 216,000. A physical request address is `bank_base + plane_offset + tile × 32 + block × 8`. The module includes the unchanged V70 memory map. The next descriptor is generated independently of decoder lookups, so hidden tiles cannot make reference-request count diverge from canonical tile order.

There are exactly two 512-bit reference buffers. Each carries generation, reference bank, plane, tile, fill progress, and consumer ownership. A slot becomes lookup-valid only after all four BL8 blocks have completed correctly. The walker may fill the other slot while a full slot is retained by the decoder. When both slots are owned it stops allocating and reading; it has no unbounded descriptor queue.

A lookup is accepted only on an exact generation/reference-bank/plane/tile match to a complete unclaimed slot. Wrong or stale identities remain backpressured and produce no response. One reference response may be held at a time. Its identity and all 512 payload bits remain unchanged until `ref_ready`, unless abort, reset, or a protocol fault cancels the epoch. The response is a mux from the owned slot, not a third payload buffer. Accepted lookup does not release the slot.

`retire_valid` means that the integrating caller has authenticated a successful candidate canonical-write completion for the matching source generation, plane, and tile. `retire_reference_bank` names the epoch's reference bank; it is **not** the candidate-write bank. The caller must translate between those bank identities after authenticating the actual completion. That translation and completion shim are not implemented here.

A consumed reference can retire only after its response handshake. `retire_unused=1` instead retires a complete unclaimed hidden reference without delivering it. A hidden completion presented before fill stays backpressured until the tile is complete. An unused token cannot claim or free a held/delivered response. Concurrent lookup and unused retirement for the same slot give lookup priority: exactly one handshake occurs. Retirement also waits an extra cycle after a response handshake, so simultaneous response consumption and retirement cannot free a held slot. A late duplicate or wrong-identity retirement cannot free a replacement. Retirement tokens must remain asserted with stable identity until accepted or the epoch is cancelled.

A future receiver integration cannot simply connect this backpressure to the frozen `write_done_ready`: the present receiver accepts write completion independently of that ready signal in relevant paths. It needs a held retirement token/shim or coordinated changes to all completion consumers. Prefetch-owned physical reads must also join `memory_drained` and the reference-bank lease condition. These are integration prerequisites, not changes made by this prototype.

## Physical stream, abort, faults, and reset

There is at most one accepted physical BL8 request outstanding. Its response consists of eight actually transferred x16 beats, with explicit zero-based `mem_rsp_beat`, `mem_rsp_last`, and `mem_rsp_error`. Response gaps are allowed. `mem_rsp_ready` remains asserted through an abort drain. The module counts accepted beats itself and does not trust an early or missing `last` marker to end ownership.

Abort immediately gates new reads/lookups/retirement and suppresses a held reference response. An unaccepted memory request is cancelled. If a physical request was already accepted, all eight actual beats must drain before a new epoch can be admitted; only then are old ownership and the external lease requirement released. Buffers are invalidated and no stale reference reply survives. Repeated abort does not extend or invent accepted traffic.

A memory error, bad beat index/count, malformed `last`, unsolicited response, or lost lease faults and aborts the epoch using the same drain rule. The combinational fault check gates new work on the fault edge itself, preventing a simultaneous new request, lookup, retirement, or reference response from escaping. Fault codes are:

| Code | Meaning |
| --- | --- |
| 1 | Invalid/stale epoch generation, bank, or initial lease |
| 2 | External lease lost during an epoch |
| 3 | Response offered with no accepted read outstanding |
| 4 | Memory response error |
| 5 | Beat index differs from the internal accepted-beat count |
| 6 | `last` differs from the eighth accepted beat |

Malformed `last` followed by all eight actual beats can finish draining. A missing physical beat cannot: ownership remains held until the missing data arrives or an external joint reset resets both this block and its backend. The module does not manufacture drain completion on a timeout. The bounded testbench proves a stalled stream retains ownership; its finite watchdog and runner timeout bound tests, not production recovery.

Reset has a different contract from live abort: the backend/controller and this module must reset together. Reset is not permitted as a local shortcut to forget an accepted live backend read. Reset clears buffers, outstanding state, statistics, and generation history.

## Verification and resources

Final qualification attempt 6 passed nine case groups. The full data replay uses deterministic seed 2,041,262,477, random memory-request readiness and response gaps, held reference responses, an independent address oracle, and exact full-payload checks for **all 8,100 tiles**, including both sides of every plane transition. It checks that two full retained slots stop all new reads. The separate unused replay uses seed 2,031,236,182 and retires all 8,100 tiles without a lookup, including the first and last tiles of every plane.

Each complete walk issues exactly **32,400 BL8 commands / 259,200 x16 beats / 518,400 physical read bytes**. Prefetching hidden references therefore deliberately retains the extra traffic identified by the memory study; this experiment does not eliminate reads using qmap lookahead.

The remaining directed groups cover exact wrong/stale lookup and retirement fields, early/late retirement, concurrent lookup and unused retirement, immutable held payloads, hidden completion held through fill, all eight between-beat abort offsets and abort coincident with each of eight accepted beats, missing-beat lease retention, abort of blocked unaccepted requests and held replies, memory errors, wrong beat index, early/missing `last`, unsolicited response, lease loss, joint reset, duplicate/stale generation rejection and recovery, and simultaneous protocol fault with new work or an already-held reference response. The backend returns a deterministic address-dependent data pattern. It is not an SDRAM command model. All tests have finite waits and a five-million-tick test watchdog; the executable has a 60-second in-container timeout.

Logical storage is two × 512-bit reference payloads: **128 bytes**. Per-slot identity/control state is 92 bits (generation 64, bank 2, plane 2, tile 17, state 2, claimed 1, served 1, block progress 3), or 184 bits for both slots. That gives 1,208 raw payload-plus-slot-state bits / 151 logical bytes before global walker, response/stream control, generation history, counters, implementation packing, and integration logic. No candidate staging is implemented. The memory study's conservative 320-byte working-window reservation also included two 64-byte candidate staging buffers and a 32-byte metadata allowance per slot; this standalone block does not claim to implement that entire datapath.

Attempt 6 used Verilator 5.020 (Debian 5.020-1) and completed its runner in approximately 2.111 seconds on this host. Its main replay took 440,447 simple-backend test ticks; those ticks do not model the real controller, display contention, refresh, decoder overlap, or target timing. There is no latency-speedup, sustained-source-fps, physical 30fps, under-10ms, Fmax/fit/CDC, or hardware validation claim. Actual-system campaign evidence remains separately pinned and unchanged.
