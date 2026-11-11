#!/usr/bin/env python3
"""Summarize the retained top-50 routed setup paths; does not run Vivado."""
import hashlib
import json
from pathlib import Path
import re
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]
INPUTS = {
    'v128': ('experiments/python-gamebub-v128/native/20261110T215644882105Z/receipt.json',
             '83bbb490ed16e83f0cb68f29bf0d9dc1d7480d1df9da64dbbe4902c131cf286b'),
    'v129': ('experiments/python-gamebub-v129/native/20261111T003938700577Z/receipt.json',
             '5576fa6e190f82f0583d3e1b5e94b50757d31e11822dcc2d62590a071f1f3ab1'),
}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def parse(text):
    blocks = re.split(r'(?=^Slack \()', text, flags=re.M)[1:]
    def get(pattern, block):
        match = re.search(pattern, block, re.M)
        if not match:
            raise ValueError('Missing routed timing field: ' + pattern)
        return match.groups()
    paths = []
    for b in blocks:
        slack, = get(r'^Slack \([^\n]*?:\s*([-+\d.]+)ns', b)
        src, = get(r'^  Source:\s+(\S+)', b)
        dst, = get(r'^  Destination:\s+(\S+)', b)
        total, logic, route = get(r'^  Data Path Delay:\s*([\d.]+)ns\s+\(logic\s+([\d.]+)ns\s+\([\d.]+%\)\s+route\s+([\d.]+)ns', b)
        levels, = get(r'^  Logic Levels:\s+(\d+)', b)
        if src.startswith('base_kill') and '/admission/memory_reg' in dst:
            family = 'kill_to_admission_ram'
        elif 'request_epoch_reg' in src and 'prepared_successor_tile' in dst:
            family = 'scratch_request_epoch_to_successor'
        elif '/parser/' in src and '/parser/' in dst:
            family = 'parser_to_parser'
        elif '/scratch/' in dst:
            family = 'other_to_scratch'
        elif 'prepared_successor_tile' in dst:
            family = 'other_to_successor'
        else:
            family = 'other'
        paths.append(dict(slack_ns=float(slack), source=src, destination=dst,
                          data_ns=float(total), logic_ns=float(logic), route_ns=float(route),
                          logic_levels=int(levels), family=family))
    if len(paths) != 50:
        raise ValueError('Expected exactly 50 reported paths, got ' + str(len(paths)))
    return paths

def main():
    summaries = {}
    for version, (receipt_rel, receipt_hash) in INPUTS.items():
        receipt = ROOT / receipt_rel
        if sha(receipt) != receipt_hash:
            raise ValueError('Receipt changed: ' + version)
        data = json.loads(receipt.read_text())
        if data['status'] != 'COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN':
            raise ValueError('Incomplete route: ' + version)
        report = receipt.parent / 'reports/route-setup-paths.rpt'
        digest = sha(report)
        if digest != data['retained_artifact_sha256']['reports/route-setup-paths.rpt']:
            raise ValueError('Path report hash mismatch: ' + version)
        paths = parse(report.read_text())
        if paths[0]['slack_ns'] != data['result']['timing']['WNS_ns']:
            raise ValueError('Worst path differs from receipt: ' + version)
        groups = defaultdict(list)
        for path in paths:
            groups[path['family']].append(path)
        summaries[version] = dict(receipt=receipt_rel, receipt_sha256=receipt_hash,
            report=str(report.relative_to(ROOT)), report_sha256=digest,
            timing=data['result']['timing'],
            families={k:dict(reported_paths=len(v), worst_slack_ns=min(x['slack_ns'] for x in v),
                             representative=next(x for x in v if x['slack_ns']==min(y['slack_ns'] for y in v)))
                      for k,v in sorted(groups.items())}, paths=paths)
    output = ROOT / 'experiments/python-gamebub-v130/route-families.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(dict(schema='v130-route-family-comparison-v1',
        status='PASS_RETAINED_REPORT_ANALYSIS', script_sha256=sha(Path(__file__)),
        scope='Top 50 paths per run only; not all endpoints or isolated causal experiment.',
        hardware_qualification=False, sources=summaries), indent=2, sort_keys=True) + '\n')
    print(output)

if __name__ == '__main__':
    main()
