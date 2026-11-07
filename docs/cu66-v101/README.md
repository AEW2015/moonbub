# V101: constraints audit and a verified scratch compatibility candidate

V101 adds a clock/reset/interface ledger, corrects the OOC constraint-loading
order, and tests an isolated scratch priority-loop replacement. The numbered
roadmap assigns V101 to constraints and methodology; the scratch change is
supporting implementation-readiness work identified by V100. Arithmetic
width and MAC scheduling changes remain separate future experiments.

**Native component synthesis and behavioral regressions pass; placement is
blocked by LUT RAM capacity and physical V101 signoff remains open.** The
research profile stays CS88/all-BR88 q16, 720×480 and a 49,152-byte complete
packet cap. Historical RTL and constraints remain unchanged. The existing
JPEG/MSV1 firmware/image remains the deployment fallback.

## Results

| Test or audit | Observed result | Scope |
| --- | --- | --- |
| Fresh V99 q16 key/P/late-CRC fixtures | 24 case/profile runs and 52 directed checks pass across baseline/candidate and two seeds | Identical transcripts, events and cycle counters; includes expected rejection behavior |
| Historical V91k canonical reconstruction | 88 case/profile runs and 84 directed checks pass across baseline/candidate and two seeds | Identical transcripts, events, cycles and actual canonical memory bytes |
| Focused scratch priority cone | 43,068 actual RTL prepared-state cases pass; independent Python trace replay also passes | All 47 output names on the 79-port scratch interface; zero clock edges in this focused test |
| Constraints/source ledger | Seven static checks pass; 308 top-level ports, 29 clocked source processes and seven board clock roles inventoried | Source-backed inventory, separate from vendor CDC or methodology signoff |
| Timing requirements | Eight timing files and four flow hooks pinned; ten timing obligations explicitly open | Existing SDRAM/LCD budgets are provisional; no guessed external delays or new exceptions |
| Scratch-only sv2v/Yosys frontend | Reaches a different `zigzag.diagonal` function-iterator error | Complete process lowering and mapping remain failed; no resource or speed gain established |
| Native Vivado 2026.1 baseline synthesis | 74,340 LUTs, 34,985 FFs, 16 RAMB36, 28 DSP blocks; synthesis checkpoint saved | Complete selected component; original RTL, public interface and 10-ns target retained |
| Native pre-placement DRC | 22,286 distributed-RAM LUTs required versus 19,000 compatible sites; `UTLZ-1` errors | Placer did not run; no route or achieved clock exists |
| Native synthesized timing | WNS −16.629 ns, TNS −73,220.930 ns; worst reported path has 49 logic levels | Unplaced synthesis estimates; the 100-MHz target is not achieved |

A [read-only checkpoint capacity report](../../experiments/python-gamebub-v101/constraints/2026-build/analysis/20261107T205034716223Z/utilization-flat.rpt)
confirms 117.26% total LUT use and 117.29% memory-LUT use. FFs, BRAM and DSPs
are at 27.59%, 11.85% and 11.67%, respectively. These are synthesized baseline
utilizations, without a claimed before/after physical improvement.

[Regression evidence](../../experiments/python-gamebub-v101/regression/) records
two seeds, `101401` and `101402`, with unchanged C++ checkers and strict
Verilator assertions/warnings. Fresh tests check 9,158,144 samples at each of
the coefficient/assembly/dequant/residual stages across all four variant/seed
runs. The canonical tests also compare real memory output, without adding a
new standalone RGB565 replay or a complete HUD/C2/display-publication claim.
These are bounded component tests, including intentional invalid-packet cases,
rather than 112 distinct displayed source frames.

## Candidate and source preservation

The [candidate scratch source](../../fpga/experiments/cu66-v101-scratch/packed_scratch_v91g2.sv)
replaces only the conditional three-band loop with explicit DC → band 1 →
band 2 → band 3 priority. It preserves the final word-address expression,
32-bit arithmetic before the masked 18-bit cast, cancellation, raw mode,
ownership, public ports and assertions. Its SHA-256 is
`ba0f184ae2f1a70b550208fa36535457c5115398a12a5f25ec7707426c5ee142`.
The [change manifest](../../experiments/python-gamebub-v101/scratch/change.json)
binds identical original prefix/suffix/header bytes and the replaced span.

[Scratch results](scratch-results.md) describe the exhaustive guards, address
boundaries, random cases and retained verification-compile failure. The
frontend's initial receipt used an overly broad iterator diagnostic flag;
the hash-bound correction identifies the exact later zigzag error. Preserve
both records. No additional RTL/IR workaround suppresses the new failure.

The change deliberately preserves the simulated schedule: no cycle, area,
compression, achieved-clock or hardware-frame-rate improvement is claimed.
Native Vivado 2026.1 also elaborates the original priority and zigzag loops
without the old Yosys iterator error. Keep the original as the physical control;
retain the unrolled candidate as an isolated experiment until a matched
physical comparison justifies selecting it. Further old-frontend work should
not displace measured native-Vivado optimization.

## Constraints and physical gates

[Constraints and methodology](constraints-methodology.md) distinguish the
single-clock OOC custom component from the existing JPEG/MSV1 board design.
The [ledger](../../experiments/python-gamebub-v101/constraints/ledger.json)
includes historical timing Tcl files omitted by V100's XDC-only view, reset
release and crossing families, exact source evidence and interface obligations.

The [new recipe](../../fpga/experiments/cu66-v101-constraints/run.tcl) loads the
same 10-ns comparison clock **before synthesis**. The report recipe requests
min/max and unconstrained timing, clock interactions, methodology, DRC, CDC and
exception reports. Board I/O contracts and those netlist checks remain open;
no false-path blanket, fabricated delay or waiver hides them. Prepared source
snapshots and candidate overrides are separately hashed.

The working 2025.2 installation still reports zero Artix-7 parts. A fresh
container using the installed 2026.1 tools, the existing license read-only
and the real host network identity now starts successfully: exact target
count **1**, Series-7 count **210**, installed part count **289**. Earlier
runtime/license failures remain retained. No host ID, license or active Acorn
project was modified. AMD
documents a [valid launch-license requirement from 2026.1](https://docs.amd.com/r/en-US/ug973-vivado-release-notes-install-license/Supported-Devices-and-Features)
and lists a [free Basic tier supporting Linux and 7-series](https://www.amd.com/en/products/software/adaptive-socs-and-fpgas/vivado/vivado-licensing-options.html).
This restores the tool/device prerequisite. Actual synthesis, implementation
and report outcomes are recorded separately in the constraints report;
the successful query alone does not establish physical signoff.
Physical 30 fps and strictly-under-10-ms validated FPGA decoding remain open.

The [native utilization report](../../experiments/python-gamebub-v101/constraints/2026-build/20261107T203934371554Z/reports/synth-utilization.rpt)
attributes 44,040 LUTs, including 19,956 LUT RAMs, to admission. This makes
the packet-memory read topology the immediate fit experiment. The
[setup report](../../experiments/python-gamebub-v101/constraints/2026-build/20261107T203934371554Z/reports/synth-setup-paths.rpt)
shows the long reconstruction plane-to-counter-enable path. The
[vendor RTL review](vendor-rtl-review.md) gives source-backed memory and
fixed-geometry predicate experiments for V102. Do not lower DRC severity,
delete diagnostics, remove validation or relax the comparison clock to hide
these measured blockers.

The native methodology report contains 2,451 reported findings; its per-rule
enumeration limit was not verified. `check_timing` reports no missing internal
clocks or unconstrained internal endpoints, while 1,101 input bits and 12,885
output bits lack external delay contracts. The single-clock OOC CDC result
does not qualify the missing board/controller crossings. This is measured
methodology evidence with unresolved findings, rather than signoff.

## Reproduce

The operator supplied the 2026.1 installation at host
`/home/lori/acorn-nexys4-ddr/tools/2026.1/Vivado` and license at
`/home/lori/acorn-nexys4-ddr/cache/vivado.lic`. Mount them read-only at
`/opt/amd-tools/2026.1/Vivado` and `/cache/vivado.lic` in the prepared runtime.
Inside that container the explicit environment setup is:

```sh
source /opt/amd-tools/2026.1/Vivado/settings64.sh
export XILINXD_LICENSE_FILE=/cache/vivado.lic
```

The working container uses the real host network identity for the existing
node-bound license. It needs no USB access. License contents are excluded from
Git. The native build receipts preserve the environment and paths actually
used; the constraints report documents the supplied-path alias separately.

Use the retained Docker build environment with GCC 13.3, Verilator 5.020,
Yosys 0.33 and external sv2v 0.0.13. Repository and external `/build` binds must
match the runner paths. Fixtures and goldens are already tracked; no connected
Game Bub or external video download is needed for these component regressions.

```sh
python3 scripts/cu66-v101/constraints.py
python3 scripts/cu66-v101/regress.py --mode fresh
python3 scripts/cu66-v101/regress.py --mode canonical
python3 scripts/cu66-v101/scratch.py
python3 scripts/cu66-v101/scratch.py --frontend
```

The final frontend command currently exits nonzero on the retained failure.
All runners create fresh attempt directories. Regenerating test evidence
requires a new audit and bundle; it does not replace the published checkpoint.
Heavy jobs require at least 8 GiB available RAM and memory PSI full avg10 below
1; keep at most two heavy host jobs and the shared 4-GiB build-container limit.
Swap occupancy alone does not block work.

To verify retained evidence without rerunning expensive tools:

```sh
python3 scripts/cu66-v101/audit.py
python3 scripts/cu66-v101/bundle_manifest.py --verify
```

The [independent audit](audit.md) checks source scope, actual terminal verdicts,
trace/receipt hashes and the boundaries of each claim. Its evidence PASS does
not close the remaining physical signoff gates.
