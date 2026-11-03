# Moonshine prototype firmware

This is an isolated snapshot of the existing modified Rust/ESP-IDF + Slint
GameBub application, with streaming added. `source-snapshot.json` records the
upstream revision, preexisting modifications, and original file hashes. The
original sibling GameBub checkout was not modified. Firmware remains GPLv3.

The implemented connection is **standalone experimental MSV1 MJPEG**, not
Sunshine or Moonlight pairing. Pairing, app discovery, audio, and H.264 are not
implemented. JPEG is forwarded compressed; there is no ESP decoded framebuffer.

## Build

Installed dependencies used by this Windows build: Espressif Rust `esp193`
(1.93.0.0), `ldproxy`, ESP-IDF 5.4.3, its ESP32-S3 cross compiler and Python
environment, CMake 3.30.2, Ninja 1.12.1, and Visual C++ host tools. Cargo.lock
pins Rust dependencies; components_esp32s3.lock pins the TinyUSB components.
No original GameBub source checkout is needed to rebuild this snapshot. Initial
dependency downloads require network access. The short target path avoids
ESP-IDF Windows canonical-path limits.

```powershell
.\firmware\build.ps1 -TargetDirectory C:\mbt -Package
```

This builds `rev4`, verifies the application-only UF2 against the production
DFU parser, and writes `firmware/release/moonshine-rev4.{elf,bin,uf2,json}`.
It does not install an update or program hardware. UF2 addresses are confined
to the application partition `[0x100000,0x600000)`; system_data, bootloader,
saved settings, and existing bitstreams are preserved by that update.

Protocol tests compile the exact module included by device firmware:

```powershell
& "$env:USERPROFILE\.cargo\bin\rustc.exe" +stable --edition=2021 --test firmware/handheld/src/streaming/protocol.rs -o firmware/evidence/protocol-tests.exe
.\firmware\evidence\protocol-tests.exe
python scripts/integration_checks.py
```

## Runtime setup

1. Keep the existing working firmware update and FPGA image for recovery.
2. Copy `moonshine.cfg.example` to microSD root as `moonshine.cfg`, then enter
   your host IPv4 address and 2.4 GHz Wi-Fi credentials. This plaintext file is
   local configuration; the firmware does not print credentials.
3. Copy the matching prototype FPGA bitstream to microSD root as
   `moonshine.bit` (raw `.bit`, not heatshrink). The FPGA USERID must be
   `0xB0100004`; the firmware also requires the core's MSV1 magic, version,
   and JPEG capability before forwarding data.
4. Open **Streaming** on the main menu. Leave Host IPv4 blank to use the file,
   or focus the Host button (Up from Connect), press A to select an octet,
   and Left/Right to adjust. Select Connect to save the edited host. This connects
   Wi-Fi and loads `moonshine.bit` into volatile FPGA configuration when the
   matching core is not already present.
5. Start the standalone host sender to the handheld's DHCP address, UDP5533.
   Select View video to hide the menu; Home opens the existing game menu.
   Disconnect stops video reception and sends a remote release mask. Exiting
   the game menu restores the existing boot image.

The current FPGA build must supply the stock QSPI overlay compositor for the
Slint menu to remain visible after video-core loading. Consult the top-level
verification report for whether that integration has passed; stock-menu source
compilation alone does not prove it on the streaming image.

## Transport and limits

The firmware forwards a strictly ordered stream of at most 1024-byte compressed
chunks from a 1065-byte internal DMA buffer, checks metadata and incremental
IEEE CRC32, and aborts incomplete frames after 500 ms. The firmware checks
FPGA register `0x0c` before every chunk. It reports bytes remaining in the
current compressed frame, not free entries in the clock-crossing write FIFO;
it does not by itself prevent FIFO overflow. The separate transport overflow
counter at `0x50` records lost bus words. No full compressed or decoded frame
is held in ESP memory. The existing SPI driver is DMA-enabled; QSPI writes
are capped at 40 MHz and reads at 16 MHz. Neither rate has been qualified by this firmware
build. sdkconfig.defaults does not enable external PSRAM; no PSRAM is assumed.

The worker uses a bounded two-command queue. New connect generations invalidate
queued/stale sessions. It releases the device mutex after each chunk and never
waits behind the UI/input holder: a busy FPGA lock drops a frame. Existing USB
and controller input paths are retained. Their merged twelve-button state is
sent in MSF1 feedback on changes (socket polling up to 20 ms), every 250 ms, and
as zero on disconnect or network silence. The host logs these masks by default;
its optional `--inject-keys` mode sends Windows keys with release on timeout/exit.
Only mocked injection has been tested. No input responsiveness or Wi-Fi /
QSPI concurrency rate has been measured on GameBub yet.

RX FPS counts completed, integrity-checked ingress frames; decoded/presented
counters are read separately from FPGA. A received frame is not evidence of
successful decode or visible output. Network bitrate covers forwarded JPEG
payload. Sender quality, bitrate, and target FPS are configured on the standalone
sender; this screen does not advertise unimplemented negotiation. Zero-rate or
missing hardware measurements must not be reported as 720x480/30 performance.

## Recovery

Disconnect and return to the existing boot menu; a power cycle restores the
normal boot FPGA image. Remove `moonshine.bit`/`moonshine.cfg` to prevent its
selection. Restore the preserved application UF2 through the standard Rev4
USB updater if needed. This prototype never replaces system_data or the
updater and never changes persistent FPGA flash.
