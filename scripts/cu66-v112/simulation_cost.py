#!/usr/bin/env python3
"""Measure retained full-Q host cost, never target throughput or cycle accuracy."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'experiments/python-gamebub-v112'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    path = AREA / 'canonical/results.json'
    q = json.loads(path.read_text())
    assert q['status'] == 'PASS_EXACT_V112_CANONICAL' and q['actual_RTL_run']
    selected = ROOT / q['selected_receipt']
    assert json.loads(selected.read_text()) == {k: v for k, v in q.items() if k != 'selected_receipt'}
    bench = ROOT / 'fpga/experiments/cu66-v107-elastic/verification/bench.cpp'
    assert sha(bench) == q['source_sha256'][str(bench.relative_to(ROOT))]
    assert 'd.clk=1;d.eval();++cycle;' in bench.read_text()
    rows = []
    for run in q['runs']:
        seed = run['seed']
        suffix = f'candidate-{seed}-canonical.tsv'
        commands = [c for c in q['commands'] if c['argv'][-1].endswith('/' + suffix)]
        assert len(commands) == 1 and commands[0]['exit_code'] == 0
        command = commands[0]
        elapsed = command['wall_seconds']
        cycles = run['verdict']['clock_edges']
        rate = cycles / elapsed
        rows.append(dict(seed=seed, clock_steps=cycles, command_wall_seconds=elapsed,
                         simulated_clock_steps_per_host_second=rate,
                         host_seconds_per_assumed_125MHz_simulated_ms=125000 / rate,
                         projected_host_hours_for_60s_at125MHz=7500000000 / rate / 3600,
                         projected_host_days_for_600s_at125MHz=75000000000 / rate / 86400))
    result = dict(schema='v112-actual-component-simulator-cost-v1', status='MEASURED_HOST_COST_CONDITIONAL_PROJECTION_ONLY',
                  qualification=dict(path=str(path.relative_to(ROOT)), sha256=sha(path)),
                  selected_receipt=dict(path=str(selected.relative_to(ROOT)), sha256=sha(selected)),
                  counter_source=dict(path=str(bench.relative_to(ROOT)), sha256=sha(bench),
                                      clock_step='tick evaluates clk=0 then clk=1 and increments cycle once; verdict clock_edges is that counter.'),
                  assumed_scenario_clock_Hz=125000000, actual_host_wall_measurements=rows,
                  actual_60s_system_run=False, actual_600s_system_run=False, hardware_30fps=False,
                  limits=['Measured component bench includes dense event/pixel trace I/O and finite software service helpers.',
                          'Canonical compilation overlapped bounded harness work; late seed execution ran without native synthesis. Each simulation allocation capped at two CPUs/8GiB, compile-j1.',
                          'Projections assume the observed instrumented cost per tick stays constant; complete parent/emulator/bridge may differ substantially.',
                          'No RF timing, MCU silicon cycles, achieved FPGA frequency, system FPS or complete validated-decode latency inferred.',
                          'Projection excludes compile, setup, hashing/compression and fault-campaign overhead.'])
    (AREA / 'simulation-cost.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(rows, sort_keys=True))


if __name__ == '__main__':
    main()
