#!/usr/bin/env python3
"""Run all four immutable histories against one prebuilt monitored RTL model.

Each process resets once at its own independent history boundary. There is no
reset between sources in a history, and repeated sources are not manufactured
to stand in for a longer sustained campaign.
"""
import argparse
import concurrent.futures
import hashlib
import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'fpga/experiments/cu66-v79/campaign'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workers', type=int, choices=range(1, 5), default=4)
    args = parser.parse_args()
    AREA.mkdir(exist_ok=True)
    index = ROOT / 'experiments/cu66-native-v69/index.tsv'
    counts = {}
    for line in index.read_text().splitlines():
        cohort = int(line.split('\t')[0])
        counts[cohort] = counts.get(cohort, 0) + 1
    assert counts == {0: 119, 1: 119, 2: 119, 3: 100}, counts
    runner = ROOT / 'scripts/cu66-v79/run_system.py'
    pins = {str(p.relative_to(ROOT)): sha(p) for p in (index, runner, Path(__file__).resolve())}
    started = time.monotonic()
    results = []

    def run(cohort):
        command = ['python3', str(runner), '--cohort', str(cohort), '--frames', 'full',
                   '--mode', 'fixed30', '--tac', '2', '--skip-build']
        output = AREA / f'cohort{cohort}.log'
        begin = time.monotonic()
        with output.open('w') as stream:
            process = subprocess.run(command, cwd=ROOT, stdout=stream,
                                     stderr=subprocess.STDOUT, timeout=10800)
        return dict(cohort=cohort, requested_sources=counts[cohort], command=command,
                    exit_code=process.returncode, wall_seconds=time.monotonic()-begin,
                    log=str(output.relative_to(ROOT)), sha256=sha(output))

    # Read-only runtimes share a prebuilt binary, never concurrent make processes.
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(run, cohort): cohort for cohort in sorted(counts)}
        for future in concurrent.futures.as_completed(futures):
            cohort = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                result = dict(cohort=cohort, requested_sources=counts[cohort],
                              exit_code=None, error=repr(exc))
            results.append(result)
            print(json.dumps(result), flush=True)
    assert pins == {name: sha(ROOT/name) for name in pins}, 'campaign inputs changed'
    passed = len(results) == 4 and all(r['exit_code'] == 0 for r in results)
    data = dict(schema='cu79-history-campaign-v1',
                status='PASS_ALL_REQUESTED_HISTORIES' if passed else 'FAIL_RETAINED_HISTORIES',
                requested_sources=sum(counts.values()), workers=args.workers,
                wall_seconds=time.monotonic()-started, cases=sorted(results, key=lambda r:r['cohort']),
                source_sha256=pins,
                limitations=['Four independent histories, not one continuous457-source stream',
                             'Not the1800-distinct-source60s or18000-source600s qualification',
                             'No target Fmax/fit/CDC, liveESP32 or charged CPU HUD cost'])
    (AREA/'results.json').write_text(json.dumps(data, indent=2)+'\n')
    print('V79_CAMPAIGN_PASS' if passed else 'V79_CAMPAIGN_FAIL', flush=True)
    if not passed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
