# V111 baseline inventory (source and artifact audit)

Inventory frozen against Moonbub `study/gamebub-v111-harness-timing-20261108` at
`08e91145e0fc103c81d0b383338cfa70970ec399` (2026-11-08). Sunshine was read at
`handoff/gamebub-app-codec-v20-20261103`, `3d49c6fe87753eb5b35d693991fdff0365e4bbbf`,
clean. The V111 inventory's workspace changes are limited to this document and
the sibling inventory JSON. Existing untracked
`fpga/experiments/throughput30/burst/marker-recovery/` was present at inspection
and is intentionally untouched.

## What actually exists

The Sunshine fork has an experimental Python MSV1 sender, explicitly documented
in its module as a test sender, not Sunshine integration. It captures via
Pillow (`ImageGrab`) or clip inputs, encodes a receiver-compatible baseline JPEG
with Pillow, packets and paces UDP datagrams, handles feedback and logs events.
The code is reusable for deterministic host-input-to-MSV1 trace work. Its
`tools/gamebub/experiments/capture-buffer-adapter/` is a separate native
capture/scaling prototype that produces RGB buffers; it is not wired to MSV1 or
the firmware. The fork's production Sunshine path is its ordinary video capture
and AVCodec/NVENC stack (`src/video.cpp`, `src/nvenc/*`, platform capture files).
No GameBub custom encoder backend, Sunshine sender hook, native MSV1 encoder,
or host-output trace capture was found. Ordinary H.264/HEVC NVENC bitstreams
cannot be forwarded to this firmware's JPEG receiver. Current Python host
sender and Sunshine capture/encoder are separate executables and paths.

Moonbub firmware is an isolated ESP-IDF/Rust + Slint snapshot. Its implemented
product path is standalone experimental MSV1 MJPEG, not Sunshine/Moonlight
pairing: no pairing/discovery/audio/H.264. The production receiver parses and
validates bounded datagrams, forwards JPEG chunks using DMA-enabled QSPI,
checks CRC and FPGA credit/status, and does not decode/store a full frame on the
ESP. The separate Rust `protocol97.rs` is opt-in study/parser code (module is
exported) and states its capacities are not production capability; do not treat
its research profiles or simulated endpoint as deployed behavior. Exact
production stream worker is `firmware/handheld/src/streaming/mod.rs`; protocol
parser is `.../protocol.rs`.

Existing live guest/RTL bridge demonstrates actual synthetic MSV1 guest receive,
actual guest receiver DATA bytes crossing a bounded localhost adapter, and RTL
JPEG decode/display model for two commits plus an integrity abort/recovery.
It does not run the release application receiver end-to-end, has no shared
clock, and Verilator time freezes during host socket waits. Guest fixtures are
oracles, and the LCD/SDRAM are functional models. Count this as bounded
functional bridge evidence only, not synchronized timing or target performance.

## Emulator and firmware boundary

The local ESP32-S3 executable is Espressif `esp-emu` 0.51.0, x86-64, at
`/home/lori/gamebub-tools/esp-emu-study-0510/esp-emu-0.51.0-x86_64-unknown-linux-gnu/esp-emu`;
its archive/executable and prior run evidence are hash-pinned in that directory's
`SHA256SUMS.txt`. The emulator is external to the repo. Prior experiments ran a
stub app, an erased-system-data negative full-app image, and isolated SPI probes.
The complete production app did not pass startup: logs stop at LCD initialization;
trace evidence supports SPI transaction polling as the immediate noncompletion
hypothesis. Separate probes found SPI2 writes complete while the tested SPI3
polling transactions do not. No cause is proven and this is not evidence of
silicon behavior. In particular, no booted actual production receiver has
received a packet in this emulator, and no emulated Wi-Fi/QSPI link to the RTL
is established. Firmware full-flash provenance also remains incomplete because
the intended 2 MiB system-data image is absent. The erased-data image is
explicitly a negative control, not a production installation.

Recorded firmware build environment in `firmware/README.md`: Espressif Rust
esp193 1.93.0.0, ESP-IDF 5.4.3, CMake 3.30.2, Ninja 1.12.1; Rust dependencies
are locked. Current local PATH probes found Python 3.14.4; `esp-emu`, `vivado`,
`iverilog`, `verilator`, `cargo`, `rustc`, ESP-IDF `idf.py`, and the Xtensa
ESP32-S3 compiler were not found on PATH. This records discoverability, not
absence from all pinned/offline paths. No build or emulator run was done for
this inventory.

## FPGA clock, memory, and display facts from source

Production `moonshine_top.sv` takes 50 MHz board input. Its PLLE2 creates 200 MHz
QSPI/overlay service, 100 MHz decoder/core and SDRAM controller clocks, and a
100 MHz phase-shifted SDRAM read clock. The panel MMCM formula is
50 MHz × 56.375 / 3 / 32 = 29.361979 MHz pixel clock. These are RTL-generated
frequencies; routed board timing evidence remains tied to the source XDC and
existing reports, not a V111 125 MHz decoder. Core and memory presently share
the same 100 MHz domain. The only 125 MHz requirement in the V111/V115 plan is
a proposed new decoder target; no matching production clock generation,
crossing, constraints, or routed parent is yet present.

LCD source specifies physical active area 480×800 and total 541×834. It renders
the centered landscape 720×480 canvas as 720 vertical pixels across the panel's
480-wide axis, leaving 40 landscape pixels of side border; framebuffer word
address is transposed `(x+40)*480+y`. Firmware and FPGA READMEs agree on
720×480 coded input / portrait Rev4 panel. The JPEG cap is 49,152 bytes in the
firmware path. SDRAM is one 16-bit bus/controller, 100 MHz SDR, BL8 reads,
CAS3, single writes, with refresh and row management; two physical chips on
that bus are not independent channels. QSPI source/README design point is
200 MHz service clock with write at most 40 MHz and read at most 16 MHz. The
firmware docs explicitly state those serial rates are not yet qualified.

## Direct reuse and open gates

Use `tools/gamebub/stream_sender.py` plus its `msv1.py`, `host.py`,
`pipeline.py`, `event_log.py`, and frame telemetry modules for host-side
deterministic input/packetization/logging; adapt it to capture immutable frame
IDs, hashes, release timestamps, and measured encode/send durations. Preserve
the existing host-vs-firmware boundary explicitly. Use the emulator study's
`live-bridge/run-multi.py`/adapter/event audit and
`live-multiframe-bridge/` to reuse bounded functional chain scaffolding. Reuse
the RTL top, actual qspi endpoint, bus CDC, JPEG core, SDRAM and LCD for source
facts and later pins-level integration.

Before calling the requested full harness complete, still resolve: successful
production receiver boot in emulator or a clearly scoped firmware guest; SPI3
transaction and guest timing control; actual Wi-Fi or labeled adapter path;
one integer/rational simulation-time authority while FPGA/memory/scanout clocks
continue through idle; bounded queues and backpressure; and evidence that the
release firmware, not test-only Rust receiver, reaches actual RTL ingress.
For timing, separately need a fresh source-bound 100 MHz control, newly
generated 125 MHz decoder clock/CDC and timing constraints, plus a sourced
125 MHz diagnostic. Existing 10 ns V110 component routes are negative
(reported best route WNS −1.022 ns per roadmap); they are not reusable as a
125 MHz pass and full-parent timing is open. V111 header/path-family audit and
reproducible clock snapshots remain work for the timing track.

`inventory.json` is the compact machine-readable companion with selected input
SHA-256s and actual repository/tool provenance.
