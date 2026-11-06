# Direct tile-major YUV display prototype

This is an isolated successor experiment. It does not replace the passing RGB renderer/scanout sources or select a hardware image. The root receiver must validate canonical/HUD tags and hold their leases before PREPARE. This block does not invent an integrity attestation or claim an RGB framebuffer is ready.

## Data and ownership

Canonical physical tiles contain 64 row-major bytes in four aligned BL8 transfers. Plane offsets remain 0, 172800 and 216000 x16 words, with 90/45 tiles per tile row. The CU66 wire representation, logical hash order and HUD row-major layout are unchanged. It requires the `cu71_memory_system_direct` backend; the legacy physical canonical layout is incompatible.

`cu71_direct_scanout` owns two cache contexts. PREPARE carries generation, frame ID, canonical bank, HUD bank and cache slot. Bank 3 and an occupied slot are rejected before DMA. A successful prepared result follows all 3600 initial BL8 reads, cache writes and backend drain: complete HUD plus the first two Y groups and first two groups of both chroma planes. COMMIT descriptor identity must match a READY context. It becomes FRONT only at the LCD frame boundary with line, pixel and memory pipelines drained. The previous FRONT is released at that same fence.

Cancellation names the provisional generation/frame/slot triple. FILL and READY may be canceled after drain; PENDING and FRONT cannot be rolled back. Reset recovery requires coordinated memory ownership, backend and pixel-domain reset. A pixel-only reset is not a supported ownership recovery operation.

The physical BL8 port has no generation echo. The DMA wrapper retains one request's identity until response or acknowledged abort drain. Its backend contract forbids a late successful response after that fence. An unowned response is discarded and counted. Without a physical echo, an arbitrary old response arriving during a newly owned transaction cannot be distinguished in this interface; the drain contract is essential.

## Bounded operational lifetime

The current frozen owner uses a 32-bit internal DMA cookie and **fails closed before exhaustion**. It never silently wraps/reuses an owned identity. At about 2.1 million BL8 commands/s, exhaustion could occur in roughly half an hour; the actual bound depends on traffic. Before a long-duration release, qualify a separate 64-bit-cookie successor with abort/stale tests, or a coordinated owner/backend/pixel reset policy. The current component proof is not an unbounded or 20+minute30fps release qualification.

## Rendering

The unreset synchronous RAM caches hold two Y 8-column groups and two groups of each chroma plane per context. Chroma top/bottom storage is duplicated for simultaneous neighboring-row reads. The entire 21120-word HUD is cached per context. Group tags gate use, including the neighboring chroma group at each interpolation boundary. The last chroma column clamps at 359.

The native bilinear interpolation, integer rounding, clipping and HUD words pass through one synchronous cache read and five color stages. Throughput within a generated 480-word line is one pixel per 100 MHz clock. Runtime prefetch fills future groups while the LCD consumes previously generated line buffers. Missing cache pages delay line admission; the LCD fails to an entire black line rather than mixing stale or partial data.

LCD clock, porch, active dimensions and existing panel border timing are unchanged. `cu71_lcd_lines_direct` is a separate derived endpoint with an added held line-error bit. That CDC payload needs explicit physical constraint review in any board integration.

## Executed evidence

- `evidence/pixel-pipe02`: 8,985,600 native canvas comparisons, reset pipeline flushing and exact native rounding.
- `evidence/cache-pixel01`: 9,676,800 native canvas comparisons across actual key/P fixtures, synthetic extremes, both contexts, chroma halos/clamps, HUD, rejected writes and coordinated reset.
- `evidence/cache-dma01`: 166 four-state checks of command bounds, last-row/HUD payload, errors, four abort phases, stale cancellation and unexpected responses.
- `evidence/direct-owner05`: positive deterministic/seeded key/P tests, 1,152,000 panel pixels per seed; cold PREPARE exactly 3600 reads; concurrent second-context preparation; two identity-qualified presentations; no underruns, memory errors or unowned responses. Negative owner tests cover four PREPARE abort phases, wrong-identity rejection, READY cancellation, protected FRONT/PENDING contexts, invalid-bank/live-slot rejection and coordinated reset recovery.
- `evidence/cache-ooc01`: exact XC7A100T cache/color synthesis, 744 LUT, 270 FF, 41 RAMB36, no DSP; internal 100 MHz setup +3.273 ns. This excludes complete owner, root integration and routed CDC/timing.

- `evidence/direct-pin-fast03`: actual selected SDRAM controller and pin model, native 29.36 MHz LCD raster, 384000 exact native panel pixels, zero black lines/underruns/faults. All 36000 BL8 responses independently checked; cold preparation took 113094 memory clocks, backend maximum wait 35 clocks, refresh active. This is LCD-only with testbench-preloaded canonical/HUD data.
- `evidence/direct-ooc01`: full frozen owner resource synthesis fits at 3659 LUT, 2363 FF, 41 RAMB36 + 2 RAMB18, no DSP. Internal 100 MHz setup **fails ?5.240 ns** from requested-line/page selection to `f_tile_base`; CDC paths also remain unqualified. Resource success is not timing success.

`cu71_direct_scanout_pipe` is a new isolated same-port successor that registers page selection and separates address construction from command issue. `evidence/direct-owner-pipe02` passes the same native key/P and owner-abort/fence regressions. Its fast actual pin-model full raster passes in `direct-pipe-pin-fast01` with zero underruns. Its OOC (`direct-pipe-ooc01`) improves memory intra-clock slack to +0.255 ns at 100 MHz (pixel +15.866 ns), using 3837 LUT,2373 FF,41 RAMB36+2 RAMB18,no DSP. The overall summary still fails ?2.336 ns on CDC paths, which have deliberately not been cut or hidden. The slow pin corner also passes (`direct-pipe-pin-slow01`). Isolated write contention passes in `direct-burst-contention-fast01` (front CAN0/HUD0, canonical1/HUD2 writers:10776 completed tiles+673 HUD words) and `direct-burst-banktradeoff-fast01` (front CAN1/HUD1, canonical2/HUD2 writers:10724 tiles+670 HUD words), each384000 exact pixels/zero underruns. These are raw write-capacity controls: actual reference-copy/decode/root scheduling remains a separate, unqualified workload. `frozen-port-contract-pipe-v002.json` binds the current same-port candidate to these exact proofs. The base owner and its frozen contract remain unchanged. The pin fixture is exported from the independent native decoder/render oracle. Canonical/HUD memory is testbench-preloaded, so that experiment is not a decoder or write-path proof.

Historical failed attempts are retained. `direct-owner01` incorrectly pulsed testbench prepared-ready without guaranteeing a memory edge. `direct-owner03/04` failed because the synthetic adapter did not hold abort acknowledgment to a sampling edge. `direct-pin-fast01/02` initially mistook a naturally black first pixel for a whole missing line; the corrected monitor checks the LCD's actual line-valid state and separately checks every physical BL8 payload. These were testbench corrections, not hidden RTL fixes.

No direct-profile hardware playback, complete CU66 root integration, concurrent decode cadence, 30 unique displayed fps, routed timing or board/PVT signoff is claimed.
