#!/usr/bin/env python3
"""Replay the selected V103 admission trace without an RTL simulator."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/cu66-v103'))
from admission import replay


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    area = ROOT / 'experiments/python-gamebub-v103/admission'
    selected = area / 'results.json'
    selection = json.loads(selected.read_text())
    report_path = ROOT / selection['selected_report']
    report = json.loads(report_path.read_text())
    assert selection['status'] == report['status'] == 'PASS'
    for name, digest in report['source_sha256'].items():
        assert sha(ROOT / name) == digest, ('source changed', name)
    for name, digest in report['artifacts_sha256'].items():
        assert sha(report_path.parent / name) == digest, ('artifact changed', name)
    trace = report_path.parent / report['trace_replay']['path']
    assert sha(trace) == report['trace_replay']['sha256']
    result = dict(replay(trace), selected_report=selection['selected_report'],
        report_sha256=sha(report_path), selection_sha256=sha(selected),
        trace_sha256=sha(trace), candidate=report['candidate'])
    (area / 'trace-audit.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print('V103_ADMISSION_TRACE_AUDIT', result['status'], result['rows'])


if __name__ == '__main__':
    main()
