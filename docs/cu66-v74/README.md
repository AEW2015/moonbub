# CU66 V74 — tile-major memory prototype

Matched predicted-frame time improves **129.17 → 92.38 ms (28.48%)** in the
checked SDRAM command model. Four chronological frames are exact with zero LCD
underruns. Native and converted painter tests each verify 39 rasters. The larger
input cache currently costs substantial distributed RAM; target 30 fps,
under-10-ms validated decoding and exact-device fit remain open.

- [Results, integration instructions and next milestones](hardware-handoff.md)
- [Iteration plan](plan.md)
- [Tile-major memory and wide auxiliary reads](memory.md)
- [Tile-aware painter](display.md)
- [Frontend validation and unplaced mapping](elaboration.md)
- [Direct-YUV Python study](direct-yuv.md)

Source, retained logs and machine-readable results are in
`fpga/experiments/cu66-v74/`. Producers and read-only integrity gates are in
`scripts/cu66-v74/`. Frozen V69–V73 bundles are preserved.
