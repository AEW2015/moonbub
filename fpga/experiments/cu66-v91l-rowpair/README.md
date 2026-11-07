# Three-plane tile-row retention reader

`tile_rowpair_reader.sv` implements aligned 16-byte canonical reads over tile8×8 physical BL8 bursts. The static `RETAIN_ROWS=0` control discards physical scratch at each new logical request. The `RETAIN_ROWS=1` candidate retains each even row's unused eight-byte fragments for the next odd row in **three independent plane contexts**, allowing the source-derived Cb/Cr prefill order to interleave with luma.

## Data allocation and interface

The retained candidate declares 180 × 64-bit fragments (90 Y +45 Cb +45 Cr), one 128-bit physical scratch and one 128-bit logical response: **1,472 data bytes**, plus 180 valid bits, row tags, plane cursors, owner identities and counters. This replaces the earlier 752-byte Python proposal, which supported a monotonic all-plane traversal. The control's retention RAM writes/hits are disabled by its static parameter; its active scratch/response data are 32 bytes. No synthesis or mapped-memory allocation is proven by these declarations.

One accepted `start` grants an immutable `(bank, epoch, generation)` lease. Banks 0..2 and nonzero epoch/generation are required. The caller must grant safe read ownership of the bank; the reader does not implement accepted/reference/front roles or publication. Plane cursors begin at 0, 345600 and 432000. Logical requests may interleave planes, but each plane must advance by exactly 16 bytes from its cursor. Out-of-order, unaligned, out-of-range or mismatched lease requests return a tagged error and invalidate the session without physical reads. `finish` has priority over a simultaneous logical request.

Each logical response preserves address, bank, epoch, generation and token. Only one logical request and one accepted aligned 16-byte physical burst may be pending. Physical responses must match burst address and lease identity. A wrong generation leaves `mem_rsp_ready` low and retains physical ownership until the actual matching return. A matching memory-error response drains the owner and returns a logical error.

Warm reset/cancel stops new issue, invalidates all caches, and waits for any accepted physical burst before offering a cancellation response. A response already offered remains immutable through reset/cancel and backpressure. Cold reset is allowed only with no physical owner. Starting a new lease cannot reuse the interface until the prior response is consumed. Scratch/cache invalidation includes same-bank generation changes. The interface does not detect silent memory corruption.

A 360-wide chroma line can straddle two raster rows. Processing each logical response as two eight-byte fragments preserves the earlier row's final fragment and the next row's first fragment without clearing that odd row's other valid fragments. Division/modulo uses explicit constant 720/360 branches. The RTL has not been joined to the real SDRAM controller or existing converter top.

## Tests and measured boundary

Run from the repository root in the existing `gamebub-cu66-v69-build` environment:

```sh
python3 scripts/cu66-v91l-rowpair/run_comparison.py
```

The runner compiles two static variants using Verilator `--cc --exe --build --assert -Wall`, C++20 `-Wall -Wextra -Werror` and two compiler jobs. Both seeds 912501/912502 run 17 directed checks, including full canonical native key/delta comparisons, independent plane order, 360-wide chroma crossings, same-bank changed generation/content through a 24,480-byte prefix that includes the first changed native luma bytes, wrong-generation physical responses, matching memory errors, reset/cancel before and after physical acceptance, held success/error responses, invalid starts and requests, and simultaneous finish/request. All accepted physical work must drain before the logical response.

The 32,400-address input schedule is **derived from existing converter sources**, not a captured per-address trace. It preserves CHECK_ROWS Cb/Cr prefill and raster luma order with each plane's aligned-line tag behavior. Both complete 518,400-byte reconstructed outputs match the retained native canonical goldens in all four modes.

| Component result | Independent gathers | Three-plane retention |
|---|---:|---:|
| Physical BL8 reads/native frame | 64,800 | 32,400 |
| Read component cycles across two frames and two seeds | 1,025,784–1,026,327 | 593,795–594,408 |
| Matched cycle reduction | — | 42.06–42.14% |

The component fence starts one cycle after accepted `start`, before its first logical request, and ends one cycle after the last logical response ACK. It includes driver request scheduling, ready stalls and held responses. The physical service model charges eight payload cycles plus one-to-five seeded wait cycles and seeded request-ready stalls. The same seeded rule is used, but changed traffic consumes the random sequence differently. This is **not real SDRAM command/refresh/arbitration timing**, validated frame decoding latency, or hardware throughput.

`comparison-results.json` points to the successful retained attempt, with exact sources, inputs, commands, logs, compressed trace receipts and canonical output files. Early failed lint/build diagnostics and the earlier retained-only trace remain exploratory artifacts; their causes and removed temporary input expansion digests are recorded in `exploration-receipt.json`.

Physical controller integration, complete existing converter/RGB565 comparison, shared-service contention, target resource/timing fit and hardware 30 fps/under-10-ms validated decoding remain open.
