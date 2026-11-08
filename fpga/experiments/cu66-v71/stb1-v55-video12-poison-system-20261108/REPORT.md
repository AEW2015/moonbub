# Selected V028/V55 twelve-frame nonzero-SDRAM functional gate

PASS: the authoritative result is layout-v2/result.json. The selected V028/V001 production RTL, actual V55 Rust/native/HBU driver and full selected decoder/SDRAM/scanout model completed all twelve new local video frames. This is the selected fallback receiver, not the CE-factor variant. All 37 executed input files and selected production RTL identities were checked; the only functional environment delta from the completed zero-init twelve-frame control is the reviewed SDRAM model initial fill. Output paths and the finite wall timeout were adjusted separately.

| Check | Result |
|---|---:|
| Accepted / presented | 12 / 12 |
| Rejected / underruns | 0 / 0 |
| Actual HBU words written / verified | 253,440 / 253,440 |
| Canonical bank bytes compared | 6,220,800; zero mismatches |
| Composed video pixels compared | 4,147,200; zero mismatches |
| Displayed HUD words compared | 253,440; zero mismatches |
| Simulated border mismatches | 0 |
| Native logical arena cap / peak | 98,304 / 95,053 bytes |
| Largest native allocation / allocation failures | 16,384 bytes / 0 |
| Simulator wall time | 2591.515 seconds |

The actual memory fill witness passed once: evaluated MEM_WORDS=16,777,216; mem[0]=8fa1, mem[1]=15c7 and last=d9c7. The same initial block asserts those actual array values before the first clock. Model SHA-256 is `5af3451e4ab30cc8c3a81e8d1054eb922b27fa8fbdcf6a93ae642cc133ae3468`. Each address-dependent folded word is OR 0x0101, so neither byte is zero. The marker is buffered until process shutdown; final verification requires its runtime occurrence and values, not its source text. See runtime-witness-result.json.

Every completed canonical/pixel/HUD hash is identical to the independent references and to the separate zero-init control. Model reads/writes/refreshes are 6,509,544 / 5,137,920 / 410,510, also identical. zero-poison-comparison.json records this equality without changing either control. Only independently known presented front data is compared. Unowned banks are excluded. Front banks alternate exactly 0/1; bank 2 was not selected or forced. Other two-state model state remains unchanged, so this is not a four-state unknown-memory proof or coverage of every possible starting data pattern.

The transition is explicit and successful: actual packet HU bytes are HX33 for frames 0?8 and HU25 for frames 9?11. HU25 P9 references HX33 frame 8. Frames 8?11 each completed actual native Prepare, HBU write/readback, native drain/commit and real model presentation, with zero independent canonical/pixel/HUD/border differences. envelope-boundary-result.json preserves those results and bank reuse. No new-video12/HU25 coverage is inherited from either two-frame CE test; this run executes the selected production receiver directly.

These are twelve distinct first decoded frames of local motion-test.mp4, source PTS 0 through 0.366667 seconds, prepared 720x405 at (0,37) inside 720x480 with no loop or temporal resampling. It is not the 120-second Mass Effect sequence, live capture or a live CU66 encoder. Already independent native-v69 and frozen-Python outputs were reused unchanged. The selected oracle is explicitly layout-v2/goldens, including the independently proved tile-major canonical bank layout. All 48 reference files matched the corrected zero-init control before launch and after execution. Top-level goldens contains historical planar references only and is labeled PLANAR-ONLY.md; its misleading legacy canonical.u16 filenames are never selected for raw-bank comparison. No new reference came from DUT output.

This is functional evidence, not physical speed. Each direct CSR consumes eight 100 MHz model cycles; each host yield advances 100 us, while the actual Adapter uses thread yield without a fixed sleep and the ESP timer. Every Prepare has an explicit 200 ms service delay while RTL/SDRAM/scanout tick. Native callback CPU virtual time is 0. Poll quantization and raster observation contribute to virtual elapsed time; neither that time nor simulator wall time is a physical QSPI/CPU/FPS or 30 fps result.

Reset, real SDRAM init-command behavior and clocks are unchanged. Accelerated powerup 20 and refresh 750 remain model parameters, with AC/OH 2.223 ns and flight 0.757 ns. The digital memory/refresh checks remain active. No full routed/SDF behavior, board SPI/CDC/PLL, SDK/radio/DMA, physical LCD margins/porches, target heap fragmentation/reserve/stack, malformed/stale/recovery injection or app-only failure-hook coverage is claimed. Native logical peak headroom is only 3,251 bytes and does not prove target heap safety.

Frozen source binding SHA-256: `12cfc36218601ff904bdee3805d589c17e19e1fdc33efd79c5dbd1b0489af76d`. Selected result SHA-256: `bb15062235a8938f273458eadec864a24626b4610e93e6ef4f1ead04d9bfd2c9`. Independent comparison SHA-256: `5d3ac3b7c58ad51f84cf42e62e339099f8500cd5c89bff6c21e4d6b8ec31f4b8`. Source/native/executable/packet/reference/tool hashes were checked after execution; the runtime witness was mandatory. There was no retry, target ELF execution, hardware write or Vivado operation. The selected baseline and all prior evidence remain intact. Active experiment footprint, including disposable Verilator build products and raw comparison data, is 288,675,524 bytes, wholly under C:/moon.
