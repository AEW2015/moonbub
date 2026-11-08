# STB1 KEY/P full-system functional replay

**Completed:** `result.json` reports `PASS_STB1_KEY_P_FULL_SYSTEM_COMPOSITIONAL`. The pair presented with no rejection, underrun or native staging fault. All canonical bytes, 691,200 composed video pixels and 42,240 displayed HUD words matched. Compilation took 53.5 seconds and replay 410.5 seconds wall time; these are tool execution times, not playback throughput.

This fresh experiment reuses the previously qualified exact-selected-V027 full-system harness from `C:/moon/maintenance/v45-system-cached5`, preserving that baseline. It reads frozen board-overlay sources from `C:/moon/builds/stb1-v001` without modifying them. The replacement controller has the module-name-only adaptation recorded by `overlay-binding.json`, and the new STB1 module is added to the original selected source list.

The replay uses the actual decoder, metadata/reference/cache pipeline, memory arbiter/controller, SDRAM pin-level functional/timing-check model, HUD service interface, native staging RAM, presentation path, pixel pipeline and LCD line/rotation model. The same vendor RAMB18E1 model and file-specific unused-ECC lint exception are retained. It does not instantiate the board PLL/IOBUF/QSPI/CDC; the latter transport has a separate actual-pin gate under `../evidence/pins08`.

`service_pair.py` uses the abstract STB1 batching protocol against the real controller CSR bus, then services each actual FPGA HUD request using the pinned actual V48 C++ native endpoint. All HUD words are written through the real HBU1/AUX/SDRAM path and read back for byte-exact comparison before the native external-drain ACK. Native commit occurs only in response to the real typed software request, and presentation/canonical tag checks follow the real pipeline. No CPU ACK or readback result is fabricated.

## Timing and memory assumptions

- Core: 100 MHz. Read-clock edges at 2.625/7.625 ns in each model tick give the selected 7.625 ns relative phase to the core rising edge at 5 ns.
- Pixel clock: 17.029 ns half-period.
- SDRAM model: 16,777,216 words, `T_AC_NS=2.223`, `T_OH_NS=2.223`, flight delay 0.757 ns. Original command/burst/mask/refresh checks and backpressure remain enabled.
- Initialization is accelerated to 20 core cycles in this functional harness; refresh interval remains 750 cycles. This is not power-up timing signoff.
- The actual host native endpoint uses the same 98,304-byte arena cap. Host allocator/ABI behavior is not an ESP32 fragmentation or physical-reserve model.
- Every native Prepare is followed by an explicit **200,000 microsecond modeled service delay** while RTL/memory/refresh/scanout continue running. Actual host callback wall time is recorded separately. Native READ/other callbacks remain outside HDL virtual time. Neither zero-time callbacks nor this selected delay establish target CPU throughput.
- CSR RPC operations advance eight core cycles. These are functional CSR transactions, not a physical QSPI timing or ESP-IDF overhead model.
- Raster snapshots pause next-frame admission until a complete physical raster has been observed. This adds interframe delay and prevents FPS inference.

## Independent outcomes

The run is not complete until `compare.py` and `finalize.py` succeed. It requires:

1. KEY0 then P1 with exact native/FPGA reference identities, real external drain and real software commit.
2. Two accepted/presented frames, no rejections/underruns/native staging faults, and 42,240 actual HUD SDRAM words written/read/compared across the pair.
3. Every canonical-bank byte compared to the separately retained fresh reference.
4. Every one of 345,600 composed video pixels and both 40-column simulation borders compared per frame.
5. All 21,120 displayed HUD RGB565 words independently reconstructed from each actual output raster and compared to the retained golden HUD words.
6. Real SDRAM read/write/refresh activity and successful model termination, with no assertion bypass.

Fixtures come from the retained qualified `v45-sequence/qualification` source, not the requested later two-minute clip. `fixture-binding.json` verifies their packet hashes against the pinned qualified manifest and pins the canonical/HUD/RGB565 references. Finalization rechecks all source, native-library, overlay and fixture hashes.

## Artifacts and reproduction

`compile-command.json`, `compile-result.json`, `native-compile.json`, `tool-versions.json`, `source-binding.json`, `fixture-binding.json`, stdout/stderr and all per-frame canonical/raster dumps retain this exact execution. Tools were Verilator 5.053 devel (recorded revision), Ubuntu g++ 11.4.0 and Python 3.11.6. Compilation and native replay wall times are recorded separately.

The source files are replay inputs, while `build/` is a disposable compiler cache after qualification. Preserve the small source/bindings/fixtures/reference outputs and final result before pruning the cache. Do not rerun into these result files: the top-level wrappers reserve unique logs. A fresh sibling experiment must rebind the absolute C++ snapshot-output path and compile/run paths before replay.

The one-shot sequence used here is:

```powershell
python compile.py
# Native build command is recorded in native-compile.json.
python run.py
python compare.py
python finalize.py
```

Only a final `result.json` with `PASS_STB1_KEY_P_FULL_SYSTEM_COMPOSITIONAL` qualifies this experiment. The result is functional compositional evidence, not full-board routed timing, physical SDRAM/IO margins, hardware playback or 30 fps acceptance.

## Separate oversized-raw-transaction limitation

`wrap-diagnostic.py` and `wrap-limit-v001` deliberately send 257 raw u32 words in one alias SPI transaction. The 257th word wraps to ignored CSR `0x000`; no STB fault is raised. The result is `LIMITATION_CONFIRMED_OVERSIZED_RAW_SPI_OUTSIDE_CONTRACT`, **not** fail-closed qualification. Supported drivers must enforce a maximum of 256 u32 / 1,024 bytes before any descriptor or SPI write. Longer malformed raw transactions can reach writable legacy registers. Root chose this explicit supported-driver precondition for the frozen build; no RTL, overlay or current route input was changed.
