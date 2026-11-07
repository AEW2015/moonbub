#!/usr/bin/env python3
"""Bind independently qualified shared service/native joins and review bundle."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'experiments/python-gamebub-v91l-shared-service'
SHARED=['docs/gamebub-application-specific-codec-plan.md','docs/gamebub-v91-v110-development-plan.md',
        'docs/literature-review-2026-11-06/README.md']
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def read(p):return json.loads(p.read_text())
def fresh(path,report):
    for name,digest in report['source_sha256'].items():assert sha(ROOT/name)==sha(path.parent/'sources'/name)==digest,name
    for name,digest in report['artifacts_sha256'].items():assert sha(path.parent/name)==digest,name
    for name,digest in report.get('inputs_sha256',{}).items():assert sha(ROOT/name)==sha(path.parent/'inputs'/Path(name).name)==digest,name
    assert all(c['exit_code']==0 for c in report['commands'])
def main():
    audit=read(AREA/'audit.json')
    assert audit['status']=='PASS_INDEPENDENT_LIVE_PHYSICAL_WRITE_VALIDATION_AND_SAME_MEMORY_RGB'
    assert audit['verifier_sha256']==sha(AREA/'verify_results.py') and audit['memory_verifier_sha256']==sha(AREA/'memory_audit.py')
    for name,digest in {**audit['helper_sha256'],**audit['reviewed_source_sha256']}.items():assert sha(ROOT/name)==digest,name
    reports=[]
    for kind,alias_name in [('unit','fpga/experiments/cu66-v91l-shared-service/results.json'),('live','fpga/experiments/cu66-v91l-shared-live/results.json')]:
        path=ROOT/audit[kind+'_report'];report=read(path)
        assert sha(path)==audit[kind+'_report_sha256']
        assert read(ROOT/alias_name)==dict(report,selected_report=str(path.relative_to(ROOT)))
        fresh(path,report);reports.append((path,report))
    up,unit=reports[0];lp,live=reports[1]
    assert len(unit['modes'])==2 and {m['t_ac_ns'] for m in unit['modes']}=={2,7}
    assert sum(m['verdict']['checks'] for m in unit['modes'])==178
    assert len(audit['checker_negative_controls'])==20 and all(n['rejected'] for n in audit['checker_negative_controls'])
    assert len(audit['live_modes'])==4 and audit['exact_native_RGB_outputs']==8 and audit['rtl_sha_jobs']==8200
    assert {(m['seed'],m['t_ac_ns']) for m in audit['live_modes']}=={(s,t) for s in (912801,912802) for t in (2,7)}
    samples=[]
    for mode in audit['live_modes']:
        assert len(mode['frames'])==2 and mode['rtl_sha_jobs']==2050 and mode['presented_fids']==[0,1]
        assert mode['physical']['physical_write_words']==560640
        assert mode['physical']['physical_captured_words']==518400
        assert mode['physical']['require_prior_pin_write_for_every_native_read']
        runner=next(m for m in live['modes'] if (m['seed'],m['t_ac_ns'])==(mode['seed'],mode['t_ac_ns']))
        assert len(runner['frames'])==2 and len(runner['live_cases'])==2
        for frame,observed in zip(runner['frames'],mode['frames']):
            assert all(observed[k]==v for k,v in frame.items()),frame['id']
            samples.append(dict(seed=mode['seed'],t_ac_ns=mode['t_ac_ns'],**observed))
    model=read(AREA/'model-results.json');assert model['status']=='PASS'
    for name,digest in model['source_pin']['frozen_inputs'].items():assert sha(ROOT/name)==digest,name
    subprocess.run(['python3',str(AREA/'ownership_model.py'),'--check'],cwd=ROOT,check=True)
    generation=read(AREA/'generation-audit.json')
    assert generation['status']=='PASS_CAPTURE_ONLY_BYTE_IDENTICAL_GENERATION' and generation['verifier_sha256']==sha(AREA/'verify_generation.py')
    for name,digest in {**generation['source_sha256'],**generation['outputs_sha256']}.items():assert sha(ROOT/name)==digest,name
    ranges={}
    for fid in (0,1):
        selected=[f for f in samples if f['fid']==fid]
        ranges[str(fid)]={field:[min(f[field] for f in selected),max(f[field] for f in selected)] for field in
                         ('live_cycles','rgb_cycles','joint_serial_cycles','packet_complete_to_commit_cycles')}
    assert all(f['joint_serial_cycles']*30>100000000 for f in samples),'unexpected serial30Hz result needs review'
    summary=dict(schema='cu66-v91l-shared-service-summary-v1',status='PASS_LIVE_CANDIDATE_WRITE_VALIDATION_AND_SHARED_MEMORY_RGB',
        plan_version='V91l partial; V91m not promoted',
        reports=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p,r in reports],
        integrity={n:sha(AREA/n) for n in ('audit.json','verify_results.py','memory_audit.py','ownership_model.py','model-results.json','generation-audit.json','verify_generation.py')},
        live_frames=samples,cycle_ranges_by_fid=ranges,assumed_source_clock_ns=10,
        modeled_memory_t_ac_ns=[2,7],seeds=[912801,912802],exact_native_base_RGB_outputs=8,distinct_native_source_images=2,
        rtl_SHA_jobs_checked=8200,standalone_checks_per_corner=89,standalone_checks_total=178,checker_corruptions_rejected=20,
        candidate_logical_rows_per_frame=70080,candidate_pin_write_words_per_frame=280320,
        physical_BL8_reads_per_frame=32400,physical_captured_words_per_frame=259200,
        native_pin_write_words=sum(m['physical']['physical_write_words'] for m in audit['live_modes']),
        native_pin_read_words=sum(m['physical']['physical_captured_words'] for m in audit['live_modes']),
        no_canonical_or_pixel_SDRAM_preload=True,actual_live_producer_to_physical_candidate_writes=True,
        actual_C2_HUD_seal_and_atomic_commit=True,actual_RGB_reads_same_physical_model=True,
        bank_roles_and_publication_hold_fences_checked=True,serial_live_commit_then_RGB=True,
        native_overlap_qualified=False,physical_reference_scratch_service_qualified=False,
        full_RTL_HUD_decoder_overlay=False,common_all_client_service_complete=False,
        serial_nominal_30Hz_budget_met=False,achieved_clock_or_routed_timing=False,
        sustained_hardware_30fps_proven=False,complete_validated_decode_under10ms_proven=False,
        next='Move finite logical reference/scratch endpoints onto the same controller; qualify native bank-safe overlap against this serial control, then full HUD/profile, fixed source cadence and Series7 physical/hardware gates.')
    (AREA/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    directories=[AREA,ROOT/'fpga/experiments/cu66-v91l-shared-service',ROOT/'fpga/experiments/cu66-v91l-shared-live',
                 ROOT/'scripts/cu66-v91l-shared-service',ROOT/'scripts/cu66-v91l-shared-live',ROOT/'docs/cu66-v91l-shared-service']
    files=[p for directory in directories for p in directory.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='bundle-manifest.json']
    files.extend(ROOT/n for n in SHARED)
    assert len(files)==len(set(files))
    assert all(p.stat().st_size<95*1024*1024 for p in files),'oversized Git artifact'
    (AREA/'bundle-manifest.json').write_text(json.dumps(dict(schema='cu66-v91l-shared-service-bundle-v1',files={str(p.relative_to(ROOT)):sha(p) for p in sorted(files)}),indent=2)+'\n')
    print(json.dumps(dict(status=summary['status'],files=len(files),ranges=ranges)))
if __name__=='__main__':main()
