# V74 tile-major memory and wide auxiliary reads

Canonical banks retain the V70 physical allocation sizes and plane offsets. Only the within-plane layout changes: physical x16 word address = canonical base + plane offset + tile index × 32 + tile word. Plane offsets are 0, 172800, and 216000. Tile words carry the unchanged row-major 8×8 packed-u8 pixel payload, low byte first. No auxiliary address translation occurs.

Each tile now issues four aligned BL8 writes with byte-enable `ffff`, or four aligned 128-bit reads, at word offsets 0, 8, 16, and 24. This halves tile command count and physical canonical write beats against V73 masked half-rows. Accepted operations retain generation, bank, plane, and tile identity; abort waits for the currently accepted physical block to drain and suppresses normal completion.

`cu74_word_bridge` adds `p1_read_burst` and `p1_rsp_burst_data[127:0]`. `cu74_memory_system` exposes these as `aux_req_read_burst` and `aux_rsp_burst_data`. The wrapper latches the flag together with address and payload at request acceptance. Wide P1 reads require read-only, aligned-eight-word addressing with all eight words mapped. Invalid flag combinations and addresses return errors before issuing SDRAM commands. P0 retains its generic legacy offset-zero/four full-block snapshot API; the V74 tile adapter uses aligned-zero requests only.

Both cache-hit and cache-miss P1 responses snapshot all eight words, including the final SDRAM beat, and hold the full payload while stalled. Writes invalidate matching tags in both physical caches. The shared burst-data register is safe because the bridge owns exactly one transaction until its response drains. Scalar auxiliary responses retain their selected-word behavior.

All nine V73 profile metrics retain their definitions and widths. The legacy `p0_row_reads` name now counts accepted P0 128-bit block requests: four per complete tile. P1 wide requests do not increment this counter.

The frozen V72 SDRAM controller and checked command-pin model are used unchanged. The V71/V73 LCD bounded-priority and one-clock grace rules are unchanged. Validation results are recorded by `scripts/cu66-v74/run_memory.py` in `fpga/experiments/cu66-v74/memory/adapters/results.json`; this is functional command-level simulation, not electrical timing, routed Fmax, or board qualification.


A raster sample `(x,y)` maps to `tile_index=(y/8)*tiles_per_row+x/8`, `word_in_tile=(y%8)*4+(x%8)/2`, and byte lane `x%2`, using integer division. `tiles_per_row` is 90 for Y and 45 for U/V. Software and the painter must use this explicitly; sending an old raster offset to auxiliary memory performs an ordinary physical access with no translation.

A complete canonical YUV420 bank contains 8,100 tiles and 259,200 x16 words. V74 writes need 32,400 commands / 259,200 physical word beats, versus V73’s 64,800 commands / 518,400 physical beats. Allocation capacity and active pixel updates are unchanged. LCD and HUD/RGB traffic are separate and must still be included in end-to-end frame timing.

The preserved per-client metrics are `p0_cache_hits`, `p0_cache_misses`, `p0_row_reads`, `p0_wait_cycles`, `p0_service_cycles`, `p1_cache_hits`, `p1_cache_misses`, `p0_read_wait_cycles`, and `p0_read_service_cycles`. The read-only counters remain subsets of total P0 wait/service time. Global cache hits/misses equal the sum of the two client counters.

Validation covers actual command-pin traffic against the frozen checked 32 MiB SDRAM model; independently addressed scalar readback across all planes/banks; first/last and boundary tile indices; full-block neighbor sentinels; physical cache alias invalidation; producer-payload immutability after acceptance; full128-bit payload stability during response stalls; eight accepted-read-beat abort positions plus preissue cancellation; malformed read/write/burst flag combinations; cache1/cache8 compatibility; LCD bounded fairness, finite grace and line deadlines; and reset recovery. Testbench writes populate payloads through the real request interface. Model backdoor writes are limited to out-of-allocation guard sentinels.


`tb_rows_v74` deliberately retains the generic P0 offset-zero/four snapshot and cache1/cache8 tests using strided physical addresses. Those are bridge compatibility probes; they do not define canonical raster layout. `tb_memory_v74` independently defines canonical addresses using literal bank bases, plane capacities and `tile_index*32`, then reads every tile word through the physical scalar port to detect symmetric reader/writer mapping mistakes.


The retained `adapters/build-failed-unused-task-output.log` records an initial strict Verilator `UNUSEDSIGNAL` diagnostic for a testbench task output. The testbench variable was renamed to identify it as intentionally unused, then the complete matrix was rerun. This diagnostic log is not a passing qualification result; it is preserved for provenance. No RTL change was needed for that diagnostic.


The final source-stable regression passed **44 simulation cases**: 24 main stress cases, 4 reset cases, 4 physical-cache alias cases, 8 cache1/cache8 generic wide-P0 cases, and 4 dedicated full-payload P1-wide cases. Both Verilator and Icarus agree at tAC 2 ns and 7 ns. Each main case completes 8,786 assertions/checks, 237 tile transactions, 17 explicit wide-P1 checks, 9 wide-read abort paths, and 250 LCD bursts / 2,000 LCD words. Accepted P0 blocks are exactly 454: 111 complete tile reads × 4, plus 10 accepted blocks across aborted reads. All nine per-client profile values are exported in each main result row.

The maximum observed LCD line service was **1,673 clocks**, below the retained 1,842-clock test deadline; the maximum consecutive LCD grant count with a scalar waiter was four. Main-case elapsed work, including rejected and aborted operations and refresh, ranges from 113,274 to 114,651 clocks. These are command-model component measurements, not a complete video-frame or physical-panel throughput qualification. All regression input hashes and all 64 command-log hashes were rechecked after completion.
