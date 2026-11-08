#!/usr/bin/env python3
"""Summarize retained native methodology findings; never edits constraints."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v107'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    summary=json.loads((AREA/'summary.json').read_text())
    audit=json.loads((AREA/'audit/baseline-audit.json').read_text())
    selected=summary['selected']['variant']
    item=next(x for x in audit['native_builds']['attempts'] if x['variant']==selected)
    route=item['route'];t=route['summary']
    receipt_path=ROOT/item['path']/'receipt.json'
    receipt=json.loads(receipt_path.read_text())
    build=Path(receipt['build_external'])
    setup_disposition=('Internal component setup passes in this completed route; clean-repeat and parent qualification remain open.' if summary['decoder_100MHz'] else 'OPEN. Exact RTL rewrites, tuple staging and mapped table changes target actual reported cones. Negative setup remains unresolved.')
    text=f'''# V107 methodology resolution report

Design: `cs88_pipeline_v91k`, component out-of-context on `xc7a100tcsg324-1`.
Tool: Vivado 2026.1 build 6511674. Selected measured frontier: `{selected}`.

The unchanged comparison clock is **10.000 ns / 100 MHz**. Routed WNS is
**{t['WNS_ns']:+.3f} ns** with **{t['setup_failing']:,} failing setup endpoints**.
Hold slack is {t['WHS_ns']:+.3f} ns and pulse-width slack {t['WPWS_ns']:+.3f} ns.
The decoder timing target is {'met for internal component paths' if summary['decoder_100MHz'] else 'NOT MET'}.
The evidence audit verifies reports; it does not waive negative slack.

## Native reports and constraints

The [selected receipt](../../{item['path']}/receipt.json) and
[comparison](vendor-comparison.md) bind read-only source snapshots, input map,
Tcl/XDC, exact tool command, logs, stage reports and final checkpoint hash.
The native source list and 10 ns constraint load before synthesis. There are
no valid decoder timing exceptions. Board input/output delays remain open
because the component comparison has no external board timing contract.
No clock, path or endpoint was excluded to manufacture a timing pass.

Report commands include `check_timing`, `report_timing_summary -delay_type
min_max -report_unconstrained`, setup/hold paths, `report_clocks`, clock
interaction, exceptions, CDC, DRC, methodology JSON/text, routing status,
utilization, memory primitive configuration and high-fanout/control sets.
Both slow and fast timing corners are enabled in the timing summary.

## Findings and disposition

| Finding | Disposition |
| --- | --- |
| Setup timing / TIMING-16 where reported | {setup_disposition} |
| TIMING-18: missing input/output delay | OPEN parent integration requirement. No guessed board delay or waiver was added to the OOC decoder. |
| SYNTH-5: distributed RAM mapping | Inspect actual inferred primitives, fanout and route delay. The table candidates use actual mapped/UNISIM checks; this advisory is not automatically waived. |
| SYNTH-6: potentially suboptimal RAM timing | OPEN where retained; inspect actual RAM read/write/output registers and collision behavior before changing structure. |
| DSP DPIP/DPOP advisories | OPEN where retained. IDCT/dequant remain exact. A pipeline change needs full tuple, cancellation and canonical qualification. |
| CFGBVS | OPEN board-level electrical configuration. The OOC component has no board configuration-voltage contract. |
| OOC HD.CLK_SRC/PARTPIN or routing advisories | Retained as reported; no invented clock location or board constraint was supplied. Complete routable-net status is independently checked. |
| Single-clock decoder CDC report | Applies only to this component. It cannot establish production board CDC/reset signoff. |

Actual selected route rule counts:

'''
    for kind in ('methodology','drc'):
        text+='### '+kind+'\n\n'
        for rule,data in route[kind]['by_rule'].items():
            text+=f"- `{rule}`: {data['severity']}, {data['reported']} reported.\n"
        text+='\n'
    text+='''## Separate CDC repair and remaining integration

The isolated reset-safe CDC experiment routes with WNS +2.078 ns, hold +0.027 ns
and pulse +2.000 ns. Per-FIFO synchronizer notification and synchronous local
RAM address/control reset remove the observed CDC-11 fanout hazards and
REQP-1839/1840 asynchronous RAM-control findings. Its actual Gray crossings use
bounded datapath and bus-skew constraints, without blanket clock groups that
would override those bounds. Remaining generic Gray CDC-6 warnings and the
reset-combination finding require parent review; this is not metastability or
board signoff. See [CDC source/rate and native evidence](cdc-sync.md).

The production parent still uses legacy JPEG. CU66 transport/reference/memory,
publication, LCD buffering and real interface contracts are not implemented
in the new experimental fabric. The pixel FIFO repair delivers only 0.5 word
per receiving clock; it is not a sufficient direct native-scanout replacement.
Preserve the existing related DDR capture clock and qualify actual clocks,
reset recovery/removal, external delays and electrical configuration at parent
integration.

## Resolution boundary and next work

The selected decoder source is a measured implementation frontier. A clean
repeat, full parent fit, real clock/interface qualification, sustained hardware
30 fps and complete validated decoding below 10 ms remain open. No Fmax is
inferred from a negative or single routed slack. Follow the measured remaining
cones rather than adding timing exceptions or launching an unbounded strategy
sweep.

'''
    text+=f"Source receipt SHA-256: `{sha(receipt_path)}`.\n"
    portable=ROOT/'docs/cu66-v107/METHODOLOGY_RESOLUTION_REPORT.md'
    portable.write_text(text)
    assert build.is_dir()
    (build/'METHODOLOGY_RESOLUTION_REPORT.md').write_text(text)
    record=dict(schema='v107-methodology-resolution-v1',selected_variant=selected,
        selected_receipt=str(receipt_path.relative_to(ROOT)),selected_receipt_sha256=sha(receipt_path),
        report=str(portable.relative_to(ROOT)),report_sha256=sha(portable),
        external_design_report=str(build/'METHODOLOGY_RESOLUTION_REPORT.md'),
        external_report_sha256=sha(build/'METHODOLOGY_RESOLUTION_REPORT.md'),
        target_met=summary['decoder_100MHz'],constraints_modified=False,waivers_created=False,
        full_parent_signoff=False,hardware_30fps=False,complete_under10ms=False)
    (AREA/'methodology-resolution.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
    print(json.dumps(record))


if __name__=='__main__':main()
