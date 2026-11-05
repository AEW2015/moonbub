# Portable v32 CPL1 observer source and executed proof

All572 selected firmware/test/tool source inputs are included, with complete assets, fonts, lockfiles, licenses and nested/empty files. The selected source snapshot is5fd0e6ca0feec223da6606f35729a3c6e27056eaa8cacc80b95cb90592f83b27. This application adds read-only CPL1 capture/cached pages to v31; normal streaming/AV settings and transport remain unchanged. It neither uploads custom frames nor starts/resets/programs a decoder. A compatible CPL1 FPGA image is a separate unfinished gate.

The sealed original candidate's check/release and production UF2 validation passed. Its manifest20b4b6abf9860936109041659daa4db26bcdfaba6fe0974f84b3eabfa747aba5 is retained under provenance. Original images are NOT bundled: ELF5bbb988144eeee7fcd96fb442573171f25912168fa94586a6a6fb2ce36e3e8fd, BIN932d515d032561623d36f4f9f14b0e534b5bc5deeca211c7b15eb99311e4b3fe, UF213c27ca9a919dd7d40b7ff7aa4d55e5d97e00ad79e596d5aeee732966e9c3d4d. Local hardware installation/identity verification remains separate. The declared handheld/bootloader.bin and binary test fixtures are source inputs, not an instruction to flash a bootloader.

## Rebuild evidence and dependencies

One clean relocated release of the preceding source package passed in9m36s, without another GameBub checkout, retries or source changes. Its exact original package manifest71040d17f504604791155bac688d12540558cd3583e5247c75c0fae9b8043120 and compact logs/results are retained under provenance. This revision adds documentation/evidence only: all572 selected inputs and build_rev4.ps1 are byte-identical to that successfully built package. Its rebuilt ELF8868d6618219d16c023a6c7857212a734b5ed79a57fb21348e101888054b392a is unselected, not packaged/programmed. Build dates/paths can change ELF hashes; no byte-identical rebuild claim follows.

Generated SDKconfig/ABI match the original selected v32 exactly, StackType_t=u8, no configured PSRAM, static shared SRAM130812B(+376 versus v31). That excludes dynamic task stacks, TLS/TCB and heap peaks. Individual function frames do not prove whole-task headroom. Physical stack/heap, logger delivery, SPI-driver WCET and CPL1 electrical/rendered behavior remain unmeasured. Build duration is not a performance benchmark; other offline work was active.

External prerequisites are the pinned esp193 Rust commit, ESP-IDF5.4.3, CMake/Ninja, Cargo/managed-component caches and host compiler in DEPENDENCIES.md. No other GameBub repository is assumed present. The optional helper invokes Cargo check/build only, never cargo run/espflash or a device. Both target/evidence paths must be fresh, nonoverlapping and outside this export. Root preflight tested expected Git fallback and rejected overlapping paths; the UTF-16 Windows PowerShell log decoder correction is preserved separately from the successful target build.

```
python verify_source.py
python validate_copy.py --evidence C:/new-v32-host-replay
./build_rev4.ps1 -PreflightOnly -EvidenceDirectory C:/new-v32-preflight -TargetDirectory C:/v32src01
./build_rev4.ps1 -Action build -EvidenceDirectory C:/new-v32-build -TargetDirectory C:/v32src01
```

Original copied host replay passed97 Rust suite tests,39 model cases,66 SDK-host cases and24 expected compiler rejections. The final package's new copied replay is recorded outside the export by its owner. Supplied metadata is historical proof, not a live device result. The package verifier binds included files and selected source paths, not omitted original build outputs.

## Diagnostic semantics

FirstP captures while quiet under an existing diagnostic permit, then eachP prints one of10 cached40-word pages with one cookie/generation. Reads use the existing bounded16MHz/eight-dummy-byte laboratory profile. Every group checks CPL1 identity/schema/CAPS0/image, fresh generation and cookie before/after. Failures, reset/epoch change, quarantine, either PLL unlock and timeout reject. There is no persistent cross-ESP32-boot identity or ownership/ACK/reference continuity. The expected CRC4c5725e5 is metadata only; actual values remain raw. Pad launches are not SDRAM ACKs; repeated canvases are not unique frame rate. Installed v30/build50 is unchanged.

Packaging correction: the upstream GPLv3 license text and upstream README are explicitly included under licenses/. They were omitted from the initially published a9898867... source package because that directory lies outside the572 selected input list. This completion changes no selected firmware input, build helper, candidate image or target result; provenance/license-completion.json records exact source hashes. Per-file/third-party notices retain their existing terms.
