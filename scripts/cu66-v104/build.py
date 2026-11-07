#!/usr/bin/env python3
"""Prepare a source-pinned V104 variant and optionally run the tested native flow."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from regress import OVERRIDES, BASELINE, BASELINE_OVERRIDES

FLOW = ROOT / 'fpga/experiments/cu66-v104-flow'
BUILD_ROOT = Path('/home/lori/gamebub-build/cu66-v69')
FROZEN = ROOT / 'fpga/experiments/cu66-v100-baseline/frozen-inputs.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--variant', choices=['baseline', *OVERRIDES], required=True)
    ap.add_argument('--synth-only', action='store_true')
    ap.add_argument('--run', action='store_true')
    ap.add_argument('--timeout', type=int, default=1800)
    ap.add_argument('--license-file', type=Path, default=Path('/home/lori/acorn-nexys4-ddr/cache/vivado.lic'))
    args = ap.parse_args()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-' + uuid.uuid4().hex[:6]
    build = BUILD_ROOT / ('v104-' + args.variant + '-' + stamp)
    build.mkdir(parents=True, exist_ok=False)
    manifest = json.loads(FROZEN.read_text())
    overrides = {**BASELINE_OVERRIDES, **OVERRIDES.get(args.variant, {})}
    hashes, origins = {}, {}
    for name in manifest['rtl_sources'] + manifest['include_headers']:
        assert sha(ROOT / name) == manifest['source_sha256'][name], ('historical source changed', name)
        original_bytes = subprocess.check_output(['git', 'show', BASELINE + ':' + name], cwd=ROOT)
        assert hashlib.sha256(original_bytes).hexdigest() == sha(ROOT / name)
        baseline_source = BASELINE_OVERRIDES.get(name, name)
        assert hashlib.sha256(subprocess.check_output(['git', 'show', BASELINE + ':' + baseline_source], cwd=ROOT)).hexdigest() == sha(ROOT / baseline_source)
        source = ROOT / overrides.get(name, name)
        target = build / 'snapshot' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        hashes[name] = sha(target)
        origins[name] = dict(path=str(source.relative_to(ROOT)), sha256=sha(source))
    for name in ('run.tcl', 'report.tcl', 'component.xdc'):
        shutil.copyfile(FLOW / name, build / name)
    mapped = Path('/build') / build.relative_to(BUILD_ROOT)

    def word(value):
        value = str(value)
        assert not any(x in value for x in '{}\r\n')
        return '{' + value + '}'

    commands = ['set part xc7a100tcsg324-1', 'set synth_only ' + ('1' if args.synth_only else '0'),
        'set rtl_sources [list ' + ' '.join(word(mapped / 'snapshot' / n) for n in manifest['rtl_sources']) + ']',
        'set include_dirs [list ' + ' '.join(word(mapped / 'snapshot' / n) for n in manifest['include_directories']) + ']',
        'set constraint_file ' + word(mapped / 'component.xdc')]
    (build / 'inputs.tcl').write_text('\n'.join(commands) + '\n')
    inputs = dict(schema='v104-prepared-ooc-inputs-v1', variant=args.variant,
        baseline_revision=BASELINE, frozen_manifest=str(FROZEN.relative_to(ROOT)),
        frozen_manifest_sha256=sha(FROZEN), source_sha256=hashes, source_origins=origins,
        source_overrides=overrides, baseline_overrides=BASELINE_OVERRIDES, synth_only=args.synth_only,
        recipe_sha256={n: sha(build / n) for n in ('run.tcl', 'report.tcl', 'component.xdc', 'inputs.tcl')},
        constraints='Same V101 10ns OOC comparison clock, no fabricated I/O timing/exceptions',
        hardware_or_full_custom_top_qualified=False)
    (build / 'inputs.json').write_text(json.dumps(inputs, indent=2, sort_keys=True) + '\n')
    print('V104_PREPARED', args.variant, build, flush=True)
    if args.run:
        subprocess.run([sys.executable, str(FLOW / 'run_vivado2026.py'), '--build', str(build),
            '--license-file', str(args.license_file), '--timeout', str(args.timeout)], check=True)


if __name__ == '__main__':
    main()
