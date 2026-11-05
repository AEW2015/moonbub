# Capture135 validation — 2026-11-05

**Overall: FAIL / NOT FOR HARDWARE.** The complete digital fixture passes, but
the source-bound routed implementation fails SDRAM setup and constraint-coverage
checks. No image was generated; no hardware programming occurred in this work.

## Executed functional checks

Exact candidate product RTL, native ODDR/IOBUF branches, strict hold model,
unchanged ROM/assets and the actual board testbench were used. `SIMULATION`
was not defined. Each complete run passed 139 checks, 40 guarded QSPI reads,
259,200 modeled pad write beats, two identical canvas scans and the independent
fixture checker. Both reported `4c5725e5`:

| Effective clock-flight assumption | Access assumption | Hold assumption | Result |
|---:|---:|---:|---|
| 0 ns | 2 ns | 0.5 ns | Full modeled fixture PASS |
| 4 ns | 4 ns | 0.5 ns | Full modeled fixture PASS |

These are synthetic delay assumptions. The primitive subset has no real I/O
buffer propagation, PLL jitter or analog board behavior. They are not measured
physical corner qualification. Two scans of one fixed input are not unique FPS.

Source/asset hashes, compile/run commands, wall times, checker outputs and
full logs are retained under the candidate's `evidence/full-early01` and
`evidence/full-late01`. The full runner refuses existing output directories.

## Executed implementation — rejected

Candidate: `cp23-sdram-capture135-20261105-v001`, `implementation01`.
Routed checkpoint SHA-256:
`fec9283f0c7a3e667f8ad93a99f2eb3e1c726f6200a840fa49369fc37f71629b`.

| Gate | Measured result |
|---|---|
| Setup | **-3.605 ns**, 2,981 failing endpoints |
| Hold | +0.034 ns, zero failing endpoints |
| Pulse | +2.000 ns, zero failing endpoints |
| Routing | 49,988 / 49,988 nets, zero routing errors |
| Four declared bus-skew checks | All met; minimum +3.587 ns |
| Coverage gaps | 18 input / 7 output / 0 partial-input, versus retained baseline 17 / 2 / 1 — **FAIL** |

The input setup path is `sdram_dq[3]` to `dq_capture_reg[3]/D`. Its routed
requirement is 8.750 ns; external delay is 7.000 ns, data path 1.489 ns and
clock skew -3.687 ns. Therefore internal replication cannot repair this path.
The earlier synthesized edge audit also failed it (-4.269 ns).

The coverage check caught an overly broad constraint-block replacement: it
dropped the original first-stage synchronizer exceptions and QSPI propagation
bounds along with the intended old receive-clock section. The failure is
preserved. The gate reader now records coverage failure explicitly rather than
stopping before writing a failure report. It does not accept the new gaps.

Fresh `cp23-sdram-capture135-20261105-v002` restores the exact unchanged common
constraint tail. Its product RTL is identical to v001, so the HDL model result
still describes those product files; v002 has no implementation result or BIT.
The preparation script now changes only the receive-clock section. Reinstating
the common bounds does not itself correct the measured SDRAM input deficit.

## Consequences for the next design

The functional-model success and physical timing failure expose different
gates. Keep the declared input/output budgets and actual buffer/clock delays
visible. The source already uses FAST slew and DRIVE12 for SDRAM_CLK; do not
describe FAST slew as an unimplemented improvement.

Screen supported I/O-buffer settings and a correctly indexed previous-beat
capture window before rebuilding another complete candidate. Any checkpoint
parameter screen is hypothesis evidence only: it needs matching source,
correct constraints, functional delay-model coverage and a fresh implementation
before hardware. Do not add a multicycle solely to hide a violation.

Then run independent raw memory/read-return diagnostics and the unchanged
physical CRC. Consider the available SERDES4 PHY as a separate integration if
the focused architecture cannot provide a qualified window. The earlier
conditional 1–2 hour estimate was for a first testable candidate; **a fixed
hardware ETA is not established after this rejection**.

Sunshine custom network testing remains blocked. Offline sender/log validation
can continue. Installed v32 / restored build50 is unchanged; any legacy JPEG/AV
control test requires its own fresh readiness/counter announcement.

The [timing-margin plan](FPGA-TIMING-MARGIN-PLAN-20261105.md) now puts this I/O
correctness/window work ahead of internal replication and pipelining.

## Next checkpoint screen and fresh source

Screen03 reopened the rejected route in memory, reinstated the missing common
bounds, and evaluated a 270-degree previous-beat clock with setup-2/strong-hold
semantics. It reported SDRAM input setup +0.145 ns and input hold +0.434 ns.
It also reported -7.535 ns on the restored CS-to-DQ max-delay path in that old
placement. It is not a qualified implementation. It did not write a checkpoint,
BIT or hardware. The screen set a supported DRIVE16 port property; no delay
benefit is inferred from that property edit without a fresh source build.

Earlier screens are retained: DRIVE24 was rejected as unsupported for this
standard, and changing IBUF_LOW_PWR on checkpoint cells was rejected by Vivado.
Neither was adopted. No new source uses those unsuccessful settings.

Fresh `cp23-sdram-capture274p5-20261105-v001` starts from the sealed source,
uses a 274.5-degree read clock and rising retime, preserves the original
previous-beat setup-2/strong-hold convention and exact common constraint tail,
and keeps FAST/DRIVE12 and the original external budgets. This is a new
correctness candidate, not a reproduction of the old phase.

Its focused burst tests pass two implementation-derived budget points, with
zero write or read errors. A deliberately out-of-envelope zero-loop case fails.
The points separate clock-loop and data-buffer contributions: slow SCD-DCD
3.768 ns with access budget 7+1.489 ns; fast SCD-DCD 0.757 ns with hold/access
budget 2+0.223 ns. These are mathematical reductions of a checkpoint's reports,
not measured board delays, and must be rechecked on the fresh implementation.
The source is currently undergoing full-board model tests and a fresh build;
it has no final timing/CRC qualification or BIT yet.
