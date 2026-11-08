# Actual V55 + CE receiver + new parser: twelve-frame functional PASS

All twelve new local-video frames passed through the exact Rust receiver driver, native HUD FFI, selected RTL decoder, SDRAM model, HBU write/readback, commit and scanout. The actual parser entered the new validation state twelve times. This is a finite functional composition result; it does not establish hardware playback speed.

| Check | Result |
|---|---:|
| Accepted / presented / rejected / underruns | 12 / 12 / 0 / 0 |
| Actual parser state 19 visits | 12 |
| HUD words written / independently read back | 253,440 / 253,440 |
| Canonical bytes compared / mismatched | 6,220,800 / 0 |
| Composed video pixels compared / mismatched | 4,147,200 / 0 |
| Displayed HUD words compared / mismatched | 253,440 / 0 |
| Full raster samples per presentation | 384,000 |
| Front-bank sequence | 0,1,0,1,0,1,0,1,0,1,0,1 |
| Host replay wall time | 2,728.422 seconds |

Frames 0-8 use HX33; frames 9-11 use HU25. The frame 9 P reference to frame 8 crosses that envelope boundary and passes with repeated bank reuse. The twelve source canvases are distinct and span 0.366666667 seconds of the previously prepared local motion-test source. This is not the user's 120-second Mass Effect clip, a two-minute stream or live capture. No re-encoding was performed for this gate.

The selected independent oracle is explicitly layout-v2/goldens: 48 files byte-identical to the prior qualified new 12 baseline. It uses the independently proved tile-major 8x8 canonical bank layout, not planar YUV bytes as a bank oracle. Native-v69 and frozen-Python receipts plus the original independent layout proof are retained. No DUT output was used to generate goldens. The entire new comparison.json is byte-identical to the qualified baseline comparison, SHA-256 `5d3ac3b7c58ad51f84cf42e62e339099f8500cd5c89bff6c21e4d6b8ec31f4b8`.

Two production modules differ versus selected V028: the CE receiver SHA-256 `316123fb1db92d67a797b2a49263500314d5173561a2eff52ef451734f94deb9` and parser SHA-256 `39197a682b894f55d4a9a73ed039e58c0f3bed1aeb3a6cc24139c1c4d5325c56`. The 37 explicit executed inputs contain exactly one new parser path and no old parser path. The remaining selected RTL is unchanged. Three actual include dependencies were checked against the original 79-input source freeze and actual Verilator dependency record, then rechecked after completion. Source-side wrapper and C++ changes only expose/count hierarchical state 19 and require exactly twelve visits; no production interface was altered for the witness.

Exact V55 Rust and the host01 native DLL/import are preserved. The native logical allocation cap was 98,304 bytes, peak 95,053 bytes, largest request 16,384 bytes, 410 allocation calls and zero failures. These are host/native allocator observations, not proof that the ESP32's fragmented physical heap or target stack will pass. The target ELF, SDK, radio path and app network-failure diagnostic hook were not executed.

Model assumptions remain direct CSR accesses of 8 cycles at 100 MHz, modeled yield 100 us, explicit Prepare service 200 ms per frame and native CPU virtual timer 0. The physical adapter uses thread yield without a fixed sleep. SDRAM starts at default zero; powerup 20/refresh 750 are accelerated functional-test parameters. Model clocks, reset and memory timing remain unchanged. Model counts are 6,509,544 reads, 5,137,920 writes and 410,510 refreshes, identical to the prior baseline. Host wall time and virtual stage times are not physical throughput. No SDF, poisoned or unknown memory, bank 2, malformed/stale/recovery traffic, SPI/SDK timing, target memory safety, routed timing or hardware qualification is inherited into this run.

Preparation history is preserved. Before compilation, a guard caught a missing packet-directory copy; the copy was completed before any binding was frozen or simulator ran. Root review then caught a stale original-pair source label in the new 12 assumptions; the old binding is retained under preparation-history and the final label was corrected before launch. The related pair's earlier Windows/WSL path compile failure is preserved in its separate sibling package. This new 12 compile and replay each ran once, without a whole-run retry.

Authoritative evidence is result.json, layout-v2/comparison.json, bindings.json, header-source-postrun-check.json, baseline-output-comparison.json, native-run.log, rtl-stderr.log and final-check.log. Their source and data hashes were checked after completion. No Vivado or hardware action was performed for this replay.
