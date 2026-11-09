# V114 source inventory and integration boundary

Read-only inventory on V114 base `3c2f644933d438c3ecb6d74677b896a3e2b42e38` (`study/gamebub-v114-reserved-control-20261108`). Machine-computed SHA pins, source-origin aliases, six native timing controls, tool limits, and the resource notes are in [`source-inventory.json`](../../experiments/python-gamebub-v114/inventory/source-inventory.json). No builds, test reruns, native jobs, hardware access, source edits, or network activity were performed.

## What executes today

| Segment | Existing executable evidence | What it does not establish |
| --- | --- | --- |
| Sunshine fork | `sunshine-30fps-study/src/gamebub/msv1.{h,cpp}` contains a native 40-byte MSV1 packet serializer. | It accepts already encoded JPEG bytes; it is not a CS88 encoder, sender, codec negotiation, or connected Sunshine capture path. |
| ESP32-S3 | `moonbub/firmware/handheld/src/streaming/{protocol.rs,mod.rs}` receives bounded MSV1 UDP and forwards bytes over the FPGA SPI driver. | It accepts codec byte `1` (restricted JPEG) only. The module states Sunshine pairing/video are not implemented; no CS88 negotiated receiver profile exists. |
| FPGA parent | `fpga/rtl/moonshine_top.sv` instantiates the 200 MHz QSPI endpoint, 100 MHz JPEG core and SDRAM path, pixel-clock LCD and overlay. `moonshine_core.sv` validates JPEG length/dimensions/CRC/SOI/EOI, decodes with `jpeg_core`, writes pixels through the one shared SDRAM controller, and toggles the display buffer at a frame boundary. | The production parent has no CS88/BR88 instance, custom QSPI register adapter, C2/HUD seal path, or custom-frame publication path. This remains an actual JPEG parent, not a completed custom parent. |
| CS88/BR88 | The selected `cs88_pipeline_v91k` and BR88 hierarchy have actual component source and V113 RTL/OOC evidence. Protocol 97 has a separate bounded 2 KiB FIFO/two-descriptor parallel ingress. | V113's custom transport test uses a parallel command/DMA adapter. Protocol 97 is not wired to the production QSPI pins/register map and ingress commit is not syntax validation, C2 seal, or display publication. |
| V113 spatial and timing | `experiments/python-gamebub-v113/spatial/results.json` reports actual RTL simulation with the custom transport adapter; source-bound OOC native component routes exist at 100 and 125 MHz. | No live Sunshine→firmware→production-QSPI→CS88→LCD path, full-parent fit/timing, physical board rate, or 30-fps claim. Both native route setup results fail their period targets. |

For packet details see [`docs/cu66-v97/protocol.md`](../cu66-v97/protocol.md), [`fpga/experiments/cu66-v97-forward/README.md`](../../fpga/experiments/cu66-v97-forward/README.md), and the pinned Moonbub protocol source. MSV1's codec field is already defined as JPEG and must not be silently reused for CS88.

## Timing controls and V113 source binding

The inventory JSON pins the four earlier controls (Count100 −1.022 ns, Count125 −3.264 ns, V112100 −1.034 ns, V112125 −2.844 ns) and the two V113 native receipts (100 MHz −1.686 ns, 125 MHz −3.303 ns), including each receipt's SHA-256. The selected V113 125 MHz composition is based on frozen V112 source with the exact three geometry/scratch/inverse candidate bodies; the JSON contains the V113 receipt's 18 source-origin aliases, each path, and SHA-256. The V113 native Vivado and Verilator images, strict compile profile, and container bounds are pinned there too: each is limited to 2 CPUs, 8 GiB memory, and an 8 GiB combined memory-plus-swap ceiling (no additional container swap). Native timeout is 3600 seconds; Verilator command caps are 300 or 900 seconds. These are component measurements, not parent signoff.

## Memory and lanes

The retained JPEG parent report [`fpga/build-final/utilization.rpt`](../../fpga/build-final/utilization.rpt) maps 32 DSP48E1, 113 RAMB36 and 15 RAMB18; its exact SHA is recorded in the JSON. The routed V113 single-lane OOC component report maps 42 DSP, 36,976 LUT, 39,225 FF, 32 RAMB36 and 12 RAMB18. The V113 lane ledger's `17 shared + lanes × (8 dequant + 17 IDCT)` gives conditional DSP arithmetic of 42/67/117 for 1/2/4 lanes. It explicitly records `actual_RTL_run=false`: 2- and 4-lane storage, placement, and service are not measured. The port design must account for existing synchronous BRAM ingress accesses, banking, fill/write traffic, read latency, and finite output slots; a primitive's dual-port label is not proof of two independent lane services.

The parent memory is one 16-bit SDR SDRAM bus/controller. `moonshine_memory.sv` prioritizes a line read over pixel writes; `moonshine_sdram.sv` issues BL8 reads and single writes, and the LCD fetches 480 words in 60 bursts per line. There is no measured whole-parent budget for concurrent custom decode, scanout, JPEG fallback, overlay, or reference/hash/HUD traffic. Do not add the separate OOC custom/JPEG resource counts or turn conditional lane arithmetic into hardware throughput.

## Smallest missing integration sequence

1. Define a versioned CS88 packet/profile negotiation and preserve JPEG codec id 1. Pin deterministic payload fixtures, output hashes, limits, and service assumptions.
2. Implement one native CS88 encoder/packetizer in the isolated Sunshine fork and route both live and deterministic capture modes through that same implementation.
3. Add a bounded ESP32 receiver state for the negotiated CS88 profile: frame IDs, exact byte lengths, CRC, cap, credits, abort/recovery, and explicit QSPI register/transaction mapping.
4. Add a bounded QSPI/CDC adapter to CS88 ingress and actual finite-memory requests. Preserve generation, owner, cancellation, drain, and ready/valid semantics across the boundary.
5. Integrate full-frame validation and decoder drain with C2 seal, buffer ownership/publication, HUD/hash ordering, and LCD scanout. Then qualify clocks, resets, CDC, arbitration, resources, and timing in the full parent.
6. Run Python/native/RTL packet round-trips, malformed/recovery cases, 300 distinct frames over ten modeled seconds under stated service, then full-parent fit and timing. Until those exist, V114 remains an integration proposal.

The roadmap's product targets remain 720×480, 30 distinct displayed frames/s, 49,152-byte payload cap, and strict full validated decode below 1,250,000 cycles at exact 125 MHz. None is established by the current source inventory or component evidence.
