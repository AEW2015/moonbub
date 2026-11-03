# Moonshine / MoonBub prototype

The latest application-specific codec handoff is
[`handoff/gamebub-app-codec-v9-20261103`](https://github.com/AEW2015/moonbub/tree/handoff/gamebub-app-codec-v9-20261103).
Start with the [application-specific plan](docs/gamebub-application-specific-codec-plan.md),
[iteration9 results](docs/custom-codec-prototype-v9-2026-11-03.md), and
[developer handoff](docs/dev-handoff-2026-11-03.md). The matching
[Sunshine handoff](https://github.com/AEW2015/Sunshine/tree/handoff/gamebub-app-codec-v9-20261103)
contains host-laboratory references. Earlier handoffs remain frozen snapshots.
V9 adds finite GM01/GF02/GA01 replay, a delivered-buffer ownership correction,
and exact565 UI patch experiments. These remain Python software studies.
The baseline build and timing results below do not qualify the experimental
dual-bank, SDRAM staging, gateway, or host candidates for hardware use.

Source attribution and component licenses are listed in [NOTICE.md](NOTICE.md).

An isolated Game Bub Rev4 Wi-Fi video prototype: PC JPEG sender → ESP32-S3
Rust/ESP-IDF firmware → existing quad SPI framing → FPGA JPEG decoder → SDRAM
double buffer → native LCD. The firmware extends the existing Slint interface
and preserves the copied controller, USB and LCD changes. This is experimental
standalone test-source mode; Sunshine pairing and JPEG negotiation are not yet
implemented.

The source panel is **800×480 landscape** (480×800 scanout), rather than the
720×480 native panel assumed in the brief. The transmitted 720×480 canvas is
centered inside it. A 1280×720 source becomes 720×405 content with 37/38 black
rows. Existing native panel timing and the stock overlay mapping are retained.
The prototype does not provide the stock dock output.

Final build/check status and artifact hashes are in [evidence/manifest.json](evidence/manifest.json).
The offline prototype gate passes. The final FPGA has +0.031 ns setup slack,
+0.014 ns hold slack, zero failing timing endpoints, zero routing errors and
zero DRC errors. All 345,600 pixels of the 720x480 JPEG fixture match the
fixed-point software reference.
Physical streaming FPS and latency have **not** been demonstrated. The recorded
PC localhost rates are not Game Bub results. No hardware has been programmed.

## Files and build

- [Firmware setup/build](firmware/README.md),
  [application UF2](firmware/release/moonshine-rev4.uf2).
- [Streaming screen preview](firmware/evidence/ui-streaming-preview/streaming-view-focus.png)
  and [desktop UI verification](firmware/evidence/ui-streaming-preview/README.md).
- [FPGA bitstream](fpga/build-final/moonshine-rev4.1.bit),
  [register protocol](fpga/PROTOCOL.md) and `fpga/rtl/`.
- [PC sender setup](host/README.md), [wire protocol](host/PROTOCOL.md),
  [codec/Moonlight audit](host/CODEC_AUDIT.md).
- [Integration decisions](docs/integration.md) and the original
  [requested prototype](docs/requested-prototype.txt).

Firmware builds with the installed ESP193 toolchain and ESP-IDF 5.4.3:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File firmware/build.ps1 -Package
```

The FPGA uses Vivado 2025.2 and XC7A100T-CSG324-1. Use the final build command
in the FPGA documentation. The delivered bitstream passed a second, post-route
physical-optimization step using `fpga/scripts/close_timing.ps1` and its included
source-bound routed seed. `build.ps1` regenerates the initial synthesis/route;
that initial route has a small timing failure and needs the separate closure
step. Earlier attempts and failed logs remain available for review.

The snapshot includes the existing modified Game Bub application and the
selected FPGA framework sources. It does not require the original Linux paths
or an assumed checkout inside this workspace. The derivation is recorded in
`firmware/source-snapshot.json`, `fpga/vendor/` and `evidence/source-before.json`.
Dependencies/tool installations are separate from source snapshots. The original
`C:/Users/lavat/codex/gamebub` workspace remains separate and unmodified.

## Repeat verification

```powershell
python -m pip install -r host/requirements.txt
python -m unittest discover -s host/tests -v
python scripts/integration_checks.py
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/test_firmware_protocol.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/test_qspi.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/test_transport_overflow.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/test_lcd.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/test_overlay.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File fpga/scripts/test.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File fpga/scripts/test_memory.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File fpga/scripts/test_pipeline.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File fpga/scripts/test_pipeline64.ps1
python host/build_cmodel.py
python host/compare_decoder.py --require-fixed-exact
```

The full-resolution JPEG test checks 345,600 unique pixels and an exact match
to the software model using the RTL color arithmetic. The independent Pillow
comparison remains available: its default chroma interpolation differs from the
core. LCD tests exercise independent refresh, buffer changes, delayed lines,
whole-line underrun handling and recovery. SPI tests use the actual pin parser
and CDC bridge. SDRAM model tests are functional simulation, not board timing
qualification. Each saved log identifies its scope.

## Device setup and recovery

Place `moonshine.cfg` on microSD using the firmware example and copy the final
Moonshine bitstream as `/moonshine.bit`. Firmware loads it into volatile FPGA
configuration when Connect needs it; the standard system/core files are not
replaced. Configure the host IPv4 and Wi-Fi in that file or the Streaming screen.
Start the standalone PC sender as described in `host/README.md`. View video hides
the UI through the stock transparent game screen; Home returns to its menu.
Disconnect/exit releases remote controls and coordinates receiver teardown.

Before first installation, retain the currently working application UF2 and its
hash. This project's UF2 updates only the application partition; it does not
include the updater, NVS, or system-data FPGA images. Game exit restores the
normal boot image; a normal restart reloads the existing standard boot core.
To revert the application, use the retained known-working Rev4 UF2 with the
normal Volume-minus power-on USB updater procedure. No recovery artifact is
described as hardware-verified merely because it was named in historical notes.

## Remaining physical verification

Identify the connected board and preserve its current image before deployment.
Then verify local pattern, known JPEG, Wi-Fi→QSPI concurrency, real moving game
footage, queue age, drops and control response. The first performance target is
720×480/30; 60 fps is a later measured goal. The 40 MHz quad data clock gives a
calculated 20 MB/s wire ceiling before overhead; it is not measured throughput.
ESP32 memory is bounded to datagrams/DMA chunks, not a decoded framebuffer.

Sunshine negotiation/pairing, an explicitly negotiated JPEG extension, audio,
and stock dock support are subsequent work. Audio is absent from the standalone
capture/protocol. Optional Windows keyboard injection is explicitly enabled
by `--inject-keys`; automated tests mock it and do not inject desktop keys.
