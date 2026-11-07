# V101 independent evidence audit

The standard-library auditor checks source bindings, immutable regression and
Vivado receipts, retained artifact hashes, and the explicit open gates. Its
`PASS_EVIDENCE` status means the reports are internally consistent and their
limits are represented accurately. It does not mean V101 physical or product
qualification is complete. See the machine-readable [audit result](../../experiments/python-gamebub-v101/audit.json)
and the V101 [constraints/methodology notes](constraints-methodology.md).

## Frozen sources and candidate scope

The V100 baseline commit `e8bb1c9cc3cec6775cf128c8fd538a56f022575f` is in the
checkout history. The CS88-V99-RC1-Q16-BR88 profile matches its V100 Git blob
(SHA-256 `8e17b24a…735be`), and all 63 frozen V100 inventory files match both
their recorded hashes and baseline blobs. The candidate is an isolated copy of
`packed_scratch_v91g2.sv`; the original remains byte-identical to its baseline
blob. The auditor verifies that candidate prefix and suffix bytes match around
the one approved change: expanding the band-priority loop into explicit
band-1/2/3 checks.

## Actual RTL evidence

Fresh and canonical regressions compare the original frozen RTL against the
isolated candidate with the same seeds and unchanged checkers. Each run in each
variant passes terminal status `TEST_PASS`; same-seed stdout, event traces,
cycle results, and canonical memory bytes where applicable are byte-identical.

- Fresh key/component: 2 seeds × 2 variants, 6 cases and 13 directed checks
  per run; 24 case/profile runs and 52 directed checks total. Each transform
  stage has 9,158,144 exact comparisons across the four seed/variant runs.
- Canonical reconstruction: 2 seeds × 2 variants, 22 cases and 21 directed
  checks per run; 88 case/profile runs and 84 directed checks total. Each
  transform stage has 16,233,472 exact comparisons across the four runs, and
  canonical output has 28,339,200 exact comparisons.
- Scratch priority cone: 43,068 actual RTL comparisons across two seeds
  (21,534 each), 79 public port views including 47 outputs and five internal
  cone signals. This combinational probe advances zero clock edges. A separate
  Python model replays all 43,068 saved trace rows.

The scratch-only Yosys process-lowering attempt is a retained failure. Synthesis
of its converted file stopped at a different `zigzag` function iterator latch;
the removed priority iterator itself is absent. The runner's broad latch flag
is superseded by a hash-bound precise diagnosis. This attempt supplies no
successful scratch mapping, area, or timing result. The Verilator probe and
Python replay do not establish sequential equivalence or hardware behavior.

## Clock, reset, and constraints inventory

The frozen component exposes 308 ports (37 inputs and 271 outputs), with 29
clocked source events, all on `posedge clk`. The selected OOC recipe defines
only one 10 ns comparison clock and loads it before synthesis. Its XDC contains
no input/output delays, clock groups, false paths, or other exceptions.

The existing JPEG/MSV1 board source inventory records seven clocks, three reset
groups, four crossing classes, eight historical constraint sources, and ten
unresolved timing obligations. The historical sources include prior timing
Tcl files, but are not applied to the custom component. The component has no
qualified external arrival/required times. The source-level inventory is not
an instantiated CDC or timing-coverage report.

## Vivado 2026.1 component attempt

The read-only 2026.1 installed-part query found one exact
`xc7a100tcsg324-1` part, 210 Series-7 parts, and 289 total installed parts. The
provided license path was verified byte-identical to the existing license used
for the successful query and build. No license contents or fingerprint were
recorded, and no host ID, MAC address, license file, or other project was
changed.

The unchanged `cs88_pipeline_v91k` OOC baseline synthesized for the exact part
with a 10 ns comparison clock and produced native synthesis timing, DRC,
methodology, CDC, exception, utilization, and checkpoint evidence. The
synthesis-stage hierarchy reports 74,340 total LUTs (52,054 logic LUTs and
22,286 LUTRAM), 34,985 registers, 16 RAMB36 tiles, and 28 DSP48E1 cells. A
separate read-only checkpoint analysis confirms the 28 DSP cells and reports
capacity usage of 117.26% for total slice LUTs and 117.29% for LUT-as-memory;
it did not repeat synthesis or implementation.

Placement did not start. Vivado's unmodified DRC stopped before the placer with
three `UTLZ-1` errors: 22,286 LUTRAM cells require 19,000 compatible sites, and
19,956 RAMD64E cells also exceed the 19,000 compatible sites. No waiver or
error downgrade was applied. There is no place/route checkpoint or achieved
Fmax.

The actual synthesis reports show 2,451 methodology findings with zero
resolved and zero waived. They include 1,000 `TIMING-16` large-setup warnings,
1,000 `TIMING-18` missing-I/O-delay warnings (the methodology extraction is
explicitly non-exhaustive at this count), 378 `SYNTH-5`, eight `SYNTH-6`, one
`ULMTCS-2`, and 64 `RTGT-1` advisories. `check_timing` reports 1,101 inputs and
12,885 outputs without delays, with zero unconstrained internal endpoints.
Post-synthesis estimates include WNS −16.629 ns and TNS −73,220.930 ns; these
are not routed timing or an achieved frequency. The CDC report says “All paths
are Safely Timed” for this single-clock OOC design; it does not qualify the
multi-clock board design.

## Open gates

Actual board/controller I/O timing requirements, placement and route, resource
fit, reviewed methodology/DRC/CDC findings, justified exceptions, and a complete
custom top remain open. The existing component is not an integrated decoder
with HUD/C2/publication, shared memory, display, and transport. This evidence
does not qualify hardware 30 fps or complete validated decoding below 10 ms.

Reproduce the audit with:

```sh
python3 scripts/cu66-v101/audit.py
```
