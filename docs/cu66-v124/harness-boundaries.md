# V124 endpoint harness boundaries

V124 advances two independently checked paths. They do not yet form one live
Sunshine → ESP32 firmware → custom-codec FPGA system.

| Boundary | Implementation used | What it can establish |
| --- | --- | --- |
| Production packetization | Actual Sunshine `msv1.cpp` compiled unchanged; pre-encoded JPEG fixture | Native wire bytes and producer bounds; no capture/encoder/session timing |
| Production protocol receive | Actual Rust firmware `protocol.rs` included unchanged by a host wrapper | Header/sequence/integrity decisions and feedback; wrapper buffers accepted payloads and commits only on `done` |
| Native packet file → QSPI/CDC/JPEG | V124 replay preparation uses the native C++ output file and frozen V115 pin bench, endpoint, CDC and guarded JPEG sources | A source-bound replay when an executed receipt passes; the receipt, rather than preparation, decides execution status |
| Experimental custom-codec path | Fresh V124 coefficient owner lanes, full decoder/actual V97 transport, peer and byte/row validation parent | Exact finite functional/cycle checks against V123; separate custom CU66/CS88 format |
| Native FPGA timing | Fresh RTL synthesis/place/route of the selected custom component at 8 ns | Internal component timing only, with missing external I/O constraints reported explicitly |

The [endpoint results](endpoint-results.md) and [JPEG replay results](jpeg-wire-results.md)
record selected execution status, provenance and limits. Neither path runs a
Windows Sunshine service, its capture/encoding pipeline, the Rust firmware
session worker, ESP-IDF scheduling, ESP32 instructions, radio or the real SPI
driver. The native C++ producer and Rust receiver exchange files across host
processes; the RTL bench later replays those exact bytes. This is not dynamic
co-scheduling on one simulation timebase. A shared JPEG fixture is not evidence
that the experimental custom profile has been negotiated by production endpoints.

## Remaining full-harness work

1. Add an explicit negotiated CU66/CS88 profile and fallback contract to the
   production producer/receiver. Preserve the JPEG baseline and bind real
   encoder/decoder parameters, caps, frame identity and publication rules.
2. Connect actual endpoint outputs and the actual firmware session adapter to
   the RTL pin driver through bounded queues. A common deterministic scheduler
   must own capture/send/receive/SPI/validate/publish timestamps; subprocess wall
   times cannot substitute for modeled device service.
3. Model finite ESP32 SRAM/PSRAM buffers, CPU/task service, cache and DMA ownership,
   Wi-Fi arrival/backpressure, SPI packet overhead and FPGA memory contention.
   Label transaction models separately from instruction-emulated firmware, and
   later calibrate both with traces from the remote hardware system.
4. Carry the same frame/epoch/CRC through every boundary. Include loss, reorder,
   disconnect, abort/reset with outstanding physical debt and retry, with no
   premature buffer reuse or validation/publication after cancellation.
5. Validate distinct-frame rates and tail latency from a frame ledger. Measure
   capture→display separately from last-input-byte→validated-commit. Replaying
   six retained goldens or a single JPEG repeatedly does not qualify sustained
   gameplay, silicon decode time or Wi-Fi throughput.

The timing experiment preserves public cycles. The retained row parent needs
1,145,104 cycles without stalls and 1,553,197 with its modeled stalls. At an
assumed complete-parent 125 MHz these are 9.160832 and 12.425576 ms; the stalled
case needs at least 303,198 fewer cycles for strictly under 10 ms. Complete-parent
timing and real memory service must be checked before interpreting these as
hardware latency. The FPGA target alone is not a 30-fps system qualification.
