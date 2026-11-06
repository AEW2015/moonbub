# Explicit pipelined direct-owner selection

This is an isolated DY71 successor binding, not a replacement of the frozen base experiment. The top differs from `cu71_system_direct` only by its module name and the explicit `cu71_direct_scanout_pipe` instance. The grouped bridge, qualified controller, PHY, memory map, codec and identity/fence adapter remain byte-identical to the passing grouped baseline selection.

The native chronological KEY/P/P A/B passes full canonical/HUD verification, lost-COMMIT-ACK recovery and a complete clean LCD raster for all three generations. Both owners observe zero underruns and zero black lines. Relative to the base-owner/grouped selection, transaction cycle deltas are 0, +12 and +2,765. The pipelined selection takes 2,049,238; 3,438,483; and 4,552,368 memory clocks respectively. Presentation and first-canvas timestamps are identical in this cohort.

`qualification-three-v001.json` binds selected RTL, native fixture/HUD tests, per-stage durations and every observed complete-raster identity. The owner hash is `825ffcd0b134a894ab21612edb4d2aafce299abb3cf15c2d29fdd13fbef9c6dc`; the grouped bridge remains `8c73e1f3bac525e51db7777416c6a291a7e061c8e9e2ed0d23a532c9097c7a9a`.

The owner's separate positive internal synthesis setup result is not a complete-board timing pass. Fit, routed setup/hold, bundled-data CDC, a separately reviewed DY71 CSR/firmware adapter and controlled physical tests remain required. The second P is 45.52368 ms in this native test; no steady 30-fps result is claimed. The frozen 32-bit internal DMA cookie and diagnostic counter limits also remain unchanged.
