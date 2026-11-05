# CU66 v70 integrated receiver prototype

Start with [the hardware handoff](../../../docs/cu66-v70/hardware-handoff.md),
[reproduction](../../../docs/cu66-v70/reproduction.md) and
[verification matrix](../../../docs/cu66-v70/verification-matrix.md).

Actual packet/qmap/base RTL now reconstructs against previous RTL-written
references. The system top joins that owner to real SDRAM commands, verified
HUD transfer, exact portrait RGB565 output and native LCD descriptor ownership.
Functional framebuffers pass; concurrent clean scanout and30fps do not.

| Directory | Deliverable |
|---|---|
| `receiver/` | Full-packet/generation/bank owner, typed HUD/painter contracts, diagnostics and457-frame transactional-RAM replay |
| `memory/` | Packed-u8 tile and scalar adapters, shared32MiB map, actual conservative SDRAM controller and checked command model |
| `display/` | Exact painter, optional8-row strip, asynchronous LCD descriptor/line wrapper and raster tests |
| `system/` | Connected hardware/simulation tops, guarded HUD writer, actual functional readback, full key/P tests and measured performance failure |
| `control-abi/` | Strict Python HC70/HR70 framing and fragmented-stream codec |
| `software-control/` | Portable C++ encoded HUD semantic endpoint and cross-Python compatibility tests |
| `owner-control/` | Watchdog, stale-response, fault/counter and event-ring tests |
| `negatives/` | All28 malformed/unsupported full-packet reject/recovery tests, preserved harness-failure diagnosis |
| `formal/` | Bounded bank-safety assertions and reachability witnesses |
| `build/` | Exact-part OOC staging and unavailable-target evidence |

Read existing source/log evidence without rebuilding:

```sh
python3 scripts/cu66-v70/verify_baseline.py
python3 scripts/cu66-v70/verify_evidence.py
python3 scripts/cu66-v70/bundle_manifest.py
```

The study does not change the deployed JPEG backend, production RTL or v69
evidence. No board programming, ESP32 memory-fit test, achieved FPGA clock,
physical30fps or wire-to-RTL control transport is claimed. The existing
untracked `marker-recovery/` experiment is unrelated and untouched.
