# CU66 V75 — BRAM caches and guarded HUD bursts

The painter's input caches now map to BRAM: RAM64M **2,304 → 0**, RAMB18E1
**8 → 32**, with an added read cycle per active pixel. Guarded full-BL8 HUD
transfers remove 18,480 write commands and 147,840 physical beats per frame.
Four chronological sources remain exact with zero LCD underruns.

The matched P transaction improves **92.38 → 75.87 ms** in the command model;
the key regresses **45.43 → 47.16 ms**, and the four-frame maximum is **87.28 ms**.
Target 30 fps, under-10-ms validated decoding and exact-device fit remain open.

- [Results, integration and next milestones](hardware-handoff.md)
- [Iteration plan](plan.md)
- [Clocked input-cache painter](display.md)
- [Frontend and unplaced family mapping](elaboration.md)
- [Guarded HUD interface and control tests](hud.md)

Retained evidence is in `fpga/experiments/cu66-v75/`; producers and read-only
audits are in `scripts/cu66-v75/`. Frozen V69–V74 bundles are preserved.
