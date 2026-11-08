#!/usr/bin/env python3
"""Exhaust actual RTL expressions from an exact full-production source edit."""
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
FPGA = ROOT / 'fpga/experiments/cu66-v107-value-check'
AREA = ROOT / 'experiments/python-gamebub-v107/value-check'
sys.path.insert(0, str(ROOT / 'scripts/cu66-v100'))
from run_rtl import resources


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    recipe = json.loads((FPGA / 'edit-recipe.json').read_text())
    for key in ('original', 'candidate'):
        assert sha(ROOT / recipe[key]['path']) == recipe[key]['sha256']
    old = (ROOT / recipe['original']['path']).read_text()
    assert old.count(recipe['before']) == 1
    assert old.replace(recipe['before'], recipe['after'], 1) == (ROOT / recipe['candidate']['path']).read_text()
    probe = (FPGA / 'value_check_probe.sv').read_text()
    assert 'assign baseline_bad=in_qscale==3||' + recipe['before'] + ';' in probe
    assert 'assign candidate_bad=in_qscale==3||' + recipe['after'] + ';' in probe
    for bits in range(65536):
        signed = bits if bits < 32768 else bits - 65536
        assert ((bits >> 11) in (0, 31) or bits == 2048) == (-2048 <= signed <= 2048)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = AREA / 'attempts' / stamp
    out.mkdir(parents=True)
    build = Path('/home/lori/gamebub-build/cu66-v69') / ('v107-value-' + stamp)
    build.mkdir()
    mapped = '/build/' + build.name
    files = [*(p for p in FPGA.iterdir() if p.is_file()), Path(__file__).resolve(), ROOT / recipe['original']['path']]
    result = dict(status='FAIL', schema='v107-exhaustive-signed16-rtl-expression-v1',
        source_sha256={str(p.relative_to(ROOT)): sha(p) for p in files},
        candidate=recipe['candidate'], model_binary_values=65536, commands=[],
        full_module_RTL_run=False, actual_expression_RTL_run=False,
        limits=['Two-state exact expression proof, not four-state or formal equivalence.',
                'Full production body changes one expression only; complete-pipeline integration tests required separately.',
                'No timing/FPS/hardware conclusion from expression simulation.'])
    began = time.monotonic()
    def command(argv, name, cap):
        item = dict(argv=argv, timeout_seconds=cap, resource_gate=resources())
        result['commands'].append(item)
        with (out / name).open('w') as log:
            proc = subprocess.run(argv, stdout=log, stderr=subprocess.STDOUT, cwd=ROOT, timeout=cap+10)
        item['exit_code'] = proc.returncode
        assert proc.returncode == 0, name
    try:
        for p in files:
            dest = out / 'sources' / p.relative_to(ROOT)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, dest)
        snap = out / 'sources' / FPGA.relative_to(ROOT)
        command(['docker', 'exec', 'gamebub-cu66-v69-build', 'timeout', '--kill-after=5s', '120s',
                 'verilator', '--cc', '--exe', '--build', '-j', '2', '--assert', '-Wall',
                 '--language', '1800-2017', '--top-module', 'value_check_probe', '--Mdir', mapped,
                 '-CFLAGS', '-std=c++17 -O2 -Wall -Wextra -Werror',
                 str(snap / 'value_check_probe.sv'), str(snap / 'tb_value.cpp')], 'compile.log', 120)
        assert '%Warning-' not in (out / 'compile.log').read_text()
        command(['docker', 'exec', 'gamebub-cu66-v69-build', 'timeout', '30s', mapped + '/Vvalue_check_probe'], 'simulation.json', 30)
        verdict = json.loads((out / 'simulation.json').read_text())
        assert verdict == dict(status='TEST_PASS', vectors=262144)
        result.update(status='PASS_EXACT_RANGE_RECODE', actual_expression_RTL_run=True, verdict=verdict)
        assert result['source_sha256'] == {str(p.relative_to(ROOT)): sha(p) for p in files}
    finally:
        result['wall_seconds'] = time.monotonic()-began
        result['artifacts_sha256'] = {str(p.relative_to(out)): sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
        (out / 'receipt.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
        (AREA / 'results.json').write_text(json.dumps(dict(result, selected_receipt=str((out/'receipt.json').relative_to(ROOT))), indent=2, sort_keys=True)+'\n')
        print('V107_VALUE_CHECK', result['status'], flush=True)
    assert result['status'] == 'PASS_EXACT_RANGE_RECODE'


if __name__ == '__main__':
    main()
