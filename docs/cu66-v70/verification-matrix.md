# CU66 v70 verification matrix

This matrix separates functional, modeled deadline and physical gates. Results
are indexed in [the handoff](hardware-handoff.md) and independently reconciled
by `scripts/cu66-v70/verify_evidence.py`. Historical failed/pre-fix runs are
retained separately and are not current-source PASS evidence.

| Requirement | Retained evidence | Status / remaining boundary |
|---|---|---|
| Packet owner, qmap and generations | `receiver/results.json`:457 original packets, actual parser/base and prior RTL-written references; seven control modes | PASS with transactional RAM and completion-model painter/scanout |
| Real memory map/adapters/completion | `memory/results.json`:8 dual-backend/seed/corner runs;227 tiles,3695aux ops and43abort probes per run | PASS for full x16 writes, reads and drains; masked/odd-byte/BL8 writes unimplemented |
| 32MiB address bounds | Full24-bit word model, guards, four internal banks and word0xffffff; no address truncation | PASS command-model scope; capacity is not physical validation or BRAM fit |
| Exact display/HUD/portrait | `display/results.json`, `strip-results.json`, `strip-control-results.json`:91 complete raster executions | PASS exact stored outputs; repeated fixture executions, not91 independent captures |
| LCD descriptors and reader drain | Component async-clock tests; actual generation/frame/slot ACK controls root bank release | PASS declared simulations and safe whole-black-line fallback; clean loaded cadence fails |
| HUD control framing and native endpoint | Python11 tests; native release/sanitized457 histories each; Python/C++ compatibility | PASS host codec/endpoint; system processor peer remains typed, physical link unimplemented |
| HUD global commit and retry | Same-lease semantic/readback/transfer fences; root shared commit; lost COMMIT ACK and encoded COMMIT/ABORT retries | PASS tested RTL/native paths separately; no wire-to-RTL/ESP32 deployment claim |
| Sticky fault/diagnostics/watchdog | `owner-control/results.json`:618 assertions,561 clocks,10 stale notifications,512-cycle watchdog and checked ring | PASS public control scope; fault address is last observed request context |
| Failure preservation/recovery | `negatives/results/results.json`:28 reject/recovery cases; write-error/manual-abort/stale-message controls | PASS accepted canonical/HUD preservation with actual stored reference feedback; all source pins checked |
| Actual controller and display together | `system/full-direct/results.json`, `full-strip/results.json`:key/P pair per painter, full canonical/RGB/HUD readback | PASS functional framebuffers; FAIL_UNDERRUNS for presentation cadence |
| Reset and CDC | Joint reset/flush contract; asynchronous pixel/memory schedules; staged OOC CDC report commands | Simulation evidence only; formal CDC/reset-domain and physical timing signoff NOT_RUN |
| Bank formal safety | `formal/results.json`:16 assertions at8/16/24 solver-state bounds,5 reachability witnesses | PASS_BOUNDED only; no induction/liveness/full-receiver/CDC proof |
| Long fixed-arrival cadence | Current runs are decoder-driven finite chronological pairs; black-line loss and transaction tails retained | Failed current throughput gate;1800 distinct sources/jitter/loss and10-minute physical30fps NOT_RUN |
| Built-in bring-up sequence | Replay scripts exercise memory, bars/edge patterns, real key/P and abort/recovery | Simulation/native test sequence available; autonomous board ROM/firmware BIST unimplemented |
| Exact target implementation | `build/preflight.log`, `build/status.json`, staged hardware-only OOC script | UNAVAILABLE:xc7a100tcsg324-1 not installed; no device Fmax/fit/route claim |

The command-level system uses real controller commands and a checked functional
SDRAM model. It is not a vendor/electrical model. Native HUD CPU execution,
live capture/Wi-Fi/QSPI, firmware coexistence and achieved device clocks are
outside simulated time/evidence. Complete framebuffer comparison remains
independent of the LCD's observed whole-line fallback. Descriptor ACKs and
expected-black lines are not counts of complete clean game frames.

The audited environment is the existing tools container
`gamebub-cu66-v69-build`, image
`sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf`:
GCC13.3, Verilator5.020, Icarus12, Yosys0.33 and CMake3.28.3.
The 15 reviewed baseline files and all4,879 v69 bundle files remain unchanged.
The unrelated untracked `marker-recovery/` tree is excluded from all v70 work.
