# V32 read-only CPL1 observer

V32 is an **uninstalled ESP32 application candidate** for a separate local-ROM FPGA diagnostic. It preserves v31 trace changes and normal video/AV behavior. V31 remains the proposed first legacy streaming comparison; installing v32 and a new FPGA together would be a different experiment. Installed v30/build50, SD contents and handheld settings remain unchanged.

Portable source: `firmware/exports/v32-cpl1-observe-source-v002-20261105`, manifest `c8ac02fa841e5745450219ecd2894179fdc83504cce80b09e7246318676054cc`. It includes598 files/all572 selected inputs, assets, fonts, locks and licenses; no other GameBub checkout is assumed. External pinned Rust/IDF/compiler/component caches are documented. Candidate binaries remain local and are not bundled in this source export.

| Evidence | Result |
|---|---|
| Original fresh target check/release | PASS, esp193/ESP-IDF5.4.3,6m28s/1m17s |
| Production application-only UF2 parser | PASS,12,549 blocks |
| Fresh copied final source host replay |97 Rust suite tests,39 model,66 SDK-host,24 expected compiler rejections PASS |
| Clean relocated release | PASS9m36s, all572 inputs and build helper identical; same generated SDKconfig/ABI and SRAM |
| Physical query/stack/heap/electrical checks | NOT_RUN |

Original candidate manifest `20b4b6abf9860936109041659daa4db26bcdfaba6fe0974f84b3eabfa747aba5`; ELF `5bbb988144eeee7fcd96fb442573171f25912168fa94586a6a6fb2ce36e3e8fd`; BIN `932d515d032561623d36f4f9f14b0e534b5bc5deeca211c7b15eb99311e4b3fe`; UF2 `13c27ca9a919dd7d40b7ff7aa4d55e5d97e00ad79e596d5aeee732966e9c3d4d`. The separate relocated ELF `8868d6618219d16c023a6c7857212a734b5ed79a57fb21348e101888054b392a` is unselected. Exact proof logs retain its preceding source-package manifest; v002 adds documentation/evidence only.

Static shared SRAM130,812B, +376 versus v31; CPL1 state400B and Trace8272B. Compiled StackType_t=u8 and no configured PSRAM. Actual observer command/tick/page/step entry frames832/608/320/224B; existing USB dispatcher416B. These individual frames do not establish a whole-task bound. Task stacks, heap peaks, logger framing, SPI blocking WCET and physical minima remain open.

## Interface

Uppercase `P`, while quiet under an existing diagnostic permit, requests one atomic retained40-word CPL1 capture at500. Subsequent ten `P` commands emit one bounded cached page each. There is no decoder start/reset/cancel, programming or video-upload path. Strict CPL1/schema/CAPS0/image guards, fresh nonzero ESP-boot-lifetime cookies, generation advancement, program epoch and before/after group checks reject stale/torn/unexpected captures. Both PLL locks, quarantine, reserved bits and completed-canvas consistency are checked. Cached pages are historical, not live.

The existing laboratory SPI profile is16MHz with at least eight dummy bytes. It is not maximum-bandwidth or external-hold qualification. No NVS or persistent query namespace is added; cross-ESP32-boot ownership/reference/ACK continuity is unsupported.

`host/cpl1-observer-20261105` decodes saved pages and compares the separately named fixed fixture. Its16 parser/CLI tests and an actual exported Rust formatter round trip pass, including preservation/rejection of a bad actual CRC. It opens no device/socket and does not attest a supplied log's origin. Actual tags/CRC remain distinct from expected values. Pad-launch counts are not SDRAM chip ACKs; repeated canvas counts are not unique FPS; writer retirement is not front-bank release.

## Separate FPGA gate

The CPL1 board source has passed source-oriented platform/reset simulations and the actual ROM→decoder→SDRAM model→RGB/HUD canvas CRC4c5725e5. A separate guarded-read successor adds actual BRAM-read enable evidence. Neither result supplies routed board setup/hold/pulse/CDC/I/O qualification or a hardware-ready BIT. The optimized compute composition is still undergoing timing repair. No custom network endpoint or port is assigned, CP25 remains unselected, and30 unique physical fps remains unverified.
