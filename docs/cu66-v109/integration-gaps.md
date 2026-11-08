# V109 parent integration gaps

The current production parent remains the JPEG path. The V108 routed receipt is
for `cs88_pipeline_v91k` (`xc7a100tcsg324-1`, 10 ns) and explicitly reports
`full_custom_top_qualified: false`; it cannot stand in for a routed
`moonshine_top` result. The plan defines V109 as complete-top implementation,
real primitive/controller replay, and calibrated counters
([development plan](../gamebub-v91-v110-development-plan.md#L804),
[qualification evidence](../gamebub-v91-v110-development-plan.md#L953)).

## Existing parent and its dependencies

- **Clock and reset domains:** `fpga/rtl/moonshine_top.sv:14-27` accepts a
  50 MHz input; its PLL/MMCM derive 200 MHz SPI/overlay, 100 MHz core/memory,
  phase-shifted 100 MHz SDRAM read capture, and panel pixel clocks, each with
  synchronized reset release. `moonshine_top.sv:54-76` bridges SPI→core,
  drives core/memory in 100 MHz, line scanout into the pixel domain, and the
  overlay into the same pixel domain. V109 needs constraints and CDC/reset
  signoff for this complete clock topology and board ports; the V108 component
  run only used its component 10 ns XDC.
- **Codec and byte transport:** `fpga/rtl/moonshine_top.sv:54-62` connects the
  QSPI endpoint through `moonshine_bus_cdc` to `moonshine_core`. The core is
  still explicitly instantiated with `jpeg_core` at
  `fpga/rtl/moonshine_core.sv:91-100`, with compressed-byte RAM reads/writes at
  `:101-107`. There is no CU66/CS88 packet adapter in this production parent;
  integration needs negotiated packet/profile framing, byte ingress, decode
  completion/error handling, and publication ownership wired to this parent.
- **Memory and display service:** `moonshine_top.sv:63-72` arbitrates decoded
  RGB565 pixel writes and LCD line requests through `moonshine_memory` into the
  SDRAM controller, while `moonshine_lcd` scans lines from the pixel clock
  domain. The CU66 component proofs do not prove this shared finite SDRAM
  schedule, line-buffer deadline/underrun behavior, framebuffer writes, or
  panel-domain presentation under simultaneous traffic.
- **Counters and latency endpoints:** `fpga/rtl/moonshine_core.sv:20-22` has
  frame/byte/fault/drop/watchdog/pixel counters; `:128-142` counts accepted
  decoded pixels and frame publication. The top synchronizes transport-overflow
  counts (`moonshine_top.sv:42-56`). This is not yet evidence of calibrated
  packet-complete→validated-publication latency distributions or per-cause
  stall/queue accounting with real RAM/controller delays.

## Evidence still required

1. Integrate the qualified CU66/CS88 path and fallback into `moonshine_top`,
   preserving transport framing, error recovery, reference/HUD/hash checks and
   safe framebuffer publication.
2. Run clean full-top synthesis/place/route on the exact part with valid board
   clock, I/O, generated-clock and CDC constraints; close setup, hold, pulse
   width, methodology and routing checks. No complete-top result is present in
   this baseline audit.
3. Replay fixed full-frame workloads through actual BRAM/SDRAM/controller and
   display service. Demonstrate pixel/reference/HUD/hash parity, finite queues,
   bounded stalls and zero scanout underruns; calibrate counters and report
   complete packet-complete→publication latency distribution/max.
4. Keep product gates open until there is separate hardware evidence for 1,800
   distinct frames over 60 s then 18,000 over 600 s at 30 fps, and strict
   validated decode below 10 ms for every qualified sample. The V108 receipt
   and five functional RTL proofs contain no such hardware evidence.
