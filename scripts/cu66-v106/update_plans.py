#!/usr/bin/env python3
"""Reconcile the active plans with completed, audited V106 measurements."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v106'
START, END = '<!-- V106-CHECKPOINT-START -->', '<!-- V106-CHECKPOINT-END -->'


def obj(path):
    return json.loads(path.read_text())


def main():
    summary = obj(AREA / 'summary.json')
    selection = obj(AREA / 'selection.json')
    source = obj(AREA / 'source-audit.json')
    native = obj(AREA / 'native-audit.json')
    assert source['status'] == native['status'] == 'PASS_EVIDENCE'
    assert summary['status'] == 'PARTIAL_IMPLEMENTATION_CHECKPOINT_QUALIFICATION_OPEN'
    for item in summary['audits']:
        assert hashlib.sha256((ROOT / item['path']).read_bytes()).hexdigest() == item['sha256']
    assert hashlib.sha256((AREA / 'selection.json').read_bytes()).hexdigest() == summary['next_study_selection']['sha256']
    name, timing, resources = selection['selected_variant'], selection['timing'], selection['resources']
    paired = summary['paired_regression']
    target_met = summary['qualification']['component_100MHz_internal_timing_target_met']
    verdict = ('The fixed **10 ns / 100 MHz internal component target is met in this single routed result**.'
               if target_met else 'The fixed **10 ns / 100 MHz internal component target remains unmet**.')
    unit = obj(AREA / 'idct-area/unit-synthesis-comparison.json')
    assert unit['status'] == 'UNIT_SYNTHESIS_EVIDENCE_COMPLETE'
    paths = obj(AREA / 'path-analysis.json')['rows']
    selected = [row for row in paths if row['variant'] == name and row['stage'] == 'route']
    if name == 'baseline':
        selected = [row for row in paths if row['variant'] == 'V105_control' and row['stage'] == 'route']
    assert len(selected) == 1
    worst = selected[0]
    followup = ('Next qualify the actual parent clocks, input/output arrival contracts, CDC and shared-memory/display service.'
                if target_met else
                f"The selected route's worst reported path is `{worst['source']}` → `{worst['destination']}` "
                f"({worst['logic_levels']} levels, {worst['data_path_delay_ns']:.3f} ns data delay). Continue measured timing work from this path before treating the component as 100-MHz qualified.")
    documents = [
        ('docs/gamebub-v91-v110-development-plan.md', '**V105 partial checkpoint:', 'cu66-v106/'),
        ('docs/gamebub-application-specific-codec-plan.md', '**V105 partial checkpoint:', 'cu66-v106/'),
        ('docs/literature-review-2026-11-06/README.md', 'V105 implementation follow-up:', '../cu66-v106/'),
    ]
    for relative, anchor, prefix in documents:
        path = ROOT / relative
        text = path.read_text()
        block = f'''{START}
**V106 partial checkpoint: exact datapaths, locality and measured timing.**
The [V106 handoff]({prefix}README.md) retains the 720×480 CS88 q16/all-BR88
profile, 49,152-byte cap, checked canonical pixels and public cycle schedule.
All {len(paired['lanes'])} required paired RTL lanes pass: {paired['total_case_profile_runs']:,}
case/profile runs and {paired['total_directed_checks']:,} directed checks. The independent
source audit passes {len(source['checks'])} checks on two byte-identical executions.
These counts include both implementations, seeds/profiles and expected rejects;
they are not unique displayed frames or hardware FPS.

The selected completed route is `{name}`: {resources['total_LUT']:,} LUTs,
{resources['LUTRAM']:,} LUTRAMs, {resources['FF']:,} FFs,
{resources['RAMB36']} RAMB36 / {resources['RAMB18']} RAMB18 and {resources['DSP']} DSPs,
with WNS {timing['WNS_ns']:+.3f} ns versus V105's −13.124 ns
({selection['setup_WNS_change_from_V105_ns']:+.3f} ns change).
{verdict} Single-route results do not establish implementation robustness.
See the [stage-matched comparison]({prefix}vendor-comparison.md) and
[physical-locality analysis]({prefix}physical-locality.md).

The sixth integration passed its required RTL pair but reached the unchanged
1,800-second build limit after synthesis, before placement/routing completed.
Its synthesis WNS −3.205 ns is not a routed result. A separately audited
[post-route probe]({prefix}postroute-probe.md) on the selected checkpoint
improved WNS to −3.777 ns, with 44,630 failing setup endpoints remaining.
That diagnostic is excluded from the Default-flow source selection; it also
fails the fixed 100 MHz target.

The first IDCT prefetch failed full-top packing and its parser variant failed
strict production lint; its unrun canonical lane is explicitly excluded, never
counted as a pass. A shared-selector repair passes exact clocked/golden tests
and matched standalone synthesis uses only {unit['shared_minus_original_LUTs']:+,} LUTs
versus the original unit, saving {-unit['shared_minus_prefetch_LUTs']:,} versus the first
prefetch. Unit synthesis is separate from complete-pipeline routing. The private
24-bit projection and producer transition model are explicitly model/source
proofs, supplemented by actual integrated RTL checks.

{followup} The [remaining timing plan]({prefix}remaining-timing-plan.md)
records the actual paths and qualifications. Scratch predecode adds an input
capture path whose real parent arrival timing remains open. Parent clock/I/O/
CDC, whole-device fit and memory arbitration/service, complete live integration,
**sustained hardware 30 fps** and **validated complete FPGA decode below 10 ms**
remain open. This implementation iteration adds no codec quality, bitrate,
power or HEVC/AV1 benchmark claim.
{END}

'''
        if START in text:
            start = text.index(START)
            finish = text.index(END, start) + len(END)
            text = text[:start] + block.rstrip() + text[finish:]
        else:
            index = text.index(anchor)
            text = text[:index] + block + text[index:]
        if relative.endswith('gamebub-v91-v110-development-plan.md'):
            lines = []
            for line in text.splitlines():
                if line.startswith('| **V106'):
                    if len(line.split('|')) == 7:
                        line = (f'| **V106** datapaths/locality — **partial** | **Implemented:** exact helper/storage/CSA, guarded parser/ingress paths, IDCT operand selection and all-offset scratch predecode; full guards and ownership retained. '
                                f'| **Measured:** selected `{name}`, {resources["total_LUT"]:,} routed LUTs / WNS {timing["WNS_ns"]:+.3f} ns at fixed 10 ns; required/native/rejected trials explicit. '
                                f'| **Passed:** {len(paired["lanes"])} required paired lanes, {paired["total_case_profile_runs"]:,} case/profile runs, {paired["total_directed_checks"]:,} directed checks; exact public cycles/events/canonical outputs. '
                                '| **Open:** parent input capture/I/O/CDC, whole-system fit/service, hardware 30 fps and validated under 10 ms; internal target status follows actual route, no timing cuts. [Evidence](cu66-v106/README.md). |')
                    else:
                        line = (f'| **V106 — partial** | **Measured datapath and control locality.** Exact private caches, arithmetic/table identities, storage and guard-specific paths with clocked/golden/source proofs; rejected fit/lint point retained. '
                                f'| [V106 evidence](cu66-v106/README.md): {len(paired["lanes"])} required paired lanes; selected `{name}`, WNS {timing["WNS_ns"]:+.3f} ns at 10 ns. Parent clock/input capture, whole-device service and hardware goals remain open. |')
                lines.append(line)
            text = '\n'.join(lines) + '\n'
        path.write_text(text)
    print('V106_ACTIVE_PLANS_UPDATED', name, 'internal100MHz', target_met)


if __name__ == '__main__':
    main()
