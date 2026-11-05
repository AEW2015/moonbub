# V71 independent LCD burst memory service

The new `cu71_memory_system` keeps the v70 canonical tile and scalar auxiliary contracts and adds an aligned eight-word LCD read client. It uses the frozen v70 controller and checked 32 MiB SDRAM command model. The controller still performs BL8 reads and **single-word writes**; this change is not a write-burst implementation.

The new ports are:

| Port | Meaning |
| --- | --- |
| `lcd_req_valid`, `lcd_req_ready` | One request transfers on their rising-edge handshake. |
| `lcd_req_addr[23:0]` | Physical x16 word address, eight-word aligned. |
| `lcd_rsp_valid`, `lcd_rsp_ready` | Each response beat transfers on handshake; a stalled response remains stable. |
| `lcd_rsp_data[15:0]` | Eight consecutive x16 words, in ascending address order. |
| `lcd_rsp_last` | Asserted only for response beat 7. |
| `lcd_rsp_error` | Alignment or allocation rejection; the rejected request returns eight zero/error beats without issuing an SDRAM command. |
| `lcd_busy` | The accepted LCD burst remains active through the last response handshake. |

An eight-entry, sixteen-byte elastic LCD buffer captures the unbackpressured SDRAM burst. Response delivery starts as soon as the first entry is available, while later beats arrive. Independent received/delivered counters preserve beat order and hold output stable under arbitrary consumer stalls. The bridge retains the transaction through the final response handshake, so the buffer cannot be overwritten and global idle cannot become true while any LCD response remains held. Scalar p0 retains one eight-word cache line. Scalar p1 has four fully associative eight-word lines with round-robin replacement, allowing four interleaved reader working sets to coexist. Both scalar clients' writes invalidate every matching cache line before the serialized write. A later request cannot overtake the accepted transaction. `completed_reads` counts actual controller read bursts, including LCD reads; `cache_hits` and `cache_misses` describe scalar accesses only.

The scheduler prefers LCD reads at transaction boundaries, with a maximum of four consecutive LCD grants while scalar requests wait. It then grants one scalar request; p0 and p1 remain round-robin. After an LCD completion, a single finite grace clock waits for the next LCD request if no request is yet visible and fewer than four consecutive LCD grants have occurred. This catches a one-clock request-adapter bubble. Grace is never renewed without another completed LCD burst, and the fourth burst does not reserve grace while scalar service is due. This is a **grant bound, not a cycle deadline**: an unresponsive consumer can hold its response indefinitely. The frozen controller retains refresh scheduling and rejects a new request when refresh is due. `aux_busy` continues to describe only the admitted scalar auxiliary operation; global `idle` includes tile, auxiliary, bridge/LCD and controller activity. LCD cancellation requires the shared reset/flush procedure; there is no independent LCD-abort port.

Run the component regression with:

```sh
python3 scripts/cu66-v71/run_memory.py
```

It uses the existing `gamebub-cu66-v69-build` container, one compile job, and separate `/build/v71-memory-tac2` and `/build/v71-memory-tac7` directories. Twenty-four normal executions cover Verilator and Icarus, seeds 7101 and 7102, SDRAM tAC values of 2 ns and 7 ns, and three concurrency scenarios. Four additional reset executions cover both tools and both tAC corners. All 28 passed, with identical per-seed/scenario counts across both simulators and both tAC corners.

Each normal run completed 231 tile operations, 5,871 scalar auxiliary operations, 43 accepted-operation abort probes, and 250 LCD burst requests comprising 2,000 checked response words. Three rejected bursts generated no controller read. The model also checked refresh and command timing, physical-bank addressing, the highest aligned burst in the 32 MiB space, and data read back after scalar writes. Targeted LCD stalls hold the first, middle and last response beats for at least 17 additional clocks. The reset tests separately hold valid responses for 32 clocks at beat positions 0, 3 and 7, plus an invalid-burst response; each requires busy and stable response framing, flushes the lease with reset and verifies a fresh eight-word burst afterward.

For each normal scenario, four 480-word LCD lines run alongside canonical writes and scalar auxiliary traffic. Their measured service clocks are:

| Scenario | Min–max clocks | Max at configured 100 MHz | Margin to nominal line period |
| --- | ---: | ---: | ---: |
| Continuous LCD requests | 1,296–1,339 | 13.39 us | 5.035 us |
| One idle request clock between bursts | 1,340–1,375 | 13.75 us | 4.675 us |
| One idle request clock plus scalar writes alternating RGB backslot rows in the same SDRAM bank as scanout | 1,457–1,502 | 15.02 us | 3.405 us |

The configured native period is 541 pixel clocks × 34.058 ns = 18.425378 us, or 1,842.5378 memory clocks. Every normal execution explicitly asserts its worst tested line takes at most 1,842 clocks. The four-LCD fairness cap is reached in all three scenarios. A separate producer-silent probe admits a scalar auxiliary operation at the final LCD beat: it encounters the actual grace hold and completes after two clocks of response wait, demonstrating finite grace rather than an indefinite reservation. The maximum LCD burst service across the complete run is 93 clocks, including deliberate response stalls; this is not a normal-load line service measurement.

These bounded component scenarios now fit the nominal line period. They do not establish a deadline for every possible access pattern, physical scanout reliability, verified 30 fps, or sub-10-ms decoding. The controller still performs single-word writes.

`fpga/experiments/cu66-v71/memory/results.json` contains commands, raw-log hashes, source hashes and all 28 terminal result rows. The integrated snapshots retain the development counterexamples: the initial fully buffered bridge passed functional checks but failed full-system cadence, and the intermediate elastic bridge without grace exceeded the native line period when request bubbles let scalar service interrupt every burst (1,899–1,935 clocks; 2,364–2,379 clocks with same-bank backslot conflicts). The final finite-grace scheduler addresses those measured cases. `system/initial-buffered` and `system/elastic-before-grace` hold the corresponding source/log archives and manifests.

`build-first.log` preserves the initial testbench-only width/unused-signal lint failure. `verilator-first-fairness.log` preserves a failed coverage assertion from the first request generator: its bubbles allowed scalar service between every LCD burst, so it did not exercise four consecutive grants. `build-reset-first.log` retains the reset bench's initial unused-result lint error. Final tests correct those bench issues without disabling diagnostics.
