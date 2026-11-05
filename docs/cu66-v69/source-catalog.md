# CU66 v69 source and hardware catalog

This catalog is a pre-implementation source map for the native/RTL CU66 phase. It distinguishes board design evidence from the simulation prototype and pins the reused source set in [`source-pins.json`](source-pins.json). The current checkout is the parent snapshot recorded in that file.

## Board and memory parts

The primary board source is the official [`gamebub/gamebub-pcb` repository](https://github.com/gamebub/gamebub-pcb), `handheld_rev4_1`, commit `88f578a1a4c4096a33ab038eae82348cafab1229` (retrieved 2026-11-05). The KiCad RAM sheet SHA-256 is `757e907b7d0d800f371916269453231c1512a39f3b22ca553150fb93fe0d9b42`; its PDF SHA-256 is `79f5a4c54345166d140a0f5447a5c8769829882a2ce38bdb194cd8a5853483aa`.

| Device | Rev4.1 design record | Datasheet-level capability | Integration caveat |
|---|---|---|---|
| FPGA | AMD/Xilinx Artix-7 `XC7A100T-CSG324-1`, the board-repo FPGA design and this repo's Vivado project part | Build/constraints are in `fpga/scripts/build_final.tcl` and `fpga/scripts/timing-reviewed.tcl` | This prototype's routed source snapshot is not the custom-codec implementation. |
| SDRAM | Two `Winbond W9825G6KH-6` parts, references U1401/U1403 in the Rev4.1 RAM schematic; each is `4M × 4 banks × 16`, 256 Mbit = 32 MiB, 16-bit | Winbond datasheet A04 identifies -6 as 166 MHz at CL3 (133 MHz at CL2), 3.3 V ±0.3 V, commercial 0–70 °C; `tCK(min)=6 ns` at CL3, `tRCD/tRP(min)=15 ns`, `tRC(min)=60 ns` | Board documentation describes 2×32 MiB SDRAM on a 16-bit interface. Current prototype `moonshine_sdram.sv` is a 24-bit **word-address** controller, 100 MHz, and hard-selects only one of its two CS outputs (`2'b10`). Do not count the second chip as usable in this RTL without explicit address/chip-select integration. |
| SRAM | `IS61WV25616BLL-10TLI`, U1402, asynchronous `256K × 16` = 512 KiB | ISSI datasheet family identifies 10 ns high-speed BLL part | This custom video prototype does not use it as a framebuffer or as an inferred CU66 scratchpad. |
| ESP | ESP32-S3 on GameBub Rev4 | firmware build manifest says external PSRAM disabled/not assumed | Firmware/heap/DMA/QSPI/RF service is not simulated by this RTL project. |

The Winbond datasheet is [the manufacturer PDF](https://www.winbond.com/resource-files/w9825g6kh_a04.pdf), A04 dated 2017-03-20, SHA-256 `9530f7a59a18e062b6832dc96c7a60725b97d85c295631434a12538ee6e1aaf3`. The official Winbond [product guide](https://www.winbond.com/export/sites/winbond/product-selection-guide/file/2026-Winbond-Customized-Memory-Solution.pdf?__locale=en) also lists the -6 family at 256 Mbit, 166 MHz, 3.3 V, 16 I/O, commercial grade. The ISSI [manufacturer datasheet](https://www.issi.com/WW/pdf/61-64WV25616EDBLL.pdf) is linked from the primary schematic; the schematic's MPN is `IS61WV25616BLL-10TLI` (without the `E` found in the symbol-library name).

These are part-design records, not inspection of a particular assembled user's board or lot. The repo's older `docs/requested-prototype.txt` describes a 64 MiB SDRAM target; the Rev4.1 primary sources support two 32 MiB parts, but the installed hardware revision and memory population must be confirmed before a board-level capacity claim.

## Reusable source paths

| Role | Existing files | What they can support | What they do not establish for CU66 |
|---|---|---|---|
| Existing compressed ingress and control | `fpga/rtl/moonshine_qspi_endpoint.sv`, `fpga/rtl/moonshine_bus_cdc.sv`, `fpga/PROTOCOL.md`, `fpga/scripts/platform.xdc` | Existing native-framework QSPI register/FIFO path, CDC mailboxes, digital protocol tests | No AR03/CU66 capability negotiation, CU66 packet parser, WAN/Wi-Fi service, or ESP32 cycle cost. |
| Current decoder/top | `fpga/rtl/moonshine_core.sv`, `fpga/rtl/moonshine_top.sv`, `fpga/vendor/core_jpeg/src_v/*` | Known JPEG baseline, compressed-frame staging and pixel-stream boundary | It implements JPEG only; it is not an AR03/CU66 receiver or a proof of custom entropy/inverse/hash hardware. |
| Memory and scanout | `fpga/rtl/moonshine_memory.sv`, `fpga/rtl/moonshine_sdram.sv`, `fpga/rtl/moonshine_lcd.sv`, `fpga/sim/sdram_model.sv` | Existing single-word writes, BL8 scan reads, functional memory model, two line buffers and display timing | The model is not a full vendor/PVT SDRAM model. The controller maps one 32 MiB chip, not both. No CU66 reference bank, concurrent codec traffic, hardware panel, or custom throughput is proven. |
| Color/UI | `fpga/rtl/esp32_overlay.sv`, `fpga/evidence/lcd_pins_rev4.xdc`, `fpga/scripts/platform.xdc` | Existing display pin map and overlay path | Existing RGB565/JPEG color conversion is not the CU66 reference/tag domain; display UI must not contaminate canonical YUV or tags. |
| CU66 native arithmetic and wire contract | `hardware/gamebub-v20/src/gb_inverse.c`, `include/gb_inverse.h`, `wire-contract.json`, `development-profile.json`; `experiments/python-game-canonical-tag-v66-study/protocol.py`, `receiver.py`; `experiments/python-game-hash-stream-v67-study/model.py` | Frozen scalar inverse oracle, exact CU66 packet profile, planar-u8 tag definition, tile/hash ordering reference | V20 C is not a complete native encoder/receiver. V66/V67 Python models are executable reference models, not deployed firmware or RTL. |

The project pin/constraint source is listed in [`source-pins.json`](source-pins.json). The Vivado project selects `xc7a100tcsg324-1`. SDRAM constraints keep the existing 100 MHz clock and provisional board delays: output max/min `+2.0/-1.3 ns`, input max/min `+7.0/+2.0 ns`. The reviewed exception is structurally guarded and scoped to existing SDRAM I/O; this phase must not broaden it to make new CU66 paths pass.

Existing proof entrypoints include `fpga/scripts/test.ps1`, `test_qspi.ps1`, `test_sdram.ps1`, `test_memory.ps1`, `test_pipeline.ps1`, `test_pipeline64.ps1`, `test_lcd.ps1`, `test_transport_overflow.ps1`, and `fpga/scripts/build_final.tcl`. Their passing logs are preserved under `fpga/evidence/`. Treat them as compatibility controls only. They do not qualify the new profile.
