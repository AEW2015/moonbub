# V103: geometry arithmetic and parser technology-mapping review

V103 continues from published V102 commit
`6d2ca3ae9abe207215d6130cfb0087fd07928917`. It isolates two exact geometry
rewrites before changing the pipeline schedule. The CS88/all-BR88 q16 profile,
720×480 coded resolution, 49,152-byte cap, ports, validation, public counters
and historical sources remain unchanged. The production JPEG/MSV1 image is
outside this experiment.

## Candidate changes

The [reconstruction candidate](../../fpga/experiments/cu66-v103-reconstruct/cu66_reconstruct_stream_v91k.sv)
changes only `quant_cell`. It replaces runtime division/modulo with a parallel
constant interval-to-offset decode and eleven-bit subtraction. Its complete
four-plane, thirteen-bit-tile domain passes **32,768 actual RTL comparisons**
against V102 and an independent model. All invalid/out-of-picture function
inputs are included. The [focused report](reconstruct-results.md) gives the
algebra, exact edit boundary and independent Python trace replay.

The [admission candidate](../../fpga/experiments/cu66-v103-admission/cs88_admission_v91i2a.sv)
changes only `cell_index`. Its full unsigned 32-bit identity is
`floor(t/2) − 45*ceil(floor(t/90)/2)` for Y, retaining `t` for other planes.
The source narrows intermediate arithmetic using proven mathematical bounds;
the tile state and function result stay 32 bits. **130,920 actual RTL
comparisons** cover every tile 0–8191 on all four planes, high-value and
quotient/power boundaries, and deterministic random samples. This is not
exhaustive simulation of all 2³⁴ plane/tile inputs. The
[focused report](admission-results.md) distinguishes its full-domain algebra
from its sampled simulation and independent Python trace replay.

Both focused probes have **zero clock edges**: they test combinational
functions through adapters that preserve the whole production module body.
Sequential protocol behavior is checked by the paired pipeline regressions,
which retain the historical strict Verilator/C++ checkers and stall/abort/
reset/error coverage.

The [stopped-attempt ledger](../../experiments/python-gamebub-v103/stopped-attempts.json)
retains a combined-regression attempt whose first baseline simulation passed,
then whose next launch was denied by transient host memory pressure. No paired
result completed in that attempt and no RTL mismatch was reported. The retry
uses unchanged sources, seeds and resource thresholds. Only complete selected
receipts count toward the passing regression totals.

| Selected paired lane | Case/profile runs | Directed checks | Result |
| --- | ---: | ---: | --- |
| Reconstruction only, canonical | 88 | 84 | PASS |
| Admission only, fresh key/P/late-CRC | 24 | 52 | PASS |
| Admission only, canonical | 88 | 84 | PASS |
| Combined, canonical retry | 88 | 84 | PASS |
| Total | 288 | 304 | PASS |

The counts include baseline/candidate, two seeds, memory profiles and expected
reject cases. They are not 288 unique displayed frames. Every selected lane
has byte-identical same-seed transcripts, stage events and cycle counters;
canonical lanes also compare actual canonical memory bytes. The independent
source/provenance audit passes **19/19 checks** and reproduces deterministically.

## Implementation and proof scope

The [native comparison](vendor-comparison.md) records isolated synthesis
effects and the combined implementation against matched V102 stages. The
[checkpoint JSON](../../experiments/python-gamebub-v103/summary.json) binds
selected functional/native receipts, counts and open qualification gates.
The [source audit](audit.md) and separate native audit verify retained input
hashes and actual terminal results; their evidence PASS is not timing signoff.

| Routed component | LUTs | LUT RAMs | RAMB36 | DSPs | Setup WNS at 10 ns |
| --- | ---: | ---: | ---: | ---: | ---: |
| V102 control | 48,522 | 2,718 | 32 | 28 | −13.976 ns |
| V103 reconstruction only | 48,179 | 2,718 | 32 | 28 | −14.036 ns |
| V103 combined | 47,740 | 2,718 | 32 | 28 | −17.586 ns |

Both V103 components complete routing with zero routing errors: reconstruction
routes all 72,392 routable nets, and combined routes all 72,075. Reconstruction
saves 343 LUTs but loses 0.060 ns of worst setup slack; combined saves 782 LUTs
but loses 3.610 ns. Their hold slacks are +0.071 and +0.079 ns respectively.
Neither closes the 100-MHz comparison target or demonstrates a routed timing
gain. The modest synthesis improvement did not carry through to route.

The [source selection](../../experiments/python-gamebub-v103/selection.json)
therefore **retains V102** for the next study. Its recorded rule requires
strictly better routed setup slack, nonnegative hold/pulse slack, zero routing
errors and no LUT/weighted-BRAM/DSP increase; then it prefers best setup slack.
V103 candidates remain reproducible experiments, with their area/timing
tradeoffs retained. This selection is not production image or hardware
qualification. All four native attempts exited successfully; no V103 build
remains running.

The [parser mapping review](parser-mapping-review.md) inventories the actual
Rice/context/ingress widths, controls and mapped resources, and ranks bounded
prefix/reservoir experiments. Parser RTL remains unchanged in these geometry
variants. V102's worst routed path was geometry-to-residual-enable logic,
so geometry gets the first native comparisons; parser-specific area or speed
improvement is not claimed from that review.

The separate [prefix model](parser-prefix-model.md) passes **1,548,910 Python
comparisons** between the source-style scan and an aligned-window leading-zero
formulation. It covers all 65,535 distinct prefix words over widths 0–15 at
representative availability counts, plus random 64-bit reservoirs, every
availability 0–64 and unused-tail boundaries. It has no actual RTL, complete
parser-state, synthesis or physical-performance claim. Parser-native variants
remain open; these counts are separate from the geometry RTL regressions.

Native jobs use Vivado 2026.1 build 6511674, `xc7a100tcsg324-1`, the unchanged
10-ns comparison clock loaded before synthesis, Default directives, two
threads, and unchanged public diagnostic visibility. Parent clock location,
boundary pin locations and external I/O contracts remain unknown. No invented
I/O delays, clock-buffer locations, false paths, waivers or retiming conceal
those obligations. These are single-clock OOC component experiments, with
full HUD/C2/frame seal/shared-memory/display/ESP32 integration still open.

The existing legitimate license and installed tools are mounted read-only
into task-owned containers. Vivado MCP returned `Transport closed`; the
working bounded batch flow is used. Its CLI now propagates failed/missing
terminal results after saving their receipts. Checkpoints and executables
stay in external build directories; reports and source/hash manifests are
retained in this handoff. No attached hardware is contacted.

## Reproduce

```sh
python3 scripts/cu66-v103/reconstruct.py
python3 scripts/cu66-v103/admission.py
python3 scripts/cu66-v103/regress.py --variant reconstruct --mode canonical
python3 scripts/cu66-v103/regress.py --variant admission --mode fresh
python3 scripts/cu66-v103/regress.py --variant admission --mode canonical
python3 scripts/cu66-v103/regress.py --variant combined --mode canonical
python3 scripts/cu66-v103/build.py --variant reconstruct --synth-only --run
python3 scripts/cu66-v103/build.py --variant admission --synth-only --run
python3 scripts/cu66-v103/build.py --variant combined --run
python3 scripts/cu66-v103/build.py --variant reconstruct --run
python3 scripts/cu66-v103/audit_sources.py
python3 scripts/cu66-v103/audit_native.py
python3 scripts/cu66-v103/summarize.py
python3 scripts/cu66-v103/bundle_manifest.py --verify
```

Each experiment creates a fresh attempt. Baseline compilation uses V102's
memory and predicate candidates; candidate compilation replaces only the
selected V103 function(s). The fresh V91j source closure excludes reconstruction,
so a reconstruction-only fresh run is unnecessary; combined fresh has the
same changed source closure as admission fresh.

Use the existing `gamebub-cu66-v69-build` Verilator 5.020/GCC 13.3 environment
and `acorn-nexys4-ddr:2026.1` native runtime. Launch only with at least 8 GiB
available RAM and memory PSI full avg10 below 1, with at most two heavy jobs.
Native jobs have an 8-GiB hard limit without extra swap, two CPUs, two Vivado
threads and finite watchdogs. The shared Verilator container retains its
4-GiB limit. Available RAM/pressure gates govern launches; stale swap occupancy
alone does not block them.

Sustained hardware 30 fps and complete validated FPGA decoding below 10 ms
remain open. These representation-only changes preserve behavioral cycles;
even at the comparison target, the fresh key's 1,386,271 component cycles
exceed 10 ms before missing whole-path work. Routed timing and eventual board
measurements, rather than source arithmetic or a simulator's wall time, must
determine achievable performance.
