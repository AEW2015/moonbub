#!/usr/bin/env python3
"""Render V105 handoff tables from the audited, source-pinned summary."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v105'
DOCS = ROOT / 'docs/cu66-v105'


def table_row(name, stage, value):
    r, t = value['resources'], value['timing']
    return f"| {name} | {stage} | {r['total_LUT']:,} | {r['LUTRAM']:,} | {r['FF']:,} | {r['RAMB36']} / {r['RAMB18']} | {r['DSP']} | {t['WNS_ns']:+.3f} |"


def main():
    summary = json.loads((AREA / 'summary.json').read_text())
    selection = json.loads((AREA / 'selection.json').read_text())
    native = summary['native']
    stages = ('synth', 'place', 'route')
    rows = [table_row('V102 control', stage, native['control']['stages'][stage])
            for stage in stages if stage in native['control']['stages']]
    for variant in native['variants']:
        rows.extend(table_row(variant['variant'], stage, variant['stages'][stage])
                    for stage in stages if stage in variant['stages'])
    comparison = '''# V105 native comparison

Vivado 2026.1 build 6511674 targets `xc7a100tcsg324-1`, using the retained
17-file component closure, a 10 ns clock loaded before synthesis, Default
directives and two tool threads. Each owned build is limited to two CPUs and
8 GiB. The actual host identity and installed read-only license are used.
V102's published reports are the immutable control; V105 does not substitute
a different historical admission or reconstruction source.

| Variant | Stage | LUTs | LUTRAMs | FFs | RAMB36 / RAMB18 | DSPs | WNS (ns) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
''' + '\n'.join(rows) + f'''

The next-study selection is **{selection['selected_variant']}**, with setup WNS
{selection['timing']['WNS_ns']:+.3f} ns and a
{selection['setup_WNS_change_from_V102_ns']:+.3f} ns change from the V102 routed
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
'''
    (DOCS / 'vendor-comparison.md').write_text(comparison)
    a = summary['focused']['admission_verdict']
    m = summary['focused']
    readme = f'''# V105: admission coordinates and memory locality

This partial implementation checkpoint preserves 720×480 video, the
49,152-byte CS88 packet cap and the tested public cycle schedule. It changes
representation and storage inference; it does not change the codec, quality
or measured network bitrate.

The admission candidate replaces repeated active-cell division/modulo with a
reachable-state coordinate cache. Full 32-bit tile/group counters and existing
validation remain. Successful header entry initializes the cache; reset,
replacement start and abort invalidate it. Assertions compare live coordinates
with the original integer function. [Admission evidence](admission-results.md)
covers {a['cases']} retained/mutated packet cases, {a['directed_checks']} directed
checks and {a['clock_edges']:,} clock edges, including dead-cache perturbation
and independent active-cell replay. These are not independent raw gameplay
captures or an arbitrary-state formal equivalence proof.

The memory candidate consolidates five guarded mode writes into a single
synchronous write port and retains the original registered, held lookup.
[Memory evidence](memory-results.md) covers {m['memory_cases']:,} explicitly
prepared cases and {m['memory_clock_edges']:,} edges, all 8,100 valid addresses,
write branches, suppression and output holds. Invalid lookup addresses remain
undefined; physical mapped-netlist collision behavior is not qualified.

Both edit recipes recover their standalone source exactly and produce the
same composed bytes in either order. The module interface is byte-identical.
The eight integrated lanes pass **512 case/profile runs and 576 directed
checks** at seeds 105401/105402, comparing the selected V102 baseline with each
candidate. Transcripts, events, cycle counters and canonical bytes where
applicable are identical. Counts include both implementations, seeds, profiles
and expected rejects; they are not displayed frames or hardware FPS.
Fresh V91j lanes exercise admission, coefficient and inverse-transform stages;
canonical V91k lanes also include reconstruction.

The [native comparison](vendor-comparison.md) measures all five variants.
The selected next-study source is **{selection['selected_variant']}**.
For parent integration, apply `source_overrides` from the
[selection manifest](../../experiments/python-gamebub-v105/selection.json)
to the frozen source list, compiling exactly one production file per module.
The focused probe adapters belong in verification source sets. Requalify the
parent memory/clock/ownership contracts when integrating these component files.
[Machine-readable summary](../../experiments/python-gamebub-v105/summary.json),
[independent source audit](../../experiments/python-gamebub-v105/source-audit.json)
and [baseline audit](baseline-audit.md) retain the exact pins and limitations.
The source audit passes 24/24 checks on two deterministic runs.
Failed bootstrap, compile or resource-gated attempts remain in their ledgers.

Reproduce the source composition and functional matrix from this checkout:

```sh
python3 scripts/cu66-v105/compose.py
python3 scripts/cu66-v105/run_matrix.py
python3 scripts/cu66-v105/audit_sources.py
```

The matrix needs the existing `gamebub-cu66-v69-build` container (Verilator
5.020 and GCC 13.3) with this repository and external `/build` mount visible.
It uses assertions, strict warnings, two compilation jobs, finite timeouts,
available-RAM and memory-pressure gates. Host-side docker-exec timeouts are
retained from the prior runner; a timeout requires checking for an orphaned
container process before retrying. No test timed out in the selected receipts.

Native builds require the existing Vivado/Artix installation and legitimate
license. Run at most two heavy jobs; each native job is capped at 8 GiB and
two CPUs. Do not overlap this five-build sequence with the functional matrix
unless the shared resource policy permits it.

```sh
python3 scripts/cu66-v105/build.py --variant admission --synth-only --run
python3 scripts/cu66-v105/build.py --variant memory --synth-only --run
python3 scripts/cu66-v105/build.py --variant geometry --run
python3 scripts/cu66-v105/build.py --variant combined --run
python3 scripts/cu66-v105/build.py --variant locality --run
python3 scripts/cu66-v105/audit_native.py
python3 scripts/cu66-v105/analyze_paths.py
python3 scripts/cu66-v105/methodology.py --write-external
python3 scripts/cu66-v105/summarize.py
python3 scripts/cu66-v105/render.py
python3 scripts/cu66-v105/bundle_manifest.py --verify
```

Hardware remains on a different system. Whole-device external-memory service,
parent clock/I/O/CDC signoff, complete custom-path integration, sustained
hardware 30 fps and validated complete FPGA decoding below 10 ms remain open.
V106 should use the measured path/fanout/congestion evidence to choose the next
isolated change, while retaining the verified building blocks and exact source
selection from this checkpoint.
'''
    (DOCS / 'README.md').write_text(readme)
    print('V105_DOCS_RENDERED')


if __name__ == '__main__':
    main()
