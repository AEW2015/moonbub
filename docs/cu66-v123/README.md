# V123: prepared scratch rank and spatial-overlap prototypes

**V123 improves timing, but still fails 125 MHz and is not promoted.**
The [routed results](timing-results.md) are WNS −1.086 ns, TNS −1,709.649 ns and
6,724 setup failures, versus V122's −1.949 ns/−4,597.575 ns/11,866 failures.
All 1,063 independent evidence checks pass while design timing remains FAIL.

The [new scratch source](../../fpga/experiments/cu66-v123-rank/packed_scratch_v91g2.sv)
prepares a 64-bit rank-threshold mask on the existing APPEND edge, then uses its
selected bit in parallel with live full32 position/block comparisons. Full-width
generic semantics, first-fault priority, accepted debt, cancellation and public
cycles are preserved. No packet format, quality/rate policy or production
Sunshine/ESP32 endpoint changes. All other seventeen source/include origins
remain exactly V122, including its admission preparation and V121 refill queue.

## Measured and modeled results

- [Focused RTL](focused-results.md), complete decoder/actual V97 transport,
  physical-debt peer and byte/row parent all PASS. Ten raw stream sets match
  frozen V122 exactly; public-cycle delta is zero.
- RAW-mode all-endpoint slack improves **−1.949 → −0.891 ns**. The new mask's
  all-endpoint worst is **+0.159 ns**. Global worst is now emit-bank → owner-ready
  retirement. Some unchanged paths still regress; see the full timing table.
- The mask maps to 63 FFs; total LUTs fall 378, global FFs rise 381, DSP/BRAM use
  stays unchanged. Fresh TIMING-16 large-setup entries fall 800→2, while 6,724
  setup endpoints still fail. Counts are not interchangeable timing gates.
- The [independent Python rank model](rank-model.md) checks mapping, full32
  boundaries/random cases and phase/error contexts. It supplements RTL evidence.
- The [causal overlap prototype](spatial-results.md) preserves six retained
  canonical byte vectors and passes 14 fault/model checks. Two slots reduce
  synthetic batch cycles 1.92–2.00×; a second compute lane adds no benefit under
  those particular costs. These are architecture hypotheses with unbudgeted
  mirror/port and omitted physical traffic costs, not measured FPGA speedups.

The [machine result](../../experiments/python-gamebub-v123/results.json) binds
selected proofs, audits, native run, checkpoint queries and Python studies.
See [functional results](functional-results.md), the frozen [design](rank-design.md)
and [verification plan](verification-plan.md), and [reproduction](reproduce.md).
The retained first focused attempt stopped at an inherited prepared fixture;
its reference-cache initialization was repaired without changing RTL or checks.

## Remaining timing and hardware gates

The [next bounded experiment](next-timing.md) compares each bank's full owner
identity before selecting a single match bit, targeting the measured cross-module
bank/owner/ready return. It is proposed and not implemented here.

Row post-input→validated-commit cycles remain 1,145,104/1,553,197. At an assumed
complete-parent 125 MHz these project to 9.160832/12.425576 ms. The stalled case
still needs 303,198 fewer cycles for strict <10 ms. Actual overlap implementation,
complete-parent timing, calibrated ESP32/Wi-Fi/QSPI/memory service, sustained
distinct hardware 30 fps and validated hardware <10 ms remain open. The broader
V123 spatial-compute/validation-overlap milestone is not closed by these studies.

Use the [qualified V120 Source B100 handoff](../cu66-v120/handoff.md) for the
remote board control. Its original eighteen files remain byte-identical to
`69c0f145`. No board was contacted/programmed or complete board image generated.
The production parent remains JPEG/MSV1 until negotiated custom-codec integration.
