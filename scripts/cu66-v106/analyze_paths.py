#!/usr/bin/env python3
"""Extract measured worst setup cones for the next locality/fanout iteration."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v106'


def pin(path):
    return dict(path=str(path.relative_to(ROOT)),
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def parse_path(block):
    source = re.search(r'^  Source:\s+(\S+)', block, re.M)
    dest = re.search(r'^  Destination:\s+(\S+)', block, re.M)
    slack = re.search(r'^Slack \([A-Z]+\)\s*:\s*(-?[\d.]+)ns', block)
    delay = re.search(r'^  Data Path Delay:\s+([\d.]+)ns\s+\(logic ([\d.]+)ns.*?route ([\d.]+)ns', block, re.M)
    levels = re.search(r'^  Logic Levels:\s+(\d+)\s+\(([^\n]+)\)', block, re.M)
    assert source and dest and slack and delay and levels, 'missing native timing fields'
    values = list(map(float, delay.groups()))
    # Vendor fields are printed to 1 ps; permit only their rounding difference.
    assert abs(values[0] - values[1] - values[2]) <= 0.002
    return dict(source=source[1], destination=dest[1],
                setup_slack_ns=float(slack[1]), data_path_delay_ns=values[0],
                logic_delay_ns=values[1], route_delay_ns=values[2],
                logic_levels=int(levels[1]), reported_primitive_levels=levels[2])


def extract(path, expected_wns):
    text = path.read_text()
    starts = [m.start() for m in re.finditer(r'^Slack \(', text, re.M)]
    assert 1 <= len(starts) <= 50, ('unexpected report_timing coverage', path)
    ends = starts[1:] + [len(text)]
    paths = [parse_path(text[a:b]) for a, b in zip(starts, ends)]
    assert paths[0]['setup_slack_ns'] == expected_wns, ('worst path/summary mismatch', path)
    assert all(row['setup_slack_ns'] >= expected_wns for row in paths)
    return dict(report=pin(path), **paths[0], reported_path_count=len(paths),
                reported_paths=paths,
                report_scope='At most 50 reported worst setup paths; not exhaustive endpoint coverage.')


def main():
    path = AREA / 'native-audit.json'
    native = json.loads(path.read_text())
    assert native['status'] == 'PASS_EVIDENCE'
    rows = []
    baseline = native['V105_control']
    for stage, value in baseline['stages'].items():
        report = ROOT / Path(baseline['receipt']).parent / 'reports' / (stage + '-setup-paths.rpt')
        rows.append(dict(variant='V105_control', stage=stage,
                         **extract(report, value['timing']['WNS_ns'])))
    for name, attempt in native['measured_variants'].items():
        for stage, value in attempt.get('stages', {}).items():
            report = ROOT / Path(attempt['path']).parent / 'reports' / (stage + '-setup-paths.rpt')
            rows.append(dict(variant=name, stage=stage,
                             **extract(report, value['timing']['WNS_ns'])))
    out = dict(schema='v106-measured-setup-cones-v1', status='PASS_EVIDENCE',
               native_audit=pin(path), analyzer=pin(Path(__file__)),
               rows=rows,
               scope='First/worst cone cross-checked against each stage summary, with at most 50 reported setup paths per stage. Not exhaustive endpoint coverage. Synthesis/place estimates and routed component results remain separate. No causal cone-removal, achieved Fmax, parent-clock or hardware claim.')
    (AREA / 'path-analysis.json').write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
    print('V106_PATH_ANALYSIS_PASS', len(rows), 'stage-matched cones')


if __name__ == '__main__':
    main()
