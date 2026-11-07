#!/usr/bin/env python3
"""Bind the independent byte/RGB/pin audit, probe RTL test and Python model."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v91l-burst-converter'
SHARED=['docs/gamebub-application-specific-codec-plan.md',
        'docs/gamebub-v91-v110-development-plan.md',
        'docs/literature-review-2026-11-06/README.md']
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()
def read(path): return json.loads(path.read_text())
def fresh(report,path):
    for name,digest in report['source_sha256'].items():
        assert sha(ROOT/name)==sha(path.parent/'sources'/name)==digest,name
    for name,digest in report['artifacts_sha256'].items():
        assert sha(path.parent/name)==digest,name
    for name,digest in report.get('inputs_sha256',{}).items():
        assert sha(ROOT/name)==sha(path.parent/'inputs'/Path(name).name)==digest,name
    assert all(c['exit_code']==0 for c in report['commands'])
def main():
    audit=read(AREA/'audit.json')
    assert audit['status']=='PASS_INDEPENDENT_NATIVE_RGB_CANONICAL_BYTES_AND_TIMED_SDRAM_PINS'
    assert audit['verifier_sha256']==sha(AREA/'verify_results.py')
    path=ROOT/audit['selected_report']; assert sha(path)==audit['report_sha256']
    report=read(path); fresh(report,path)
    alias=read(ROOT/'fpga/experiments/cu66-v91l-burst-converter/timed-results.json')
    assert alias==dict(report,selected_report=str(path.relative_to(ROOT)))
    for name,digest in audit['helper_sha256'].items(): assert sha(ROOT/name)==digest,name
    for name,digest in audit['reviewed_source_sha256'].items(): assert sha(ROOT/name)==digest,name
    assert len(audit['modes'])==len(report['modes'])==8
    assert {(m['variant'],m['seed'],m['t_ac_ns']) for m in report['modes']}=={
        (v,s,t) for v in ('scalar','burst') for s in (912701,912702) for t in (2,7)}
    assert len(audit['checker_negative_controls'])==156
    assert all(n['rejected'] for n in audit['checker_negative_controls'])
    assert sum(m['verdict']['checks'] for m in report['modes'])==56
    scalar=[]; burst=[]
    for mode in report['modes']:
        assert len(mode['frames'])==2
        for frame in mode['frames']:
            assert frame['pixels']==345600 and frame['bytes']==691200
            assert frame['logical_reads']==frame['physical_reads']==32400
            assert frame['canonical_consumed']==518400
            if mode['variant']=='burst':
                assert frame['external_byte_leases']==frame['external_byte_returns']==32400
                assert frame['direct_consumes']==486000 and frame['adapter_hits']==0
                burst.append(frame['start_to_closed'])
            else:
                assert frame['external_byte_leases']==frame['external_byte_returns']==518400
                assert frame['direct_consumes']==0 and frame['adapter_hits']==486000
                scalar.append(frame['start_to_closed'])
    assert len(scalar)==len(burst)==8
    compare=audit['matched_comparisons']; assert len(compare)==8
    assert all(c['assumed_100mhz_component_30hz_budget_met'] for c in compare)
    probe_alias=read(ROOT/'fpga/experiments/cu66-v91l-burst-probe/results.json')
    probe_path=ROOT/probe_alias['selected_report']; probe=read(probe_path)
    assert probe_alias==dict(probe,selected_report=str(probe_path.relative_to(ROOT)))
    assert probe['status']=='PASS_DIRECT_PROBE_OWNERSHIP' and probe['hardware_tested'] is False
    fresh(probe,probe_path)
    assert probe['verdict']['checks']>=200 and probe['verdict']['clocks']<400
    model=read(AREA/'hit-model-results.json')
    assert model['status']=='PASS_PYTHON_SOURCE_DERIVED_BYTE_EXACT'
    assert model['generator_sha256']==sha(AREA/'hit_model.py')
    for name,digest in model['source_sha256'].items(): assert sha(ROOT/name)==digest,name
    for name,digest in model['inputs_sha256'].items(): assert sha(ROOT/name)==digest,name
    subprocess.run(['python3',str(AREA/'hit_model.py'),'--check-freshness'],cwd=ROOT,check=True)
    spec=importlib.util.spec_from_file_location('summary_independent_byte_audit',AREA/'verify_results.py')
    oracle=importlib.util.module_from_spec(spec); spec.loader.exec_module(oracle)
    order=b''.join(a.to_bytes(4,'little') for a in oracle.BYTE_SCHEDULE)
    assert hashlib.sha256(order).hexdigest()==model['access_order_sha256']
    assert model['request_service_clock_estimate']['saved_request_service_clocks_per_frame_estimate']==486000
    assert len(model['frames'])==3
    for frame in model['frames'].values():
        assert frame['direct_probe_equals_scalar_byte_for_byte']
        assert frame['direct_probe']['owned_line_hit_consumptions']==486000
        assert frame['direct_probe']['misses_using_existing_byte_lease_and_refill']==32400
    for key in ('shared_service_complete','physical_hardware_tested','sustained_hardware_30fps_proven',
                'validated_full_frame_decode_under10ms_proven'): assert report[key] is False,key
    savings=[100*(c['scalar_cycles']-c['burst_cycles'])/c['scalar_cycles'] for c in compare]
    summary=dict(schema='cu66-v91l-direct-line-summary-v1',status='PASS_DIRECT_LINE_CONSUMPTION_COMPONENT',
        plan_version='V91l partial; V91m not promoted',
        selected_report=str(path.relative_to(ROOT)),report_sha256=sha(path),
        probe_report=str(probe_path.relative_to(ROOT)),probe_report_sha256=sha(probe_path),
        integrity={str(p.relative_to(ROOT)):sha(p) for p in
            (AREA/'audit.json',AREA/'verify_results.py',AREA/'hit_model.py',AREA/'hit-model-results.json')},
        matched_comparisons=compare,scalar_closure_cycles_range=[min(scalar),max(scalar)],
        burst_closure_cycles_range=[min(burst),max(burst)],cycle_reduction_percent_range=[min(savings),max(savings)],
        assumed_source_clock_ns=10,burst_component_ms_range=[min(burst)/100000,max(burst)/100000],
        nominal_request_service_clocks_saved=486000,added_payload_bytes=0,
        frame_canonical_bytes=518400,external_byte_leases_scalar=518400,external_byte_leases_burst=32400,
        direct_consumes_per_native_frame=486000,physical_BL8_reads_per_native_frame=32400,
        static_modes=8,directed_entries=56,exact_complete_base_RGB_outputs=16,
        probe_checks=probe['verdict']['checks'],checker_negative_controls=len(audit['checker_negative_controls']),
        python_source_frames=3,distinct_native_RGB_source_frames=2,
        isolated_assumed_clock_30hz_component_budget_met=True,
        canonical_preload_outside_fences=True,live_codec_common_memory_service_complete=False,
        semantic_HUD_decode_overlay_qualified=False,physical_timing_qualified=False,
        sustained_hardware_30fps_proven=False,complete_validated_decode_under10ms_proven=False,
        next='Join live reconstruction/writes, reference/scratch, hashing/publication and display traffic on one finite controller, preserving this qualified scalar/direct comparison. Close HUD, negotiated profile, ESP32/physical timing and V91m source-cadence gates.')
    (AREA/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    directories=[AREA,ROOT/'fpga/experiments/cu66-v91l-burst-converter',ROOT/'fpga/experiments/cu66-v91l-burst-probe',
                 ROOT/'scripts/cu66-v91l-burst-converter',ROOT/'scripts/cu66-v91l-burst-probe',ROOT/'docs/cu66-v91l-burst-converter']
    files=[p for d in directories for p in d.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='bundle-manifest.json']
    files.extend(ROOT/n for n in SHARED)
    assert len(files)==len(set(files))
    assert all(p.stat().st_size<95*1024*1024 for p in files),'oversized Git artifact'
    manifest=dict(schema='cu66-v91l-direct-line-bundle-v1',files={str(p.relative_to(ROOT)):sha(p) for p in sorted(files)})
    (AREA/'bundle-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(dict(status=summary['status'],files=len(files),cycles=summary['burst_closure_cycles_range'],
                         reduction_percent=summary['cycle_reduction_percent_range'])))
if __name__=='__main__': main()
