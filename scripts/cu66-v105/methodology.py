#!/usr/bin/env python3
"""Record resolved scope and open methodology obligations without waivers."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v105'
DOCS = ROOT / 'docs/cu66-v105'
BUILD_ROOT = Path('/home/lori/gamebub-build/cu66-v69')


def pin(path):
    return dict(path=str(path.relative_to(ROOT)),
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def report(attempts, audit):
    lines = ['# V105 methodology resolution report', '',
        '**Status: component evidence measured; methodology signoff OPEN.**', '',
        'Constraint source: `component.xdc`, line 4. The command is `create_clock -name component_clk -period 10.000 [get_ports clk]`: clock component_clk, period 10 ns, target input port clk. It is loaded before synthesis. Default implementation directives and two tool threads are retained. No comparison clock, exception, waiver, I/O delay or parent clock-source location was fabricated to clear findings.', '',
        '| Variant | Stage | WNS ns | No clock | Unconstrained internal endpoints | Missing input delays | Missing output delays |',
        '| --- | --- | ---: | ---: | ---: | ---: | ---: |']
    for attempt in attempts:
        for stage in ('synth', 'place', 'route'):
            if stage not in attempt.get('stages', {}):
                continue
            value = attempt['stages'][stage]
            checks = value['check_timing']
            lines.append(f"| {attempt['variant']} | {stage} | {value['timing']['WNS_ns']:+.3f} | {checks['no_clock']} | {checks['unconstrained_internal_endpoints']} | {checks['no_input_delay']} | {checks['no_output_delay']} |")
    lines += ['', 'The endpoint numbers above come from check_timing. Methodology rule counts below are the tool-reported summary counts; per-rule enumeration limits have not been qualified.', '',
        '| Variant | Stage | Report | Rule | Severity | Reported count |',
        '| --- | --- | --- | --- | --- | ---: |']
    for attempt in attempts:
        for stage in ('synth', 'place', 'route'):
            if stage not in attempt.get('stages', {}):
                continue
            value = attempt['stages'][stage]
            for kind in ('methodology_reported', 'DRC_reported'):
                for rule, finding in sorted(value[kind]['by_rule'].items()):
                    lines.append(f"| {attempt['variant']} | {stage} | {kind} | {rule} | {finding['severity']} | {finding['reported']} |")
    lines += ['', '## Resolution and remaining work', '',
        '- **TIMING-16 / setup:** real architectural/route work remains. The 10 ns requirement is the fixed experiment target. Read the retained full setup paths and measured logic/route delays; the GEOMETRY route specifically identifies coefficient tile-to-cell validation feeding inverse coefficient-buffer write enable. The separate RTL review records exact source and guard/ownership obligations. Combined/locality path reports remain independent measurements.',
        '- **TIMING-18 / parent boundaries:** check_timing still reports missing external delays. Integrate the actual parent clocks, interface timing and boundary locations before system timing signoff. This OOC component does not establish those contracts.',
        '- **SYNTH-6 / RAM pipeline advisory:** native primitive ledgers retain optional output-register settings. The mode table maps to RAMB18 with the tested logical registered lookup. Any additional primitive output stage needs an explicit latency/ownership change and replay; it is not an attribute-only timing fix.',
        '- **RTGT-1 / RAM retargeting advisory:** keep reported retarget opportunities separate from demonstrated mapping. Additional packet/table/intermediate banking requires actual port, latency and collision proofs plus matched native measurements.',
        '- **DPIP/DPOP / DSP advisories:** report actual AREG/BREG/MREG/PREG settings per primitive and variant. V104 product prefetch is included only in the relevant variants; its local mapping does not qualify every DSP path or prove a system clock gain.',
        '- **CFGBVS/configuration and OOC route/clock-source findings:** actual parent/board configuration and boundary contracts remain integration obligations. No board configuration value or HD.CLK_SRC/HD.PARTPIN_LOCS was guessed.', '',
        'The scope is architectural RTL improvement with bounded behavioral evidence and component native measurements. No finding was waived, downgraded or hidden by a timing cut. The remaining setup/I/O/clock/CDC/configuration obligations prevent methodology, achieved-Fmax, board 30 fps and complete under-10-ms decode signoff.', '',
        f"Native evidence audit: `{audit['path']}`, SHA-256 `{audit['sha256']}`.",
        'It pins each source/constraint/recipe, full report and terminal outcome. PASS_EVIDENCE authenticates evidence, including failures; it does not clear the findings above.', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-external', action='store_true',
                        help='Also write the report in each actual design/build working directory.')
    args = parser.parse_args()
    path = AREA / 'native-audit.json'
    native = json.loads(path.read_text())
    assert native['status'] == 'PASS_EVIDENCE'
    audit = pin(path)
    attempts = [native['measured_variants'][name] for name in sorted(native['measured_variants'])]
    dest = DOCS / 'METHODOLOGY_RESOLUTION_REPORT.md'
    dest.write_text(report(attempts, audit))
    external = []
    if args.write_external:
        for attempt in attempts:
            receipt = json.loads((ROOT / attempt['path']).read_text())
            work = Path(receipt['build_external']).resolve()
            work.relative_to(BUILD_ROOT)
            assert work.is_dir()
            text = report([attempt], audit)
            # Write a relative report name in the actual design cwd, as required
            # by the methodology workflow. No vendor run or checkpoint is opened.
            subprocess.run([sys.executable, '-c',
                "from pathlib import Path; import sys; Path('METHODOLOGY_RESOLUTION_REPORT.md').write_text(sys.stdin.read())"],
                input=text, text=True, cwd=work, check=True)
            external.append(dict(build_external=str(work),
                report='METHODOLOGY_RESOLUTION_REPORT.md', sha256=hashlib.sha256(text.encode()).hexdigest()))
    result = dict(schema='v105-methodology-resolution-record-v1', status='SIGNOFF_OPEN',
                  native_audit=audit, generator=pin(Path(__file__)), report=pin(dest),
                  external_reports_written=external, waivers_or_constraint_edits=False,
                  methodology_DRC_CDC_signed_off=False, hardware_qualified=False)
    (AREA / 'methodology-resolution.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print('V105_METHODOLOGY_RECORDED', len(attempts), 'variants', len(external), 'design cwd reports; SIGNOFF_OPEN')


if __name__ == '__main__':
    main()
