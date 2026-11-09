# V115 source inventory and qualification boundary

Read-only inventory for branch `study/gamebub-v115-timing-cuts-20261108`, base `6098d48e5c4b57576fddeec1ae6facbc25165a11`. The machine-readable inventory contains the exact 18 V114 B-composition source-origin alias/path/SHA pins, RTL read order, native receipts and inputs, policy pins, tool images, and reproduction paths. All 18 mapped worktree source hashes match the pinned SHA values. No builds, test reruns, native jobs, hardware access, or network activity were performed.

## Routed evidence carried forward

| Composition | Clock | WNS | Setup failures | Receipt SHA-256 |
| --- | ---: | ---: | ---: | --- |
| Reserved control A | 100 MHz | −1.670 ns | 8,299 | `2ab4321ee00df9245578cc1de9e6cf67655dd37975909ae890dea3c0114cf141` |
| Prepared-prefetch B | 100 MHz | −0.965 ns | 3,032 | `325d79fb5338ab57f84a5d01f81c11449df84eedcefdc4299ee0670917f293cc` |
| Prepared-prefetch B | 125 MHz | −2.696 ns | 33,428 | `521daae4a0f1ddc8c119a116c71eaee523cc3bf7c8295fe9b7a9e5ba5c7de1b1` |

Each route completed with zero hold failures, zero pulse-width failures and zero routing errors, but all three fail internal setup. B100 improves on A100 and remains negative; B125 remains negative and has more setup-failing endpoints than the V112125 comparison. These component routes do not qualify a usable clock or whole-parent fit.

## V115 qualification remains open

The branch has no live Sunshine CS88 encoder/packetizer, negotiated CS88 ESP32 receiver, production QSPI/CDC-to-CS88 ingress, complete CS88 production parent, C2/HUD seal, or display publication path. Existing V114 transport simulation uses a parallel command adapter. No deterministic full-system 60 s or 600 s campaign is qualified. Modeled campaigns cannot stand in for actual firmware CPU cycles or hardware service without calibrated silicon evidence.

A useful small handoff while timing cuts proceed is a one-frame trace through the existing JPEG/MSV1 sender→receiver/FPGA-SPI path, recording actual serialized bytes/hash, frame identity, timestamps, credit/status transitions, and recovery outcome. Keep it explicitly JPEG-only (codec id 1) and drive existing endpoints; this trace is a harness control, not CS88 integration.

## Reproduction references

See [`docs/cu66-v114/reproduce.md`](../cu66-v114/reproduce.md) and [`docs/cu66-v114/timing-summary.md`](../cu66-v114/timing-summary.md). The pinned simulation image is `gamebub-cu66-v69-tools:20261105`; the native image is `acorn-nexys4-ddr:2026.1` with Vivado 2026.1. Timing and functional artifacts are linked in [`inventory.json`](../../experiments/python-gamebub-v115/inventory/inventory.json).
