# Actual Rust receiver + STB1 full-system functional gate

This isolated experiment binds the exact V52 network driver, local bus trait, framing, STB1 state machine and Rust HUD FFI to the selected STB1 board candidate's decoder/controller, SDRAM pin model and scanout. It uses the existing qualified host05 native DLL, whose complete C++ source hashes match V52. It does not change firmware, the frozen board overlay, Vivado or hardware.

`main.rs` is the new host adapter. It owns a WSL Verilator subprocess and implements `local::Bus` using its binary CSR RPC. The Rust driver's ordinary metadata/mailbox/HBU batching methods issue their real logical operations through sequential RPC reads/writes; these are not physical SPI transactions. Raw staging descriptor/payload overrides retain the 1,024-byte limit, numeric big-endian word serialization and actual descriptor/fence checks. A finite `Source` supplies the original KEY0/P1 fixtures, verifies stored-prefix progress and snapshots actual SDRAM and one complete raster only after the real Rust driver reports presentation. Real native Prepare, HBU write/readback, drain, software commit and presentation logic execute unchanged.

Each `Source.active(NATIVE)` advances the actual RTL, SDRAM model, refresh and display by 200,000 virtual microseconds before the native call. Native C++ execution itself does not advance the virtual clock, so `hud_cpu_us` is deliberately zero. This models a fixed service delay, not target CPU speed or 30 fps. Every direct CSR RPC advances eight core cycles; core is 100 MHz, accelerated powerup is 20 cycles, refresh 750 cycles, SDRAM AC/OH 2.223 ns and flight 0.757 ns. The existing memory/display model remains active through the explicit delay and full raster snapshots. Runtime uses host64 allocation without the target physical reserve callback. Full board SPI/CDC/PLL, ESP-IDF, radio and DMA are absent; separately retained pin-level gates cover the selected endpoint/CDC/staging path.

`bindings.json` pins original full-system bindings, exact copied Rust sources/native DLL, native source identity, harness sources and assumptions. `compile-command.json` contains the complete actual RTL source list. `driver.cpp` differs from the prior qualified RPC wrapper only in its output directory. The original V027 experiment and earlier Python composition outputs stay preserved. An initial path-substitution preparation error is retained as `initial-compile-wrong-path.log` and `initial-run-missing-server.log`; that invocation had no simulation server and is not a qualification pass.

Commands (PowerShell, under C:/moon; compilation and replay logs are one-shot files):

```powershell
python C:/moon/dev/experiments/stb1-real-rust-system-20261108/compile.py
$env:TEMP='C:/moon/tmp'; $env:TMP='C:/moon/tmp'
C:/Users/lavat/.cargo/bin/rustc.exe +stable --edition=2021 C:/moon/dev/experiments/stb1-real-rust-system-20261108/main.rs -L native=C:/moon/dev/experiments/stb1-real-rust-system-20261108 -l dylib=hud -o C:/moon/dev/experiments/stb1-real-rust-system-20261108/actual-rust.exe
python C:/moon/dev/experiments/stb1-real-rust-system-20261108/run.py
python C:/moon/dev/experiments/stb1-real-rust-system-20261108/compare.py
```

The comparison independently checks every canonical byte, all 691,200 video pixels, black simulated borders and all 42,240 displayed HUD words against retained goldens. Passing counters alone are insufficient. These are retained original small KEY/P fixtures, not the later 120-second Mass Effect clip. The supported raw staging contract remains at most 256 words/1,024 bytes per alias transaction. The separate pin diagnostic demonstrates that an oversized 257th raw word wraps to CSR000 without a hardware fault; longer raw bursts can reach writable CSRs. This is an explicit driver precondition, not arbitrary-burst fail-closed hardware qualification.
The independent comparison uses unchanged simulation placement: 720x480 video in an 800x480 raster at horizontal origin 40. It does not qualify physical margin 13 or LCD porch settings.


Final result: PASS_EXACT_V52_RUST_STB1_FULL_SYSTEM_KEY_P_COMPOSITIONAL. Both frames accepted/presented; no rejects/underruns. Actual HBU words written and verified 42,240 each. Both 518,400-byte canonical banks, 691,200 composed video pixels and 42,240 displayed HUD words exactly match goldens, with no black-border errors. Replay 411.609 seconds; selected SDRAM model: 626,904 reads, 856,320 writes and 66,841 refreshes. Native host arena peak 88,942 bytes, allocation failures 0. Fixture and qualified-manifest hashes also independently rechecked. See result.json, comparison.json, bindings.json and raw logs.
