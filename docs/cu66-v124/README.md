# V124: bank-owner lanes and native endpoint replay

**Functional checks pass; 125 MHz still fails and V124 is not promoted.**
The fresh route measures **−1.170 ns WNS, −2,527.615 ns TNS and 9,787 setup
failures**, versus V123's −1.086 ns/−1,709.649 ns/6,724. Hold, pulse, internal
clock coverage and routing checks pass. The [independent terminal audit](../../experiments/python-gamebub-v124/audit/native-independent.json)
passes 1,177 evidence checks while reporting failed design timing.

The [new producer](../../fpga/experiments/cu66-v124-owner/cs88_coefficients_v91k.sv)
compares each bank's full32 epoch/full16 block owner before selecting one match
bit. Exactly two scalar result bits have a new RTL KEEP hint. There are no new
registers, public cycles, packet fields or quality/rate changes. The other
seventeen source/include origins remain V123. See the frozen [design](owner-design.md)
and [verification plan](verification-plan.md).

## Results

- [Focused and full functional qualification](functional-results.md) passes:
  generic/actual-controller pairs, complete decoder, actual V97 transport,
  physical-debt peer and byte/row validation parent. Ten raw stream sets match
  V123 exactly; public-cycle delta is zero. The first parent compile's PSI
  watchdog stop is retained; a fresh unchanged-source retry passed.
- The [matched routed observations](timing-results.md) show emit-bank → busy
  improving **−1.086 → −0.562 ns**. Owner-tag, RAW/rank and some refill paths
  regress. The new global worst is admission tile → tile clock-enable, with
  83.7% routing delay. A local improvement does not qualify the component.
- Actual Sunshine C++ packetizer bytes pass through the actual firmware Rust
  protocol receiver in a [portable native probe](endpoint-results.md), including
  bounds, loss/reorder/duplicate/corruption, recovery, ID wrap and feedback.
  Production source snapshots are unchanged and verified against Git blobs.
- The exact native packet file passes the separately reviewed
  [QSPI/CDC/guarded-JPEG RTL replay](jpeg-wire-results.md): both clock alignments,
  four repeated good-frame checks in total, 1,382,400 verified pixels, bad-CRC
  rejection, reset/retry and held-output/bus oracles. Its independent audit
  passes 376 checks. This uses the existing JPEG path, separate from custom CS88.
- The [independent Python owner model](owner-model.md) supplements the RTL
  proofs. It is not a physical timing or formal-equivalence result.

The [machine result](../../experiments/python-gamebub-v124/results.json) pins
selected proofs, audits, native route, queries and auxiliary studies. See
[reproduction](reproduce.md), including the endpoint probe's pinned-HEAD
[worktree instructions](endpoint-reproduce.md).

## Next gates

The [next timing proposal](next-timing.md) prepares full-width tile predicates on
existing register-write edges and localizes control consumers. It requires
additional read-only tile-family observations, exact priority/wrap/hidden-tile
proofs, full regressions and a fresh route. It is not implemented, and RAW and
other negative families remain open. No unchanged negative-source reroute or
positive qualification repeat was performed.

The broader V124 [single-timebase endpoint harness](harness-boundaries.md)
remains open: current proofs use native process/file replay, not the complete
firmware session, ESP32 instruction execution, DMA, Wi-Fi or calibrated physical
memory service. Production JPEG/MSV1 and experimental CU66/CS88 are separate
paths; custom-profile negotiation is still needed.

The row parent remains 1,145,104/1,553,197 last-input→validated-commit cycles.
At an assumed complete-parent 125 MHz these project to 9.160832/12.425576 ms;
the stalled profile needs at least 303,198 fewer cycles for strict <10 ms.
Complete-parent timing, sustained distinct hardware 30 fps and validated hardware
decode below 10 ms remain open. Use unchanged
[qualified V120 Source B100](../cu66-v120/handoff.md) as the remote hardware
integration control. No board was contacted/programmed or board image generated.
