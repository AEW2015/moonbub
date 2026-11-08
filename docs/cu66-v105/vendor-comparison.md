# V105 native comparison

Vivado 2026.1 build 6511674 targets `xc7a100tcsg324-1`, using the retained
17-file component closure, a 10 ns clock loaded before synthesis, Default
directives and two tool threads. Each owned build is limited to two CPUs and
8 GiB. The actual host identity and installed read-only license are used.
V102's published reports are the immutable control; V105 does not substitute
a different historical admission or reconstruction source.

| Variant | Stage | LUTs | LUTRAMs | FFs | RAMB36 / RAMB18 | DSPs | WNS (ns) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| V102 control | synth | 49,040 | 3,854 | 34,689 | 32 / 0 | 28 | -12.181 |
| V102 control | place | 48,522 | 2,718 | 34,795 | 32 / 0 | 28 | -12.979 |
| V102 control | route | 48,522 | 2,718 | 34,795 | 32 / 0 | 28 | -13.976 |
| memory | synth | 47,482 | 2,330 | 34,672 | 32 / 1 | 28 | -11.728 |
| admission | synth | 49,432 | 3,854 | 34,716 | 32 / 0 | 27 | -11.108 |
| geometry | synth | 46,691 | 3,854 | 34,721 | 32 / 0 | 27 | -11.593 |
| geometry | place | 46,115 | 2,718 | 34,760 | 32 / 0 | 27 | -12.375 |
| geometry | route | 46,115 | 2,718 | 34,760 | 32 / 0 | 27 | -13.124 |
| combined | synth | 49,649 | 3,854 | 34,791 | 32 / 0 | 28 | -12.014 |
| combined | place | 49,040 | 2,718 | 34,829 | 32 / 0 | 28 | -12.703 |
| combined | route | 49,040 | 2,718 | 34,829 | 32 / 0 | 28 | -13.653 |
| locality | synth | 48,522 | 2,330 | 34,769 | 32 / 1 | 28 | -12.015 |
| locality | place | 47,966 | 1,194 | 34,827 | 32 / 1 | 28 | -12.599 |
| locality | route | 47,966 | 1,194 | 34,827 | 32 / 1 | 28 | -13.956 |

The next-study selection is **geometry**, with setup WNS
-13.124 ns and a
+0.852 ns change from the V102 routed
control. See the exact [source map and selection rule](../../experiments/python-gamebub-v105/selection.json).
Only fully routed variants can be selected. A single implementation run does
not establish a robust speedup across seeds or hardware.

GEOMETRY is the selected measured point: 46,115 LUTs and 27 DSPs, reducing
routed LUT use by 2,407 (4.96%) from V102. The mode RAM remains an independently
verified building block: LOCALITY preserves its RAMB18 through routing and
uses 1,194 LUTRAMs, versus 2,718 in COMBINED. The joint RAM/DSP variant does
not win the routed setup comparison. GEOMETRY plus mode RAM with DSP prefetch
omitted is an unmeasured next comparison; this matrix is not an exhaustive
factorial or a globally optimal implementation claim.

Admission and memory alone are synthesis-only experiments. Geometry combines
the new admission cache with V104's reconstruction cache. Combined adds
V104's dequantizer product prefetch. Locality adds the V105 single-port mode
table to that combination. Synthesis counts and timing estimates must be
compared with synthesis; only routed values are physical routing comparisons.

Detailed [native evidence](../../experiments/python-gamebub-v105/native-audit.json)
retains terminal outcomes, capacity, primitive RAM/DSP properties, check_timing,
DRC, methodology and route-status counts for every attempt. The audit's
PASS_EVIDENCE status verifies those records, including any failed outcomes.
The [memory inventory](memory-inventory.md) separates source access semantics
from native primitive properties and external-memory unknowns.
The [measured setup cones](../../experiments/python-gamebub-v105/path-analysis.json)
record each stage's worst reported source/destination, logic/route delay and
logic depth, cross-checked against its timing-summary WNS. They also retain
up to 50 reported paths per stage. Use the actual routed cones and the
[RTL review](next-cone-review.md) to choose V106's fanout/locality experiment.
The [methodology resolution report](METHODOLOGY_RESOLUTION_REPORT.md) records
remaining setup, boundary, RAM/DSP pipeline and configuration obligations,
with the actual per-stage reported findings and zero waivers.

The clock is an OOC comparison target. Parent clock-source/boundary locations,
I/O delays and full-system constraints are unavailable. No missing constraints
were hidden by false paths, waivers or a relaxed comparison clock. The native
OOC warnings and remaining violations are retained. There is no achieved-Fmax,
board timing, complete-path service, hardware 30 fps or complete under-10-ms
decode claim.
