# 30 fps throughput investigation — 2026-11-02

**Result: this simulation does not establish 30 fps.** With the current
single-pixel SDRAM write controller, the modeled memory path exceeds the
33.333 ms/frame budget even before input, JPEG decode and frame publication.
The tested transpose prototype improves locality, but also exceeds the budget
when the existing LCD scanout competes for memory. Burst writes or a different
memory/display architecture are candidates for the next iteration.

This is a simulation-only branch. It does not alter the delivered bitstream,
firmware, service or physical board. No real display FPS or latency is claimed.
The base receiver revision is `75f8497b6ffefadd8c0403728b93ccfbbfa02f52`.

## Experiments

Vivado 2025.2 XSim behavioral RTL replayed the checked-in
`fpga/sim/decoded-rgb565.txt` trace: 345,600 pixels, in the decoder's 8×8 block
order. SDRAM controller, LCD line fetch and arbitration are the checked-in RTL;
SDRAM is the repository's **functional model, not a vendor timing model**. The
100 MHz memory clock and approximately 29.362 MHz pixel clock are modeled.
The LCD test preinitializes the front buffer, warms the line-fetch path, then
streams the decoded back-buffer writes as fast as accepted. It poisons all
back-buffer locations first and verifies every written pixel after each run.
Refresh is enabled. These tests omit JPEG decoding time, QSPI/ESP32/network
input, and real frame-presentation scheduling; the test fixture is one image.

| Workload | 100 MHz cycles | Time per 345,600 writes | Reciprocal rate | LCD underruns during test |
| --- | ---: | ---: | ---: | ---: |
| Current order, no scanout | 4,748,791 | 47.49 ms | 21.06/s | Not applicable |
| Offline sorted order, no scanout | 2,459,661 | 24.60 ms | 40.66/s | Not applicable |
| Actual transpose RTL, no scanout | 2,761,887 | 27.62 ms | 36.21/s | Not applicable |
| Current order with LCD scanout | 8,875,956 | 88.76 ms | 11.27/s | 0 |
| Transpose RTL with LCD scanout | 5,310,461 | 53.10 ms | 18.83/s | 0 |

The reciprocal numbers are **write-service estimates, not displayed FPS**.
The zero underruns only cover these runs and startup phase. The contended tests
generate real LCD line requests, but do not replay a complete continuously
streaming decoder or exercise frame swaps. A faster decoder cannot overcome
the simulated saturated write path in this configuration. Conversely, an
improved writer meeting this budget would not alone prove the complete system
meets it.

`moonbub_tile_transpose.sv` is an isolated, single-block buffer; it validates
input order, transposes one 8×8 RGB565 block and emits eight aligned groups,
but **does not implement burst writes**. The existing SDRAM controller remains
single-write. Its short XSim bench tested stalls, abort and malformed addresses;
its separate full-trace bench checked every pixel of this fixture. The
coalescer-to-controller experiments also checked all output memory locations.
Both tests use generic RTL. This container's Vivado installation lacks the
Artix-7 part, so the behavioral project selected an available `xck24` part;
there is no Artix synthesis, place/route or timing result for the candidate.

## Reproduce or inspect

Sources and transcripts are under `fpga/experiments/throughput30/`:

- `tb_sdram_throughput.sv` tests the current SDRAM controller and coalescer
  without scanout; `tb_memory_throughput.sv` adds the existing memory arbiter
  and LCD. Both take `+TRACE_FILE=/absolute/path/to/decoded-rgb565.txt`.
- Add `moonshine_sdram.sv`, `moonshine_memory.sv`, `moonshine_lcd.sv`,
  `moonbub_tile_transpose.sv`, `sdram_model.sv` and the desired testbench to a
  Vivado behavioral XSim project. Define `SIMULATION` in the simulation
  fileset. The trace is `fpga/sim/decoded-rgb565.txt` in this repository.
  The memory test's internal watchdog is 500 ms of simulated time; do not run
  without a bounded runtime or the watchdog.
- `tb_tile_full_trace.sv` checks the transpose independently; the short bench
  checks stalls and abort behavior. A PASS marker, not a clean launch, is the
  verdict. Logs in this directory contain the observed PASS markers.

## Physical-system context and next gates

A separate Windows host report records individually displayed fixtures at
conservative rates and a video-only ~1 fps game diagnostic; those are physical
observations, not results of this simulation. See the Sunshine fork's
`tools/gamebub/measurements/handheld-fixture-bringup.md` and
`handheld-live-game-test-01.md`. The physical sequence errors at higher trial
rates do not identify whether Wi-Fi, receive buffering or QSPI was responsible.

1. Implement an isolated burst-capable write path with correctly timed SDRAM
   data, mode-register configuration, scanout priority, refresh, backpressure
   and abort semantics. Compare its pixels with the current controller.
2. Run the same contended full-frame test and then a full JPEG decode/scanout
   simulation over multiple frames. Record cycle counts and all underruns.
3. Build for the actual Artix-7 and validate timing, IO constraints and device
   memory margins; the currently available tools container lacks that part.
4. On the separately managed hardware, measure simultaneous Wi-Fi/QSPI ingress,
   decoded and presented frame counters, frame age, underruns and controller
   behavior with representative moving content. Measure capture/encode on the
   Windows host too. Only sustained 30 **displayed** fps under the agreed
   quality, loss and latency conditions completes the proof.
