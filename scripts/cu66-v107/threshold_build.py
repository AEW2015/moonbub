#!/usr/bin/env python3
"""Prepare a source-pinned V107 variant and optionally run the tested native flow."""
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
from elastic_pipeline import OVERRIDES as ELASTIC_OVERRIDES, BASELINE, BASELINE_OVERRIDES, ADDITIONAL
BASELINE_OVERRIDES = {**BASELINE_OVERRIDES, **ELASTIC_OVERRIDES['elastic']}
OVERRIDES = {'threshold': {
    'fpga/experiments/cu66-v91i2/cs88_admission_v91i2a.sv': 'fpga/experiments/cu66-v107-tables/cs88_admission_v91i2a.sv',
    'fpga/experiments/cu66-v69/inverse/cu66_dequant.sv': 'fpga/experiments/cu66-v107-payload-reset/cu66_dequant.sv',
    'fpga/experiments/cu66-v69/inverse/cu66_idct8x8.sv': 'fpga/experiments/cu66-v107-idct-reset/cu66_idct8x8.sv',
    'fpga/experiments/cu66-v91g2/packed_scratch_v91g2.sv':'fpga/experiments/cu66-v107-count-threshold/packed_scratch_v91g2.sv',
    'fpga/experiments/cu66-v91h/br88_packet_ingress_sync_v91h.sv':'fpga/experiments/cu66-v107-count-threshold/br88_packet_ingress_sync_v91h.sv',
    'fpga/experiments/cu66-v91h/br88_packet_ingress_v91h.sv':'fpga/experiments/cu66-v107-count-threshold/br88_packet_ingress_v91h.sv',
    'fpga/experiments/cu66-v91h/br88_pipeline_v91h.sv':'fpga/experiments/cu66-v107-count-threshold/br88_pipeline_v91h.sv',
    'fpga/experiments/cu66-v91j/cu66_inverse_stream_v91j.sv':'fpga/experiments/cu66-v107-meta-flags/cu66_inverse_stream_v91j.sv',
    'fpga/experiments/cu66-v91k/cs88_pipeline_v91k.sv':'fpga/experiments/cu66-v107-meta-flags/cs88_pipeline_v91k.sv',
    'fpga/experiments/cu66-v107-elastic/cu66_coefficient_elastic.sv':'fpga/experiments/cu66-v107-meta-flags/cu66_coefficient_elastic.sv'}}

FLOW = ROOT / 'fpga/experiments/cu66-v107-flow'
BUILD_ROOT = Path('/home/lori/gamebub-build/cu66-v69')
FROZEN = ROOT / 'fpga/experiments/cu66-v100-baseline/frozen-inputs.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--variant', choices=['baseline', *OVERRIDES], required=True)
    ap.add_argument('--synth-only', action='store_true')
    ap.add_argument('--run', action='store_true')
    ap.add_argument('--timeout', type=int, default=3600)
    ap.add_argument('--license-file', type=Path, default=Path('/home/lori/acorn-nexys4-ddr/cache/vivado.lic'))
    args = ap.parse_args()
    qualification = None
    if args.run:
        qualified_path = ROOT / 'experiments/python-gamebub-v107/threshold-pipeline/results.json'
        checked = json.loads(qualified_path.read_text())
        assert checked['status'] == 'PASS_EXACT_THRESHOLD_CANONICAL' and checked['actual_RTL_run']
        assert len(checked['runs']) == 2 and checked['baseline_reused_actual_RTL']
        for run in checked['runs']:
            assert run['exact_stdout_events_cycles_and_canonical']
        for name, digest in checked['source_sha256'].items():
            assert sha(ROOT / name) == digest, ('payload source drift', name)
        for label in ('payload-reset','idct-reset','guard-dsp','meta-flags','plan-prefix','count-threshold'):
            proof_path=ROOT/('experiments/python-gamebub-v107/'+label+'/results.json')
            proof=json.loads(proof_path.read_text())
            assert proof['status']=='PASS' and proof['actual_RTL_run']
            for name,digest in proof['source_sha256'].items():assert sha(ROOT/name)==digest,name
        unit_path = ROOT / 'experiments/python-gamebub-v107/tables/unit/20261108T051111105011Z/receipt.json'
        unit = json.loads(unit_path.read_text())
        assert unit['status'] == 'PASS_MAPPED_UNISIM_TABLES_COLLISIONS'
        assert unit['source_unchanged'] and unit['exit_code'] == 0
        assert sha(ROOT / unit['source']['path']) == unit['source']['sha256']
        assert unit['source']['path'] in checked['source_sha256']
        assert checked['source_sha256'][unit['source']['path']] == unit['source']['sha256']
        for name, digest in unit['retained_sha256'].items():
            assert sha(unit_path.parent / name) == digest, ('mapped-unit artifact drift', name)
        activation_path=ROOT/'experiments/python-gamebub-v107/coordination/threshold-native-activation.json'
        activation=json.loads(activation_path.read_text())
        policy=json.loads((ROOT/'experiments/python-gamebub-v107/study-policy.json').read_text())
        assert activation['source_limit']==8 and policy['threshold_native_activation']==activation
        assert activation['canonical_qualification']==str(qualified_path.relative_to(ROOT))
        assert activation['canonical_sha256']==sha(qualified_path)
        assert activation['unit_sha256']==sha(ROOT/activation['unit_qualification'])
        assert sha(ROOT/activation['parent_receipt'])==activation['parent_receipt_sha256']
        assert sha(ROOT/activation['parent_setup_report'])==activation['parent_setup_report_sha256']
        qualification = dict(path=str(qualified_path.relative_to(ROOT)), sha256=sha(qualified_path),
            mapped_unit_path=str(unit_path.relative_to(ROOT)), mapped_unit_sha256=sha(unit_path),
            activation_path=str(activation_path.relative_to(ROOT)),activation_sha256=sha(activation_path),
            threshold_native_unit_path=activation['unit_qualification'],threshold_native_unit_sha256=activation['unit_sha256'])
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-' + uuid.uuid4().hex[:6]
    build = BUILD_ROOT / ('v107-' + args.variant + '-' + stamp)
    build.mkdir(parents=True, exist_ok=False)
    manifest = json.loads(FROZEN.read_text())
    overrides = {k: v for k, v in {**BASELINE_OVERRIDES, **OVERRIDES.get(args.variant, {})}.items() if k in set(manifest['rtl_sources']) | {str(ADDITIONAL.relative_to(ROOT))}}
    hashes, origins = {}, {}
    extra = str(ADDITIONAL.relative_to(ROOT))
    for name in manifest['rtl_sources'] + manifest['include_headers'] + [extra]:
        if name != extra:
            assert sha(ROOT / name) == manifest['source_sha256'][name], ('historical source changed', name)
            original_bytes = subprocess.check_output(['git', 'show', BASELINE + ':' + name], cwd=ROOT)
            assert hashlib.sha256(original_bytes).hexdigest() == sha(ROOT / name)
        source = ROOT / overrides.get(name, name)
        target = build / 'snapshot' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        hashes[name] = sha(target)
        origins[name] = dict(path=str(source.relative_to(ROOT)), sha256=sha(source))
    if args.run:
        expected={name:digest for name,digest in checked['source_sha256'].items() if Path(name).suffix in ('.sv','.svh')}
        actual={entry['path']:entry['sha256'] for entry in origins.values()}
        assert len(expected)==18 and expected==actual, ('native/canonical production closure drift', sorted(set(expected)^set(actual)))
    for name in ('run.tcl', 'report.tcl', 'component.xdc'):
        shutil.copyfile(FLOW / name, build / name)
    mapped = Path('/build') / build.relative_to(BUILD_ROOT)

    def word(value):
        value = str(value)
        assert not any(x in value for x in '{}\r\n')
        return '{' + value + '}'

    commands = ['set part xc7a100tcsg324-1', 'set synth_only ' + ('1' if args.synth_only else '0'),
        'set rtl_sources [list ' + ' '.join(word(mapped / 'snapshot' / n) for n in manifest['rtl_sources'] + [extra]) + ']',
        'set include_dirs [list ' + ' '.join(word(mapped / 'snapshot' / n) for n in manifest['include_directories']) + ']',
        'set constraint_file ' + word(mapped / 'component.xdc')]
    (build / 'inputs.tcl').write_text('\n'.join(commands) + '\n')
    inputs = dict(schema='v107-prepared-latency-aware-ooc-inputs-v1', variant=args.variant,
        baseline_revision=BASELINE, frozen_manifest=str(FROZEN.relative_to(ROOT)),
        frozen_manifest_sha256=sha(FROZEN), source_sha256=hashes, source_origins=origins,
        source_overrides=overrides, baseline_overrides=BASELINE_OVERRIDES, synth_only=args.synth_only,
        additional_sources=[extra], RTL_files=len(manifest['rtl_sources'])+1, closure_files=len(hashes),
        behavioral_qualification=qualification, public_cycle_schedule_unchanged=False,
        declared_change='Qualified META plus header-owned eight-edge exact count-ceiling pipeline and staged prefix sums; same public cycles, live blocks/owners/fault priorities retained',
        header_and_tables_zero_extra_cycles_relative_to_elastic=True,
        recipe_sha256={n: sha(build / n) for n in ('run.tcl', 'report.tcl', 'component.xdc', 'inputs.tcl')},
        constraints='Same V101 10ns OOC comparison clock, no fabricated I/O timing/exceptions',
        hardware_or_full_custom_top_qualified=False)
    (build / 'inputs.json').write_text(json.dumps(inputs, indent=2, sort_keys=True) + '\n')
    print('V107_PREPARED', args.variant, build, flush=True)
    if args.run:
        subprocess.run([sys.executable, str(FLOW / 'run_vivado2026.py'), '--build', str(build),
            '--license-file', str(args.license_file), '--timeout', str(args.timeout)], check=True)


if __name__ == '__main__':
    main()
