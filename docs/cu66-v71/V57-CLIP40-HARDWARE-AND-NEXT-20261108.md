# Longer custom-codec hardware test and next memory work

The no-pause forty-frame test **did not complete**. V56 presented frames 0â€“7; its first allocation issue was repaired in V57, which then presented frames 0â€“16 before encountering a second allocation failure. The twenty-second source interval is not qualified for complete hardware playback. Neither run establishes 20 fps or 30 fps.

| Physical observation | V56 | V57 |
|---|---:|---:|
| Frames presented | 8 | 17 |
| First failing frame | 8 | 17 |
| Requested allocation | 16,384 bytes | 7,680 bytes |
| Reported free heap at failure | 58,740 bytes | 27,476 bytes |
| Largest free block | 15,616 bytes | 7,168 bytes |
| Native allocation-failure kind | 3: actual malloc failure | 3: actual malloc failure |
| FPGA accepted/presented at failure | 8/8 | 17/17 |
| FPGA rejects/underruns at failure | 0/0 | 0/0 |

Both failures occurred during native HUD Prepare, after complete packet staging. These passive FPGA counters are failure-time observations, not a complete all-core fault snapshot. The largest-block probe is diagnostic; it did not itself reject the allocation. The allocator attempted malloc and received failure.

The source and packets stayed the same across the two runs: a local rendering-breakdown clip covering a twenty-second interval, sampled at 2 fps without looping, center-cropped to 16:9 and scaled to 720Ã—405 at (0,37) in the 720Ã—480 canvas. Preparation used RGB444 and uniform legal q32. This is not the Mass Effect source, live Sunshine capture or a quality/performance comparison. It has 40 distinct prepared frames, one KEY followed by 39 dependent P frames. The sender added no inter-frame pauses and stopped at the first matching status-3 failure, withholding subsequent frames.

The V57 sender ran for 25.328 seconds **including its initial Wi-Fi/receiver wait**. That is not 25 seconds of successful video. Frames 18â€“39 were never transmitted. Two complete 23-record exports agree on checksum `6acef56c`; underlying USB transmit-loss count remains unknown. The camera covered the panel, and the final image remains held. No restart, retry or FPGA programming followed this failure.

## What was fixed

The first call stack identified geometric growth in `decode_full_patch`: a validated 7,680-word HR01 output needs 15,360 bytes, but vector growth requested capacity for 8,192 words, or 16,384 bytes. V57 reserves exact validated sizes in the full-raw, HP01, HR01 and HD25-raw branches. Its native HUD hash is `92171e1573dc78173b12f5739dc632d09d473daefa3186e286344bdd57b784e0`.

Original twelve-frame and new forty-frame independent HUD comparisons pass. The isolated old frame-8 contiguous-allocation failure now passes all forty frames. Four direct branch checks and malformed-input checks pass. The new forty-frame native peak falls from 96,964 to 90,307 bytes. The 98,304-byte arena limit, 8,192-byte physical reserve, packet caps and 16,384-byte worker stack are unchanged. Target build, 213 Rust tests, native tests, production UF2 parsing and static SRAM/configuration checks pass. Physical V57 passed the previous failure at frame 8, so this was a useful fix, but it did not solve general fragmentation.

## What the next failure means

The second stack identifies the final HS33 patch's `Vector<uint16_t>::assign` output allocation: 3,840 words, exactly 7,680 bytes. It is not geometric growth, `byte_planes`, or a channel temporary. An isolated late-allocation fault reproduces the failure while retaining accepted frame 16. Host allocation/live-byte figures differ from the ESP32; this is a targeted mechanism reproduction, not an exact TLSF heap simulation.

Next work should compare two bounded designs before another firmware installation:

1. Reserve/reuse private candidate output buffers before transient scratch allocations. Measure the overlap of old accepted pixels, all candidate pixels, cached HC70 input and scratch storage; earlier allocation can move the peak rather than reduce it.
2. Reduce channel scratch lifetimes or stream expansion into private candidate storage. This may reduce pressure, but the failing allocation itself is final output storage and cannot be removed merely by changing `byte_planes`.
3. Preserve immutable accepted-reference rollback, generation checks and failed-candidate cleanup. Never reuse accepted pixels destructively to make a memory test pass.
4. Run exact forty-frame output/oracle and malformed/rollback checks, allocator-event traces, the old frame-8 case and the later frame-17 case. Keep cap/reserve unchanged and distinguish ideal total-byte models from physical contiguous capacity.
5. Build one selected candidate, verify exact artifacts and SRAM, then repeat this identical source/packet sequence with V029 unchanged. Stop on the first failure and retain a complete export. Throughput testing follows successful complete playback.

V57 remains installed: SDK ELF `c2f4fbef591d85409aed7908e90ab132f1b4348c72379881fd1067dc66fc8ae0`. V029 remains the same volatile image, BIT SHA `59a2439488c529941661debcf3f3c75f8fd2f6e61418c3c63a45e377e971e7c3`, DONE=1/USERCODE `44593741`, with the user's accepted 0.000 ns setup slack. This measured blocker is ESP32 memory allocation; no FPGA rebuild is selected for it.

The [V57 source, actual firmware artifacts and evidence](../../firmware/experiments/v57-hud-exact-reserve-20261108/README.md) and [exact forty-packet replay](../../host/dy71-clip40-20261108/README.md) are preserved. Full raw flash backups and Wi-Fi logs remain private under `C:/moon`. App-only updates were read-back verified, preserving updater, partition table and SD files. Windows required fresh device-specific UAC driver rebinding after each software-DFU transition; that limitation remains unresolved. The endpoint is held/quarantined, so a reviewed explicit restart is required before reconfiguration.


Follow-up: [V58 passed the same forty-frame sequence](V58-CLIP40-HARDWARE-20261108.md); V57 failure evidence above remains historical.
