# Final V44 native / V027 functional replay: PASS

November 7, 2026 (America/Denver). Fresh repeat after the targeted HS plain1 immutable-reference prediction borrowing fix. Original V027 selected RTL is unchanged. No hardware or UDP transmission.

The actual final V44 native HUD header hash is `cd65e262b66efe5e5b70db685b8f6cc417d35c113cb34b902d23a49b6d77bd70`. The DLL/import library and Rust driver/RPC harness were rebuilt against it. Native arena limit is the original **98,304 bytes**, with measured host peak **92,379 bytes**, rather than the earlier old-native peak103,484/enlarged106,496 run. Physical reserve behavior is qualified separately by the target-oriented native heap model and mandatory target guard; it is not simulated by this RTL harness.

## Completed checks

- Actual native/RTL run exit0: **3 accepted /3 presented /0 rejected /0 LCD underruns**.
- **63,360 HUD words** written and actually read back equal through the real native service, bulk CSR/HBU and modeled SDRAM path.
- Front banks0,1,0, exercising reference/canonical-bank reuse across the distinct KEY/P/P sequence.
- Each518,400-byte canonical front-bank dump exactly matches the independently prepared tile-packed reference.
- All345,600 active-image pixels per stable frame exactly match the software reference: **1,036,800 matched pixels**, zero mismatched black side-border pixels.
- Frame2 canonical hash remains `d62337bc14c9273cd9e1c22f67c99b887be69737ab85b166b12735048dc749a5`.
- All67 bound source/helper/native-library hashes and every fixture manifest hash/length rechecked by `finalize.py`.

The unchanged functional trace ran23,031,653 core clocks,437,568 modeled reads,1,284,480 modeled writes and30,327 refreshes. Native/RTL wall time249.672s, Verilator build49.312s. These are simulation wall times, not device throughput.

## Evidence and limits

`result.json` is the final receipt, binding the executed Windows harness, Linux simulator, fresh native DLL, exact source/commands/logs and per-frame comparisons. `comparison.json` contains each actual/expected canonical hash and pixel/border mismatch counts. Earlier `system-three-frame` evidence is preserved separately and does not certify this revised native candidate.

Official AMD RAMB18E1/glbl sources are unchanged. The declared vendor-file BLKANDNBLK suppression concerns unused ECC/status outputs only; all production functional assertions remain active. Actual bulk memory write/readback and output equality pass. Source/core/control assertions were not waived.

Physical QSPI/transport CDC, PLL/reset distribution, board analog/timing margin and ESP32 scheduling are omitted by the functional wrapper. Native computation advances no virtual CPU time. Eight core cycles are modeled per CSR transaction. The inherited fast SDRAM model uses T_AC2.223ns/flight0.757ns/T_OH2.223ns and command/refresh behavior; no new slow-corner run is claimed.

Full stable-raster capture pauses the next admission, so this is not a streaming-FPS result or an exhaustive scanout-transition mixed-generation proof. The retained three-frame corpus is not the user's requested120-second source. This gate supports the bounded three-frame correctness hardware trial once the final target app/package/identity and network/heap prerequisites pass; it does not establish readiness for a long custom-codec video stream.
