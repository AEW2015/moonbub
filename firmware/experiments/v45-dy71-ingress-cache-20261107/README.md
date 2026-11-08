# V45: HU ingress cache, bounded sequences and retained diagnostics

Offline-qualified candidate, November7,2026, America/Denver. **V45 has not been installed or physically tested.** V44/V027's final image/lease remains held. The next controlled hardware window requires a fresh update/power cycle, not a warm mutation of that owner.

## Selected package and unchanged FPGA

`release-ingress-cache-v001` is the only selected package:

- ELF SHA256 `0c263a944775f5523cc7eb316bdacfb44da02c193f444fc5136644b90318f643`.
- UF2 SHA256 `ead4b81da7fe2e697d094acfba2b7d514df7e8500ddfd373742ccf9f24595a12`.
- BIN SHA256 `1dde12ed392e170e129f649b0fde133b31dffecfe2f68424e831ecae19da54f2`.
- Existing V027 BIT remains `9922aa617c21a03e8a31f932d45e22d905e91d4e263ef593692898d363d07dee`, DONE1/USERCODE4459373f, ABI2/caps31/HBU1. No FPGA source, constraints or clocks changed.

Target02 built against frozen handheld/native inputs with esp193/IDF5.4.3. Effective SDK checks passed; static shared SRAM131,572bytes is below the unchanged163,840 guard. Production updater parser accepted13,367 app-only UF2 blocks and exact BIN round trip. Do not install anything from failed target01 or an incidental target-cache ELF.

## Firmware behavior

`~` selects cached3, `@` cached12, `^` scalar3; all use explicit `dy71-sequence-v3` on5535 with expected finite count. V1/v2 and wrong count are refused before transport header admission/staging. One frame remains in flight, full actual HUD readback remains enabled, and success/failure ownership is retained as before. No auto-KEY recovery, STOP or warm session restart is claimed.

The HU cache reuses the bounded HU+36 HC70 allocation during ingress; after exact complete frame/staging integrity and live request checks, native consumes that cached HU instead of scalar command21 reads. Full packet caching is not added. Source/header-prefix mismatch is detected after START but before payload/native publication; failure retention is still required.

Finite API limit12,000 is independent of fixed three-record diagnostic storage. Records retain actual ordinal/frame/generation. Cached HU timestamps are an ingress-copy span that includes intervening network/staging time, not native copy CPU time or the old post-admission scalar-fetch duration.

Paced retained export emits BEGIN/body/END at40ms intervals through the existing USB task, with epoch/attempt/index/count/checksum. `$` requests read-only re-export after an attempt completes. Validate captured text with `tools/validate_telemetry.py`; do not combine incomplete attempts. Underlying USB loss count remains unknown even when a complete export validates. Detailed partial stage arrays are unavailable on errors, but last observed phase/identity and transport progress survive.

Arena ceiling98,304, initial114,688free/24,576largest and per-allocation8,192reserve remain unchanged. Native owned motion prediction is reconstructed in place by independent RGB channel. Exact12 passes the conservative allocator/wire-lifetime model with peak92,544 and253,440 actual HUDword comparisons. This excludes malloc metadata, SDK concurrency and physical fragmentation; hardware stack/heap still need checks.

## Executed gates

- 59 actual-native/driver/wire tests, including cached/scalar equality, HU boundary coverage, staged CRC/live request failures, zero command21, ring turnover and cached12.
- 11 retained/paced telemetry tests,8 pure uploader tests,11 Python/Rust wire tests.
- Actual localhost cached12:12matching presentation replies,253,440 words and complete indexed/checksummed31-record telemetry. Additional independent validator rejects7missing/duplicate/order/corruption cases. FPGA MMIO/health are modeled here.
- Exact-selected V027 cached5 complete-system functional replay:5accepted/5presented,0rejects/underruns,105,600 actual HUD comparisons, all1,728,000 composed pixels/borders and canonical banks equal, independently observed command21count0. Runtime checks pin the actual loaded DLL. Physical SPI/CDC/PLL and target CPU timing are excluded; raster sampling adds delay, so no FPS claim.
- Final native broad semantic regression:457frames/9,651,840 golden HUDwords and3malformed rejections; its1MiB diagnostic cap is not target memory qualification for the full corpus.

See `evidence/readiness-v001/readiness.json`, `evidence/DRIVER-CACHE-RESULT.md`, [development/hardware ladder](../../../docs/cu66-v71/V45-INGRESS-CACHE-PLAN-20261107.md) and matching [host package](../../../host/dy71-sequence-v3/README.md). The readiness manifest remains overall INCOMPLETE for untested physical behavior while its offline candidate gate is PASS.

This is the next short-sequence step. The twelve retained historical frames are not the user's two-minute clip. Real Windows CU66 encoding and subsequent throughput/recovery work remain necessary before that video or30fps acceptance.
