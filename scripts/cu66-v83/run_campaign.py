#!/usr/bin/env python3
"""Run the four independent Python histories in parallel and retain every exit."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]


def main():
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = ROOT / 'experiments/python-gamebub-v83/campaigns' / f'session-{stamp}-{uuid.uuid4().hex[:8]}'
    out.mkdir(parents=True)
    started = time.monotonic()
    children = []
    for cohort in range(4):
        command = [sys.executable, 'scripts/cu66-v83/prototype_pipeline.py', '--cohort', str(cohort)]
        stream = (out / f'cohort{cohort}.log').open('w')
        process = subprocess.Popen(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
        children.append((cohort, command, process, stream))
    print('PIPELINE_SESSION', out, flush=True)
    records = []
    for cohort, command, process, stream in children:
        code = process.wait()
        stream.close()
        log = out / f'cohort{cohort}.log'
        lines = log.read_text().splitlines()
        reports = [line.split('PIPELINE_REPORT ', 1)[1].rsplit(' ', 1)[0] for line in lines if line.startswith('PIPELINE_REPORT ')]
        records.append(dict(cohort=cohort, command=command, exit_code=code,
                            log=str(log.relative_to(ROOT)), log_sha256=hashlib.sha256(log.read_bytes()).hexdigest(),
                            report=str(Path(reports[-1]).relative_to(ROOT)) if reports else None))
        print('PIPELINE_COHORT_EXIT', cohort, code, flush=True)
    result = dict(schema='cu66-v83-parallel-session-v1', status='PASS' if all(r['exit_code']==0 for r in records) else 'FAIL',
                  cohorts=records, wall_seconds=time.monotonic()-started,
                  runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (out / 'results.json').write_text(json.dumps(result, indent=2)+'\n')
    print('PIPELINE_SESSION_REPORT', out / 'results.json', result['status'], flush=True)
    return 0 if result['status']=='PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
