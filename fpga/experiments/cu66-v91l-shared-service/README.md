# V91l physical shared SDRAM service

Run from the repository root:

```sh
python3 scripts/cu66-v91l-shared-service/run.py
```

The runner requires the existing `gamebub-cu66-v69-build` container and verifies Verilator5.020. Every attempt has an immutable source snapshot, source hashes, exact tool/compiler commands, strict compile logs, bounded simulation receipts, and a result manifest. Failed attempts remain available. The selected run is recorded in `results.json`. Both2ns and7ns modeled tAC pass89 checks each in qualifying attempt `20261107T012706648267Z-05bf6aae`.

`shared_sdram_service.sv` synthesizably composes the frozen tiled8-byte writer and aligned16-byte BL8 read bridge. `interface.json` describes the simulation wrapper ports, also declared explicitly in `shared_sdram_timed.sv`. Writer addresses retain canonical logical byte meaning and the original tile mapping; read addresses retain aligned physical byte meaning. Writer token and reader generation retain their respective frozen bridge meanings. Source owner0=none,1=writer,2=reader. Round robin starts with the writer when both clients offer. A grant persists from selection, through request acceptance, all physical work and idle fences, through an arbitrarily held response, and until the bridge closes after response acknowledgement. A client cannot accept a second logical request in that closing cycle.

Only the granted bridge receives controller readiness, and controller read-valid reaches only the owned read bridge. Per-client reset/cancel drain existing accepted physical work and leave the controller running. A kill after a successful response is already offered leaves that response unchanged. Cold power-on reset is reserved for no logical ownership or bridge work; assertions reject its use while a transaction or held response belongs to either bridge.

The simulation-only wrapper uses unchanged writepipe controller and SDRAM pin-model sources, the established2.75ns read-clock phase,4ns forwarded-clock flight, and selected2ns/7ns modeled tAC. It contains no native/model preload plusarg. The model's existing deterministic initial contents remain useful for standalone reads; live integration independently establishes written-memory provenance. `peek_addr`/`peek_data` expose independent observations of actual memory; all writes and readbeats also produce original model pin receipts.

Wrapper event receipts are sampled on actual rising edges using `$realtime`: `arbitrate`, `ownership`, `kill`, `wr_req`, `rd_req`, `ctrl_req`, `controller_read`, `wr_rsp_offer`, `wr_rsp`, `rd_rsp_offer`, `rd_rsp`, and `fence`. Immediate responses emit both offer and acknowledgement at the same timestamp. Physical command/read receipts from the unchanged pin model use their own actual event timestamps. Request and read-response payloads are hexadecimal strings. Arbiter and bridge counters, state, pending flags, owner and controller observations are exposed separately.

Directed tests cover simultaneous requests in different SDRAM banks; write ACK before same-address read; whole-transaction fairness under continuously asserted requests; held writer/reader responses blocking ownership reuse and remaining immutable during late cancel/reset; cancel before a physical command; read cancellation after0/3captured beats with all8physical words drained; cancellation of1/2/3accepted writer prefixes with independent memory peeks; invalid epochs, generation, bank, alignment and aperture; warm writer/reader reset; periodic refresh and read/write turnarounds. A finite2ms simulation watchdog and120-second wall watchdog bound each simulation.

The first strict attempts captured missing runner SIMULATION define, then verification-only BLKSEQ warnings, followed by an observed Verilator5.020 constant-folding discrepancy in SV coroutine counter observations. The narrow verified workaround adds `public_flat_rw` only to unit-test observations. The failure's generated C++, official documentation links, diagnosis and preserved simulation receipts are retained under attempt `20261107T012546373204Z-2ec9c533/compiler-evidence/`.

This evidence is standalone timed functional RTL simulation. It does not establish hardware operation, board timing, routed clock/PVT closure, full-codec correctness, or sustained frame rate.
