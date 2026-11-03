# 30 fps investigation: parallel verification progress

- The existing 64×64 JPEG/core/memory test passes in Verilator 5.020: three
  JPEG decodes, two manually triggered frame publications, 12,288 pixel writes,
  functional SDRAM model readback and injected error recovery. It does not run
  the real LCD timing, real SPI, ESP32, a live stream or 30 fps. Its memory
  scoreboard checks against the RTL decoder's own output, not an independent
  decoder. `fpga/experiments/throughput30/run-pipeline64-verilator.sh` rebuilds
  and runs it; `pipeline64-verilator.log` is the saved result.
- The instrumented test exports its first decoded frame. Pillow independently
  decodes the same fixture: 1,593/4,096 pixels have equal RGB565, and the
  greatest observed component difference is two quantized channel units. This
  is a single-fixture comparison and not a general correctness tolerance. See
  `experiments/fixture30/` for fixtures, two-version hash reproducibility, the
  comparison and how to rerun it.
- A separate unintegrated BL8 SDRAM controller candidate passes Verilator and
  XSim on 1,200 aligned bursts, 9,600 written words, 40 checked eight-word reads
  and 305 refreshes. The model is derived from the controller assumptions and
  is not an independent SDRAM timing model. The candidate is not tied to scanout
  or the JPEG decoder, requires pre-aligned input, and does not prove 30 fps.
  Details and excluded cases: `fpga/experiments/throughput30/burst/README.md`.
- Renode's [maintainer clarification](https://github.com/renode/renode/issues/704)
  distinguishes Xtensa/ESP32 core translation and a UART peripheral from a
  full ESP32 SoC. Its [generic Xtensa sample](https://github.com/renode/renode/blob/master/platforms/cpus/xtensa-sample-controller.repl)
  is not the ESP32-S3 Game Bub platform. The current target firmware uses
  ESP-IDF Wi-Fi, FPGA SPI and other board peripherals; no real-firmware boot or
  Renode–Verilator co-simulation has been demonstrated here. The
  [Espressif emulator](https://github.com/espressif/esp-emulator) is an option
  to investigate, not proof that Wi-Fi, QSPI or this firmware will work.

The next decisive result is an end-to-end benchmark with burst writes and
simultaneous LCD fetch and checks of the actual display swap. Compare decoded
pixel output against a characterized independent reference, and do not count
LCD refreshes as new video frames. Simulation remains distinct from real board
measurements and Artix-7 implementation timing.

## Follow-up results

The full original memory/LCD test now passes under Verilator after a
verification-only clock scheduling change; it reproduces both prior XSim cycle
counts exactly on this trace. See `renode-verilator-assessment.md`. A separate
Verilator component test generates and decodes 10 distinct 64×64 JPEGs,
verifies 40,960 writes and checks 10 ordered published IDs with manually
injected frame boundaries. It uses the decoder's own output as its memory
reference and has no actual LCD timing, ingress or FPS workload. See
`experiments/fixture30/README.md`.

The experimental BL8 collector and writer have since been connected to the
real tile reorder and LCD line requests in a one-frame memory-path replay.
Both XSim and Verilator reported **2,165,697 cycles (21.65697 ms at 100 MHz)**,
345,600 verified back-buffer pixels and zero modeled scanout underruns. This
meets the 33.33 ms memory-write budget for that one saturated replay, but the
front buffer is fixed and the test excludes decoder, networking, QSPI and frame
swaps; it is not a displayed 30 fps result. The model is not an independent
SDRAM timing signoff. See `fpga/experiments/throughput30/burst/README.md`.

The instrumented 64×64 decoder's 4,096 pixels also matched a separately
compiled fixed-color C-model output exactly. The model uses related upstream
algorithms and RTL-matched color arithmetic; this is stronger than comparing
memory against decoder output but is not a fully independent decoder. See the
Pillow comparison for an independent implementation.

Finally, a single checked-in 720×480 synthetic q65 JPEG was decoded through the
actual JPEG core, tile transpose, experimental burst collector/controller,
functional SDRAM model and running LCD scanout. XSim and Verilator both
reported 2,537,677 cycles (25.37677 ms at 100 MHz) from **after compressed-frame
upload/commit** to the first display swap, including wait for that boundary;
345,600 unique pixel writes, 43,200 bursts, a single presented frame ID and
zero new modeled scanout underruns. All pixels matched the fixed-color C model,
which shares upstream algorithms with the RTL. The independently decoded Pillow
image matched 224,931 RGB565 pixels exactly and had a maximum component error
of 15 quantized units; investigate the discrepancy and visual quality. See the
burst README and exact logs. This is one synthetic frame and excludes network,
QSPI and continuous multi-frame operation. It is not an end-to-end FPS result
or proof that all game scenes fit the budget.

## Ten-frame cadence and parser fault

Ten synthetic 720×480 q65 JPEGs were scheduled at 30 Hz. With the unmodified
JPEG input and no external queue, frame 4 arrived while the preceding frame
was pending; the test failed explicitly. With a hypothetical one-frame external
queue, frame 7 independently exposed an ungated SOF marker side effect: during
an invalid/stalled input cycle the decoder cleared width/height. The preserved
diagnostic identifies the byte values and confirms the actual JPEG was valid.

With an **experimental, unintegrated SOF guard** and the abstract external
queue, XSim and Verilator presented all 10 frame IDs with no modeled drops,
queue overflows or LCD underruns; output dumps match across simulators and
match the related C model. The 9 presentation intervals cover 307.33531 ms,
or 29.284 fps, and maximum modeled arrival-to-present age was 36.06722 ms.
All compressed inputs arrive instantaneously in the test, the buffer does not
model ESP32 memory or networking, and the transfer to the core uses an
optimistic synthetic register bus. This is not a 30 displayed fps pass, a
60-second stability test, hardware proof, or a verified deployed fix. The guard
covers only SOF0 metadata; audit other marker side effects before integration.
See `fpga/experiments/throughput30/burst/README.md` and its saved pass/fail logs.

The independent Pillow discrepancy is analyzed in
`experiments/jpeg-discrepancy/README.md`: edge clustering and a combined
nearest-style upsampling/fast-IDCT setting point to upsampling as a likely
contributor, but the experiment does not isolate its cause or establish an
acceptable visual tolerance.
