# V59 independent preflash review ? 2026-11-08

No static preflash blocker identified. This review performed no hardware operation. Applied the GameBub skill ESP32 firmware reference; application-only firmware scope requires no FPGA rebuild.

Candidate: `C:/moon/dev/experiments/v59-throughput-probe-20261108`. Build: `C:/moon/builds/v59-target-run01`. Package: candidate `release-throughput-v001`.

- All609 handheld source files and all8 native source/header files currently match the exact prebuild SHA256 manifests. Build returned0 with no source/native changes during compilation. Subsequent tools-only changes do not invalidate this handheld/native comparison. Input manifests and reviewed source hashes are bound in the JSON receipt.
- Build ELF, packaged ELF and recorded ELF SHA256 match: `9ea80b4a4588925bd507477990a26e260ec6c116d358d06804b028fdf4cfc94f`. Every artifact in release `hashes.json` recomputes correctly. Effective SDK config and package evidence hashes are recorded.
- All package commands passed. esptool image checksum/validation hash passed. Production UF2 parser accepted17,883 blocks with Rev4 identity, application addresses and exact binary round trip. Build uses Rev4/esp193/offline locked release; image is ESP32-S3 application with dio80m8MB packaging.
- BIN is4,578,048 bytes against5,242,880-byte factory capacity, leaving664,832 bytes. Starting at0x100000, it ends exclusively at0x55db00, below0x600000 system_data boundary. UF2 padding is already included in the BIN size; parser independently checks addresses.
- Independently found every entire FLASH40 packet byte string in the packaged image DROM segment at mapped address0x3c230020. All40 packets total1,041,478 bytes and each occurrence address/hash is recorded. ELF `FLASH40` pointer table is at0x3c39febc,320 bytes, also within DROM. This verifies the fixture payloads/table are flash mapped read-only data rather than1MiB of allocated SRAM.
- Static shared SRAM is132,308 bytes, exactly31,532 bytes below163,840-byte build guardrail. Runtime heap reserves remain unchanged. Static usage does not establish available runtime heap or stack.

The worker still requests16,384 bytes of stack and reports task high-water after execution. New throughput aggregates enlarge Report and intermediate report/snapshot values by roughly a few hundred bytes; compiler lifetimes/copies and native exception/decoder call depth prevent a sound full-stack bound from Rust type sizes alone. No unconditional array scales with40/120 sequence count; flash cursor and diagnostic ring remain bounded. Runtime minimum free heap, largest free block and worker high-water must be captured during the first controlled local/network run before claiming target stability. This is a runtime evidence limitation, not a discovered static deployment blocker.

Exact machine-readable receipt: `C:/moon/maintenance/V59-PREFLASH-REVIEW-20261108.json`. No claim of successful device update, runtime stability, SDRAM word readback verification, or completed unique panel raster follows from this preflash audit.
