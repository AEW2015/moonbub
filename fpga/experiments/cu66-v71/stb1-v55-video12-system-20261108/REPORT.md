# V55 actual-Rust replay of twelve new local video frames

PASS, with an explicitly preserved and independently corrected oracle-layout error. The authoritative result is `layout-v2/result.json`; full independent comparisons are in `layout-v2/comparison.json`. The original planar references, initial failing raw-bank comparison and original checker are retained. No packet, running Rust/C++/RTL source, clock or setting was changed during the replay.

The exact V55 network driver, local bus trait, STB1 driver, framing and HUD FFI ran against the selected STB1 controller/decoder, actual native HUD code, HBU write/readback, SDRAM model and scanout. A finite Source supplied the packaged frames; real native drain/commit and selected-model presentation completed. Results:

| Check | Result |
|---|---:|
| Accepted / presented | 12 / 12 |
| Rejected / underruns | 0 / 0 |
| Actual HBU words written / verified | 253,440 / 253,440 |
| Canonical bank bytes compared | 6,220,800; zero mismatches |
| Composed video pixels compared | 4,147,200; zero mismatches |
| Displayed HUD words compared | 253,440; zero mismatches |
| Simulated black-border mismatches | 0 |
| Native logical arena cap / peak | 98,304 / 95,053 bytes |
| Largest native allocation / allocation failures | 16,384 bytes / 0 |
| Simulator wall time | 2,722.204 seconds |

The native cap leaves only 3,251 bytes of logical peak headroom. Host64 allocations enforce that cap but do not reproduce ESP heap fragmentation, the physical reserve callback, SDK stacks or radio memory. This is not a claim that the target heap is safe for the same sequence.

The source is twelve distinct first decoded frames of local motion-test.mp4, PTS 0 through 0.366667 seconds, prepared at 720x405 in a 720x480 canvas at (0,37), with no loop or temporal resampling. It is not the 120-second Mass Effect sequence or live capture/encoding. Exact native-v69 and the preserved frozen Python receiver independently produced identical manifest canonical YUV, HUD and display hashes before simulation. All twelve source canvases and all twelve expected canonical/HUD/display outputs are distinct.

The new coverage includes an envelope transition. Actual packet bytes and manifest show HX33 for frames 0?8, then HU25 for frames 9?11. HU25 P-frame 9 references accepted HX33 frame 8. All three HU25 frames passed actual native/HBU/commit/presentation and independent bank, pixel and HUD comparisons. See envelope-boundary.json and envelope-boundary-result.json. Front banks were exactly 0,1,0,1,0,1,0,1,0,1,0,1; bank 2 was not exercised by this serialized sequence.

The initial canonical mismatch was a reference serialization mistake. Package canonical hashes describe planar Y/U/V bytes; raw bank storage is 8x8 tile-major within each plane. Both standard-Python loops and NumPy reshape/transpose independently reproduced the original prequalified KEY/P planar-to-bank goldens before either was applied to the new data. Both agreed for all twelve new manifest-validated planes, and an inverse/random 518,400-byte test passed. The converter read no new DUT output. Selected tile-memory/map source, old reference hashes and new frozen golden hashes are bound in layout-v2/independent-layout-proof.json. No firmware or FPGA fix was selected for this checker error.

Timing is deliberately modeled. Each direct CSR operation consumes eight 100 MHz core cycles; the host yield_now advances the model by a fixed 100 microseconds. The physical Adapter uses std::thread::yield_now with no fixed sleep and reads the ESP timer. Each Prepare also receives a fixed 200 ms model service delay; the native callback itself pauses virtual time, so its virtual CPU timer is zero. Poll quantization and raster observation contribute to the 3.119268-second virtual elapsed time. Neither that value nor simulator wall time is a physical rate or a 30 fps result. TIMING-QUALIFICATION-20261108.md supplements earlier frozen Rust-pair evidence with the same qualification.

SDRAM starts at zero in this Verilator configuration, not poison or four-state unknown. The model array has no explicit RTL fill; generated reset calls VL_SCOPED_RAND_RESET_I and the unchanged context defaults randReset=0. Accelerated powerup is 20 core cycles and refresh interval 750 cycles at 100 MHz. Read-clock edges are 2.625/7.625 ns relative to the modeled core cycle, AC/OH are 2.223 ns and clock flight is 0.757 ns. The digital SDRAM model/refresh checks remain active through service waits and raster capture. See model-assumptions.json and its generated-reset snippet. No full routed netlist or SDF, board PLL/SPI/CDC, ESP-IDF/DMA/radio, physical LCD margin13/porches, or app-only network failure diagnostic hook is covered by this replay.

Exact bindings are frozen. Original running-input bindings SHA-256: `0fb58458ec92475c6d093c53af0f7b64090730b647994c8ae583943da4fcbde3`. Corrected layout proof SHA-256: `1b7382d015a4966a22b549d7476098d57ea259ab20d2e789357b509888873e27`. Authoritative result SHA-256: `2a4b6515e8c8f75879783c1c2d70a9e4fad4086f6636e6947f0ffb3a1b13bd07`. Those receipts pin the five exact V55 Rust modules, all 37 executed RTL/C++ inputs, native DLL/import/executable, package, independent native/Python sources and goldens. The end gate rechecked them after execution. The target ELF was not executed. V52/V55 original pair evidence, selected overlay, Vivado jobs and hardware remain untouched.

Per-phase numbers below are model-only, with the fixed-yield/service assumptions above; they must not be used as physical QSPI or CPU timings:

| Frame | Envelope | Pending to native start | HUD write | HUD readback | Drain to commit ACK | Commit ACK to presentation |
|---:|---|---:|---:|---:|---:|---:|
| 9 | HU25 | 200002 us | 20118 us | 9291 us | 1204 us | 14647 us |
| 10 | HU25 | 200001 us | 20319 us | 9291 us | 1204 us | 14446 us |
| 11 | HU25 | 200001 us | 20319 us | 9291 us | 1204 us | 14446 us |
