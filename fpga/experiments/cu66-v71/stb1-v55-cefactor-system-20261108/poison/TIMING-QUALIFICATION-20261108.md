# Qualification of modeled time in the STB1 actual-Rust system replays

The V52 pair, V55 pair and V55 new-video12 experiments are functional compositions, not physical throughput measurements. Their host Bus implementation advances the selected RTL model by a fixed 100 microseconds each time Rust calls yield_now. The target V55 Adapter instead calls std::thread::yield_now with no prescribed 100-microsecond sleep and reads the real ESP timer. The host adapter reads a virtual clock. A model yield therefore affects polling quantization, phase timing, deadlines and elapsed virtual time differently from the physical scheduler.

Each direct CSR read/write costs eight 100 MHz core cycles in the model. Batched methods execute logical sequences of those accesses; physical SPI headers, dummy clocks, DMA, mutex/SDK scheduling and radio are absent. Each Prepare also has an explicit 200,000-microsecond service delay while RTL, SDRAM and scanout tick. The native C++ callback itself pauses virtual time; its reported CPU timing is consequently zero. Raster snapshots add model cycles. The new12 elapsed 3.119268 seconds includes these chosen delays and observation work; it must not be converted into a physical decoder rate or treated as a 30 fps result. Host simulation wall time measures simulator cost only.

These assumptions apply to the immutable main.rs executed in:

- C:/moon/dev/experiments/stb1-real-rust-system-20261108 (V52 pair).
- C:/moon/dev/experiments/stb1-v55-cefactor-poison-real-rust-system-20261108 (V55 pair).
- C:/moon/dev/experiments/stb1-v55-video12-real-rust-system-20261108 (V55 new-video12).

Each file's yield_now is at line 21. The physical contrast is V55 handheld/src/cu66/local_usb.rs lines58–59. This note supplements frozen evidence without changing original source, logs, bindings or result files. Future CE-factor pair replays must record the same fixed-yield assumption explicitly. The earlier Python-oracle composition has its own RPC/poll schedule and explicit service delay; its timing likewise is not physical performance and should not be silently equated with Rust's 100-microsecond yield.

The SDRAM model has no explicit memory-array initial fill; this Verilator context uses its default randReset=0, so unwritten model SDRAM starts at zero. It does not model four-state unknown powerup or a poison-filled array. Accelerated POWERUP_CYCLES=20 and REFRESH_CYCLES=750 at 100 MHz, AC/OH 2.223 ns, clock flight 0.757 ns and the selected digital read/hold policy remain test assumptions. Observed serialized front banks alternate 0/1; bank 2 is unexercised. Host64 native allocation enforces the 98,304-byte logical arena cap but does not reproduce target heap fragmentation, reserve probes, SDK task stacks or physical clock/timing effects.
